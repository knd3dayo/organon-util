from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, Sequence

from .assurance import AssuranceLayer
from .extractor import Proposition
from .hypothesis import HypothesisRecord, HypothesisStatus


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    FALSIFIED = "falsified"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    evidence: str = ""
    reason: str = ""


class HypothesisGenerator(Protocol):
    def generate(
        self,
        facts: Sequence[Proposition],
        observations: Sequence[Proposition],
    ) -> Sequence[Proposition]:
        ...


class HypothesisVerifier(Protocol):
    def verify(self, hypothesis: Proposition) -> VerificationResult:
        ...


@dataclass
class DiscoveryReport:
    hypotheses: list[HypothesisRecord] = field(default_factory=list)
    promoted_facts: list[Proposition] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "hypotheses": [
                {
                    "proposition_id": item.proposition.proposition_id,
                    "status": item.status.value,
                    "derived_from": list(item.proposition.derived_from),
                    "verification_method": item.proposition.verification_method,
                    "falsification_condition": item.proposition.falsification_condition,
                    "verification_evidence": item.verification_evidence,
                    "decision_reason": item.decision_reason,
                    "approved_by": item.approved_by,
                }
                for item in self.hypotheses
            ],
            "promoted_fact_ids": [item.proposition_id for item in self.promoted_facts],
        }


class ScientificDiscoveryWorkflow:
    """Observation -> abduction -> falsification -> verification workflow."""

    def __init__(self, assurance_layer: AssuranceLayer) -> None:
        self.assurance_layer = assurance_layer

    def run(
        self,
        *,
        facts: Sequence[Proposition],
        observations: Sequence[Proposition],
        generator: HypothesisGenerator,
        verifier: HypothesisVerifier | None = None,
        approved_by: str = "",
    ) -> DiscoveryReport:
        generated = list(generator.generate(facts, observations))
        report = DiscoveryReport()
        for proposition in generated:
            record = HypothesisRecord(proposition)
            report.hypotheses.append(record)
            assurance = self.assurance_layer.validate([*facts, *observations, proposition])
            blocking = [
                finding
                for finding in assurance.findings
                if finding.severity == "error"
                and proposition.proposition_id in finding.proposition_ids
            ]
            if blocking:
                record.falsify(
                    evidence="assurance",
                    reason="; ".join(finding.message for finding in blocking),
                )
                continue

            record.request_verification()
            if verifier is None:
                continue
            verification = verifier.verify(proposition)
            if verification.status == VerificationStatus.FALSIFIED:
                record.falsify(
                    evidence=verification.evidence,
                    reason=verification.reason or "falsification condition was met",
                )
            elif verification.status == VerificationStatus.VERIFIED:
                record.verify(evidence=verification.evidence)
                if approved_by:
                    report.promoted_facts.append(
                        record.approve_as_fact(approved_by=approved_by)
                    )
            elif verification.status != VerificationStatus.PENDING:
                raise ValueError(f"unsupported verification status: {verification.status}")
        return report