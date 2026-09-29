#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/reuse-mini-build-receiver.sh <remote-bundle> <tip-full-commit>

The bundle must already be present on the build host. The helper updates one
fixed receiver and checks out the requested exact commit. It refuses dirty
receivers and active BitBake processes, and it never touches the canonical
checkout or creates a commit-suffixed TMPDIR.

Required environment:
  BUILD_HOST BUILD_RECEIVER BUILD_DIR BUILD_TMPDIR
EOF
}

test "${1:-}" != "--help" || { usage; exit 0; }
test "$#" -eq 2 || { usage >&2; exit 2; }

build_host=${BUILD_HOST:?BUILD_HOST must be set in the local environment}
remote_bundle=$1
tip=$2
receiver=${BUILD_RECEIVER:?BUILD_RECEIVER must be set in the local environment}
build_dir=${BUILD_DIR:?BUILD_DIR must be set in the local environment}
tmpdir=${BUILD_TMPDIR:?BUILD_TMPDIR must be set in the local environment}

if ! [[ "$tip" =~ ^[a-fA-F0-9]{40}$ ]]; then
    echo "reuse-mini-build: tip must be a 40-character full SHA" >&2
    exit 2
fi

ssh "$build_host" bash -s -- "$remote_bundle" "$tip" "$receiver" "$build_dir" "$tmpdir" <<'REMOTE'
set -euo pipefail

remote_bundle=$1
tip=$2
receiver=${3:?fixed receiver role is required}
build_dir=${4:?fixed build role is required}
tmpdir=${5:?fixed TMPDIR role is required}

test -f "$remote_bundle" || { echo "bundle is missing" >&2; exit 1; }
test -d "$receiver" || { echo "fixed receiver is missing" >&2; exit 1; }
git -C "$receiver" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "fixed receiver is not a Git worktree" >&2
    exit 1
}
test -d "$build_dir" || { echo "fixed build directory is missing" >&2; exit 1; }
test -d "$tmpdir" || { echo "fixed TMPDIR is missing" >&2; exit 1; }
command -v pgrep >/dev/null 2>&1 || { echo "pgrep is required for preflight" >&2; exit 1; }
command -v seq >/dev/null 2>&1 || { echo "seq is required for bounded preflight" >&2; exit 1; }

if pgrep -x bitbake >/dev/null 2>&1 || pgrep -x bitbake-server >/dev/null 2>&1; then
    echo "a BitBake process is active; refusing receiver update" >&2
    exit 1
fi

# Raw runtime payloads live in the fixed receiver's untracked evidence/
# directory. Ignore only that bounded path; tracked changes and any other
# untracked receiver content still block a handoff.
test -z "$(git -C "$receiver" status --porcelain --untracked-files=all -- . ':(exclude)evidence/**')" || {
    echo "fixed receiver is dirty; refusing to overwrite local changes" >&2
    exit 1
}

git -C "$receiver" bundle verify "$remote_bundle" >/dev/null || {
    echo "bundle verification failed; refusing receiver update" >&2
    exit 1
}
git -C "$receiver" bundle list-heads "$remote_bundle" |
    awk -v requested="$tip" '$1 == requested { found = 1 } END { exit !found }' || {
        echo "bundle does not contain the requested tip; refusing receiver update" >&2
        exit 1
    }

test -r "$build_dir/conf/local.conf" || { echo "fixed local.conf is missing" >&2; exit 1; }
test -r "$build_dir/conf/bblayers.conf" || { echo "fixed bblayers.conf is missing" >&2; exit 1; }
grep -Fq "$receiver/layers/meta-fluorite-trial" "$build_dir/conf/bblayers.conf" || {
    echo "build configuration does not use the fixed receiver layer" >&2
    exit 1
}
command -v timeout >/dev/null 2>&1 || { echo "timeout is required for bounded preflight" >&2; exit 1; }

canonical_dir() {
    (cd -P -- "$1" 2>/dev/null && pwd -P)
}

selected_build=$(canonical_dir "$build_dir") || { echo "cannot resolve fixed build directory" >&2; exit 1; }
selected_tmpdir=$(canonical_dir "$tmpdir") || { echo "cannot resolve fixed TMPDIR" >&2; exit 1; }

# The active AGL source checkout may be separate from /mnt/yocto's build and
# receiver trees. Find only AGL's external/poky layout, then bind it to the
# existing build through that build's persisted TEMPLATECONF value. This
# excludes a nearby standalone Poky checkout that can select a nonexistent
# template and terminate OE initialization.
test -n "${HOME:-}" && test -d "$HOME" || {
    echo "oe-init-search-root-missing: HOME" >&2
    exit 1
}
search_roots=("$HOME")
test ! -d /mnt/yocto || search_roots+=(/mnt/yocto)
oe_init_candidates=()
while IFS= read -r candidate; do
    test -n "$candidate" && oe_init_candidates+=("$candidate")
done < <(
    find "${search_roots[@]}" -maxdepth 10 \
        \( -name .git -o -name .cache -o -name .local -o -name .npm \
        -o -name node_modules -o -name tmp -o -name downloads \
        -o -name sstate-cache \) -prune -o \
        -type f -path '*/external/poky/oe-init-build-env' -print 2>/dev/null |
        sort -u
)
test "${#oe_init_candidates[@]}" -gt 0 || {
    echo "oe-init-not-found: expected AGL external/poky under fixed search roots" >&2
    exit 1
}
test -r "$build_dir/conf/templateconf.cfg" || {
    echo "build-templateconf-missing: refusing to guess the OE source tree" >&2
    exit 1
}
templateconf=$(sed -n '1p' "$build_dir/conf/templateconf.cfg")
test -n "$templateconf" || {
    echo "build-templateconf-empty: refusing to guess the OE source tree" >&2
    exit 1
}
matching_oe_inits=()
for candidate in "${oe_init_candidates[@]}"; do
    candidate_poky=${candidate%/oe-init-build-env}
    if [[ "$templateconf" = /* ]]; then
        template_dir=$templateconf
    else
        template_dir="$candidate_poky/$templateconf"
    fi
    test -d "$template_dir" && matching_oe_inits+=("$candidate")
done
test "${#matching_oe_inits[@]}" -gt 0 || {
    echo "oe-init-template-mismatch: no AGL external/poky contains the fixed build template" >&2
    exit 1
}
test "${#matching_oe_inits[@]}" -eq 1 || {
    echo "oe-init-ambiguous: multiple AGL external/poky trees match the fixed build template" >&2
    exit 1
}
oe_init=${matching_oe_inits[0]}

metadata_rc=0
metadata=$( (
    set +u
    if source "$oe_init" "$build_dir" >/dev/null 2>&1; then :; else
        source_rc=$?
        printf '__OE_INIT_FAILURE__=%s\n' "$source_rc"
        exit 0
    fi
    if timeout --foreground --signal=TERM --kill-after=5s 120s bitbake -e -T 5; then :; else
        bitbake_rc=$?
        printf '__BITBAKE_FAILURE__=%s\n' "$bitbake_rc"
        exit 0
    fi
) 2>/dev/null | awk -F'"' '
    /^__OE_INIT_FAILURE__=/ { init_failure = substr($0, index($0, "=") + 1); next }
    /^__BITBAKE_FAILURE__=/ { bitbake_failure = substr($0, index($0, "=") + 1); next }
    /^(TMPDIR|TOPDIR)=/ {
        key = substr($0, 1, index($0, "=") - 1)
        if (NF < 3 || $2 == "") invalid = 1
        count[key]++
        value[key] = $2
    }
    END {
        if (init_failure != "") {
            print "OE_INIT_FAILURE=" init_failure
            exit 70
        }
        if (bitbake_failure != "") {
            print "BITBAKE_FAILURE=" bitbake_failure
            exit 71
        }
        if (invalid || count["TMPDIR"] != 1 || count["TOPDIR"] != 1) exit 3
        print "TMPDIR=" value["TMPDIR"]
        print "TOPDIR=" value["TOPDIR"]
    }
') || metadata_rc=$?

idle=false
for attempt in $(seq 1 15); do
    if ! pgrep -x bitbake >/dev/null 2>&1 && ! pgrep -x bitbake-server >/dev/null 2>&1; then
        idle=true
        break
    fi
    sleep 1
done
test "$idle" = true || { echo "BitBake metadata query left a process active; refusing receiver update" >&2; exit 1; }
if test "$metadata_rc" -eq 124 || test "$metadata_rc" -eq 137; then
    echo "bitbake-metadata-timeout: refusing receiver update" >&2
    exit 1
fi
if test "$metadata_rc" -eq 70; then
    init_rc=$(printf '%s\n' "$metadata" | sed -n 's/^OE_INIT_FAILURE=//p')
    echo "oe-init-failed: source rc=$init_rc; refusing receiver update" >&2
    exit 1
fi
if test "$metadata_rc" -eq 71; then
    bitbake_rc=$(printf '%s\n' "$metadata" | sed -n 's/^BITBAKE_FAILURE=//p')
    if test "$bitbake_rc" -eq 124 || test "$bitbake_rc" -eq 137; then
        echo "bitbake-metadata-timeout: refusing receiver update" >&2
    else
        echo "bitbake-metadata-query-failed: rc=$bitbake_rc; refusing receiver update" >&2
    fi
    exit 1
fi
test "$metadata_rc" -eq 0 || {
    echo "bitbake-metadata-incomplete: rc=$metadata_rc; refusing receiver update" >&2
    exit 1
}
effective_tmpdir=$(printf '%s\n' "$metadata" | sed -n 's/^TMPDIR=//p')
effective_topdir=$(printf '%s\n' "$metadata" | sed -n 's/^TOPDIR=//p')
test -n "$effective_tmpdir" && test -n "$effective_topdir" || {
    echo "effective BitBake configuration is incomplete; refusing receiver update" >&2
    exit 1
}
canonical_topdir=$(canonical_dir "$effective_topdir") || { echo "effective TOPDIR does not exist" >&2; exit 1; }
canonical_effective_tmpdir=$(canonical_dir "$effective_tmpdir") || { echo "effective TMPDIR does not exist" >&2; exit 1; }
test "$canonical_topdir" = "$selected_build" || { echo "effective TOPDIR does not match the fixed build" >&2; exit 1; }
test "$canonical_effective_tmpdir" = "$selected_tmpdir" || { echo "effective TMPDIR does not match the fixed TMPDIR" >&2; exit 1; }

git -C "$receiver" fetch "$remote_bundle" "$tip"
git -C "$receiver" checkout --detach "$tip"
test "$(git -C "$receiver" rev-parse HEAD)" = "$tip" || {
    echo "receiver tip mismatch" >&2
    exit 1
}
test -z "$(git -C "$receiver" status --porcelain --untracked-files=all -- . ':(exclude)evidence/**')" || {
    echo "receiver is not clean after update" >&2
    exit 1
}

echo "receiver-revision=$(git -C "$receiver" rev-parse HEAD)"
echo "effective-topdir=PASS"
echo "effective-tmpdir=PASS"
echo "status=ready"
REMOTE
