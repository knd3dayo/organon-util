from pathlib import Path

from organon_util.extractor import extract_propositions


def test_concept_doc_generates_rule_candidates():
    text = Path("concept.md").read_text(encoding="utf-8")
    propositions = extract_propositions(text)

    assert len(propositions) > 0

    core_terms = {
        "LLM",
        "生成AI",
        "ハルシネーション",
        "MCP",
        "保証層",
        "Assurance Layer",
        "オントロジー",
        "グラフ",
    }

    matched = sum(
        1
        for p in propositions
        if (p.subject in core_terms or p.object in core_terms)
        and "###" not in p.subject
        and "```" not in p.subject
        and "##" not in p.subject
    )
    assert matched >= 1
    assert not any("###" in p.subject or "##" in p.subject or "```" in p.subject for p in propositions)


def test_concept_doc_classifies_fact_and_endoxa():
    text = Path("concept.md").read_text(encoding="utf-8")
    propositions = extract_propositions(text)

    assert any(getattr(p, "epistemic_status", None) == "Fact" for p in propositions)
    assert any(getattr(p, "epistemic_status", None) == "Endoxa" for p in propositions)
    assert all(getattr(p, "rationale", "") for p in propositions)
    assert all(getattr(p, "source_quote", "") for p in propositions)


def test_versioned_fact_graph_tracks_invalidation_and_replacement():
    from organon_util.rules import FactStatement, VersionedFactGraph

    graph = VersionedFactGraph()
    graph.add_fact(
        FactStatement(
            subject="CRM",
            predicate="uses",
            object="SystemA",
            epistemic_status="Fact",
            valid_from="2024-01-01",
        )
    )
    graph.invalidate_fact(
        subject="CRM",
        predicate="uses",
        object="SystemA",
        invalidated_at="2026-08-27",
        superseded_by="SystemB",
    )

    active = graph.active_facts()
    history = graph.history()

    assert len(active) == 0
    assert any(item.object == "SystemA" for item in history)
    assert any(item.invalidated_at == "2026-08-27" for item in history)
    assert any(item.superseded_by == "SystemB" for item in history)


def test_approval_workflow_promotes_endoxa_to_fact():
    from organon_util.rules import FactStatement, VersionedFactGraph

    graph = VersionedFactGraph()
    graph.add_fact(
        FactStatement(
            subject="CRM",
            predicate="has_property",
            object="高効率",
            epistemic_status="Endoxa",
            valid_from="2026-08-27",
        )
    )

    approved = graph.approve_fact(
        subject="CRM",
        predicate="has_property",
        object="高効率",
        approved_by="alice",
    )

    assert approved is True
    assert any(f.epistemic_status == "Fact" for f in graph.active_facts())
    assert any(f.approved_by == "alice" for f in graph.active_facts())


def test_concept_lifecycle_workflow_extracts_and_tracks_fact_updates():
    from organon_util.extractor import extract_propositions
    from organon_util.rules import FactStatement, VersionedFactGraph

    text = "LLMはハルシネーションを避けられない。MCPは外部知識を動的に注入する。"
    propositions = extract_propositions(text)
    graph = VersionedFactGraph()

    for item in propositions:
        graph.add_fact(
            FactStatement(
                subject=item.subject,
                predicate=item.predicate,
                object=item.object,
                epistemic_status=item.epistemic_status,
                valid_from="2026-08-27",
                approved_by="system",
            )
        )

    old_fact = next(f for f in graph.history() if f.subject == "LLM" and f.predicate == "cannot_avoid")
    graph.approve_fact(subject="LLM", predicate="cannot_avoid", object="ハルシネーション", approved_by="alice")
    graph.invalidate_fact(
        subject="LLM",
        predicate="cannot_avoid",
        object="ハルシネーション",
        invalidated_at="2026-08-28",
        superseded_by="LLMは再評価が必要",
    )

    active = graph.active_facts()
    history = graph.history()

    assert any(p.subject == "LLM" for p in propositions)
    assert any(f.epistemic_status == "Fact" and f.approved_by == "alice" for f in history)
    assert any(f.invalidated_at == "2026-08-28" and f.superseded_by == "LLMは再評価が必要" for f in history)
    assert all(f.subject != "LLM" or f.invalidated_at != "2026-08-28" for f in active)
    assert old_fact in history


def test_source_priority_prefers_authoritative_documents():
    from organon_util.rules import FactStatement, SourcePriority, VersionedFactGraph

    graph = VersionedFactGraph()
    graph.add_fact(
        FactStatement(
            subject="製品マニュアル",
            predicate="describes",
            object="仕様",
            epistemic_status="Fact",
            valid_from="2026-08-27",
            source="official_manual",
        )
    )
    graph.add_fact(
        FactStatement(
            subject="社内メモ",
            predicate="describes",
            object="仕様",
            epistemic_status="Endoxa",
            valid_from="2026-08-27",
            source="internal_note",
        )
    )

    source_priority = {
        "official_manual": SourcePriority.AUTHORITATIVE,
        "internal_note": SourcePriority.CONTEXTUAL,
    }
    ranked = graph.rank_by_source_priority(source_priority)

    assert ranked[0].source == "official_manual"
    assert ranked[0].epistemic_status == "Fact"
    assert any(item.source == "internal_note" for item in ranked)


def test_concept_workflow_prioritizes_authoritative_sources():
    from organon_util.extractor import extract_propositions
    from organon_util.workflow import run_concept_workflow

    text = (
        "LLMはハルシネーションを避けられない。"
        "MCPは外部知識を動的に注入する。"
        "製品マニュアルは仕様を記載する。"
    )
    result = run_concept_workflow(text, approved_by="alice")

    assert result["passed"] is True
    assert result["status"] == "approved"
    assert len(result["graph"]) >= 1
    assert len(result["history"]) >= 1
    assert any(item["approved_by"] == "alice" for item in result["history"])
    assert "assurance" in result
    assert result["assurance"]["passed"] is True


def test_concept_workflow_keeps_endoxa_pending():
    from organon_util.workflow import run_concept_workflow

    result = run_concept_workflow("この評価は懸念である。", approved_by="alice")

    assert result["pending_count"] == 1
    assert result["history"][0]["epistemic_status"] == "Endoxa"
    assert result["history"][0]["approved_by"] == ""
    assert result["assurance"]["pending_propositions"]
    assert result["status"] == "pending"


def test_versioned_fact_graph_serializes_rdf_and_json():
    from organon_util.rules import FactStatement, VersionedFactGraph

    graph = VersionedFactGraph()
    graph.add_fact(
        FactStatement(
            subject="LLM",
            predicate="has_risk",
            object="ハルシネーション",
            epistemic_status="Fact",
            valid_from="2026-08-27",
            source="official_manual",
            approved_by="alice",
        )
    )

    rdf = graph.to_rdf_graph()
    payload = graph.to_json()

    assert rdf.serialize(format="nt")
    assert payload[0]["subject"] == "LLM"
    assert payload[0]["epistemic_status"] == "Fact"
    assert payload[0]["source"] == "official_manual"
