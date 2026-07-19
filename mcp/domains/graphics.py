"""Graphics bounded context: Wayland, Vulkan, Mesa, DRM and presentation."""

from __future__ import annotations

from typing import Any, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, PATH_PROPERTY, ROOT_PROPERTY, MCPServer, Tool, object_schema

_EXTENSIONS = {".c", ".cc", ".cpp", ".h", ".hpp", ".conf", ".ini", ".json", ".yaml", ".yml", ".md", ".txt", ".bb", ".bbappend", ".inc", ".patch", ".service", ".rules"}


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("graphics")
    sources = BoundedRoots(config.roots("graphics"), extensions=_EXTENSIONS)

    def catalog(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(
            root,
            name_terms=("vulkan", "mesa", "wayland", "weston", "drm", "egl", "gpu"),
            cursor=cursor,
            limit=limit,
        )
        entries = [{"graphics_configuration": item["location"], "bytes": item["bytes"]} for item in page.items]
        return kernel.envelope(
            "catalog_graphics_configuration",
            {"graphics_configuration_candidates": entries, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            unknowns=("a source candidate does not prove the target's active graphics path",) if entries else (),
            next_queries=("search_graphics_path",) if entries else (),
        )

    def search(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        return kernel.envelope(
            "search_graphics_path",
            {"query": query, "graphics_path_matches": page.items, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_graphics_evidence",) if page.items else (),
        )

    def read(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope("read_graphics_evidence", {"graphics_stack_evidence": excerpt}, truncated=bool(excerpt["truncated"]))

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    return MCPServer(
        "graphics",
        kernel,
        [
            Tool("catalog_graphics_configuration", "Catalog Wayland, Vulkan, Mesa, DRM and GPU configuration candidates.", object_schema(paging), catalog),
            Tool(
                "search_graphics_path",
                "Search the graphics source/configuration path from compositor to presentation.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search,
            ),
            Tool(
                "read_graphics_evidence",
                "Read a bounded graphics configuration or source excerpt.",
                object_schema({"root": ROOT_PROPERTY, "path": PATH_PROPERTY, "start_line": {"type": "integer", "minimum": 1, "default": 1}, "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}}, required=("path",)),
                read,
            ),
        ],
        root_aliases=sources.aliases(),
    )
