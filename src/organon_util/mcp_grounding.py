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
        return self.lookup_entity(term)

    def lookup_entity(self, term: str) -> Dict[str, Any]:
        if term in self.knowledge:
            return {**self.knowledge[term], "term": term, "grounded": True}
        return {"kind": "unknown", "rule": None, "term": term, "grounded": False}

    def get_domain_rule(self, entity_id: str) -> Dict[str, Any]:
        entity = self.knowledge.get(entity_id, {})
        rule = entity.get("rule")
        if rule is None:
            return {"entity_id": entity_id, "found": False, "rule": None}
        return {"entity_id": entity_id, "found": True, "rule": rule}

    def get_source_metadata(self, source_id: str) -> Dict[str, Any]:
        entity = self.knowledge.get(source_id, {})
        metadata = entity.get("source_metadata")
        if metadata is None:
            return {"source_id": source_id, "found": False, "metadata": {}}
        return {"source_id": source_id, "found": True, "metadata": dict(metadata)}
