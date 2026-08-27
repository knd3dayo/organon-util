from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .extractor import Proposition, extract_propositions
from .qa import KnowledgeAssistant


@dataclass(frozen=True)
class ClassificationMetrics:
    precision: float
    recall: float
    f1: float
    true_positive: int
    false_positive: int
    false_negative: int


def proposition_key(value: Proposition | dict[str, Any]) -> str:
    if isinstance(value, Proposition):
        return "|".join((value.subject, value.predicate, value.object))
    return "|".join(
        (str(value.get("subject", "")), str(value.get("predicate", "")), str(value.get("object", "")))
    )


def classification_metrics(expected: Iterable[str], actual: Iterable[str]) -> ClassificationMetrics:
    expected_set = set(expected)
    actual_set = set(actual)
    true_positive = len(expected_set & actual_set)
    false_positive = len(actual_set - expected_set)
    false_negative = len(expected_set - actual_set)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return ClassificationMetrics(precision, recall, f1, true_positive, false_positive, false_negative)


def retrieval_metrics(
    expected_keys: Iterable[str],
    retrieved: Sequence[dict[str, Any]],
    *,
    top_k: int,
) -> dict[str, float]:
    expected = set(expected_keys)
    ranked = [proposition_key(item) for item in retrieved[:top_k]]
    hits = [index for index, key in enumerate(ranked, start=1) if key in expected]
    recall = len(set(ranked) & expected) / len(expected) if expected else float(not ranked)
    precision = len(set(ranked) & expected) / len(ranked) if ranked else float(not expected)
    reciprocal_rank = 1.0 / hits[0] if hits else 0.0
    return {f"precision@{top_k}": precision, f"recall@{top_k}": recall, "mrr": reciprocal_rank}


def citation_precision(answer: dict[str, Any], retrieved: Sequence[dict[str, Any]]) -> float:
    citations = answer.get("citations", [])
    if not citations:
        return 1.0 if not retrieved else 0.0
    valid_ids = {item.get("proposition_id") for item in retrieved}
    return sum(citation in valid_ids for citation in citations) / len(citations)


def load_evaluation_set(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data.get("expected_propositions"), list) or not isinstance(data.get("questions"), list):
        raise ValueError("evaluation set requires expected_propositions and questions lists")
    return data


def evaluate_assistant(
    assistant: KnowledgeAssistant,
    questions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for question in questions:
        top_k = int(question.get("top_k", 5))
        retrieved = assistant.search(str(question["query"]), top_k=top_k)
        answer = assistant.answer(str(question["query"]), top_k=top_k)
        metrics = retrieval_metrics(question.get("expected_keys", []), retrieved, top_k=top_k)
        metrics["citation_precision"] = citation_precision(answer, retrieved)
        metrics["insufficient_evidence_correct"] = float(
            answer["insufficient_evidence"] == bool(question.get("expected_insufficient_evidence", False))
        )
        results.append({"query": question["query"], "metrics": metrics})
    metric_names = {name for result in results for name in result["metrics"]}
    macro = {
        name: sum(result["metrics"].get(name, 0.0) for result in results) / len(results)
        for name in metric_names
    } if results else {}
    return {"questions": results, "macro_average": macro}


def evaluate_document(
    document: str,
    evaluation_set: dict[str, Any],
    *,
    document_id: str = "document",
) -> dict[str, Any]:
    propositions = extract_propositions(document)
    extraction = classification_metrics(
        {proposition_key(item) for item in evaluation_set["expected_propositions"]},
        {proposition_key(item) for item in propositions},
    )
    assistant = KnowledgeAssistant()
    assistant.add_propositions(propositions, document_id=document_id)
    return {
        "extraction": {
            "precision": extraction.precision,
            "recall": extraction.recall,
            "f1": extraction.f1,
            "true_positive": extraction.true_positive,
            "false_positive": extraction.false_positive,
            "false_negative": extraction.false_negative,
        },
        "retrieval": evaluate_assistant(assistant, evaluation_set["questions"]),
        "thresholds": dict(evaluation_set.get("thresholds") or {}),
    }