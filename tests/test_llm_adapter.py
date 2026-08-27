import pytest

from organon_util.llm import LLMAnswerGenerator, LLMPropositionExtractor, create_llm_client
from organon_util.llm_config import LLMConfig
from organon_util.source import SourceRecord


class FakeClient:
    def __init__(self):
        self.prompts = []

    def generate_json(self, prompt, schema):
        self.prompts.append(prompt)
        return {
            "propositions": [
                {
                    "subject": "仕様書",
                    "predicate": "requires",
                    "object": "承認",
                    "epistemic_status": "Fact",
                    "modality": "MUST",
                    "tense": "PRESENT",
                    "claim_type": "specification",
                    "rationale": "公式要件として記載されている",
                    "source_quote": "仕様書は承認が必要である。",
                }
            ]
        }

    def generate(self, prompt):
        self.prompts.append(prompt)
        return "Factに基づく回答です。"


def test_llm_extractor_parses_structured_output_and_source_record():
    client = FakeClient()
    extractor = LLMPropositionExtractor(client)
    record = SourceRecord(
        logical_id="manual#chunk-1",
        source_id="manual",
        source_uri="s3://docs/manual.pdf",
        content="仕様書は承認が必要である。",
    )

    propositions = extractor.extract(record.content, source_record=record)

    assert propositions[0].modality == "MUST"
    assert propositions[0].tense == "PRESENT"
    assert propositions[0].source_record_id == "manual#chunk-1"
    assert propositions[0].source_uri == "s3://docs/manual.pdf"


def test_llm_answer_generator_delegates_safe_retrieval_prompt():
    client = FakeClient()
    generator = LLMAnswerGenerator(client)

    answer = generator.generate(
        "質問",
        [{"proposition_id": "prop-1", "source_quote": "根拠"}],
    )

    assert answer == "Factに基づく回答です。"
    assert "未信頼の取得データ" in client.prompts[0]


def test_create_llm_client_rejects_disabled_configuration():
    with pytest.raises(RuntimeError, match="LLM is disabled"):
        create_llm_client(LLMConfig(enabled=False))