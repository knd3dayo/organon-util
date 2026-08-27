# organon-util

Minimal PoC for a multi-dimensional concept assurance architecture.

## Goal

Validate the core concept from concept.md:

- extract propositions from ordinary text
- build a simple graph from triples
- validate against domain rules
- allow human approval of valid knowledge

## Minimal architecture

- extractor: extract propositions from a document
- rules: define validation rules and simple checks
- graph: build a lightweight RDF-like graph representation
- workflow: orchestration for proof-of-concept execution

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
```

## LLM configuration

The extractor and answer generator can share `LLMConfig`. The current PoC
defaults to `enabled=false`, so rule-based extraction remains available when
no LLM is configured. API keys are read from environment variables and should
not be committed to configuration files.

```bash
export ORGANON_LLM_ENABLED=true
export ORGANON_LLM_PROVIDER=openai
export ORGANON_LLM_MODEL=gpt-4.1-mini
export OPENAI_API_KEY=...
```

Supported providers are `openai`, `azure_openai`, `compatible`, and `ollama`.
Provider-specific client construction will use this configuration in the LLM
integration layer; this package does not call an external LLM by default.
