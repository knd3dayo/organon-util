from pathlib import Path

from organon_util.assurance import AssuranceLayer
from organon_util.discovery import (
    ScientificDiscoveryWorkflow,
    VerificationResult,
    VerificationStatus,
)
from organon_util.extractor import Proposition
from organon_util.hypothesis import HypothesisStatus


ROOT = Path(__file__).parents[1]


class Generator:
    def generate(self, facts, observations):
        return [
            Proposition(
                subject="DBロック",
                predicate="causes",
                object="保存エラー",
                epistemic_status="Endoxa",
                claim_type="hypothesis",
                derived_from=[item.proposition_id for item in observations],
                verification_method="トランザクションログを確認する",
                falsification_condition="障害時刻にロック競合が存在しない",
            )
        ]


def workflow():
    return ScientificDiscoveryWorkflow(AssuranceLayer.from_config_dir(ROOT / "config"))


def observation():
    return Proposition(
        subject="利用者A",
        predicate="reports",
        object="保存エラー",
        epistemic_status="Endoxa",
        claim_type="observation",
    )


def test_discovery_keeps_unverified_hypothesis_pending():
    result = workflow().run(facts=[], observations=[observation()], generator=Generator())

    assert result.hypotheses[0].status == HypothesisStatus.VERIFICATION_PENDING
    assert result.promoted_facts == []


def test_discovery_preserves_falsified_hypothesis():
    class Verifier:
        def verify(self, hypothesis):
            return VerificationResult(
                VerificationStatus.FALSIFIED,
                evidence="ロック競合なし",
                reason="反証条件が成立した",
            )

    result = workflow().run(
        facts=[],
        observations=[observation()],
        generator=Generator(),
        verifier=Verifier(),
    )

    assert result.hypotheses[0].status == HypothesisStatus.FALSIFIED
    assert result.hypotheses[0].decision_reason == "反証条件が成立した"


def test_discovery_promotes_only_verified_hypothesis():
    class Verifier:
        def verify(self, hypothesis):
            return VerificationResult(
                VerificationStatus.VERIFIED,
                evidence="障害時刻にロック競合を確認",
            )

    result = workflow().run(
        facts=[],
        observations=[observation()],
        generator=Generator(),
        verifier=Verifier(),
        approved_by="alice",
    )

    assert result.hypotheses[0].status == HypothesisStatus.APPROVED_FACT
    assert result.promoted_facts[0].epistemic_status == "Fact"
    assert result.promoted_facts[0].claim_type == "verified_hypothesis"