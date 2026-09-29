#!/usr/bin/env python3
"""Refresh tracked metadata for the canonical project layer."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAYER = ROOT / "layers" / "meta-fluorite-trial"
LOCK = ROOT / "manifests" / "baseline-sources.lock"
IDENTITY_METADATA = re.compile(
    br"^(From|Signed-off-by|Co-authored-by|Tested-by|Reviewed-by): .*?$",
    flags=re.MULTILINE,
)
EMAIL_ADDRESS = re.compile(
    br"(?<![A-Za-z0-9._%+-])"
    br"(?!(?:fluorite|fluorite-trial|fluorite-devtool)@example\.invalid(?![A-Za-z0-9.-]))"
    br"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def calculate() -> tuple[str, str, int]:
    repository_rows: list[bytes] = []
    normalized_rows: list[bytes] = []
    files = sorted(path for path in LAYER.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(ROOT / "layers").as_posix()
        content = path.read_bytes()
        if EMAIL_ADDRESS.search(content):
            raise SystemExit(f"baseline refresh: non-redacted email in {relative}")
        repository_rows.append(
            f"{relative} {sha256(content)}\n".encode("utf-8")
        )
        normalized = IDENTITY_METADATA.sub(
            lambda match: match.group(1) + b": NORMALIZED", content
        )
        normalized_rows.append(
            f"{relative} {sha256(normalized)}\n".encode("utf-8")
        )
    return (
        sha256(b"".join(repository_rows)),
        sha256(b"".join(normalized_rows)),
        len(files),
    )


def main() -> None:
    if subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0:
        raise SystemExit("baseline refresh: repository is not a Git worktree")
    repository_tree, normalized_tree, file_count = calculate()
    replacements = {
        "meta_fluorite_trial_repository_tree_sha256": repository_tree,
        "meta_fluorite_trial_normalized_identity_tree_sha256": normalized_tree,
        "meta_fluorite_trial_file_count": str(file_count),
    }
    lines = LOCK.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in replacements:
            output.append(f"{key}={replacements[key]}")
            seen.add(key)
        else:
            output.append(line)
    missing = set(replacements) - seen
    if missing:
        raise SystemExit(
            "baseline refresh: lock keys missing: " + ", ".join(sorted(missing))
        )
    LOCK.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(
        "baseline-refresh=PASS "
        f"files={file_count} repository_tree_sha256={repository_tree} "
        f"normalized_identity_tree_sha256={normalized_tree}"
    )


if __name__ == "__main__":
    main()
