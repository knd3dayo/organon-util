from organon_util.extractor import extract_propositions
from organon_util.feedback_loop import FeedbackLoop
from organon_util.graph import build_rdf_graph
from organon_util.mcp_grounding import GroundingResolver
from organon_util.rules import Rule, load_rules_from_file, validate_graph
from organon_util.workflow import run_poc_pipeline


def test_extract_propositions_from_document():
    text = "仕様書は承認が必要である。仕様書は文書である。"

    propositions = extract_propositions(text)

    assert len(propositions) >= 2
    assert any(p.predicate == "requires" for p in propositions)
    assert any(p.predicate == "is_a" for p in propositions)


def test_validate_graph_detects_violation():
    rules = [
        Rule(
            rule_id="specification_requires_approval",
            subject="仕様書",
            predicate="requires",
            object="承認",
        )
    ]
    graph = [
        {"subject": "仕様書", "predicate": "requires", "object": "却下"},
    ]

    result = validate_graph(graph, rules)

    assert result["passed"] is False
    assert len(result["errors"]) >= 1


def test_build_rdf_graph_converts_triples():
    triples = [
        {"subject": "仕様書", "predicate": "requires", "object": "承認"},
        {"subject": "仕様書", "predicate": "is_a", "object": "文書"},
    ]

    graph = build_rdf_graph(triples)

    assert len(graph) >= 2
    assert graph.serialize(format="nt")


def test_load_rules_from_yaml_file(tmp_path):
    rule_file = tmp_path / "rules.yml"
    rule_file.write_text(
        "rules:\n  - rule_id: specification_requires_approval\n    subject: 仕様書\n    predicate: requires\n    object: 承認\n",
        encoding="utf-8",
    )

    rules = load_rules_from_file(str(rule_file))

    assert len(rules) == 1
    assert rules[0].rule_id == "specification_requires_approval"


def test_grounding_resolver_returns_context():
    resolver = GroundingResolver(
        {
            "仕様書": {"kind": "document", "rule": "specification_requires_approval"},
            "承認": {"kind": "approval", "rule": "approval_required"},
        }
    )

    result = resolver.resolve("仕様書")

    assert result["kind"] == "document"
    assert result["rule"] == "specification_requires_approval"


def test_feedback_loop_retries_on_validation_failure():
    document = "仕様書は文書である。"
    rules = [
        Rule(
            rule_id="specification_requires_approval",
            subject="仕様書",
            predicate="requires",
            object="承認",
        )
    ]

    loop = FeedbackLoop(max_retries=2)
    result = loop.run(document, rules)

    assert result["passed"] is True
    assert result["status"] == "approved"
    assert result["attempts"] >= 1


def test_run_poc_pipeline_approves_valid_knowledge():
    document = "仕様書は文書である。仕様書は承認が必要である。"
    rules = [
        Rule(
            rule_id="specification_requires_approval",
            subject="仕様書",
            predicate="requires",
            object="承認",
        )
    ]

    result = run_poc_pipeline(document, rules, approved_by="alice")

    assert result["passed"] is True
    assert result["approved_count"] >= 1
    assert result["status"] == "approved"
