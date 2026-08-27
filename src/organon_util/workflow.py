from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .assurance import AssuranceLayer
from .extractor import extract_propositions
from .llm import LLMAnswerGenerator, LLMPropositionExtractor
from .qa import KnowledgeAssistant
from .rules import FactStatement, Rule, SourcePriority, VersionedFactGraph, approved_graph, validate_graph
from .source import SourceRecord
from .source_adapter import SourceSearchClient, search_source_records


def run_concept_workflow(document: str, approved_by: str = "system") -> Dict[str, Any]:
    """Run the knowledge lifecycle described by the concept document.

    1. Extract propositions from text
    2. Turn them into a versioned fact graph
    3. Prefer authoritative sources when ranking candidate facts
    4. Keep Endoxa items pending until an explicit approval step
    5. Return both active knowledge and historical trace
    """
    propositions = extract_propositions(document)
    assurance = AssuranceLayer.from_config_dir(Path(__file__).parents[2] / "config")
    assurance_report = assurance.validate(propositions)
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
            modality=getattr(proposition, "modality", "ACTUAL"),
            tense=getattr(proposition, "tense", "PRESENT"),
            claim_type=getattr(proposition, "claim_type", "statement"),
            fallacy_details=getattr(proposition, "fallacy_details", None),
            proposition_id=getattr(proposition, "proposition_id", ""),
            source_record_id=getattr(proposition, "source_record_id", ""),
        )
        graph.add_fact(fact)

    ranked = graph.rank_by_source_priority(source_priority)
    active = graph.active_facts()
    pending = [item for item in active if item.epistemic_status == "Endoxa"]
    accepted_ids = set(assurance_report.accepted_propositions)
    rejected_ids = set(assurance_report.rejected_propositions)
    status = "rejected" if rejected_ids else "pending" if pending else "approved"
    return {
        "passed": True,
        "status": status,
        "approved_count": sum(
            1
            for item in active
            if item.proposition_id in accepted_ids and item.proposition_id not in rejected_ids
        ),
        "pending_count": len(pending),
        "assurance": assurance_report.as_dict(),
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


def run_source_record_workflow(
    record: SourceRecord,
    *,
    query: str = "",
    proposition_extractor: Any | None = None,
    assurance_layer: AssuranceLayer | None = None,
    llm_client: Any | None = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Ingest one SourceRecord and optionally answer a question from it."""
    if proposition_extractor is None:
        if llm_client is None:
            propositions = extract_propositions(record.content)
        else:
            propositions = LLMPropositionExtractor(llm_client).extract(
                record.content,
                source_record=record,
            )
    else:
        propositions = proposition_extractor.extract(record.content, source_record=record)

    for proposition in propositions:
        proposition.source_record_id = record.logical_id
        proposition.source_uri = record.source_uri

    assurance = assurance_layer or AssuranceLayer.from_config_dir(Path(__file__).parents[2] / "config")
    report = assurance.validate(propositions)
    assistant = KnowledgeAssistant()
    assistant.add_propositions(
        propositions,
        document_id=record.source_id,
        source_authority=str(record.metadata.get("source_authority", "contextual")),
        logical_id=record.logical_id,
        source_uri=record.source_uri,
        checksum=record.checksum,
        retrieved_at=record.retrieved_at.isoformat() if record.retrieved_at else "",
    )
    result: Dict[str, Any] = {
        "source": record.as_dict(),
        "propositions": [
            {
                "proposition_id": item.proposition_id,
                "subject": item.subject,
                "predicate": item.predicate,
                "object": item.object,
                "epistemic_status": item.epistemic_status,
                "source_record_id": item.source_record_id,
                "source_uri": item.source_uri,
            }
            for item in propositions
        ],
        "assurance": report.as_dict(),
    }
    if query:
        result["answer"] = assistant.answer(query, top_k=top_k)
        if llm_client is not None:
            retrieved = assistant.search(query, top_k=top_k)
            result["generated_answer"] = LLMAnswerGenerator(llm_client).generate(
                query,
                retrieved,
            )
    return result


def run_search_workflow(
    client: SourceSearchClient,
    query: str,
    *,
    top_k: int = 5,
    proposition_extractor: Any | None = None,
    assurance_layer: AssuranceLayer | None = None,
    llm_client: Any | None = None,
) -> Dict[str, Any]:
    """Search source records and answer using the retrieved evidence."""
    records = search_source_records(client, query, top_k=top_k)
    ingested = [
        run_source_record_workflow(
            record,
            proposition_extractor=proposition_extractor,
            assurance_layer=assurance_layer,
            llm_client=llm_client,
        )
        for record in records
    ]
    propositions = [item for result in ingested for item in result["propositions"]]
    assistant = KnowledgeAssistant()
    for record in records:
        assistant.add_source_record(record)
    answer = assistant.answer(query, top_k=top_k)
    return {
        "query": query,
        "sources": [record.as_dict() for record in records],
        "ingested": ingested,
        "answer": answer,
        "propositions": propositions,
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
