from __future__ import annotations

from rdflib import Graph, Literal, URIRef


class RDFGraph:
    """Minimal RDF-backed representation for the PoC."""

    def __init__(self, base_uri: str = "urn:organon:"):
        self.graph = Graph()
        self.base_uri = base_uri

    def __len__(self) -> int:
        return len(self.graph)

    def __iter__(self):
        return iter(self.graph)

    def __contains__(self, item: str) -> bool:
        return any(str(value) == item for value in self.graph)

    def add_triple(self, subject: str, predicate: str, obj: str) -> None:
        s = URIRef(f"{self.base_uri}{subject}")
        p = URIRef(f"{self.base_uri}{predicate}")
        o = Literal(obj)
        self.graph.add((s, p, o))

    def add_triples(self, triples: list[dict[str, str]]) -> None:
        for triple in triples:
            self.add_triple(
                triple.get("subject", ""),
                triple.get("predicate", ""),
                triple.get("object", ""),
            )

    def serialize(self, format: str = "nt") -> str:
        return self.graph.serialize(format=format)


def build_rdf_graph(triples: list[dict[str, str]]) -> RDFGraph:
    graph = RDFGraph()
    graph.add_triples(triples)
    return graph
