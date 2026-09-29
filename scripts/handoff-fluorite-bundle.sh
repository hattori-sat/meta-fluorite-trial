#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/handoff-fluorite-bundle.sh <base-commit> <tip-commit>

Creates one stable Git bundle outside the repository, verifies it locally,
copies it to the build-host inbox, verifies the remote hash, and updates the
existing fixed Mini PC receiver to the exact tip.

Required local role variables:
  BUILD_HOST BUILD_BUNDLE_INBOX BUILD_RECEIVER BUILD_DIR BUILD_TMPDIR

Optional:
  FLUORITE_BUNDLE_DIR  default: /private/tmp/fluorite-bundles
EOF
}

fail() {
    echo "fluorite-handoff: $1" >&2
    exit 1
}

file_sha256() {
    local output
    if command -v shasum >/dev/null 2>&1; then
        output=$(shasum -a 256 "$1")
    elif command -v sha256sum >/dev/null 2>&1; then
        output=$(sha256sum "$1")
    else
        fail "missing-command:shasum-or-sha256sum"
    fi
    printf '%s\n' "${output%% *}"
}

test "$#" -eq 2 || { usage >&2; exit 2; }
base=$1
tip=$2

case "$base:$tip" in
    *[!a-fA-F0-9:]*|*:*:*) fail "base and tip must be hexadecimal commits" ;;
esac

build_host=${BUILD_HOST:?BUILD_HOST must be set in local role configuration}
bundle_inbox=${BUILD_BUNDLE_INBOX:?BUILD_BUNDLE_INBOX must be set in local role configuration}
receiver=${BUILD_RECEIVER:?BUILD_RECEIVER must be set in local role configuration}
build_dir=${BUILD_DIR:?BUILD_DIR must be set in local role configuration}
build_tmpdir=${BUILD_TMPDIR:?BUILD_TMPDIR must be set in local role configuration}
bundle_dir=${FLUORITE_BUNDLE_DIR:-/private/tmp/fluorite-bundles}

case "$build_host" in
    ''|*[!A-Za-z0-9_.-]*) fail "BUILD_HOST must be an SSH role alias" ;;
esac
case "$bundle_inbox" in
    /*) ;;
    *) fail "BUILD_BUNDLE_INBOX must be an absolute remote path" ;;
esac
case "$bundle_dir" in
    /*) ;;
    *) fail "FLUORITE_BUNDLE_DIR must be an absolute local path" ;;
esac

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
bash "$repo_root/scripts/assert-canonical-repository.sh" >/dev/null || {
    fail "canonical repository check failed"
}

branch=$(git -C "$repo_root" branch --show-current)
test -n "$branch" || fail "feature branch is required"
test "$branch" != main || fail "main is not a bundle source"
test -z "$(git -C "$repo_root" status --porcelain)" || {
    fail "repository must be clean after the local commit"
}

base_full=$(git -C "$repo_root" rev-parse --verify "$base^{commit}") || {
    fail "base commit is not present"
}
tip_full=$(git -C "$repo_root" rev-parse --verify "$tip^{commit}") || {
    fail "tip commit is not present"
}
git -C "$repo_root" merge-base --is-ancestor "$base_full" "$tip_full" || {
    fail "base is not an ancestor of tip"
}

mkdir -p "$bundle_dir"
bundle="$bundle_dir/meta-fluorite-trial-active.bundle"
reuse_bundle=false
if test -e "$bundle" &&
    git -C "$repo_root" bundle verify "$bundle" >/dev/null &&
    git -C "$repo_root" bundle list-heads "$bundle" | awk '{print $1}' |
    grep -Fxq "$tip_full"; then
    reuse_bundle=true
fi
if test "$reuse_bundle" = false; then
    # The base is still checked as the declared comparison point, but the
    # bundle is self-contained because the fixed receiver may not share that
    # history.
    git -C "$repo_root" bundle create "$bundle" "refs/heads/$branch"
    git -C "$repo_root" bundle verify "$bundle" >/dev/null
fi

bundle_sha=$(file_sha256 "$bundle")
remote_bundle="$bundle_inbox/meta-fluorite-trial-active.bundle"
scp "$bundle" "$build_host:$remote_bundle"

ssh "$build_host" bash -s -- "$remote_bundle" "$bundle_sha" "$receiver" <<'REMOTE'
set -euo pipefail
remote_bundle=$1
expected_sha=$2
receiver=$3
test -f "$remote_bundle" || { echo "remote bundle is missing" >&2; exit 1; }
actual_sha=$(sha256sum "$remote_bundle" | awk '{print $1}')
test "$actual_sha" = "$expected_sha" || { echo "remote bundle hash mismatch" >&2; exit 1; }
git -C "$receiver" bundle verify "$remote_bundle" >/dev/null
echo "remote-bundle=PASS sha256=$actual_sha"
REMOTE

BUILD_HOST="$build_host" \
BUILD_RECEIVER="$receiver" \
BUILD_DIR="$build_dir" \
BUILD_TMPDIR="$build_tmpdir" \
    bash "$repo_root/scripts/reuse-mini-build-receiver.sh" "$remote_bundle" "$tip_full"

echo "bundle=$bundle"
echo "sha256=$bundle_sha"
echo "tip=$tip_full"
echo "handoff=PASS"
