"""AGL bounded context: manifests and automotive image integration."""

from __future__ import annotations

from typing import Any, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..protocol import (
    CURSOR_PROPERTY,
    LIMIT_PROPERTY,
    PATH_PROPERTY,
    ROOT_PROPERTY,
    MCPServer,
    Tool,
    object_schema,
)

_EXTENSIONS = {
    ".xml", ".yml", ".yaml", ".json", ".conf", ".inc", ".bb", ".bbappend",
    ".bbclass", ".md", ".rst", ".sh", ".service", ".toml",
}


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("agl")
    sources = BoundedRoots(config.roots("agl"), extensions=_EXTENSIONS)

    def manifest_catalog(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(root, suffixes={".xml"}, cursor=cursor, limit=limit)
        return kernel.envelope(
            "get_manifest_catalog",
            {
                "manifest_catalog": page.items,
                "root_role": root,
                "next_cursor": page.next_cursor,
            },
            truncated=page.truncated or scan_cap,
            next_queries=("search_integration_points",) if page.items else (),
        )

    def search_integration(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        matches = [dict(item, integration_role="AGL assembly reference") for item in page.items]
        return kernel.envelope(
            "search_integration_points",
            {"query": query, "integration_matches": matches, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_integration_evidence",) if matches else (),
        )

    def read_integration(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope(
            "read_integration_evidence",
            {"integration_evidence": excerpt},
            truncated=bool(excerpt["truncated"]),
        )

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    return MCPServer(
        "agl",
        kernel,
        [
            Tool(
                "get_manifest_catalog",
                "List bounded AGL repo-manifest documents; this does not describe Yocto task state.",
                object_schema(paging),
                manifest_catalog,
            ),
            Tool(
                "search_integration_points",
                "Search AGL image, feature, packagegroup, compositor and service integration metadata.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search_integration,
            ),
            Tool(
                "read_integration_evidence",
                "Read a bounded excerpt from an AGL integration document.",
                object_schema(
                    {
                        "root": ROOT_PROPERTY,
                        "path": PATH_PROPERTY,
                        "start_line": {"type": "integer", "minimum": 1, "default": 1},
                        "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80},
                    },
                    required=("path",),
                ),
                read_integration,
            ),
        ],
        root_aliases=sources.aliases(),
    )
