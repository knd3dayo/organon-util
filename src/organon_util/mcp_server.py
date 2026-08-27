from __future__ import annotations

from typing import Any

from .mcp_grounding import GroundingResolver


def create_grounding_mcp_server(
    resolver: GroundingResolver,
    *,
    mcp_factory: Any | None = None,
) -> Any:
    """Expose grounding lookups as FastMCP tools."""
    if mcp_factory is None:
        try:
            from fastmcp import FastMCP
        except ImportError as exc:
            raise RuntimeError("MCP support requires: pip install 'organon-util[mcp]'") from exc
        mcp_factory = FastMCP

    server = mcp_factory("organon-grounding")
    server.tool()(resolver.lookup_entity)
    server.tool()(resolver.get_domain_rule)
    server.tool()(resolver.get_source_metadata)
    return server