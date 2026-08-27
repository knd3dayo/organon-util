from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Proposition:
    subject: str
    predicate: str
    object: str
    source: str = "document"
    confidence: float = 1.0
    epistemic_status: str = "Fact"
    rationale: str = ""
    source_quote: str = ""
    tags: List[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    value = re.sub(r"\s+", "", text.strip())
    value = value.replace("（", "(").replace("）", ")")
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[【】]", "", value)
    value = re.sub(r"[\*`#>\-]+", "", value)
    return value.strip()


def _clean_markdown(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"```.*?```", "", cleaned, flags=re.S)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.M)
    cleaned = re.sub(r"\*\*|__|~~", "", cleaned)
    cleaned = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _classify_epistemic_status(sentence: str) -> str:
    text = sentence.lower()
    if any(token in text for token in ["推奨", "意見", "懸念", "評価", "予測", "通念", "仮説", "考え", "視点", "観点"]):
        return "Endoxa"
    if any(token in text for token in ["必須", "ルール", "定義", "組織", "実装", "構造", "基づく", "定義した", "設計", "事実", "実際"]):
        return "Fact"
    return "Fact"


def _build_proposition(subject: str, predicate: str, obj: str, sentence: str, confidence: float = 0.8) -> Proposition:
    status = _classify_epistemic_status(sentence)
    rationale = (
        "文脈依存の評価・意見として扱うべき命題である。"
        if status == "Endoxa"
        else "客観的な定義または構造的要件として扱うべき命題である。"
    )
    return Proposition(
        subject=_normalize(subject),
        predicate=predicate,
        object=_normalize(obj),
        source="document",
        confidence=confidence,
        epistemic_status=status,
        rationale=rationale,
        source_quote=sentence[:200],
        tags=[status.lower()],
    )


def _add_sentence_pattern(propositions: list[Proposition], sentence: str) -> None:
    cleaned = _clean_markdown(sentence)
    if not cleaned:
        return

    if "LLM" in cleaned and "ハルシネーション" in cleaned and ("避けられない" in cleaned or "避けられない" in cleaned):
        propositions.append(
            _build_proposition("LLM", "cannot_avoid", "ハルシネーション", cleaned, confidence=0.85)
        )
        return

    if "MCP" in cleaned and ("動的注入" in cleaned or "ルックアップ" in cleaned or "外部知識" in cleaned):
        propositions.append(
            _build_proposition("MCP", "injects_or_looks_up", "外部知識", cleaned, confidence=0.82)
        )
        return

    if "Assurance Layer" in cleaned and ("保証" in cleaned or "同一律" in cleaned or "推論" in cleaned):
        propositions.append(
            _build_proposition("Assurance Layer", "enforces", "同一律", cleaned, confidence=0.82)
        )
        return

    if "は" in cleaned and "である" in cleaned:
        left, right = cleaned.split("は", 1)
        right = right.replace("である", "").strip()
        if left and right:
            subject = _normalize(left)
            obj = _normalize(right)
            if subject and obj and not subject.startswith("###") and not obj.startswith("###"):
                propositions.append(_build_proposition(subject, "is_a", obj, cleaned, confidence=0.8))

    if "では" in cleaned and "避けられない" in cleaned:
        left, right = cleaned.split("では", 1)
        if left:
            proposition_object = "ハルシネーション"
            if "ハルシネーション" not in cleaned:
                proposition_object = right.split("を避けられない", 1)[0].strip()
            propositions.append(
                _build_proposition(_normalize(left), "cannot_avoid", proposition_object, cleaned, confidence=0.85)
            )


def extract_propositions(text: str) -> List[Proposition]:
    """Very small heuristic extractor for the PoC.

    It supports both the initial specification examples and general concept-doc
    language such as 'XではYを避けられない'.
    """
    normalized = text.strip()
    if not normalized:
        return []

    propositions: list[Proposition] = []

    if "仕様書" in normalized and "承認" in normalized and "必要" in normalized:
        propositions.append(
            Proposition(
                subject="仕様書",
                predicate="requires",
                object="承認",
                source="document",
                confidence=1.0,
                epistemic_status="Fact",
                rationale="仕様書に対する承認要件は定義的なルールとして扱える。",
                source_quote="仕様書は承認が必要である。",
            )
        )

    if "仕様書" in normalized and "文書" in normalized:
        propositions.append(
            Proposition(
                subject="仕様書",
                predicate="is_a",
                object="文書",
                source="document",
                confidence=1.0,
                epistemic_status="Fact",
                rationale="カテゴリ分類として判定可能な事実である。",
                source_quote="仕様書は文書である。",
            )
        )

    for sentence in [segment.strip() for segment in re.split(r"[。！？.!?]", normalized) if segment.strip()]:
        if sentence:
            _add_sentence_pattern(propositions, sentence)

    if not propositions:
        for sentence in [segment.strip() for segment in re.split(r"[。！？.!?]", normalized) if segment.strip()]:
            if "LLM" in sentence and "ハルシネーション" in sentence:
                propositions.append(
                    _build_proposition("LLM", "cannot_avoid", "ハルシネーション", sentence, confidence=0.8)
                )

    return propositions
