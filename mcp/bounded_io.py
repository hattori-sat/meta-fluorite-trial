"""Read-only, allowlisted filesystem adapters used by bounded contexts."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence

from .errors import BoundaryViolation, MCPDomainError
from .kernel import Page, bounded_text, paginate

DEFAULT_SKIPPED_DIRS = frozenset(
    {
        ".git",
        ".fluorite-mcp",
        "downloads",
        "sstate-cache",
        "tmp",
        "deploy",
        "node_modules",
        ".dart_tool",
    }
)
SENSITIVE_DIRS = frozenset({".fluorite-mcp"})


@dataclass(frozen=True)
class SourceMatch:
    location: str
    line: int
    excerpt: str


class BoundedRoots:
    def __init__(
        self,
        roots: Mapping[str, Path],
        *,
        extensions: Iterable[str],
        allowed_name_patterns: Iterable[str] = (),
        skipped_dirs: Iterable[str] = DEFAULT_SKIPPED_DIRS,
        max_file_bytes: int = 2 * 1024 * 1024,
        max_scan_files: int = 4000,
        max_scan_bytes: int = 32 * 1024 * 1024,
    ) -> None:
        self.roots = {alias: path.resolve() for alias, path in roots.items()}
        for root in self.roots.values():
            if any(part in SENSITIVE_DIRS for part in root.parts):
                raise BoundaryViolation("a configured root targets a sensitive directory")
        self.extensions = frozenset(ext.lower() for ext in extensions)
        self.allowed_name_patterns = tuple(
            re.compile(pattern) for pattern in allowed_name_patterns
        )
        self.skipped_dirs = frozenset(skipped_dirs)
        self.max_file_bytes = max_file_bytes
        self.max_scan_files = max_scan_files
        self.max_scan_bytes = max_scan_bytes

    def aliases(self) -> list[str]:
        return sorted(self.roots)

    def _root(self, alias: str) -> Path:
        try:
            root = self.roots[alias]
        except KeyError as exc:
            raise MCPDomainError(
                f"root must be one of: {', '.join(self.aliases())}", code="unknown_root"
            ) from exc
        if not root.exists() or not root.is_dir():
            raise MCPDomainError(f"configured root {alias} is unavailable", code="root_unavailable")
        return root

    def resolve(
        self,
        alias: str,
        relative: str,
        *,
        require_file: bool = True,
        allow_oversized: bool = False,
    ) -> Path:
        if not isinstance(relative, str) or not relative or "\x00" in relative:
            raise BoundaryViolation("path must be a non-empty relative path")
        logical = PurePosixPath(relative.replace("\\", "/"))
        if logical.is_absolute() or ".." in logical.parts:
            raise BoundaryViolation("path traversal is not allowed")
        if any(
            part in self.skipped_dirs or part.startswith(".cache")
            for part in logical.parts
        ):
            raise BoundaryViolation("path targets an excluded directory")
        root = self._root(alias)
        candidate = (root / Path(*logical.parts)).resolve()
        try:
            resolved_relative = candidate.relative_to(root)
        except ValueError as exc:
            raise BoundaryViolation("path resolves outside the configured root") from exc
        if any(
            part in self.skipped_dirs or part.startswith(".cache")
            for part in resolved_relative.parts
        ):
            raise BoundaryViolation("resolved path targets an excluded directory")
        if require_file and (not candidate.is_file() or candidate.is_symlink()):
            raise MCPDomainError("path is not a regular file", code="file_unavailable")
        if require_file:
            self._check_extension(candidate)
            try:
                if not allow_oversized and candidate.stat().st_size > self.max_file_bytes:
                    raise MCPDomainError("file exceeds the bounded read limit", code="file_too_large")
            except OSError as exc:
                raise MCPDomainError("file metadata is unavailable", code="file_unavailable") from exc
        return candidate

    def _check_extension(self, path: Path) -> None:
        if self.extensions and path.suffix.lower() not in self.extensions and not any(
            pattern.fullmatch(path.name) for pattern in self.allowed_name_patterns
        ):
            raise BoundaryViolation("file type is outside this bounded context")

    def _file_type_allowed(self, path: Path) -> bool:
        return not self.extensions or path.suffix.lower() in self.extensions or any(
            pattern.fullmatch(path.name) for pattern in self.allowed_name_patterns
        )

    def logical(self, alias: str, path: Path) -> str:
        relative = path.resolve().relative_to(self._root(alias)).as_posix()
        return f"${alias.upper()}_ROOT/{relative}"

    def _walk(
        self,
        alias: str,
        *,
        metadata_only: bool = False,
        suffixes: Iterable[str] | None = None,
        name_terms: Iterable[str] = (),
    ) -> tuple[list[Path], bool]:
        root = self._root(alias)
        result: list[Path] = []
        total_bytes = 0
        truncated = False
        suffix_filter = {value.lower() for value in suffixes or ()}
        terms = tuple(term.lower() for term in name_terms)

        def mark_walk_error(_error: OSError) -> None:
            nonlocal truncated
            truncated = True

        for directory, names, files in os.walk(
            root, followlinks=False, onerror=mark_walk_error
        ):
            names[:] = sorted(
                name for name in names if name not in self.skipped_dirs and not name.startswith(".cache")
            )
            for name in sorted(files):
                path = Path(directory, name)
                if path.is_symlink() or not self._file_type_allowed(path):
                    continue
                if suffix_filter and path.suffix.lower() not in suffix_filter:
                    continue
                if terms and not any(term in path.name.lower() for term in terms):
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    truncated = True
                    continue
                if not metadata_only and size > self.max_file_bytes:
                    truncated = True
                    continue
                if len(result) >= self.max_scan_files or (
                    not metadata_only and total_bytes + size > self.max_scan_bytes
                ):
                    truncated = True
                    return result, truncated
                result.append(path)
                if not metadata_only:
                    total_bytes += size
        return result, truncated

    def list_files(
        self,
        alias: str,
        *,
        suffixes: Iterable[str] | None = None,
        name_terms: Iterable[str] = (),
        cursor: str | None = None,
        limit: int = 20,
    ) -> tuple[Page, bool]:
        paths, scan_truncated = self._walk(
            alias,
            metadata_only=True,
            suffixes=suffixes,
            name_terms=name_terms,
        )
        suffix_filter = {value.lower() for value in suffixes or ()}
        terms = tuple(term.lower() for term in name_terms)
        values = []
        for path in paths:
            if suffix_filter and path.suffix.lower() not in suffix_filter:
                continue
            if terms and not any(term in path.name.lower() for term in terms):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                scan_truncated = True
                continue
            values.append(
                {
                    "location": self.logical(alias, path),
                    "relative_path": path.relative_to(self._root(alias)).as_posix(),
                    "bytes": size,
                }
            )
        values.sort(key=lambda item: item["relative_path"])
        return paginate(values, cursor, limit), scan_truncated

    def read_lines(
        self,
        alias: str,
        relative: str,
        *,
        start_line: int = 1,
        line_count: int = 80,
        max_chars: int = 24 * 1024,
    ) -> dict[str, object]:
        if isinstance(start_line, bool) or not isinstance(start_line, int) or start_line < 1:
            raise MCPDomainError("start_line must be a positive integer")
        if isinstance(line_count, bool) or not isinstance(line_count, int) or not 1 <= line_count <= 200:
            raise MCPDomainError("line_count must be between 1 and 200")
        path = self.resolve(alias, relative)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            raise MCPDomainError("file could not be read", code="file_unavailable") from exc
        end = min(len(lines), start_line - 1 + line_count)
        excerpt, char_truncated = bounded_text("\n".join(lines[start_line - 1 : end]), max_chars)
        return {
            "location": self.logical(alias, path),
            "start_line": start_line,
            "end_line": end,
            "total_lines": len(lines),
            "text": excerpt,
            "truncated": char_truncated or end < len(lines),
            "next_start_line": end + 1 if end < len(lines) else None,
        }

    def tail_lines(
        self, alias: str, relative: str, *, line_count: int = 80, max_chars: int = 24 * 1024
    ) -> dict[str, object]:
        if isinstance(line_count, bool) or not isinstance(line_count, int) or not 1 <= line_count <= 200:
            raise MCPDomainError("line_count must be between 1 and 200")
        path = self.resolve(alias, relative, allow_oversized=True)
        try:
            file_bytes = path.stat().st_size
        except OSError as exc:
            raise MCPDomainError("file metadata is unavailable", code="file_unavailable") from exc
        if file_bytes <= self.max_file_bytes:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exc:
                raise MCPDomainError("file could not be read", code="file_unavailable") from exc
            start = max(0, len(lines) - line_count)
            excerpt, char_truncated = bounded_text("\n".join(lines[start:]), max_chars)
            return {
                "location": self.logical(alias, path),
                "start_line": start + 1,
                "end_line": len(lines),
                "total_lines": len(lines),
                "text": excerpt,
                "truncated": char_truncated or start > 0,
                "file_bytes": file_bytes,
            }

        tail_byte_cap = max(64 * 1024, min(256 * 1024, max_chars * 8))
        bytes_to_read = min(file_bytes, tail_byte_cap)
        try:
            with path.open("rb") as handle:
                handle.seek(file_bytes - bytes_to_read)
                chunk = handle.read(bytes_to_read)
        except OSError as exc:
            raise MCPDomainError("file could not be read", code="file_unavailable") from exc

        text = chunk.decode("utf-8", errors="replace")
        if file_bytes > bytes_to_read and text:
            first_newline = text.find("\n")
            text = text[first_newline + 1 :] if first_newline >= 0 else ""
        lines = text.splitlines()
        start = max(0, len(lines) - line_count)
        excerpt, char_truncated = bounded_text("\n".join(lines[start:]), max_chars)
        return {
            "location": self.logical(alias, path),
            "start_line": None,
            "end_line": None,
            "total_lines": None,
            "text": excerpt,
            "truncated": True,
            "file_bytes": file_bytes,
            "scanned_tail_bytes": bytes_to_read,
            "tail_char_truncated": char_truncated or start > 0,
        }

    def search_literal(
        self,
        alias: str,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 20,
        max_matches: int = 500,
    ) -> tuple[Page, bool]:
        if not isinstance(query, str) or not 2 <= len(query) <= 120:
            raise MCPDomainError("query must contain 2 to 120 characters")
        if any(ord(character) < 32 and character not in "\t" for character in query):
            raise MCPDomainError("query contains control characters")
        paths, scan_truncated = self._walk(alias)
        needle = query.casefold()
        matches: list[dict[str, object]] = []
        match_truncated = False
        read_omission = False
        for path in paths:
            try:
                with path.open("r", encoding="utf-8", errors="replace") as handle:
                    for number, line in enumerate(handle, start=1):
                        if needle in line.casefold():
                            excerpt, _ = bounded_text(line.rstrip(), 500)
                            matches.append(
                                {
                                    "location": self.logical(alias, path),
                                    "relative_path": path.relative_to(self._root(alias)).as_posix(),
                                    "line": number,
                                    "excerpt": excerpt,
                                }
                            )
                            if len(matches) >= max_matches:
                                match_truncated = True
                                break
            except OSError:
                read_omission = True
                continue
            if match_truncated:
                break
        return (
            paginate(matches, cursor, limit),
            scan_truncated or match_truncated or read_omission,
        )
