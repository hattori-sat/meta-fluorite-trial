#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/setup-project.sh [repository-root]

Checks the local project prerequisites and canonical repository identity.
It does not install packages, initialize builds, or modify files.
EOF
}

if test "${1:-}" = "--help" || test "${1:-}" = "-h"; then
    usage
    exit 0
fi

if test "$#" -gt 1; then
    usage >&2
    exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=${1:-$(CDPATH= cd -- "$script_dir/.." && pwd)}
failed=0

require_command() {
    if command -v "$1" >/dev/null 2>&1; then
        printf 'project setup: %-12s PASS\n' "$1"
    else
        printf 'project setup: %-12s MISSING\n' "$1"
        failed=1
    fi
}

for command_name in bash git make rg; do
    require_command "$command_name"
done

python_command=
for candidate in "${PYTHON:-}" python3.11 python3.12 python3.13 python3; do
    test -n "$candidate" || continue
    if command -v "$candidate" >/dev/null 2>&1 && \
        "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
        python_command=$candidate
        break
    fi
done

if test -n "$python_command"; then
    echo "project setup: Python 3.11+ PASS"
else
    echo "project setup: Python 3.11+ MISSING"
    failed=1
fi

if ! test -d "$root"; then
    echo "project setup: repository root MISSING"
    exit 1
fi

for required_file in AGENTS.md TASKS.md Makefile scripts/assert-canonical-repository.sh; do
    if test -f "$root/$required_file"; then
        printf 'project setup: %-32s PASS\n' "$required_file"
    else
        printf 'project setup: %-32s MISSING\n' "$required_file"
        failed=1
    fi
done

if test -f "$root/scripts/assert-canonical-repository.sh"; then
    if (cd "$root" && bash scripts/assert-canonical-repository.sh); then
        :
    else
        failed=1
    fi
fi

if test "$failed" -ne 0; then
    echo "project setup: FAIL"
    echo "See docs/setup.md for optional, manually approved installation commands."
    exit 1
fi

echo "project setup: PASS (check-only; no files changed)"
