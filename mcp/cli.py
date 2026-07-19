"""CLI dispatch for all Fluorite MCP bounded contexts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .config import MCPConfig
from .domains import factories
from .errors import MCPDomainError


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Fluorite bounded-context MCP server")
    result.add_argument("server", choices=sorted(factories()))
    result.add_argument("--config", help="Local JSON configuration (never commit host-specific values)")
    result.add_argument("--list-tools", action="store_true", help="Print tool names and exit")
    return result


def runtime_supported(version_info: Sequence[int] = sys.version_info) -> bool:
    """Return whether the interpreter satisfies the deployed runtime floor."""

    return tuple(version_info[:2]) >= (3, 10)


def main(argv: list[str] | None = None) -> int:
    if not runtime_supported():
        print("Fluorite MCP requires Python 3.10 or newer", file=sys.stderr)
        return 2
    arguments = parser().parse_args(argv)
    try:
        config = MCPConfig.load(arguments.config)
        server = factories()[arguments.server](config)
    except MCPDomainError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}), file=sys.stderr)
        return 2
    if arguments.list_tools:
        for name in server.tool_names:
            print(name)
        return 0
    server.serve()
    return 0
