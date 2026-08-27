from __future__ import annotations

from urllib.parse import quote

from rdflib import Dataset, Literal, RDF, URIRef

from .extractor import Proposition


class ContextualRDFGraph:
    """RDF Dataset separating epistemic contexts with named graphs."""

    CONTEXTS = {
        "core": URIRef("urn:organon:graph:core"),
        "context": URIRef("urn:organon:graph:context"),
        "hypothesis": URIRef("urn:organon:graph:hypothesis"),
        "fallacy": URIRef("urn:organon:graph:fallacy"),
    }

    def __init__(self, base_uri: str = "urn:organon:") -> None:
        self.dataset = Dataset()
        self.base_uri = base_uri

    def context_for(self, proposition: Proposition) -> str:
        if proposition.epistemic_status == "Fallacy":
            return "fallacy"
        if proposition.claim_type == "hypothesis":
            return "hypothesis"
        if proposition.epistemic_status == "Endoxa":
            return "context"
        return "core"

    def add_proposition(self, proposition: Proposition) -> None:
        context_name = self.context_for(proposition)
        graph = self.dataset.graph(self.CONTEXTS[context_name])
        subject = URIRef(f"{self.base_uri}{quote(proposition.subject, safe='')}")
        predicate = URIRef(f"{self.base_uri}{quote(proposition.predicate, safe='')}")
        statement = URIRef(f"{self.base_uri}statement:{proposition.proposition_id}")
        graph.add((subject, predicate, Literal(proposition.object)))
        graph.add((statement, RDF.type, URIRef(f"{self.base_uri}Proposition")))
        graph.add((statement, URIRef(f"{self.base_uri}epistemic_status"), Literal(proposition.epistemic_status)))
        graph.add((statement, URIRef(f"{self.base_uri}claim_type"), Literal(proposition.claim_type)))
        if proposition.source_uri:
            graph.add((statement, URIRef(f"{self.base_uri}source_uri"), URIRef(proposition.source_uri)))

    def add_propositions(self, propositions: list[Proposition]) -> None:
        for proposition in propositions:
            self.add_proposition(proposition)

    def graph_size(self, context: str) -> int:
        return len(self.dataset.graph(self.CONTEXTS[context]))

    def graph(self, context: str):
        if context not in self.CONTEXTS:
            raise KeyError(f"unknown RDF context: {context}")
        return self.dataset.graph(self.CONTEXTS[context])

    def serialize(self, format: str = "trig") -> str:
        return self.dataset.serialize(format=format)