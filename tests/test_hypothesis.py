import pytest

from organon_util.extractor import Proposition
from organon_util.hypothesis import HypothesisRecord, HypothesisStatus


def hypothesis() -> Proposition:
    return Proposition(
        subject="DBロック",
        predicate="causes",
        object="保存エラー",
        epistemic_status="Endoxa",
        claim_type="hypothesis",
        derived_from=["prop-observation-1"],
        verification_method="トランザクションログを確認する",
        falsification_condition="障害時刻にロック競合が存在しない",
    )


def test_unverified_hypothesis_cannot_be_approved():
    record = HypothesisRecord(hypothesis())

    with pytest.raises(ValueError, match="verified hypothesis"):
        record.approve_as_fact(approved_by="alice")


def test_verified_hypothesis_can_be_approved_as_fact():
    record = HypothesisRecord(hypothesis())
    record.request_verification()
    record.verify(evidence="障害時刻にロック競合を確認")

    proposition = record.approve_as_fact(approved_by="alice")

    assert record.status == HypothesisStatus.APPROVED_FACT
    assert proposition.epistemic_status == "Fact"
    assert proposition.claim_type == "verified_hypothesis"


def test_falsified_hypothesis_preserves_reason():
    record = HypothesisRecord(hypothesis())

    record.falsify(evidence="競合なし", reason="反証条件が成立した")

    assert record.status == HypothesisStatus.FALSIFIED
    assert record.decision_reason == "反証条件が成立した"


@pytest.mark.parametrize(
    ("form", "quantity", "quality"),
    [
        ("A", "universal", "affirmative"),
        ("E", "universal", "negative"),
        ("I", "particular", "affirmative"),
        ("O", "particular", "negative"),
    ],
)
def test_categorical_form_exposes_quantity_and_quality(form, quantity, quality):
    proposition = Proposition(subject="S", predicate="is_a", object="P", categorical_form=form)

    assert proposition.quantity == quantity
    assert proposition.quality == quality


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("すべての仕様書は文書である。", "A"),
        ("すべての仕様書は公開文書ではない。", "E"),
        ("ある仕様書は文書である。", "I"),
        ("ある仕様書は公開文書ではない。", "O"),
    ],
)
def test_rule_based_extractor_classifies_explicit_categorical_form(text, expected):
    from organon_util.extractor import extract_propositions

    propositions = extract_propositions(text)

    assert propositions
    assert any(item.categorical_form == expected for item in propositions)