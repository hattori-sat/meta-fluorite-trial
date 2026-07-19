#!/usr/bin/env bash
set -euo pipefail

AGL_ROOT="${AGL_ROOT:-$HOME/AGL/trout}"
REPO_CMD="$AGL_ROOT/.repo/repo/repo"

printf '%s\n' '== host ==' 
hostname
id -un
df -h /mnt/yocto

printf '%s\n' '== fixed repo manifest =='
"$REPO_CMD" manifest -r

printf '%s\n' '== repo changes =='
"$REPO_CMD" status

for build in build-flourite build-flourite-qemux86-64 build-flourite-qemuarm64; do
    printf '== %s cache configuration ==\n' "$build"
    grep -E '^(MACHINE|DISTRO|DL_DIR|SSTATE_DIR|TMPDIR)[[:space:]]*[:?+.]?=' \
        "$AGL_ROOT/$build/conf/local.conf" || true
done

printf '%s\n' '== independent layers =='
git -C "$AGL_ROOT/meta-vulkan" status --short --branch
git -C "$AGL_ROOT/meta-vulkan" rev-parse HEAD
find "${PROJECT_ROOT:-$HOME/work/meta-fluorite-trial}/layers/meta-fluorite-trial" -type f -not -path '*/.git/*' -exec sha256sum {} + | sort -k2
