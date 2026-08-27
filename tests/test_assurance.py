from pathlib import Path

from organon_util.assurance import AssuranceLayer
from organon_util.extractor import Proposition


ROOT = Path(__file__).parents[1]


def layer() -> AssuranceLayer:
    return AssuranceLayer.from_config_dir(ROOT / "config")


def test_assurance_routes_fact_and_endoxa():
    fact = Proposition(subject="仕様書", predicate="is_a", object="文書")
    endoxa = Proposition(
        subject="仕様書",
        predicate="has_property",
        object="複雑",
        epistemic_status="Endoxa",
    )

    report = layer().validate([fact, endoxa])

    assert report.passed is True
    assert fact.proposition_id in report.accepted_propositions
    assert endoxa.proposition_id in report.pending_propositions


def test_assurance_rejects_fallacy_with_registered_reason():
    fallacy = Proposition(
        subject="顧客1件",
        predicate="has_property",
        object="システム全体が失敗",
        epistemic_status="Fallacy",
        fallacy_details={
            "type": "hasty_generalization",
            "reason": "1件の事例を全体へ拡張している",
        },
    )

    report = layer().validate([fallacy])

    assert report.passed is False
    assert fallacy.proposition_id in report.rejected_propositions
    assert report.findings[0].code == "hasty_generalization"


def test_assurance_detects_fact_conflict_in_same_context():
    first = Proposition(subject="CRM", predicate="uses", object="SystemA")
    second = Proposition(subject="CRM", predicate="uses", object="SystemB")

    report = layer().validate([first, second])

    assert report.passed is False
    assert first.proposition_id in report.pending_propositions
    assert second.proposition_id in report.pending_propositions
    assert any(finding.code == "fact_conflict" for finding in report.findings)


def test_assurance_applies_genus_species_topos():
    proposition = Proposition(subject="仕様書", predicate="is_a", object="文書")

    report = layer().validate([proposition])

    assert any(finding.code == "genus_species_scope" for finding in report.findings)


def test_assurance_detects_particular_to_universal_scope_expansion():
    proposition = Proposition(
        subject="顧客1件",
        predicate="has_issue",
        object="障害",
        modality="MUST",
        tags=["particular", "universal"],
    )

    report = layer().validate([proposition])

    assert report.passed is False
    assert any(finding.code == "particular_to_universal_scope" for finding in report.findings)


def test_fallacy_registry_detects_tagged_fallacies():
    from organon_util.registries import FallacyRegistry

    registry = FallacyRegistry.from_yaml(ROOT / "config" / "fallacies.yml")
    propositions = [
        Proposition(subject="用語", predicate="means", object="意味A", tags=["ambiguous"]),
        Proposition(subject="1件", predicate="proves", object="全体", tags=["particular", "universal"]),
        Proposition(subject="権威者", predicate="claims", object="結論", tags=["authority_only"]),
    ]

    findings = registry.detect(propositions)

    assert {finding["fallacy_id"] for finding in findings} == {
        "equivocation",
        "hasty_generalization",
        "ad_verecundiam",
    }


def test_grounding_resolver_exposes_explicit_lookup_tools():
    from organon_util.mcp_grounding import GroundingResolver

    resolver = GroundingResolver(
        {
            "仕様書": {
                "kind": "document",
                "rule": "requires_approval",
                "source_metadata": {"authority": "authoritative"},
            }
        }
    )

    assert resolver.lookup_entity("未知語")["grounded"] is False
    assert resolver.get_domain_rule("仕様書")["found"] is True
    assert resolver.get_source_metadata("仕様書")["metadata"]["authority"] == "authoritative"