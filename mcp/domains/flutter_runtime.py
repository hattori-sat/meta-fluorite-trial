"""Flutter runtime bounded context: embedder, surfaces and launcher."""

from __future__ import annotations

from typing import Any, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, PATH_PROPERTY, ROOT_PROPERTY, MCPServer, Tool, object_schema

_EXTENSIONS = {".cc", ".cpp", ".c", ".h", ".hpp", ".gn", ".gni", ".cmake", ".md", ".json", ".yaml", ".yml", ".bb", ".bbappend", ".patch"}


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("flutter_runtime")
    sources = BoundedRoots(config.roots("flutter_runtime"), extensions=_EXTENSIONS)

    def surfaces(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(
            root,
            name_terms=("embedder", "flutter", "ivi", "wayland", "surface"),
            cursor=cursor,
            limit=limit,
        )
        candidates = [{"runtime_source": item["location"], "bytes": item["bytes"]} for item in page.items]
        return kernel.envelope(
            "catalog_embedder_surfaces",
            {"surface_contract_candidates": candidates, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            unknowns=("file naming alone does not establish the active runtime path",) if candidates else (),
            next_queries=("search_embedder_contract",) if candidates else (),
        )

    def search(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        return kernel.envelope(
            "search_embedder_contract",
            {"query": query, "embedder_contract_matches": page.items, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_runtime_source",) if page.items else (),
        )

    def read(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope("read_runtime_source", {"runtime_contract": excerpt}, truncated=bool(excerpt["truncated"]))

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    return MCPServer(
        "flutter_runtime",
        kernel,
        [
            Tool("catalog_embedder_surfaces", "Catalog Flutter embedder, launcher, thread and surface candidates.", object_schema(paging), surfaces),
            Tool(
                "search_embedder_contract",
                "Search Flutter Engine/embedder and IVI launcher contracts.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search,
            ),
            Tool(
                "read_runtime_source",
                "Read a bounded Flutter runtime or launcher source excerpt.",
                object_schema({"root": ROOT_PROPERTY, "path": PATH_PROPERTY, "start_line": {"type": "integer", "minimum": 1, "default": 1}, "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}}, required=("path",)),
                read,
            ),
        ],
        root_aliases=sources.aliases(),
    )
