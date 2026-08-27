from __future__ import annotations

from typing import Any, Dict


class GroundingResolver:
    """Minimal grounding layer for the PoC.

    This acts like a tiny MCP-backed lookup service that provides domain context
    for ambiguous or unknown terms.
    """

    def __init__(self, knowledge: Dict[str, Dict[str, Any]] | None = None):
        self.knowledge = knowledge or {}

    def resolve(self, term: str) -> Dict[str, Any]:
        if term in self.knowledge:
            return self.knowledge[term]
        return {"kind": "unknown", "rule": None, "term": term}
