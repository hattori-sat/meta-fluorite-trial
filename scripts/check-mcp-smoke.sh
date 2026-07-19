#!/usr/bin/env bash
set -euo pipefail

root=${1:-.}

if ! test -f "$root/mcp/__init__.py"; then
    echo "MCP smoke check: SKIP (MCP package not present)"
    exit 0
fi

if ! test -f "$root/mcp/__main__.py"; then
    echo "MCP smoke check: FAIL (MCP package has no module entry point)"
    exit 1
fi

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
    echo "MCP smoke check: FAIL (Python 3.11+ missing)"
    exit 1
fi

smoke_test=$(find "$root/tests" -type f -name 'test_mcp*.py' -print -quit 2>/dev/null || true)
if test -z "$smoke_test"; then
    echo "MCP smoke check: FAIL (MCP package has no test_mcp*.py smoke test)"
    exit 1
fi

(
    cd "$root"
    PYTHONDONTWRITEBYTECODE=1 "$python_command" -m unittest discover \
        -s tests -p 'test_mcp*.py' -v
)

echo "MCP smoke check: PASS"
