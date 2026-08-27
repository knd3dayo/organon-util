import pytest

from organon_util.llm_config import LLMConfig, load_llm_config


def test_llm_config_defaults_to_disabled():
    config = LLMConfig()

    assert config.enabled is False
    assert config.provider == "openai"
    assert config.temperature == 0.0


def test_llm_config_reads_environment_without_exposing_key():
    config = LLMConfig.from_env(
        {
            "ORGANON_LLM_ENABLED": "true",
            "ORGANON_LLM_PROVIDER": "compatible",
            "ORGANON_LLM_MODEL": "local-model",
            "ORGANON_LLM_API_KEY": "secret",
            "ORGANON_LLM_BASE_URL": "http://localhost:8000/v1",
        }
    )

    assert config.enabled is True
    assert config.provider == "compatible"
    assert config.model == "local-model"
    assert config.api_key == "secret"
    assert config.base_url == "http://localhost:8000/v1"


def test_load_llm_config_accepts_explicit_mapping():
    config = load_llm_config({"provider": "ollama", "model": "qwen2.5"})

    assert config.provider == "ollama"
    assert config.model == "qwen2.5"
    assert config.enabled is False


@pytest.mark.parametrize(
    "values",
    [
        {"provider": "unknown"},
        {"model": ""},
        {"temperature": 2.1},
        {"timeout_seconds": 0},
        {"max_retries": -1},
        {"unexpected": True},
    ],
)
def test_llm_config_rejects_invalid_settings(values):
    with pytest.raises((TypeError, ValueError)):
        load_llm_config(values)