from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol

from .source import SourceRecord


class SourceSearchClient(Protocol):
    def search(self, query: str, *, top_k: int = 5) -> Iterable[Mapping[str, Any]]:
        ...


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