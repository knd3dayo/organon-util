from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS

from organon_util.assurance import AssuranceLayer
from organon_util.extractor import Proposition
from organon_util.reasoner import LocalReasoner, PurePythonReasoner


ROOT = Path(__file__).parents[1]


def test_local_reasoner_returns_assurance_report():
    reasoner = LocalReasoner(AssuranceLayer.from_config_dir(ROOT / "config"))
    proposition = Proposition(subject="仕様書", predicate="is_a", object="文書")

    report = reasoner.validate([proposition])

    assert report.passed is True
    assert proposition.proposition_id in report.accepted_propositions


def test_reasoner_protocol_is_implemented_by_local_reasoner():
    reasoner = LocalReasoner(AssuranceLayer.from_config_dir(ROOT / "config"))

    assert callable(reasoner.validate)


def test_pure_python_reasoner_expands_rdfs_subclass():
    graph = Graph()
    example = Namespace("urn:test:")
    graph.add((example.Specification, RDFS.subClassOf, example.Document))
    graph.add((example.item, RDF.type, example.Specification))

    PurePythonReasoner().infer(graph)

    assert (example.item, RDF.type, example.Document) in graph


def test_pure_python_reasoner_validates_shacl_shape():
    data_graph = Graph()
    shapes_graph = Graph()
    example = Namespace("urn:test:")
    shapes = Namespace("http://www.w3.org/ns/shacl#")
    data_graph.add((example.item, RDF.type, example.Document))
    shapes_graph.add((example.DocumentShape, RDF.type, shapes.NodeShape))
    shapes_graph.add((example.DocumentShape, shapes.targetClass, example.Document))
    shapes_graph.add((example.DocumentShape, shapes.property, example.RequiredTitle))
    shapes_graph.add((example.RequiredTitle, shapes.path, example.title))
    shapes_graph.add((example.RequiredTitle, shapes.minCount, Literal(1)))

    result = PurePythonReasoner().validate_graph(data_graph, shapes_graph)

    assert result["conforms"] is False
    assert "Validation Report" in result["report"]


def test_pure_python_reasoner_returns_failed_assurance_on_shacl_violation():
    shapes_graph = Graph()
    example = Namespace("urn:organon:")
    shapes = Namespace("http://www.w3.org/ns/shacl#")
    shapes_graph.add((example.RequirementShape, RDF.type, shapes.NodeShape))
    shapes_graph.add((example.RequirementShape, shapes.targetSubjectsOf, example.requires))
    shapes_graph.add((example.RequirementShape, shapes.property, example.RequiredTitle))
    shapes_graph.add((example.RequiredTitle, shapes.path, example.title))
    shapes_graph.add((example.RequiredTitle, shapes.minCount, Literal(1)))
    proposition = Proposition(subject="仕様書", predicate="requires", object="承認")

    report = PurePythonReasoner(shapes_graph).validate([proposition])

    assert report.passed is False
    assert report.findings[0].code == "shacl_violation"
    assert proposition.proposition_id in report.pending_propositions