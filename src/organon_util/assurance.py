from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .extractor import Proposition
from .registries import FallacyRegistry, ToposRegistry


@dataclass(frozen=True)
class AssuranceFinding:
    code: str
    message: str
    proposition_ids: tuple[str, ...] = ()
    severity: str = "warning"
    action: str = "pending_review"


@dataclass(frozen=True)
class AssuranceReport:
    passed: bool
    findings: list[AssuranceFinding] = field(default_factory=list)
    accepted_propositions: list[str] = field(default_factory=list)
    pending_propositions: list[str] = field(default_factory=list)
    rejected_propositions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [
                {
                    "code": finding.code,
                    "message": finding.message,
                    "proposition_ids": list(finding.proposition_ids),
                    "severity": finding.severity,
                    "action": finding.action,
                }
                for finding in self.findings
            ],
            "accepted_propositions": self.accepted_propositions,
            "pending_propositions": self.pending_propositions,
            "rejected_propositions": self.rejected_propositions,
        }


class AssuranceLayer:
    """Deterministic local routing before optional OWL/DL reasoning."""

    def __init__(self, topoi: ToposRegistry, fallacies: FallacyRegistry) -> None:
        self.topoi = topoi
        self.fallacies = fallacies

    @classmethod
    def from_config_dir(cls, path: str | Path) -> "AssuranceLayer":
        config_dir = Path(path)
        return cls(
            ToposRegistry.from_yaml(config_dir / "topoi.yml"),
            FallacyRegistry.from_yaml(config_dir / "fallacies.yml"),
        )

    def validate(self, propositions: Iterable[Proposition]) -> AssuranceReport:
        items = list(propositions)
        findings: list[AssuranceFinding] = []
        pending: set[str] = set()
        rejected: set[str] = set()

        for item in items:
            proposition_id = item.proposition_id
            if item.epistemic_status == "Endoxa":
                pending.add(proposition_id)
            elif item.epistemic_status == "Fallacy":
                rejected.add(proposition_id)
                details = item.fallacy_details or {}
                try:
                    finding = self.fallacies.validate_details(details)
                    findings.append(
                        AssuranceFinding(
                            code=finding["fallacy_id"],
                            message=finding["explanation"],
                            proposition_ids=(proposition_id,),
                            severity="error",
                            action=finding["action"],
                        )
                    )
                except KeyError:
                    findings.append(
                        AssuranceFinding(
                            code="unknown_fallacy",
                            message="登録されていないFallacyのため、推論対象から除外する",
                            proposition_ids=(proposition_id,),
                            severity="error",
                            action="pending_review",
                        )
                    )

        for result in self.topoi.evaluate(items):
            findings.append(
                AssuranceFinding(
                    code=result["topoi_id"],
                    message=result["explanation"],
                    proposition_ids=tuple(result["applied_to"]),
                    action="record_context",
                )
            )

        for result in self.fallacies.detect(items):
            proposition_ids = tuple(result["proposition_ids"])
            findings.append(
                AssuranceFinding(
                    code=result["fallacy_id"],
                    message=result["explanation"],
                    proposition_ids=proposition_ids,
                    severity="error",
                    action=result["action"],
                )
            )
            pending.update(proposition_ids)

        fact_groups: dict[tuple[str, str, str, str], list[Proposition]] = {}
        for item in items:
            if item.epistemic_status != "Fact":
                continue
            key = (item.subject, item.predicate, item.modality, item.tense)
            fact_groups.setdefault(key, []).append(item)
        for group in fact_groups.values():
            objects = {item.object for item in group}
            if len(objects) <= 1:
                continue
            ids = tuple(item.proposition_id for item in group)
            findings.append(
                AssuranceFinding(
                    code="fact_conflict",
                    message="同一対象・述語・様相・時制に異なる目的語が存在するため、Fact同士の衝突候補である",
                    proposition_ids=ids,
                    severity="error",
                    action="pending_review",
                )
            )
            pending.update(ids)

        accepted = [
            item.proposition_id
            for item in items
            if item.epistemic_status == "Fact"
            and item.proposition_id not in pending
            and item.proposition_id not in rejected
        ]
        return AssuranceReport(
            passed=not any(finding.severity == "error" for finding in findings),
            findings=findings,
            accepted_propositions=accepted,
            pending_propositions=sorted(pending),
            rejected_propositions=sorted(rejected),
        )