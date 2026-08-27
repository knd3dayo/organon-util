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
