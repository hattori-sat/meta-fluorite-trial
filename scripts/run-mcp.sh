#!/usr/bin/env bash
set -euo pipefail

if test "$#" -ne 1; then
    echo "Usage: scripts/run-mcp.sh <server-id>" >&2
    exit 2
fi

python_command=
python_flags=(-E -S -B)
for candidate in "${PYTHON:-}" python3.13 python3.12 python3.11 python3.10; do
    test -n "$candidate" || continue
    if command -v "$candidate" >/dev/null 2>&1 && \
        "$candidate" "${python_flags[@]}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
        python_command=$candidate
        break
    fi
done

if test -z "$python_command"; then
    echo "MCP startup: Python 3.10 or newer is required" >&2
    exit 1
fi

# Ignore inherited Python path/home/startup settings, skip site customization and
# neither create nor rely on repository-local bytecode during the fixed runtime.
exec "$python_command" "${python_flags[@]}" -m mcp "$1"
