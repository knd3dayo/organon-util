from pathlib import Path

from organon_util.extractor import Proposition
from organon_util.registries import FallacyRegistry, ToposRegistry


ROOT = Path(__file__).parents[1]


def test_proposition_has_modality_tense_and_stable_id():
    proposition = Proposition(
        subject="仕様書",
        predicate="requires",
        object="承認",
        modality="MUST",
        tense="PRESENT",
        claim_type="specification",
    )

    assert proposition.proposition_id.startswith("prop-")
    assert proposition.modality == "MUST"
    assert proposition.tense == "PRESENT"


def test_topos_registry_loads_and_evaluates_scope():
    registry = ToposRegistry.from_yaml(ROOT / "config" / "topoi.yml")
    proposition = Proposition(subject="仕様書", predicate="is_a", object="文書")

    findings = registry.evaluate([proposition])

    assert registry.get("genus_species_scope").category == "scope"
    assert registry.by_category("scope")
    assert findings[0]["topoi_id"] == "genus_species_scope"
    assert findings[0]["subject_scope"] == "文書"
    assert findings[0]["object_scope"] == "仕様書"


def test_fallacy_registry_validates_llm_details():
    registry = FallacyRegistry.from_yaml(ROOT / "config" / "fallacies.yml")

    finding = registry.validate_details(
        {"type": "hasty_generalization", "reason": "1件の報告を全体へ拡張している"}
    )

    assert finding["fallacy_id"] == "hasty_generalization"
    assert finding["action"] == "downgrade_or_request_evidence"
    assert finding["explanation"] == "1件の報告を全体へ拡張している"


def test_fallacy_registry_rejects_unknown_details():
    registry = FallacyRegistry.from_yaml(ROOT / "config" / "fallacies.yml")

    try:
        registry.validate_details({"type": "unknown"})
    except KeyError as error:
        assert "unknown fallacy_id" in str(error)
    else:
        raise AssertionError("unknown fallacy must be rejected")