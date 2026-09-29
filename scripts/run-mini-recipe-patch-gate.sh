#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/run-mini-recipe-patch-gate.sh <ticket> <recipe>

Runs one bounded, recipe-scoped authoritative patch gate on the fixed Mini PC
receiver. It verifies the receiver/build/TMPDIR contract, records only a
filtered metadata summary, resets only the selected recipe workdir with the
safe `clean` task, forces the selected recipe's do_patch, and reports the
first patch boundary plus the exact task log when the gate fails.

Required local role variables:
  BUILD_HOST BUILD_RECEIVER BUILD_DIR BUILD_TMPDIR

Optional:
  BUILD_AGL_ROOT  build-host AGL root; otherwise inferred from BUILD_DIR
EOF
}

fail() {
    echo "mini-recipe-patch-gate: $1" >&2
    exit 1
}

test "$#" -eq 2 || { usage >&2; exit 2; }
ticket=$1
recipe=$2

case "$ticket" in
    ''|*[!A-Za-z0-9._-]*) fail "ticket must be a simple identifier" ;;
esac
case "$recipe" in
    ''|-*|*[!A-Za-z0-9._+:-]*) fail "recipe must be a simple BitBake name" ;;
    agl-ivi-image-*|core-image-*) fail "image recipes are not allowed in the recipe patch gate" ;;
esac

build_host=${BUILD_HOST:?BUILD_HOST must be set in local role configuration}
receiver=${BUILD_RECEIVER:?BUILD_RECEIVER must be set in local role configuration}
build_dir=${BUILD_DIR:?BUILD_DIR must be set in local role configuration}
build_tmpdir=${BUILD_TMPDIR:?BUILD_TMPDIR must be set in local role configuration}
agl_root=${BUILD_AGL_ROOT:-}

case "$build_host" in
    ''|*[!A-Za-z0-9_.-]*) fail "BUILD_HOST must be an SSH role alias" ;;
esac
for path in "$receiver" "$build_dir" "$build_tmpdir"; do
    case "$path" in
        /*) ;;
        *) fail "role paths must be absolute: $path" ;;
    esac
done
case "$agl_root" in
    ''|/*) ;;
    *) fail "BUILD_AGL_ROOT must be an absolute path" ;;
esac

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
bash "$repo_root/scripts/assert-canonical-repository.sh" >/dev/null || \
    fail "canonical repository check failed"

ssh "$build_host" bash -s -- \
    "$ticket" "$recipe" "$receiver" "$build_dir" "$build_tmpdir" "$agl_root" <<'REMOTE'
set -euo pipefail

ticket=$1
recipe=$2
receiver=$3
build_dir=$4
tmpdir=$5
agl_root=${6:-}

test -d "$receiver" || { echo "fixed receiver is missing" >&2; exit 1; }
test -d "$build_dir" || { echo "fixed build directory is missing" >&2; exit 1; }
test -d "$tmpdir" || { echo "fixed TMPDIR is missing" >&2; exit 1; }
git -C "$receiver" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "fixed receiver is not a Git worktree" >&2
    exit 1
}
test -r "$build_dir/conf/local.conf" || {
    echo "fixed build configuration is missing" >&2
    exit 1
}
grep -Fq "TMPDIR = \"$tmpdir\"" "$build_dir/conf/local.conf" || {
    echo "build configuration does not use the fixed TMPDIR" >&2
    exit 1
}
grep -Fq "$receiver/layers/meta-fluorite-trial" "$build_dir/conf/bblayers.conf" || {
    echo "build configuration does not use the fixed receiver layer" >&2
    exit 1
}
if pgrep -x bitbake >/dev/null 2>&1 || pgrep -x bitbake-server >/dev/null 2>&1; then
    echo "an existing BitBake process is active; refusing a second patch gate" >&2
    exit 1
fi

evidence_dir="$receiver/evidence/$ticket"
mkdir -p "$evidence_dir"
test -z "$(git -C "$receiver" status --porcelain --untracked-files=all -- . \
    ':(exclude)evidence/**')" || {
    echo "fixed receiver has non-evidence changes" >&2
    exit 1
}

if test -z "$agl_root"; then
    case "$build_dir" in
        */build-*) agl_root=${build_dir%/build-*} ;;
        *) echo "BUILD_AGL_ROOT is required when BUILD_DIR has no build-* suffix" >&2; exit 1 ;;
    esac
fi
test -r "$agl_root/external/poky/oe-init-build-env" || {
    echo "AGL environment script is missing" >&2
    exit 1
}

summary="$evidence_dir/patch-gate-$recipe.summary"
output="$evidence_dir/patch-gate-$recipe.output"
metadata="$evidence_dir/bitbake-e-$recipe.summary"
task_log="$evidence_dir/patch-gate-$recipe.task-log"
clean_output="$evidence_dir/patch-gate-$recipe.clean.output"
rm -f "$summary" "$output" "$metadata" "$task_log" "$clean_output"

# oe-init-build-env is allowed to set shell variables that are not present in
# the caller. Keep nounset for the gate itself, but source the Yocto setup in
# a small subshell that does not inherit it.
metadata_rc=0
if (set +u; source "$agl_root/external/poky/oe-init-build-env" "$build_dir" >/dev/null; \
    bitbake -e "$recipe") 2>/dev/null | \
    awk '/^(PN|PV|FILE|WORKDIR|SRC_URI|S)=/ { print }' >"$metadata"; then
    metadata_rc=0
else
    metadata_rc=$?
fi
test "$metadata_rc" -eq 0 || {
    echo "metadata=FAIL rc=$metadata_rc" >"$summary"
    echo "metadata summary: $metadata" >>"$summary"
    cat "$summary"
    exit "$metadata_rc"
}

# A forced do_patch reuses the recipe workdir. Without resetting that workdir,
# a prior interrupted or manually altered run can make patch results depend on
# stale source contents. `clean` removes only this recipe's workdir; it does
# not remove downloads, sstate-cache, the shared TMPDIR, or other recipes.
clean_rc=0
if (set +u; source "$agl_root/external/poky/oe-init-build-env" "$build_dir" >/dev/null; \
    bitbake -f -c clean "$recipe") >"$clean_output" 2>&1; then
    clean_rc=0
else
    clean_rc=$?
fi
test "$clean_rc" -eq 0 || {
    {
        echo "preflight=PASS recipe=$recipe receiver=$(git -C "$receiver" rev-parse HEAD)"
        echo "metadata=PASS file=$metadata"
        echo "workdir-reset=FAIL rc=$clean_rc"
        echo "clean-output=$clean_output"
    } | tee "$summary"
    tail -n 40 "$clean_output"
    exit "$clean_rc"
}

patch_rc=0
if (set +u; source "$agl_root/external/poky/oe-init-build-env" "$build_dir" >/dev/null; \
    bitbake -f -c do_patch "$recipe") >"$output" 2>&1; then
    patch_rc=0
else
    patch_rc=$?
fi

if test "$patch_rc" -eq 0; then
    {
        echo "preflight=PASS recipe=$recipe receiver=$(git -C "$receiver" rev-parse HEAD)"
        echo "metadata=PASS file=$metadata"
        echo "workdir-reset=PASS mode=recipe-clean"
        echo "do_patch=PASS"
    } | tee "$summary"
    rm -f "$output" "$clean_output"
    exit 0
fi

# Keep the evidence bounded: preserve the raw command output outside Git, but
# expose only patch application boundaries and the first useful error lines.
failing_patch=$(sed -n "s/.*Applying patch '\([^']*\)'.*/\1/p" "$output" | tail -n 1)
{
    if test -n "$failing_patch"; then
        echo "failing-patch=$failing_patch"
    else
        echo "failing-patch=UNKNOWN"
    fi
    awk '
        /^Applying patch |^patching file |^Hunk |^1 out of .*FAILED|^ERROR: Logfile|^ERROR: Task |^Summary:/ {
            print
            shown++
        }
        shown >= 80 { exit }
    ' "$output" || true
} >"$task_log"
latest_task_log=$(sed -n 's/^ERROR: Logfile of failure stored in: //p' "$output" | tail -n 1)
if test -n "$latest_task_log"; then
    test -f "$latest_task_log" || latest_task_log=
fi
if test -z "$latest_task_log"; then
    latest_task_log=$(find "$tmpdir/work" -path "*/$recipe/*" -type f \
        -name 'log.do_patch.*' -print 2>/dev/null | sort | tail -n 1)
fi
{
    echo "preflight=PASS recipe=$recipe receiver=$(git -C "$receiver" rev-parse HEAD)"
    echo "metadata=PASS file=$metadata"
    echo "workdir-reset=PASS mode=recipe-clean"
    echo "do_patch=FAIL rc=$patch_rc"
    if test -n "$failing_patch"; then
        echo "failing-patch=$failing_patch"
    else
        echo "failing-patch=UNKNOWN"
    fi
    echo "bounded-failure=$task_log"
    if test -n "$latest_task_log"; then
        echo "task-log=$latest_task_log"
    else
        echo "task-log=UNKNOWN"
    fi
} | tee "$summary"
sed -n '1,80p' "$task_log"
exit "$patch_rc"
REMOTE
