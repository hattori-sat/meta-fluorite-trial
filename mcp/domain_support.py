"""Adapters shared by domain implementations without sharing domain vocabulary."""

from __future__ import annotations

from typing import Any, Mapping

from .bounded_io import BoundedRoots
from .errors import MCPDomainError


def string_arg(
    arguments: Mapping[str, Any], name: str, *, default: str | None = None, required: bool = False
) -> str:
    value = arguments.get(name, default)
    if required and (not isinstance(value, str) or not value):
        raise MCPDomainError(f"{name} is required")
    if not isinstance(value, str):
        raise MCPDomainError(f"{name} must be a string")
    return value


def int_arg(arguments: Mapping[str, Any], name: str, *, default: int) -> int:
    value = arguments.get(name, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MCPDomainError(f"{name} must be an integer")
    return value


def page_args(arguments: Mapping[str, Any]) -> tuple[str | None, int]:
    cursor = arguments.get("cursor")
    if cursor is not None and not isinstance(cursor, str):
        raise MCPDomainError("cursor must be a string")
    return cursor, int_arg(arguments, "limit", default=20)


def root_arg(arguments: Mapping[str, Any], sources: BoundedRoots) -> str:
    root = string_arg(arguments, "root", default="repository")
    if root not in sources.roots:
        raise MCPDomainError(
            f"root must be one of: {', '.join(sources.aliases())}", code="unknown_root"
        )
    return root
