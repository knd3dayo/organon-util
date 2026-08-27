from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .extractor import Proposition


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    VERIFICATION_PENDING = "verification_pending"
    FALSIFIED = "falsified"
    VERIFIED = "verified"
    APPROVED_FACT = "approved_fact"


@dataclass
class HypothesisRecord:
    proposition: Proposition
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    verification_evidence: str = ""
    decision_reason: str = ""
    approved_by: str = ""

    def __post_init__(self) -> None:
        if self.proposition.claim_type != "hypothesis":
            raise ValueError("HypothesisRecord requires claim_type=hypothesis")

    def request_verification(self) -> None:
        if self.status != HypothesisStatus.PROPOSED:
            raise ValueError("only a proposed hypothesis can await verification")
        self.status = HypothesisStatus.VERIFICATION_PENDING

    def falsify(self, *, evidence: str, reason: str) -> None:
        if self.status not in {HypothesisStatus.PROPOSED, HypothesisStatus.VERIFICATION_PENDING}:
            raise ValueError("hypothesis cannot be falsified from its current status")
        self.status = HypothesisStatus.FALSIFIED
        self.verification_evidence = evidence
        self.decision_reason = reason

    def verify(self, *, evidence: str) -> None:
        if self.status not in {HypothesisStatus.PROPOSED, HypothesisStatus.VERIFICATION_PENDING}:
            raise ValueError("hypothesis cannot be verified from its current status")
        if not evidence.strip():
            raise ValueError("verification evidence must not be empty")
        self.status = HypothesisStatus.VERIFIED
        self.verification_evidence = evidence

    def approve_as_fact(self, *, approved_by: str) -> Proposition:
        if self.status != HypothesisStatus.VERIFIED:
            raise ValueError("only a verified hypothesis can be approved as Fact")
        if not approved_by.strip():
            raise ValueError("approved_by must not be empty")
        self.status = HypothesisStatus.APPROVED_FACT
        self.approved_by = approved_by
        self.proposition.epistemic_status = "Fact"
        self.proposition.claim_type = "verified_hypothesis"
        return self.proposition