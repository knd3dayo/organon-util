from organon_util.contextual_graph import ContextualRDFGraph
from organon_util.extractor import Proposition


def test_contextual_graph_separates_epistemic_named_graphs():
    graph = ContextualRDFGraph()
    propositions = [
        Proposition(subject="仕様書", predicate="is_a", object="文書"),
        Proposition(subject="画面", predicate="has_property", object="複雑", epistemic_status="Endoxa"),
        Proposition(
            subject="DBロック",
            predicate="causes",
            object="障害",
            epistemic_status="Endoxa",
            claim_type="hypothesis",
            verification_method="ログを確認する",
        ),
        Proposition(
            subject="1件",
            predicate="proves",
            object="全体",
            epistemic_status="Fallacy",
            fallacy_details={"type": "hasty_generalization"},
        ),
    ]

    graph.add_propositions(propositions)

    assert graph.graph_size("core") > 0
    assert graph.graph_size("context") > 0
    assert graph.graph_size("hypothesis") > 0
    assert graph.graph_size("fallacy") > 0
    assert "urn:organon:graph:hypothesis" in graph.serialize()


def test_contextual_reasoning_workflow_reasons_over_core_only():
    from organon_util.workflow import run_contextual_reasoning_workflow

    class CapturingReasoner:
        def validate_graph(self, graph):
            self.values = {str(value) for triple in graph for value in triple}
            return {"conforms": True, "report": ""}

    reasoner = CapturingReasoner()
    result = run_contextual_reasoning_workflow(
        [
            Proposition(subject="仕様書", predicate="is_a", object="文書"),
            Proposition(
                subject="画面",
                predicate="has_property",
                object="複雑",
                epistemic_status="Endoxa",
            ),
        ],
        reasoner,
    )

    assert result["passed"] is True
    assert "文書" in reasoner.values
    assert "複雑" not in reasoner.values