"""Minimal PoC package for the multi-dimensional concept architecture."""

from .extractor import Proposition, extract_propositions
from .evaluation import (
    ClassificationMetrics,
    citation_precision,
    classification_metrics,
    evaluate_assistant,
    evaluate_document,
    load_evaluation_set,
    proposition_key,
    retrieval_metrics,
)
from .assurance import AssuranceFinding, AssuranceLayer, AssuranceReport
from .contextual_graph import ContextualRDFGraph
from .discovery import (
    DiscoveryReport,
    HypothesisGenerator,
    HypothesisVerifier,
    ScientificDiscoveryWorkflow,
    VerificationResult,
    VerificationStatus,
)
from .feedback_loop import FeedbackLoop
from .graph import build_rdf_graph
from .hypothesis import HypothesisRecord, HypothesisStatus
from .llm_config import LLMConfig, load_llm_config
from .llm import LLMAnswerGenerator, LLMClient, LLMPropositionExtractor, create_llm_client
from .mcp_grounding import GroundingResolver
from .mcp_server import create_grounding_mcp_server
from .qa import IndexedProposition, KnowledgeAssistant
from .registries import FallacyRegistry, FallacyRule, ToposRegistry, ToposRule
from .reasoner import HermiTReasoner, LocalReasoner, PurePythonReasoner, Reasoner
from .rdf_graph import RDFGraph
from .rules import FactStatement, Rule, VersionedFactGraph, load_rules_from_file, validate_graph
from .source import SourceRecord
from .source_adapter import (
    DocumentSearchRestClient,
    SourceSearchClient,
    search_source_records,
    source_record_from_search_result,
    source_records_from_search_results,
)
from .workflow import (
    run_concept_workflow,
    run_contextual_reasoning_workflow,
    run_poc_pipeline,
    run_search_workflow,
    run_source_record_workflow,
)

__all__ = [
    "Proposition",
    "ClassificationMetrics",
    "classification_metrics",
    "retrieval_metrics",
    "citation_precision",
    "proposition_key",
    "load_evaluation_set",
    "evaluate_assistant",
    "evaluate_document",
    "AssuranceFinding",
    "AssuranceLayer",
    "AssuranceReport",
    "ContextualRDFGraph",
    "DiscoveryReport",
    "HypothesisGenerator",
    "HypothesisVerifier",
    "ScientificDiscoveryWorkflow",
    "VerificationResult",
    "VerificationStatus",
    "Rule",
    "FactStatement",
    "VersionedFactGraph",
    "FeedbackLoop",
    "GroundingResolver",
    "create_grounding_mcp_server",
    "IndexedProposition",
    "KnowledgeAssistant",
    "ToposRule",
    "ToposRegistry",
    "FallacyRule",
    "FallacyRegistry",
    "Reasoner",
    "LocalReasoner",
    "PurePythonReasoner",
    "HermiTReasoner",
    "SourceRecord",
    "source_record_from_search_result",
    "source_records_from_search_results",
    "SourceSearchClient",
    "DocumentSearchRestClient",
    "search_source_records",
    "RDFGraph",
    "build_rdf_graph",
    "HypothesisRecord",
    "HypothesisStatus",
    "LLMConfig",
    "load_llm_config",
    "LLMClient",
    "LLMPropositionExtractor",
    "LLMAnswerGenerator",
    "create_llm_client",
    "extract_propositions",
    "load_rules_from_file",
    "validate_graph",
    "run_concept_workflow",
    "run_contextual_reasoning_workflow",
    "run_poc_pipeline",
    "run_source_record_workflow",
    "run_search_workflow",
]
