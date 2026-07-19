"""Yocto bounded context: layers, recipes, configuration and existing logs."""

from __future__ import annotations

import re
from typing import Any, Mapping

from ..bounded_io import DEFAULT_SKIPPED_DIRS, BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..errors import MCPDomainError
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
    ".bb", ".bbappend", ".bbclass", ".inc", ".conf", ".cfg", ".patch", ".log",
    ".manifest", ".json", ".xml", ".md", ".txt", ".sh",
}
_TASK_LOG_NAME = re.compile(r"log\.do_[A-Za-z0-9_+.-]+(?:\.[0-9]+)?")


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("yocto")
    sources = BoundedRoots(
        config.roots("yocto"),
        extensions=_EXTENSIONS,
        allowed_name_patterns=(_TASK_LOG_NAME.pattern,),
        # BitBake task evidence normally lives below build/tmp/work/.../temp.
        # Other large generated/cache directories remain excluded.
        skipped_dirs=DEFAULT_SKIPPED_DIRS - {"tmp"},
    )

    def layer_metadata(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(
            root, suffixes={".conf"}, name_terms=("layer.conf",), cursor=cursor, limit=limit
        )
        layers = [
            {"layer_conf": item["location"], "relative_path": item["relative_path"]}
            for item in page.items
        ]
        return kernel.envelope(
            "list_layer_metadata",
            {"layers": layers, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            unknowns=("layer priority and compatibility require parsing layer.conf",) if layers else (),
            next_queries=("read_metadata",) if layers else (),
        )

    def recipe_candidates(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        recipe = string_arg(arguments, "recipe", required=True)
        if not 1 <= len(recipe) <= 100 or "/" in recipe or "\\" in recipe:
            raise MCPDomainError("recipe must be a bounded recipe name")
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(
            root,
            suffixes={".bb", ".bbappend"},
            name_terms=(recipe,),
            cursor=cursor,
            limit=limit,
        )
        candidates = [
            {
                "recipe_file": item["location"],
                "kind": "append" if str(item["relative_path"]).endswith(".bbappend") else "recipe",
            }
            for item in page.items
        ]
        return kernel.envelope(
            "find_recipe_candidates",
            {"recipe": recipe, "candidates": candidates, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            unknowns=("BitBake provider selection is not evaluated by this read-only source query",),
            next_queries=("read_metadata",) if candidates else (),
        )

    def search_metadata(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        query = string_arg(arguments, "query", required=True)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.search_literal(root, query, cursor=cursor, limit=limit)
        matches = [dict(item, metadata_role="Yocto metadata occurrence") for item in page.items]
        return kernel.envelope(
            "search_metadata",
            {"query": query, "metadata_matches": matches, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("read_metadata",) if matches else (),
        )

    def read_metadata(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        excerpt = sources.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope(
            "read_metadata", {"metadata_excerpt": excerpt}, truncated=bool(excerpt["truncated"])
        )

    def tail_log(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        path = string_arg(arguments, "path", required=True)
        if not path.lower().endswith(".log") and not _TASK_LOG_NAME.fullmatch(
            path.replace("\\", "/").rsplit("/", 1)[-1]
        ):
            raise MCPDomainError(
                "tail_task_log accepts only .log or BitBake log.do_<task> evidence"
            )
        excerpt = sources.tail_lines(
            root, path, line_count=int_arg(arguments, "line_count", default=80)
        )
        return kernel.envelope(
            "tail_task_log",
            {"task_log_tail": excerpt},
            truncated=bool(excerpt["truncated"]),
            unknowns=("a log tail does not establish the first failure",),
        )

    def list_task_logs(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, sources)
        cursor, limit = page_args(arguments)
        page, scan_cap = sources.list_files(
            root,
            name_terms=("log.do_",),
            cursor=cursor,
            limit=limit,
        )
        logs = [
            {
                "task_log": item["location"],
                "relative_path": item["relative_path"],
                "bytes": item["bytes"],
            }
            for item in page.items
            if _TASK_LOG_NAME.fullmatch(str(item["relative_path"]).rsplit("/", 1)[-1])
        ]
        return kernel.envelope(
            "list_task_logs",
            {"task_logs": logs, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            unknowns=(
                "a truncated catalog is incomplete; configure a narrower task-log root",
            )
            if page.truncated or scan_cap
            else (),
            next_queries=("tail_task_log",) if logs else (),
        )

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    read_schema = object_schema(
        {
            "root": ROOT_PROPERTY,
            "path": PATH_PROPERTY,
            "start_line": {"type": "integer", "minimum": 1, "default": 1},
            "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80},
        },
        required=("path",),
    )
    return MCPServer(
        "yocto",
        kernel,
        [
            Tool("list_layer_metadata", "List layer.conf files without running BitBake.", object_schema(paging), layer_metadata),
            Tool(
                "find_recipe_candidates",
                "Find .bb and .bbappend candidates by recipe name; provider resolution remains UNKNOWN.",
                object_schema({**paging, "recipe": {"type": "string", "minLength": 1, "maxLength": 100}}, required=("recipe",)),
                recipe_candidates,
            ),
            Tool(
                "search_metadata",
                "Literal search over bounded recipe, class, configuration and patch metadata.",
                object_schema({**paging, "query": {"type": "string", "minLength": 2, "maxLength": 120}}, required=("query",)),
                search_metadata,
            ),
            Tool("read_metadata", "Read a bounded Yocto metadata excerpt.", read_schema, read_metadata),
            Tool(
                "list_task_logs",
                "List existing BitBake log.do_<task> files, including paths below build/tmp; no task is started.",
                object_schema(paging),
                list_task_logs,
            ),
            Tool(
                "tail_task_log",
                "Read the bounded tail of an existing .log or BitBake log.do_<task> file; no task is started.",
                object_schema(
                    {
                        "root": ROOT_PROPERTY,
                        "path": PATH_PROPERTY,
                        "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80},
                    },
                    required=("path",),
                ),
                tail_log,
            ),
        ],
        root_aliases=sources.aliases(),
    )
