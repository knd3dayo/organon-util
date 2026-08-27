from __future__ import annotations

import json
from typing import Any, Protocol, Sequence

from .extractor import Proposition
from .llm_config import LLMConfig
from .qa import KnowledgeAssistant
from .source import SourceRecord


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        ...

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        ...


class OpenAICompatibleClient:
    """Lazy OpenAI-compatible client for OpenAI, Azure, Ollama, and gateways."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = self._build_client()

    def _build_client(self) -> Any:
        try:
            from openai import AzureOpenAI, OpenAI
        except ImportError as exc:
            raise RuntimeError("LLM support requires: pip install 'organon-util[llm]'") from exc

        if self.config.provider == "azure_openai":
            if not self.config.api_key or not self.config.base_url or not self.config.api_version:
                raise ValueError("azure_openai requires api_key, base_url, and api_version")
            return AzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.base_url,
                api_version=self.config.api_version,
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
            )

        kwargs: dict[str, Any] = {
            "api_key": self.config.api_key or "not-required",
            "timeout": self.config.timeout_seconds,
            "max_retries": self.config.max_retries,
        }
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        return OpenAI(**kwargs)

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": json.dumps(schema, ensure_ascii=False)},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("LLM JSON response must be an object")
        return payload


def create_llm_client(config: LLMConfig) -> LLMClient:
    if not config.enabled:
        raise RuntimeError("LLM is disabled; use the rule-based fallback")
    return OpenAICompatibleClient(config)


class LLMPropositionExtractor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract(
        self,
        text: str,
        *,
        source_record: SourceRecord | None = None,
    ) -> list[Proposition]:
        schema = {
            "type": "object",
            "properties": {
                "propositions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "subject",
                            "predicate",
                            "object",
                            "epistemic_status",
                            "rationale",
                            "source_quote",
                        ],
                    },
                }
            },
            "required": ["propositions"],
        }
        payload = self.client.generate_json(text, schema)
        values = payload.get("propositions")
        if not isinstance(values, list):
            raise ValueError("LLM response propositions must be a list")

        result: list[Proposition] = []
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("each LLM proposition must be an object")
            proposition = Proposition(
                subject=str(value["subject"]),
                predicate=str(value["predicate"]),
                object=str(value["object"]),
                epistemic_status=str(value["epistemic_status"]),
                rationale=str(value["rationale"]),
                source_quote=str(value["source_quote"]),
                modality=str(value.get("modality", "ACTUAL")),
                tense=str(value.get("tense", "PRESENT")),
                claim_type=str(value.get("claim_type", "statement")),
                fallacy_details=value.get("fallacy_details"),
                derived_from=[str(item) for item in value.get("derived_from", [])],
                verification_method=str(value.get("verification_method", "")),
                falsification_condition=str(value.get("falsification_condition", "")),
                categorical_form=str(value.get("categorical_form", "UNSPECIFIED")),
                source_record_id=source_record.logical_id if source_record else "",
                source_uri=source_record.source_uri if source_record else "",
            )
            result.append(proposition)
        return result


class LLMAnswerGenerator:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def generate(self, query: str, retrieved: Sequence[dict[str, object]]) -> str:
        prompt = KnowledgeAssistant.build_answer_prompt(query, retrieved)
        return self.client.generate(prompt)