from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from typing import Any, Protocol
from urllib.request import Request, urlopen

from .source import SourceRecord


class SourceSearchClient(Protocol):
    def search(self, query: str, *, top_k: int = 5) -> Iterable[Mapping[str, Any]]:
        ...


class DocumentSearchRestClient:
    """Client for document-search-util's keyword search REST endpoint."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 30.0, opener: Any = urlopen) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.opener = opener

    def search(self, query: str, *, top_k: int = 5) -> list[Mapping[str, Any]]:
        payload = json.dumps(
            {"query": query, "metadata_filters": {}, "top_k": top_k}
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/keyword_search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener(request, timeout=self.timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, list):
            raise ValueError("document-search-util response must be a list")
        return result


def source_record_from_search_result(result: Mapping[str, Any]) -> SourceRecord:
    """Adapt one document-search-util result to the organon source contract."""
    return SourceRecord.from_mapping(dict(result))


def source_records_from_search_results(
    results: Iterable[Mapping[str, Any]],
) -> list[SourceRecord]:
    """Adapt a document-search-util result collection without importing it."""
    return [source_record_from_search_result(result) for result in results]


def search_source_records(
    client: SourceSearchClient,
    query: str,
    *,
    top_k: int = 5,
) -> list[SourceRecord]:
    """Run a document-search-util-compatible search and adapt its results."""
    return source_records_from_search_results(client.search(query, top_k=top_k))