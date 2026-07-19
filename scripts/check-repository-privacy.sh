#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

failed=0
patterns=(
    '(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])'
    '/(?:Users|home)/[A-Za-z0-9._-]+/'
    '(?:ssh://)?[A-Za-z0-9._-]+@(?:[A-Za-z0-9._-]+|\[[^]]+\])'
    'https://github\.com/[A-Za-z0-9_.-]+/meta-fluorite-trial(?:\.git)?'
)

for pattern in "${patterns[@]}"; do
    while IFS= read -r -d '' file; do
        if rg -q --pcre2 "$pattern" "$file"; then
            failed=1
            echo "privacy check: blocked candidate file detected"
            printf '%s\n' "${file#"$ROOT"/}"
        fi
    done < <(find "$ROOT" \
        \( -path "$ROOT/.git" -o -path "$ROOT/layers" \) -prune -o \
        -type f ! -path "$ROOT/scripts/check-repository-privacy.sh" \
        \( -name '*.md' -o -name '*.toml' -o -name '*.sh' -o -name '*.env' \
           -o -name '*.yml' -o -name '*.yaml' \) -print0)
done

if test "$failed" -ne 0; then
    echo "privacy check: FAIL (matched values intentionally omitted)"
    exit 1
fi

echo "privacy check: PASS"
