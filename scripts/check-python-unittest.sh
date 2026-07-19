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
    echo "Python unittest check: FAIL (Python 3.11+ missing)"
    exit 1
fi

if ! test -d "$root/tests"; then
    echo "Python unittest check: FAIL (tests directory missing)"
    exit 1
fi

(
    cd "$root"
    PYTHONDONTWRITEBYTECODE=1 "$python_command" -m unittest discover \
        -s tests -p 'test_*.py' -v
)

echo "Python unittest check: PASS"
