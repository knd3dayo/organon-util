from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LLMConfig:
    """Configuration shared by proposition extraction and answer generation."""

    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    api_key: str = ""
    base_url: str = ""
    api_version: str = ""
    temperature: float = 0.0
    timeout_seconds: float = 60.0
    max_retries: int = 2

    def __post_init__(self) -> None:
        if self.provider not in {"openai", "azure_openai", "compatible", "ollama"}:
            raise ValueError(f"unsupported LLM provider: {self.provider}")
        if not self.model.strip():
            raise ValueError("LLM model must not be empty")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("LLM temperature must be between 0 and 2")
        if self.timeout_seconds <= 0:
            raise ValueError("LLM timeout_seconds must be greater than 0")
        if self.max_retries < 0:
            raise ValueError("LLM max_retries must not be negative")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "LLMConfig":
        values = os.environ if environ is None else environ

        def get(name: str, default: str) -> str:
            return values.get(name, default).strip()

        def boolean(name: str, default: bool) -> bool:
            value = get(name, str(default)).lower()
            if value not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError(f"{name} must be a boolean")
            return value in {"true", "1", "yes"}

        return cls(
            enabled=boolean("ORGANON_LLM_ENABLED", False),
            provider=get("ORGANON_LLM_PROVIDER", "openai"),
            model=get("ORGANON_LLM_MODEL", "gpt-4.1-mini"),
            api_key=get("ORGANON_LLM_API_KEY", get("OPENAI_API_KEY", "")),
            base_url=get("ORGANON_LLM_BASE_URL", ""),
            api_version=get("ORGANON_LLM_API_VERSION", ""),
            temperature=float(get("ORGANON_LLM_TEMPERATURE", "0")),
            timeout_seconds=float(get("ORGANON_LLM_TIMEOUT_SECONDS", "60")),
            max_retries=int(get("ORGANON_LLM_MAX_RETRIES", "2")),
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "LLMConfig":
        """Create configuration from a YAML/JSON-like ``llm`` mapping."""
        allowed = {
            "enabled",
            "provider",
            "model",
            "api_key",
            "base_url",
            "api_version",
            "temperature",
            "timeout_seconds",
            "max_retries",
        }
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown LLM settings: {', '.join(sorted(unknown))}")
        return cls(**dict(values))


def load_llm_config(values: Mapping[str, object] | None = None) -> LLMConfig:
    """Load explicit settings, or fall back to environment variables."""
    if values is not None:
        return LLMConfig.from_mapping(values)
    return LLMConfig.from_env()