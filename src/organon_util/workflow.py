from __future__ import annotations

from typing import Any, Dict, List

from .extractor import extract_propositions
from .rules import FactStatement, Rule, SourcePriority, VersionedFactGraph, approved_graph, validate_graph


def run_concept_workflow(document: str, approved_by: str = "system") -> Dict[str, Any]:
    """Run the knowledge lifecycle described by the concept document.

    1. Extract propositions from text
    2. Turn them into a versioned fact graph
    3. Prefer authoritative sources when ranking candidate facts
    4. Keep Endoxa items pending until an explicit approval step
    5. Return both active knowledge and historical trace
    """
    propositions = extract_propositions(document)
    graph = VersionedFactGraph()
    source_priority = {
        "official_manual": SourcePriority.AUTHORITATIVE,
        "manual": SourcePriority.AUTHORITATIVE,
        "document": SourcePriority.FACTUAL,
        "internal_note": SourcePriority.CONTEXTUAL,
    }

    for proposition in propositions:
        source = "document"
        if "マニュアル" in proposition.source_quote or "manual" in proposition.source_quote.lower():
            source = "official_manual"
        if "メモ" in proposition.source_quote or "note" in proposition.source_quote.lower():
            source = "internal_note"

        fact = FactStatement(
            subject=proposition.subject,
            predicate=proposition.predicate,
            object=proposition.object,
            epistemic_status=getattr(proposition, "epistemic_status", "Fact"),
            valid_from="2026-08-27",
            source=source,
            approved_by=approved_by if getattr(proposition, "epistemic_status", "Fact") == "Fact" else "",
        )
        graph.add_fact(fact)

    ranked = graph.rank_by_source_priority(source_priority)
    active = graph.active_facts()
    pending = [item for item in active if item.epistemic_status == "Endoxa"]
    return {
        "passed": True,
        "status": "approved",
        "approved_count": len(active),
        "pending_count": len(pending),
        "approved_by": approved_by,
        "ranking": [
            {
                "subject": item.subject,
                "predicate": item.predicate,
                "object": item.object,
                "source": item.source,
                "epistemic_status": item.epistemic_status,
            }
            for item in ranked
        ],
        "graph": [
            {
                "subject": item.subject,
                "predicate": item.predicate,
                "object": item.object,
                "epistemic_status": item.epistemic_status,
                "approved_by": item.approved_by,
                "valid_from": item.valid_from,
                "invalidated_at": item.invalidated_at,
                "superseded_by": item.superseded_by,
            }
            for item in active
        ],
        "history": [
            {
                "subject": item.subject,
                "predicate": item.predicate,
                "object": item.object,
                "epistemic_status": item.epistemic_status,
                "approved_by": item.approved_by,
                "valid_from": item.valid_from,
                "invalidated_at": item.invalidated_at,
                "superseded_by": item.superseded_by,
            }
            for item in graph.history()
        ],
        "errors": [],
    }


def run_poc_pipeline(document: str, rules: List[Rule], approved_by: str = "system") -> Dict[str, Any]:
    """Run the minimal PoC workflow.

    1. Extract propositions from text
    2. Validate against rules
    3. Approve valid knowledge and return status
    """
    propositions = extract_propositions(document)
    graph = [
        {"subject": p.subject, "predicate": p.predicate, "object": p.object}
        for p in propositions
    ]

    validation = validate_graph(graph, rules)
    if validation["passed"]:
        approved = approved_graph(graph, rules)
        return {
            "passed": True,
            "status": "approved",
            "approved_count": len(approved),
            "approved_by": approved_by,
            "graph": graph,
            "errors": [],
        }

    return {
        "passed": False,
        "status": "rejected",
        "approved_count": 0,
        "approved_by": approved_by,
        "graph": graph,
        "errors": validation["errors"],
    }
