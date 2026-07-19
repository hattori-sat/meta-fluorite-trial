#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

failed=0
patterns=(
    '(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])'
    '(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}(?![A-Fa-f0-9:])'
    '(?<![A-Za-z0-9:.\[])(?=[A-Fa-f0-9:.]*[A-Fa-f0-9])(?=[A-Fa-f0-9:.]*:)[A-Fa-f0-9:.]*::[A-Fa-f0-9:.]*(?![A-Za-z0-9:.\]])'
    '(?<![A-Za-z0-9_])\[(?=[A-Fa-f0-9:]*:[A-Fa-f0-9:]*:)[A-Fa-f0-9:]{3,}\](?![A-Za-z0-9_])'
    '(?<![A-Za-z0-9_/@$.-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+(?:internal|local|lan|corp|private|localdomain)(?![A-Za-z0-9_.-])'
    '/(?:Users|home)/[A-Za-z0-9._-]+/'
    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    '(?<![A-Za-z0-9._/-])(?:ssh://)?[A-Za-z0-9._-]+@(?:[A-Za-z0-9._-]+|\[[^]]+\])'
    'https://github\.com/[A-Za-z0-9_.-]+/meta-fluorite-trial(?:\.git)?'
    '-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----'
    '(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])'
    '(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})(?![A-Za-z0-9])'
)

candidate_files() {
    if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        while IFS= read -r -d '' relative; do
            printf '%s\0' "$ROOT/$relative"
        done < <(git -C "$ROOT" ls-files -z --cached --others --exclude-standard)
    else
        find "$ROOT" -path "$ROOT/.git" -prune -o -type f -print0
    fi
}

for pattern in "${patterns[@]}"; do
    while IFS= read -r -d '' file; do
        case "${file##*/}" in
            Makefile) ;;
            *)
                case "$file" in
                    *.conf|*.env|*.json|*.lock|*.md|*.patch|*.py|*.sh|*.template|*.toml|*.xml|*.yaml|*.yml|*.key|*.pem) ;;
                    *) continue ;;
                esac
                ;;
        esac
        if rg -q --pcre2 -- "$pattern" "$file"; then
            failed=1
            echo "privacy check: blocked candidate file detected"
            printf '%s\n' "${file#"$ROOT"/}"
        fi
    done < <(candidate_files)
done

if test "$failed" -ne 0; then
    echo "privacy check: FAIL (matched values intentionally omitted)"
    exit 1
fi

echo "privacy check: PASS"
