#!/usr/bin/env bash
set -euo pipefail

root=${1:-.}

python_command=
for candidate in "${PYTHON:-}" python3.11 python3.12 python3.13 python3; do
    test -n "$candidate" || continue
    if command -v "$candidate" >/dev/null 2>&1 && \
        "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
        python_command=$candidate
        break
    fi
done

if test -z "$python_command"; then
    echo "Markdown link check: FAIL (Python 3.11+ missing)"
    exit 1
fi

PYTHONDONTWRITEBYTECODE=1 "$python_command" - "$root" <<'PY'
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path


root = Path(sys.argv[1]).resolve()
if not root.is_dir():
    print("Markdown link check: FAIL (repository root missing)")
    raise SystemExit(1)

excluded_directories = {".git", ".venv", "node_modules", "__pycache__"}
link_pattern = re.compile(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+['\"][^)]*['\"])?\)")
heading_pattern = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
explicit_anchor_pattern = re.compile(r"<(?:a|span)\s+(?:name|id)=['\"]([^'\"]+)['\"]", re.IGNORECASE)
external_schemes = {"data", "http", "https", "mailto", "tel"}


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in excluded_directories for part in path.relative_to(root).parts)
    )


def content_without_fenced_code(path: Path) -> str:
    kept: list[str] = []
    in_fence = False
    marker = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            current = stripped[:3]
            if not in_fence:
                in_fence = True
                marker = current
            elif current == marker:
                in_fence = False
                marker = ""
            continue
        if not in_fence:
            kept.append(line)
    return "\n".join(kept)


def github_slug(text: str) -> str:
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "").strip().lower()
    result: list[str] = []
    for character in text:
        if character.isalnum() or character in {"-", "_"}:
            result.append(character)
        elif character.isspace():
            result.append("-")
    return re.sub(r"-+", "-", "".join(result)).strip("-")


anchor_cache: dict[Path, set[str]] = {}


def anchors(path: Path) -> set[str]:
    if path in anchor_cache:
        return anchor_cache[path]

    text = content_without_fenced_code(path)
    found = set(explicit_anchor_pattern.findall(text))
    repetitions: dict[str, int] = {}
    for line in text.splitlines():
        match = heading_pattern.match(line)
        if not match:
            continue
        base = github_slug(match.group(1))
        if not base:
            continue
        occurrence = repetitions.get(base, 0)
        found.add(base if occurrence == 0 else f"{base}-{occurrence}")
        repetitions[base] = occurrence + 1
    anchor_cache[path] = found
    return found


errors: list[str] = []
checked = 0
for source in markdown_files():
    text = content_without_fenced_code(source)
    for match in link_pattern.finditer(text):
        raw_target = (match.group(1) or match.group(2)).strip()
        parsed = urllib.parse.urlsplit(raw_target)
        if parsed.scheme.lower() in external_schemes or raw_target.startswith("//"):
            continue

        checked += 1
        decoded_path = urllib.parse.unquote(parsed.path)
        fragment = urllib.parse.unquote(parsed.fragment)
        if decoded_path.startswith("/"):
            errors.append(f"{source.relative_to(root)}: absolute internal path is not portable: {raw_target}")
            continue

        destination = source if not decoded_path else (source.parent / decoded_path).resolve()
        try:
            destination.relative_to(root)
        except ValueError:
            errors.append(f"{source.relative_to(root)}: link escapes repository: {raw_target}")
            continue

        if not destination.exists():
            errors.append(f"{source.relative_to(root)}: missing target: {raw_target}")
            continue

        if fragment and destination.is_file() and destination.suffix.lower() == ".md":
            if fragment not in anchors(destination):
                errors.append(f"{source.relative_to(root)}: missing anchor: {raw_target}")

if errors:
    for error in errors:
        print(f"Markdown link check: {error}")
    print(f"Markdown link check: FAIL ({len(errors)} errors)")
    raise SystemExit(1)

print(f"Markdown link check: PASS ({checked} internal links)")
PY
