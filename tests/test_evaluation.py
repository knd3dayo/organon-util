from pathlib import Path
import json

from organon_util.evaluation import (
    citation_precision,
    classification_metrics,
    evaluate_assistant,
    load_evaluation_set,
    proposition_key,
    retrieval_metrics,
)
from organon_util.extractor import extract_propositions
from organon_util.qa import KnowledgeAssistant


ROOT = Path(__file__).parents[1]


def test_classification_metrics_counts_precision_recall_and_f1():
    metrics = classification_metrics({"a", "b"}, {"a", "c"})

    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


def test_retrieval_and_citation_metrics():
    retrieved = [
        {"subject": "wrong", "predicate": "is", "object": "first", "proposition_id": "p1"},
        {"subject": "MCP", "predicate": "injects_or_looks_up", "object": "外部知識", "proposition_id": "p2"},
    ]

    metrics = retrieval_metrics({"MCP|injects_or_looks_up|外部知識"}, retrieved, top_k=2)

    assert metrics["recall@2"] == 1.0
    assert metrics["precision@2"] == 0.5
    assert metrics["mrr"] == 0.5
    assert citation_precision({"citations": ["p2", "unknown"]}, retrieved) == 0.5


def test_concept_fixed_evaluation_set_produces_baseline_metrics():
    evaluation_set = load_evaluation_set(ROOT / "tests" / "evaluation" / "concept_quality.json")
    text = (ROOT / "concept.md").read_text(encoding="utf-8")
    assistant = KnowledgeAssistant()
    assistant.add_document(text, document_id="concept.md", source_authority="contextual")

    extracted = extract_propositions(text)
    extraction = classification_metrics(
        {proposition_key(item) for item in evaluation_set["expected_propositions"]},
        {proposition_key(item) for item in extracted},
    )
    retrieval = evaluate_assistant(assistant, evaluation_set["questions"])
    thresholds = evaluation_set["thresholds"]

    assert extraction.recall >= thresholds["extraction_recall"]
    assert retrieval["macro_average"]["recall@5"] >= thresholds["retrieval_recall_at_5"]
    assert retrieval["macro_average"]["citation_precision"] >= thresholds["citation_precision"]
    assert (
        retrieval["macro_average"]["insufficient_evidence_correct"]
        >= thresholds["insufficient_evidence_accuracy"]
    )


def test_fixed_epistemic_and_categorical_evaluation_set():
    dataset = json.loads(
        (ROOT / "tests" / "evaluation" / "epistemic_quality.json").read_text(encoding="utf-8")
    )
    categorical_results = []
    epistemic_results = []
    for case in dataset["cases"]:
        propositions = extract_propositions(case["text"])
        categorical = case.get("expected_categorical_form")
        if categorical:
            categorical_results.append(any(item.categorical_form == categorical for item in propositions))
        epistemic_results.append(
            any(item.epistemic_status == case["expected_epistemic_status"] for item in propositions)
        )

    assert sum(categorical_results) / len(categorical_results) >= dataset["thresholds"]["categorical_accuracy"]
    assert sum(epistemic_results) / len(epistemic_results) >= dataset["thresholds"]["epistemic_accuracy"]