#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/setup-macos.sh

Checks macOS tools used for repository work and local QEMU validation.
It does not install packages, start QEMU, or modify system settings.
EOF
}

if test "${1:-}" = "--help" || test "${1:-}" = "-h"; then
    usage
    exit 0
fi

if test "$#" -ne 0; then
    usage >&2
    exit 2
fi

qemu_target=${FLUORITE_MAC_QEMU_TARGET:-foundation}
case "$qemu_target" in
    foundation|qemux86-64|qemuarm64) ;;
    *) echo "macOS setup: FLUORITE_MAC_QEMU_TARGET is unsupported" >&2; exit 2 ;;
esac

if test "$(uname -s)" != "Darwin"; then
    echo "macOS setup: SKIP (host is not macOS)"
    exit 0
fi

failed=0

require_command() {
    if command -v "$1" >/dev/null 2>&1; then
        printf 'macOS setup: %-24s PASS\n' "$1"
    else
        printf 'macOS setup: %-24s MISSING\n' "$1"
        failed=1
    fi
}

for command_name in bash git make rg ssh xcode-select qemu-system-aarch64; do
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
    echo "macOS setup: Python 3.11+ PASS"
else
    echo "macOS setup: Python 3.11+ MISSING"
    failed=1
fi

if command -v xcode-select >/dev/null 2>&1; then
    if xcode-select -p >/dev/null 2>&1; then
        echo "macOS setup: Xcode command line tools PASS"
    else
        echo "macOS setup: Xcode command line tools MISSING"
        failed=1
    fi
fi

if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo "macOS setup: qemu-system-x86_64 PASS"
elif test "$qemu_target" = qemux86-64; then
    echo "macOS setup: qemu-system-x86_64 MISSING (required for selected target)"
    failed=1
else
    echo "macOS setup: qemu-system-x86_64 UNKNOWN (optional for x86 baseline)"
fi

if command -v qemu-system-aarch64 >/dev/null 2>&1; then
    case "$(qemu-system-aarch64 -accel help 2>/dev/null || true)" in
        *hvf*) echo "macOS setup: QEMU HVF accelerator PASS" ;;
        *)
            if test "$qemu_target" = qemuarm64; then
                echo "macOS setup: QEMU HVF accelerator MISSING (required for selected target)"
                failed=1
            else
                echo "macOS setup: QEMU HVF accelerator UNKNOWN"
            fi
            ;;
    esac
fi

if test "$failed" -ne 0; then
    echo "macOS setup: FAIL"
    echo "See docs/setup.md for optional, manually approved installation commands."
    exit 1
fi

echo "macOS setup: PASS for $qemu_target (check-only; no system changes)"
