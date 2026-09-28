#!/usr/bin/env bash
set -euo pipefail

root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
podman_wrapper=$root/scripts/run-podman-devtool.sh
handoff=$root/scripts/handoff-fluorite-bundle.sh
receiver_helper=$root/scripts/reuse-mini-build-receiver.sh
checkpoint_skill=$root/skills/yocto-runtime-checkpointing/SKILL.md

test -x "$podman_wrapper"
test -x "$handoff"
test -x "$receiver_helper"
bash -n "$podman_wrapper" "$handoff"
grep -Fq 'rev-parse --is-inside-work-tree' "$receiver_helper"
grep -Fq '40-character full SHA' "$receiver_helper"
grep -Fq "podman_rootless" "$podman_wrapper"
grep -Fq 'rootful connection is required' "$podman_wrapper"
grep -Fq 'FLUORITE_MAC_DEVTOOL_STATE_ROOT' "$podman_wrapper"
grep -Fq '/workspace/state:rw' "$podman_wrapper"
grep -Fq 'state-root=$state_root' "$podman_wrapper"
grep -Fq 'state-bind=rw' "$podman_wrapper"
if grep -Fq 'podman volume create' "$podman_wrapper"; then
    echo 'Podman wrapper must use a host bind, not named volumes' >&2
    exit 1
fi
if grep -Eq 'podman[[:space:]]+machine[[:space:]]+(init|create|start|rm|stop)' "$podman_wrapper"; then
    echo 'Podman wrapper must not manage a Podman machine' >&2
    exit 1
fi
if grep -Eq 'podman[[:space:]]+volume([[:space:]]|$)' "$podman_wrapper"; then
    echo 'Podman wrapper must not manage named volumes' >&2
    exit 1
fi
grep -Fq 'FLUORITE_MAC_DEVTOOL_UID' "$podman_wrapper"
grep -Fq 'does not require `podman-compose`' "$root/docs/environment.md"
grep -Fq '/workspace/project:rw' "$podman_wrapper"
grep -Fq '/workspace/agl:ro' "$podman_wrapper"
grep -Fq 'mount-permission' "$podman_wrapper"
grep -Fq 'EXTRA_BBLAYERS=/workspace/project/layers/meta-fluorite-trial /workspace/agl/meta-vulkan' "$podman_wrapper"
! grep -Fq '/workspace/agl/self-install/meta-flutter' "$podman_wrapper"
grep -Fq 'historical self-install checkout' "$root/tools/yocto-devtool/entrypoint.sh"
grep -Fq 'bundle create' "$handoff"
grep -Fq 'refs/heads/$branch' "$handoff"
grep -Fq 'self-contained' "$handoff"
grep -Fq 'bundle list-heads' "$handoff"
grep -Fq 'bundle verify' "$handoff"
grep -Fq 'scp ' "$handoff"
grep -Fq 'sha256sum' "$handoff"
grep -Fq 'file_sha256' "$handoff"
grep -Fq 'command -v sha256sum' "$handoff"
grep -Fq 'git -C "$receiver" bundle verify' "$handoff"
grep -Fq 'reuse-mini-build-receiver.sh' "$handoff"
grep -Fq 'BUILD_BUNDLE_INBOX' "$handoff"
grep -Fq 'meta-fluorite-trial-active.bundle' "$handoff"
grep -Fq 'canonical repository' "$handoff"
grep -Fq 'source "$oe_init" "$build_dir"' "$receiver_helper"
grep -Fq 'timeout --foreground --signal=TERM --kill-after=5s 120s bitbake -e -T 5' "$receiver_helper"
grep -Fq 'effective TMPDIR does not match the fixed TMPDIR' "$receiver_helper"
! grep -Fq 'TMPDIR = "$tmpdir"' "$receiver_helper"
grep -Fq 'BUILD_RECEIVER BUILD_DIR BUILD_TMPDIR' "$receiver_helper"
! grep -Fq 'flourite-receiver-active' "$receiver_helper"
! grep -Fq 'build-flr0023-active' "$receiver_helper"
! grep -Fq '/mnt/yocto/flr0023-tmp-active' "$receiver_helper"
tmpdir_check_line=$(grep -nF 'effective TMPDIR does not match the fixed TMPDIR' "$receiver_helper" | head -n1 | cut -d: -f1)
bundle_tip_line=$(grep -nF 'bundle list-heads' "$receiver_helper" | head -n1 | cut -d: -f1)
fetch_line=$(grep -nF 'git -C "$receiver" fetch "$remote_bundle" "$tip"' "$receiver_helper" | cut -d: -f1)
checkout_line=$(grep -nF 'git -C "$receiver" checkout --detach "$tip"' "$receiver_helper" | cut -d: -f1)
test "$tmpdir_check_line" -lt "$fetch_line"
test "$bundle_tip_line" -lt "$fetch_line"
test "$fetch_line" -lt "$checkout_line"
grep -Fq 'handoff-fluorite-bundle.sh' "$checkpoint_skill"
grep -Fq 'mount-permission' "$checkpoint_skill"
grep -Fq 'BUILD_BUNDLE_INBOX' "$checkpoint_skill"

if grep -Eq 'mkdir[^\n]*(source|build|tmp)|mktemp' "$handoff"; then
    echo 'handoff helper must not create source/build/TMPDIR copies' >&2
    exit 1
fi

echo 'podman/bundle handoff contract: PASS'
