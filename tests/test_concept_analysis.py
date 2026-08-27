from pathlib import Path

from organon_util.extractor import extract_propositions


def test_concept_md_can_be_analyzed_for_core_propositions():
    text = Path("concept.md").read_text(encoding="utf-8")
    target = (
        "生成AIへの期待と限界：セマンティックレイヤーの自動構築にLLMが期待されるが、"
        "LLM単独では「媒名辞曖昧の虚偽」や「誤った換位」による論理的飛躍（ハルシネーション）を避けられない。"
    )

    propositions = extract_propositions(target)

    assert len(propositions) >= 1
    assert any("LLM" in p.subject or "生成AI" in p.subject for p in propositions)
    assert any("ハルシネーション" in p.object for p in propositions)
