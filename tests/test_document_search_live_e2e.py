import os

import pytest

from organon_util.source_adapter import DocumentSearchRestClient
from organon_util.workflow import run_search_workflow


BASE_URL = os.environ.get("DOCUMENT_SEARCH_UTIL_URL")


@pytest.mark.skipif(
    not BASE_URL,
    reason="set DOCUMENT_SEARCH_UTIL_URL to run the live cross-service E2E",
)
def test_live_document_search_to_organon_answer():
    result = run_search_workflow(
        DocumentSearchRestClient(BASE_URL),
        os.environ.get("DOCUMENT_SEARCH_UTIL_QUERY", "外部知識"),
        top_k=5,
    )

    assert result["sources"]
    assert result["propositions"]
    assert result["answer"]["citations"]
    assert all(source["logical_id"] for source in result["sources"])