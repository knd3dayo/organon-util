from __future__ import annotations

from typing import Any, Dict, List

from .rdf_graph import RDFGraph


def build_rdf_graph(triples: List[Dict[str, str]]) -> RDFGraph:
    """Create a minimal RDF-backed graph representation for the PoC."""
    graph = RDFGraph()
    graph.add_triples(triples)
    return graph
