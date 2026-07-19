"""Filament bounded context: Dart/native bridge, engine and render assets."""

from __future__ import annotations

from typing import Any, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, PATH_PROPERTY, ROOT_PROPERTY, MCPServer, Tool, object_schema

_SOURCE_EXTENSIONS = {".dart", ".cc", ".cpp", ".c", ".h", ".hpp", ".cmake", ".gradle", ".md", ".json", ".yaml", ".yml", ".bb", ".bbappend", ".patch", ".mat"}
_ASSET_EXTENSIONS = _SOURCE_EXTENSIONS | {".filamat", ".gltf", ".glb", ".ktx", ".ktx2", ".obj"}


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("filament")
    roots = config.roots("filament")
    sources = BoundedRoots(roots, extensions=_SOURCE_EXTENSIONS)
    catalog = BoundedRoots(roots, extensions=_ASSET_EXTENSIONS)

    def assets(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, catalog)
        cursor, limit = page_args(arguments)
        page, scan_cap = catalog.list_files(root, cursor=cursor, limit=limit)
        entries = [
            {
                "render_resource": item["location"],
                "resource_kind": "compiled_or_model_asset" if str(item["relative_path"]).endswith((".filamat", ".gltf", ".glb", ".ktx", ".ktx2", ".obj")) else "bridge_or_material_source",
                "bytes": item["bytes"],
            }
            for item in page.items
        ]
        return kernel.envelope(
            "catalog_render_assets",
            {"render_catalog": entries, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("search_render_bridge",) if entries else (),
        )

    def search(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        return kernel.envelope(
            "search_render_bridge",
            {"query": query, "bridge_matches": page.items, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_render_source",) if page.items else (),
        )

    def read(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope("read_render_source", {"render_bridge_source": excerpt}, truncated=bool(excerpt["truncated"]))

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    return MCPServer(
        "filament",
        kernel,
        [
            Tool("catalog_render_assets", "Catalog Filament bridge, material, model and compiled render resources.", object_schema(paging), assets),
            Tool(
                "search_render_bridge",
                "Search filament_scene/filament_view, native bridge and Filament Engine references.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search,
            ),
            Tool(
                "read_render_source",
                "Read bounded Filament bridge or material source; binary render assets are excluded.",
                object_schema({"root": ROOT_PROPERTY, "path": PATH_PROPERTY, "start_line": {"type": "integer", "minimum": 1, "default": 1}, "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}}, required=("path",)),
                read,
            ),
        ],
        root_aliases=sources.aliases(),
    )
