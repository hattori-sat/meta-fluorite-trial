"""Target-validation bounded context: existing QEMU/device evidence bundles."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..bounded_io import BoundedRoots
from ..config import MCPConfig
from ..domain_support import int_arg, page_args, root_arg, string_arg
from ..kernel import bounded_text
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, PATH_PROPERTY, ROOT_PROPERTY, MCPServer, Tool, object_schema

_TEXT_EXTENSIONS = {".log", ".txt", ".json", ".yaml", ".yml", ".manifest", ".service", ".md"}
_BUNDLE_EXTENSIONS = _TEXT_EXTENSIONS | {".png", ".jpg", ".jpeg"}


def _signals(lines: Iterable[str], terms: tuple[str, ...], cap: int = 80) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    lowered = tuple(term.casefold() for term in terms)
    for number, line in enumerate(lines, start=1):
        if any(term in line.casefold() for term in lowered):
            excerpt, _ = bounded_text(line.rstrip(), 500)
            result.append({"line": number, "excerpt": excerpt})
            if len(result) >= cap:
                break
    return result


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("target_validation")
    roots = config.roots("target_validation")
    evidence = BoundedRoots(roots, extensions=_TEXT_EXTENSIONS)
    bundles = BoundedRoots(roots, extensions=_BUNDLE_EXTENSIONS)

    def list_bundles(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, bundles)
        cursor, limit = page_args(arguments)
        page, scan_cap = bundles.list_files(root, cursor=cursor, limit=limit)
        entries = [
            {
                "evidence_artifact": item["location"],
                "kind": "screen_evidence" if str(item["relative_path"]).lower().endswith((".png", ".jpg", ".jpeg")) else "machine_evidence",
                "bytes": item["bytes"],
            }
            for item in page.items
        ]
        return kernel.envelope(
            "list_validation_bundles",
            {"validation_artifacts": entries, "next_cursor": page.next_cursor},
            truncated=page.truncated or scan_cap,
            next_queries=("summarize_boot_evidence", "summarize_graphics_evidence") if entries else (),
        )

    def summarize(
        arguments: Mapping[str, Any], *, operation: str, success_terms: tuple[str, ...], failure_terms: tuple[str, ...], payload_key: str
    ) -> Mapping[str, Any]:
        root = root_arg(arguments, evidence)
        path = evidence.resolve(root, string_arg(arguments, "path", required=True))
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        successes = _signals(lines, success_terms)
        failures = _signals(lines, failure_terms)
        summary = {
            "location": evidence.logical(root, path),
            "evaluated_lines": len(lines),
            "success_signals": successes,
            "failure_signals": failures,
            "status": "signals_conflict" if successes and failures else "success_signals_present" if successes else "failure_signals_present" if failures else "unknown",
        }
        return kernel.envelope(
            operation,
            {payload_key: summary},
            truncated=len(successes) >= 80 or len(failures) >= 80,
            unknowns=("keyword signals require role-specific validation; they are not a causal diagnosis",),
        )

    def boot(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        return summarize(
            arguments,
            operation="summarize_boot_evidence",
            success_terms=("multi-user.target", "graphical.target", "startup finished", "login:"),
            failure_terms=("failed", "panic", "emergency mode", "segfault", "timed out"),
            payload_key="boot_health_evidence",
        )

    def graphics(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        return summarize(
            arguments,
            operation="summarize_graphics_evidence",
            success_terms=("vulkan", "wayland", "weston", "renderer", "gpu", "present"),
            failure_terms=("vk_error", "egl_bad", "failed", "software raster", "llvmpipe", "segfault"),
            payload_key="graphics_health_evidence",
        )

    def app_launch(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        return summarize(
            arguments,
            operation="summarize_app_launch",
            success_terms=(
                "application id",
                "bundle path",
                "loading aot",
                "fengine resolved backend",
                "native is ready",
                "event channels created",
            ),
            failure_terms=(
                "platform view type not registered",
                "missingpluginexception",
                "failed to load",
                "segmentation fault",
                "sigsegv",
                "libllvm",
            ),
            payload_key="app_launch_evidence",
        )

    def render_case(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        return summarize(
            arguments,
            operation="summarize_render_case",
            success_terms=(
                "vulkan device driver",
                "vkcreateswapchain",
                "all systems initialized",
                "pogetfilamentscene oncreated",
                "camera",
                "native is ready",
            ),
            failure_terms=(
                "material version",
                "postcondition",
                "bo allocation",
                "software raster",
                "segmentation fault",
                "sigsegv",
                "libllvm",
            ),
            payload_key="render_case_evidence",
        )

    def read(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        root = root_arg(arguments, evidence)
        excerpt = evidence.read_lines(
            root,
            string_arg(arguments, "path", required=True),
            start_line=int_arg(arguments, "start_line", default=1),
            line_count=int_arg(arguments, "line_count", default=80),
        )
        return kernel.envelope("read_target_evidence", {"target_observation": excerpt}, truncated=bool(excerpt["truncated"]))

    paging = {"root": ROOT_PROPERTY, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}
    summary_schema = object_schema({"root": ROOT_PROPERTY, "path": PATH_PROPERTY}, required=("path",))
    return MCPServer(
        "target_validation",
        kernel,
        [
            Tool("list_validation_bundles", "List existing boot, service, input, graphics and screen evidence artifacts.", object_schema(paging), list_bundles),
            Tool("summarize_boot_evidence", "Extract bounded boot success/failure signals from an existing target log.", summary_schema, boot),
            Tool("summarize_graphics_evidence", "Extract bounded Wayland/Vulkan/Mesa/DRM signals from an existing target log.", summary_schema, graphics),
            Tool("summarize_app_launch", "Extract bounded Flutter/launcher app-start and readiness signals from existing target evidence.", summary_schema, app_launch),
            Tool("summarize_render_case", "Extract bounded QEMU Fluorite render and crash signals without causal diagnosis.", summary_schema, render_case),
            Tool(
                "read_target_evidence",
                "Read a bounded excerpt of existing target evidence; no target command is run.",
                object_schema({"root": ROOT_PROPERTY, "path": PATH_PROPERTY, "start_line": {"type": "integer", "minimum": 1, "default": 1}, "line_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}}, required=("path",)),
                read,
            ),
        ],
        root_aliases=bundles.aliases(),
    )
