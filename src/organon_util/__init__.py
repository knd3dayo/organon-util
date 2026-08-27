"""Minimal PoC package for the multi-dimensional concept architecture."""

from .extractor import Proposition, extract_propositions
from .feedback_loop import FeedbackLoop
from .graph import build_rdf_graph
from .mcp_grounding import GroundingResolver
from .qa import IndexedProposition, KnowledgeAssistant
from .rdf_graph import RDFGraph
from .rules import FactStatement, Rule, VersionedFactGraph, load_rules_from_file, validate_graph
from .workflow import run_concept_workflow, run_poc_pipeline

__all__ = [
    "Proposition",
    "Rule",
    "FactStatement",
    "VersionedFactGraph",
    "FeedbackLoop",
    "GroundingResolver",
    "IndexedProposition",
    "KnowledgeAssistant",
    "RDFGraph",
    "build_rdf_graph",
    "extract_propositions",
    "load_rules_from_file",
    "validate_graph",
    "run_concept_workflow",
    "run_poc_pipeline",
]
