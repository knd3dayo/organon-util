from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from .extractor import Proposition


@dataclass(frozen=True)
class ToposRule:
    topoi_id: str
    name: str
    category: str
    premise_pattern: dict[str, Any] = field(default_factory=dict)
    conclusion_pattern: dict[str, Any] = field(default_factory=dict)
    risk: tuple[str, ...] = ()
    explanation: str = ""
    automation_level: str = "assisted"

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ToposRule":
        return cls(
            topoi_id=str(value["topoi_id"]),
            name=str(value["name"]),
            category=str(value["category"]),
            premise_pattern=dict(value.get("premise_pattern") or {}),
            conclusion_pattern=dict(value.get("conclusion_pattern") or {}),
            risk=tuple(str(item) for item in value.get("risk", [])),
            explanation=str(value.get("explanation", "")),
            automation_level=str(value.get("automation_level", "assisted")),
        )


class ToposRegistry:
    def __init__(self, rules: Iterable[ToposRule] = ()) -> None:
        self._rules = {rule.topoi_id: rule for rule in rules}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ToposRegistry":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(ToposRule.from_mapping(item) for item in data.get("topoi", []))

    def get(self, topoi_id: str) -> ToposRule:
        try:
            return self._rules[topoi_id]
        except KeyError as exc:
            raise KeyError(f"unknown topoi_id: {topoi_id}") from exc

    def by_category(self, category: str) -> list[ToposRule]:
        return [rule for rule in self._rules.values() if rule.category == category]

    def evaluate(self, propositions: Iterable[Proposition]) -> list[dict[str, Any]]:
        items = list(propositions)
        by_id = {item.proposition_id: item for item in items}
        findings: list[dict[str, Any]] = []
        for proposition in items:
            if proposition.predicate != "is_a":
                continue
            for rule in self.by_category("scope"):
                if rule.premise_pattern.get("predicate") not in {None, proposition.predicate}:
                    continue
                findings.append(
                    {
                        "topoi_id": rule.topoi_id,
                        "applied_to": [proposition.proposition_id],
                        "assessment": "scope_relation_available",
                        "explanation": rule.explanation,
                        "subject_scope": proposition.object,
                        "object_scope": proposition.subject,
                        "required_review": False,
                    }
                )
        for proposition in items:
            if proposition.modality != "MUST" or "universal" not in proposition.tags:
                continue
            if "particular" not in proposition.tags:
                continue
            for rule in self.by_category("scope"):
                if "illicit_generalization" not in rule.risk:
                    continue
                findings.append(
                    {
                        "topoi_id": rule.topoi_id,
                        "applied_to": [proposition.proposition_id],
                        "assessment": "scope_expansion_candidate",
                        "explanation": "特称命題を全称命題へ拡張している可能性がある",
                        "required_review": True,
                    }
                )
        for proposition in items:
            if proposition.categorical_form not in {"A", "E"}:
                continue
            particular_sources = [
                source_id
                for source_id in proposition.derived_from
                if source_id in by_id and by_id[source_id].categorical_form in {"I", "O"}
            ]
            if not particular_sources:
                continue
            findings.append(
                {
                    "topoi_id": "particular_to_universal_scope",
                    "applied_to": [*particular_sources, proposition.proposition_id],
                    "assessment": "scope_expansion_candidate",
                    "explanation": "特称命題を根拠として全称命題を導いている",
                    "required_review": True,
                }
            )
        return findings


@dataclass(frozen=True)
class FallacyRule:
    fallacy_id: str
    name: str
    category: str
    detection: dict[str, Any] = field(default_factory=dict)
    action: str = "pending_review"
    explanation: str = ""

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "FallacyRule":
        return cls(
            fallacy_id=str(value["fallacy_id"]),
            name=str(value["name"]),
            category=str(value["category"]),
            detection=dict(value.get("detection") or {}),
            action=str(value.get("action", "pending_review")),
            explanation=str(value.get("explanation", "")),
        )


class FallacyRegistry:
    def __init__(self, rules: Iterable[FallacyRule] = ()) -> None:
        self._rules = {rule.fallacy_id: rule for rule in rules}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "FallacyRegistry":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(FallacyRule.from_mapping(item) for item in data.get("fallacies", []))

    def get(self, fallacy_id: str) -> FallacyRule:
        try:
            return self._rules[fallacy_id]
        except KeyError as exc:
            raise KeyError(f"unknown fallacy_id: {fallacy_id}") from exc

    def by_category(self, category: str) -> list[FallacyRule]:
        return [rule for rule in self._rules.values() if rule.category == category]

    def validate_details(self, details: dict[str, Any]) -> dict[str, Any]:
        rule = self.get(str(details.get("type", "")))
        return {
            "fallacy_id": rule.fallacy_id,
            "action": rule.action,
            "explanation": str(details.get("reason") or rule.explanation),
            "required_review": rule.action == "pending_review",
        }

    def detect(self, propositions: Iterable[Proposition]) -> list[dict[str, Any]]:
        """Detect registered fallacy patterns without relying on an LLM verdict."""
        findings: list[dict[str, Any]] = []
        items = list(propositions)
        for proposition in items:
            tags = set(proposition.tags)
            candidates: list[str] = []
            if "ambiguous" in tags:
                candidates.append("equivocation")
            if "particular" in tags and "universal" in tags:
                candidates.append("hasty_generalization")
            if "authority_only" in tags:
                candidates.append("ad_verecundiam")
            if "correlation_as_causation" in tags:
                candidates.append("correlation_causation")
            if "ignored_exception" in tags:
                candidates.append("ignoring_exceptions")
            if "necessary_as_sufficient" in tags:
                candidates.append("necessary_sufficient_confusion")
            for fallacy_id in candidates:
                rule = self.get(fallacy_id)
                findings.append(
                    {
                        "fallacy_id": rule.fallacy_id,
                        "proposition_ids": [proposition.proposition_id],
                        "action": rule.action,
                        "explanation": rule.explanation,
                        "required_review": True,
                    }
                )
        return findings