from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SourceRecord:
    """Common source contract exchanged with document-search-util."""

    logical_id: str
    source_id: str
    content: str
    source_uri: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    retrieved_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("logical_id", "source_id", "content"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "SourceRecord":
        """Create a source record from a document-search-util result mapping."""
        def parse_datetime(item: Any) -> datetime | None:
            if item is None or isinstance(item, datetime):
                return item
            if isinstance(item, str) and item:
                return datetime.fromisoformat(item.replace("Z", "+00:00"))
            raise TypeError("source timestamps must be datetime values or ISO strings")

        return cls(
            logical_id=str(value["logical_id"]),
            source_id=str(value["source_id"]),
            content=str(value["content"]),
            source_uri=str(value.get("source_uri", "")),
            metadata=dict(value.get("metadata") or {}),
            checksum=str(value.get("checksum", "")),
            retrieved_at=parse_datetime(value.get("retrieved_at")),
            updated_at=parse_datetime(value.get("updated_at")),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "logical_id": self.logical_id,
            "source_id": self.source_id,
            "content": self.content,
            "source_uri": self.source_uri,
            "metadata": dict(self.metadata),
            "checksum": self.checksum,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }