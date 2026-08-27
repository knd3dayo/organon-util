from __future__ import annotations

from typing import Any, Protocol, Sequence

from .assurance import AssuranceFinding, AssuranceLayer, AssuranceReport
from .extractor import Proposition
from .graph import build_rdf_graph


class Reasoner(Protocol):
    def validate(self, propositions: Sequence[Proposition]) -> AssuranceReport:
        ...


class LocalReasoner:
    """Run the deterministic Python assurance rules without an external engine."""

    def __init__(self, assurance_layer: AssuranceLayer) -> None:
        self.assurance_layer = assurance_layer

    def validate(self, propositions: Sequence[Proposition]) -> AssuranceReport:
        return self.assurance_layer.validate(propositions)


class PurePythonReasoner:
    """Apply OWL 2 RL/RDFS entailment and SHACL validation without Java."""

    def infer(self, graph: Any) -> Any:
        try:
            from owlrl import DeductiveClosure, OWLRL_Semantics
        except ImportError as exc:
            raise RuntimeError("Pure Python reasoning requires: pip install 'organon-util'") from exc

        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def validate_graph(self, graph: Any, shapes: Any | None = None) -> dict[str, Any]:
        inferred = self.infer(graph)
        if shapes is None:
            return {"conforms": True, "graph": inferred, "report": ""}

        try:
            from pyshacl import validate
        except ImportError as exc:
            raise RuntimeError("SHACL validation requires: pip install 'organon-util'") from exc

        conforms, report_graph, report_text = validate(
            data_graph=inferred,
            shacl_graph=shapes,
            inference="none",
        )
        return {
            "conforms": bool(conforms),
            "graph": inferred,
            "report_graph": report_graph,
            "report": report_text,
        }

    def validate(self, propositions: Sequence[Proposition]) -> AssuranceReport:
        graph = build_rdf_graph(
            [
                {"subject": item.subject, "predicate": item.predicate, "object": item.object}
                for item in propositions
                if item.epistemic_status == "Fact"
            ]
        )
        self.infer(graph.graph)
        return AssuranceReport(
            passed=True,
            accepted_propositions=[item.proposition_id for item in propositions if item.epistemic_status == "Fact"],
            pending_propositions=[item.proposition_id for item in propositions if item.epistemic_status == "Endoxa"],
            rejected_propositions=[item.proposition_id for item in propositions if item.epistemic_status == "Fallacy"],
        )


class HermiTReasoner:
    """Run HermiT through Owlready2 against a prepared ontology.

    Owlready2 is a Python bridge; HermiT itself remains a Java reasoner and
    therefore requires a compatible Java runtime in the execution environment.
    """

    def __init__(self, ontology: Any) -> None:
        self.ontology = ontology

    def validate(self, propositions: Sequence[Proposition]) -> AssuranceReport:
        del propositions
        try:
            from owlready2 import sync_reasoner
        except ImportError as exc:
            raise RuntimeError("HermiT support requires: pip install 'organon-util[reasoner]'") from exc

        try:
            with self.ontology:
                sync_reasoner()
        except Exception as exc:
            return AssuranceReport(
                passed=False,
                findings=[
                    AssuranceFinding(
                        code="owl_inconsistency",
                        message=f"OWL推論器による大域整合性検証に失敗しました: {exc}",
                        severity="error",
                        action="pending_review",
                    )
                ],
            )
        return AssuranceReport(passed=True)