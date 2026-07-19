"""Fluorite bounded context: Dart scene, assets and interaction contracts."""

from __future__ import annotations

from typing import Any, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, PATH_PROPERTY, ROOT_PROPERTY, MCPServer, Tool, object_schema

_SOURCE_EXTENSIONS = {".dart", ".yaml", ".yml", ".json", ".md", ".txt", ".cc", ".h", ".cpp", ".hpp"}
_ASSET_EXTENSIONS = _SOURCE_EXTENSIONS | {".gltf", ".glb", ".obj", ".mtl", ".ktx", ".ktx2", ".png", ".jpg", ".jpeg"}


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("fluorite")
    roots = config.roots("fluorite")
    sources = BoundedRoots(roots, extensions=_SOURCE_EXTENSIONS)
    catalog = BoundedRoots(roots, extensions=_ASSET_EXTENSIONS)

    def assets(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, catalog)
        cursor, limit = page_args(arguments)
        page, scan_cap = catalog.list_files(root, cursor=cursor, limit=limit)
        entries = [
            {
                "asset_or_source": item["location"],
                "kind": "scene_source" if str(item["relative_path"]).endswith(".dart") else "asset_or_contract",
                "bytes": item["bytes"],
            }
            for item in page.items
        ]
        return kernel.envelope(
            "catalog_scene_assets",
            {"scene_catalog": entries, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("search_scene_contract",) if entries else (),
        )

    def search(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        return kernel.envelope(
            "search_scene_contract",
            {"query": query, "scene_contract_matches": page.items, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_scene_source",) if page.items else (),
        )

    def read(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope("read_scene_source", {"scene_source": excerpt}, truncated=bool(excerpt["truncated"]))

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    return MCPServer(
        "fluorite",
        kernel,
        [
            Tool("catalog_scene_assets", "Catalog Fluorite scene sources and render assets.", object_schema(paging), assets),
            Tool(
                "search_scene_contract",
                "Search Dart scene, asset, interaction, startup and platform-message contracts.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search,
            ),
            Tool(
                "read_scene_source",
                "Read bounded text evidence for Fluorite scene behavior; binary assets are excluded.",
                object_schema(
                    {"root": ROOT_PROPERTY, "path": PATH_PROPERTY, "start_line": {"type": "integer", "minimum": 1, "default": 1}, "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}},
                    required=("path",),
                ),
                read,
            ),
        ],
        root_aliases=sources.aliases(),
    )
