from pathlib import Path

from organon_util.source import SourceRecord
from organon_util.workflow import run_source_record_workflow


def test_concept_document_e2e_question_answer():
    document_path = Path(__file__).parents[1] / "concept.md"
    record = SourceRecord(
        logical_id="concept.md#document",
        source_id="concept.md",
        source_uri=document_path.resolve().as_uri(),
        content=document_path.read_text(encoding="utf-8"),
        metadata={"source_authority": "contextual"},
    )

    result = run_source_record_workflow(record, query="外部知識")
    answer = result["answer"]

    assert result["propositions"]
    assert result["assurance"]["passed"] is True
    assert answer["insufficient_evidence"] is False
    assert answer["facts"]
    assert any(item["object"] == "外部知識" for item in answer["facts"])
    assert answer["citations"]
    assert "concept.md" in answer["answer_text"] or "concept.md#document" in answer["answer_text"]
    assert answer["answer_text"].startswith("結論:")


def test_concept_document_e2e_excludes_markdown_examples_and_unknown_query():
    document_path = Path(__file__).parents[1] / "concept.md"
    record = SourceRecord(
        logical_id="concept.md#document",
        source_id="concept.md",
        source_uri=document_path.resolve().as_uri(),
        content=document_path.read_text(encoding="utf-8"),
    )

    result = run_source_record_workflow(record, query="火星基地の請求障害")

    assert result["propositions"]
    assert not any("```" in item["subject"] for item in result["propositions"])
    assert result["answer"]["insufficient_evidence"] is True