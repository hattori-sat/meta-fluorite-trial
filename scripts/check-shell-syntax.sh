#!/usr/bin/env bash
set -euo pipefail

root=${1:-.}

if ! git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "shell syntax check: FAIL (not a Git worktree)"
    exit 1
fi

checked=0
failed=0
while IFS= read -r -d '' relative_path; do
    checked=$((checked + 1))
    if ! bash -n "$root/$relative_path"; then
        printf 'shell syntax check: FAIL %s\n' "$relative_path"
        failed=1
    fi
done < <(git -C "$root" ls-files --cached --others --exclude-standard -z -- '*.sh')

if test "$checked" -eq 0; then
    echo "shell syntax check: FAIL (no shell scripts found)"
    exit 1
fi

if test "$failed" -ne 0; then
    echo "shell syntax check: FAIL"
    exit 1
fi

printf 'shell syntax check: PASS (%d files)\n' "$checked"
