import json

from organon_util.mcp_grounding import GroundingResolver
from organon_util.mcp_server import create_grounding_mcp_server
from organon_util.source_adapter import DocumentSearchRestClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_document_search_rest_client_calls_keyword_endpoint():
    captured = {}

    def opener(request, *, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(
            [{"logical_id": "doc#1", "source_id": "doc", "content": "本文"}]
        )

    results = DocumentSearchRestClient(
        "http://localhost:8000/",
        timeout_seconds=5,
        opener=opener,
    ).search("質問", top_k=3)

    assert captured["url"] == "http://localhost:8000/keyword_search"
    assert captured["body"]["query"] == "質問"
    assert captured["body"]["top_k"] == 3
    assert results[0]["logical_id"] == "doc#1"


def test_grounding_mcp_server_registers_allowed_tools():
    class FakeServer:
        def __init__(self, name):
            self.name = name
            self.tools = []

        def tool(self):
            def register(function):
                self.tools.append(function.__name__)
                return function
            return register

    server = create_grounding_mcp_server(
        GroundingResolver(),
        mcp_factory=FakeServer,
    )

    assert server.name == "organon-grounding"
    assert server.tools == ["lookup_entity", "get_domain_rule", "get_source_metadata"]