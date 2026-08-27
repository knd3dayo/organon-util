from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class Rule:
    rule_id: str
    subject: str
    predicate: str
    object: str
    description: str = ""


class SourcePriority(Enum):
    AUTHORITATIVE = 3
    FACTUAL = 2
    CONTEXTUAL = 1
    UNVERIFIED = 0


@dataclass
class FactStatement:
    subject: str
    predicate: str
    object: str
    epistemic_status: str = "Fact"
    valid_from: str = ""
    invalidated_at: str = ""
    superseded_by: str = ""
    source: str = "document"
    approved_by: str = ""


class VersionedFactGraph:
    """Minimal versioned graph for Fact lifecycle management.

    Each fact is tracked as a history item so the system can preserve invalidated
    statements while still exposing only currently active facts to validation.
    """

    def __init__(self):
        self._facts: List[FactStatement] = []

    def add_fact(self, fact: FactStatement) -> None:
        self._facts.append(fact)

    def invalidate_fact(
        self,
        *,
        subject: str,
        predicate: str,
        object: str,
        invalidated_at: str,
        superseded_by: str,
    ) -> None:
        for fact in self._facts:
            if (
                fact.subject == subject
                and fact.predicate == predicate
                and fact.object == object
                and not fact.invalidated_at
            ):
                fact.invalidated_at = invalidated_at
                fact.superseded_by = superseded_by
                return

    def approve_fact(self, *, subject: str, predicate: str, object: str, approved_by: str) -> bool:
        for fact in self._facts:
            if (
                fact.subject == subject
                and fact.predicate == predicate
                and fact.object == object
            ):
                fact.epistemic_status = "Fact"
                fact.approved_by = approved_by
                return True
        return False

    def rank_by_source_priority(self, source_priority: Dict[str, SourcePriority]) -> List[FactStatement]:
        def score(fact: FactStatement) -> int:
            priority = source_priority.get(fact.source, SourcePriority.UNVERIFIED)
            return priority.value

        return sorted(self._facts, key=score, reverse=True)

    def active_facts(self) -> List[FactStatement]:
        return [fact for fact in self._facts if not fact.invalidated_at]

    def history(self) -> List[FactStatement]:
        return list(self._facts)

    def to_json(self) -> List[Dict[str, str]]:
        """Return the fact history in a JSON-friendly, downstream-serializable form."""
        return [
            {
                "subject": fact.subject,
                "predicate": fact.predicate,
                "object": fact.object,
                "epistemic_status": fact.epistemic_status,
                "valid_from": fact.valid_from,
                "invalidated_at": fact.invalidated_at,
                "superseded_by": fact.superseded_by,
                "source": fact.source,
                "approved_by": fact.approved_by,
            }
            for fact in self._facts
        ]

    def to_rdf_graph(self):
        """Create an RDF-backed graph that preserves the fact lifecycle metadata."""
        from .rdf_graph import RDFGraph

        graph = RDFGraph()
        for fact in self._facts:
            graph.add_triple(fact.subject, fact.predicate, fact.object)
            for key, value in (
                ("epistemic_status", fact.epistemic_status),
                ("source", fact.source),
                ("approved_by", fact.approved_by),
                ("valid_from", fact.valid_from),
                ("invalidated_at", fact.invalidated_at),
                ("superseded_by", fact.superseded_by),
            ):
                if value:
                    graph.add_triple(fact.subject, key, value)
        return graph


def load_rules_from_file(path: str) -> List[Rule]:
    """Load rules from a YAML file.

    Expected YAML structure:
    rules:
      - rule_id: specification_requires_approval
        subject: 仕様書
        predicate: requires
        object: 承認
    """
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    loaded = data.get("rules", [])
    return [
        Rule(
            rule_id=item["rule_id"],
            subject=item["subject"],
            predicate=item["predicate"],
            object=item["object"],
            description=item.get("description", ""),
        )
        for item in loaded
    ]


def validate_graph(graph: List[Dict[str, str]], rules: List[Rule]) -> Dict[str, Any]:
    """Check that graph triples satisfy required rules.

    The minimal logic is: for each rule, ensure that the graph contains the
    required triple; otherwise mark it as a validation error.
    """
    errors: list[str] = []
    passed = True

    for rule in rules:
        matched = any(
            item.get("subject") == rule.subject
            and item.get("predicate") == rule.predicate
            and item.get("object") == rule.object
            for item in graph
        )
        if not matched:
            passed = False
            errors.append(
                f"Rule {rule.rule_id} failed: expected '{rule.subject} {rule.predicate} {rule.object}'"
            )

    return {"passed": passed, "errors": errors}


def approved_graph(graph: List[Dict[str, str]], rules: List[Rule]) -> List[Dict[str, str]]:
    """Return only triples that satisfy the rules.

    In the real system this would be a proper approval gate backed by a human or
    a trust policy. For the PoC, it simply filters the graph by validation.
    """
    validation = validate_graph(graph, rules)
    if not validation["passed"]:
        return []
    return graph
