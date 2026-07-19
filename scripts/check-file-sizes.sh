#!/usr/bin/env bash
set -euo pipefail

root=${1:-.}
max_bytes=${MAX_FILE_BYTES:-1048576}

case "$max_bytes" in
    ''|*[!0-9]*)
        echo "file size check: FAIL (MAX_FILE_BYTES must be a positive integer)"
        exit 2
        ;;
esac

if test "$max_bytes" -eq 0; then
    echo "file size check: FAIL (MAX_FILE_BYTES must be greater than zero)"
    exit 2
fi

if ! git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "file size check: FAIL (not a Git worktree)"
    exit 1
fi

checked=0
failed=0
while IFS= read -r -d '' relative_path; do
    file_path=$root/$relative_path
    if test -L "$file_path" || ! test -f "$file_path"; then
        continue
    fi

    checked=$((checked + 1))
    size=$(wc -c < "$file_path")
    size=${size//[[:space:]]/}
    if test "$size" -gt "$max_bytes"; then
        printf 'file size check: too large (%s bytes): %s\n' "$size" "$relative_path"
        failed=1
    fi
done < <(git -C "$root" ls-files --cached --others --exclude-standard -z)

if test "$failed" -ne 0; then
    printf 'file size check: FAIL (limit %s bytes)\n' "$max_bytes"
    exit 1
fi

printf 'file size check: PASS (%d files, limit %s bytes)\n' "$checked" "$max_bytes"
