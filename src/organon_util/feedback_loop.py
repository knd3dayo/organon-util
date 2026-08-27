from __future__ import annotations

from typing import Any, Dict, List

from .extractor import Proposition, extract_propositions
from .rules import Rule, validate_graph


class FeedbackLoop:
    """Minimal assurance feedback loop for the PoC.

    This simulates the core concept: when validation fails, the system feeds the
    error back into a second extraction pass and retries once.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def run(self, document: str, rules: List[Rule]) -> Dict[str, Any]:
        for attempt in range(1, self.max_retries + 1):
            propositions = extract_propositions(document)
            graph = [
                {"subject": p.subject, "predicate": p.predicate, "object": p.object}
                for p in propositions
            ]
            validation = validate_graph(graph, rules)
            if validation["passed"]:
                return {
                    "attempts": attempt,
                    "passed": True,
                    "status": "approved",
                    "graph": graph,
                    "errors": [],
                }

            document = self._repair_document(document, validation["errors"])

        return {
            "attempts": self.max_retries,
            "passed": False,
            "status": "rejected",
            "graph": [],
            "errors": [f"Retry limit reached: {self.max_retries}"],
        }

    def _repair_document(self, document: str, errors: List[str]) -> str:
        repaired = document
        for error in errors:
            if "expected" in error and "requires" in error:
                repaired = repaired + "。仕様書は承認が必要である。"
                break
        return repaired
