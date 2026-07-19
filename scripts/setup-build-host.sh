#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: AGL_ROOT=/path/to/agl [AGL_BUILD_DIR=/path/to/build] \
       [AGL_CACHE_ROOT=/path/to/cache-filesystem] scripts/setup-build-host.sh

Checks an existing Linux AGL/Yocto build host and source tree.
It does not source an environment, install packages, run BitBake, or delete caches.
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

if test "$(uname -s)" != "Linux"; then
    echo "build-host setup: SKIP (host is not Linux)"
    exit 0
fi

failed=0

require_command() {
    if command -v "$1" >/dev/null 2>&1; then
        printf 'build-host setup: %-18s PASS\n' "$1"
    else
        printf 'build-host setup: %-18s MISSING\n' "$1"
        failed=1
    fi
}

for command_name in \
    bash git make python3 file gcc g++ gawk patch perl tar cpio diffstat chrpath \
    rpcgen socat texi2any unzip wget xz zstd lz4 sort; do
    require_command "$command_name"
done

version_at_least() {
    current=$1
    minimum=$2
    first=$(printf '%s\n%s\n' "$minimum" "$current" | sort -V | head -n 1)
    test "$first" = "$minimum"
}

check_minimum_version() {
    label=$1
    current=$2
    minimum=$3
    if test -n "$current" && version_at_least "$current" "$minimum"; then
        printf 'build-host setup: %-18s PASS\n' "$label"
    else
        printf 'build-host setup: %-18s MISSING\n' "$label"
        failed=1
    fi
}

if command -v sort >/dev/null 2>&1; then
    minimum_git_version=1.8.3
    minimum_git_patchlevel=1
    check_minimum_version "Git minimum+" "$(git --version | awk '{print $3}')" \
        "${minimum_git_version}.${minimum_git_patchlevel}"
    check_minimum_version "tar 1.28+" "$(tar --version | sed -n '1s/.* \([0-9][0-9.]*\).*/\1/p')" "1.28"
    check_minimum_version "GCC 8+" "$(gcc -dumpfullversion -dumpversion)" "8"
    check_minimum_version "GNU make 4+" "$(make --version | sed -n '1s/.* \([0-9][0-9.]*\).*/\1/p')" "4"
fi

if python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    echo "build-host setup: Yocto Python 3.8+ PASS"
else
    echo "build-host setup: Yocto Python 3.8+ MISSING"
    failed=1
fi

if python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    echo "build-host setup: remote MCP Python 3.10+ PASS"
else
    echo "build-host setup: remote MCP Python 3.10+ MISSING"
    failed=1
fi

if test -r /proc/meminfo; then
    memory_kib=$(sed -n 's/^MemTotal:[[:space:]]*\([0-9][0-9]*\).*/\1/p' /proc/meminfo)
    if test -n "$memory_kib" && test "$memory_kib" -ge 8388608; then
        echo "build-host setup: memory 8 GiB+ PASS"
    else
        echo "build-host setup: memory 8 GiB+ MISSING"
        failed=1
    fi
fi

if locale -a 2>/dev/null | grep -Eqi '^en_US\.(utf8|UTF-8)$'; then
    echo "build-host setup: en_US.UTF-8 locale PASS"
else
    echo "build-host setup: en_US.UTF-8 locale MISSING"
    failed=1
fi

if test -z "${AGL_ROOT:-}"; then
    echo "build-host setup: AGL_ROOT MISSING"
    failed=1
elif ! test -d "$AGL_ROOT"; then
    echo "build-host setup: AGL_ROOT directory MISSING"
    failed=1
else
    echo "build-host setup: AGL_ROOT directory PASS"

    for relative_path in .repo/manifest.xml .repo/repo/repo meta-agl/scripts/aglsetup.sh; do
        if test -r "$AGL_ROOT/$relative_path"; then
            printf 'build-host setup: %-36s PASS\n' "$relative_path"
        else
            printf 'build-host setup: %-36s MISSING\n' "$relative_path"
            failed=1
        fi
    done

    if df -Pk "$AGL_ROOT" >/dev/null 2>&1; then
        echo "build-host setup: source-filesystem access PASS"
    else
        echo "build-host setup: source-filesystem access UNKNOWN"
        failed=1
    fi
fi

if test -n "${AGL_BUILD_DIR:-}"; then
    if test -r "$AGL_BUILD_DIR/conf/local.conf" && test -r "$AGL_BUILD_DIR/conf/bblayers.conf"; then
        echo "build-host setup: AGL_BUILD_DIR configuration PASS"
    else
        echo "build-host setup: AGL_BUILD_DIR configuration MISSING"
        failed=1
    fi
else
    echo "build-host setup: AGL_BUILD_DIR UNKNOWN (optional)"
fi

if test -n "${AGL_CACHE_ROOT:-}"; then
    if test -d "$AGL_CACHE_ROOT"; then
        cache_available_kib=$(df -Pk "$AGL_CACHE_ROOT" | tail -n 1 | tr -s ' ' | cut -d ' ' -f 4)
        if test "$cache_available_kib" -ge 94371840; then
            echo "build-host setup: cache filesystem 90 GiB+ free PASS"
        else
            echo "build-host setup: cache filesystem 90 GiB+ free MISSING"
            failed=1
        fi
    else
        echo "build-host setup: AGL_CACHE_ROOT directory MISSING"
        failed=1
    fi
else
    echo "build-host setup: AGL_CACHE_ROOT UNKNOWN (set to verify build filesystem capacity)"
fi

if command -v bitbake >/dev/null 2>&1; then
    echo "build-host setup: sourced BitBake environment PASS"
else
    echo "build-host setup: sourced BitBake environment UNKNOWN (not sourced automatically)"
fi

if test "$failed" -ne 0; then
    echo "build-host setup: FAIL"
    echo "See docs/setup.md for optional, manually approved installation commands."
    exit 1
fi

echo "build-host setup: PASS (check-only; no build state changed)"
