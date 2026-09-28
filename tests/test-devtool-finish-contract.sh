#!/usr/bin/env bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
wrapper="$repo_root/scripts/run-podman-devtool.sh"
helper="$repo_root/scripts/finish-fluorite-devtool-patch.sh"

rg -q --fixed-strings 'finish-source)' "$wrapper"
rg -q --fixed-strings 'devtool status' "$wrapper"
rg -q --fixed-strings 'expected one active recipe' "$wrapper"
rg -q --fixed-strings 'podman exec -i --user' "$wrapper"
rg -q --fixed-strings '(devtool finish "$recipe" "$destination" --mode patch)' "$wrapper"
rg -q --fixed-strings 'devtool finish "$recipe" "$destination" --mode patch' "$wrapper"
rg -q --fixed-strings 'finish-source destination must be the fixed finish layer' "$wrapper"
rg -q --fixed-strings 'direct finish into the canonical project layer is forbidden' "$wrapper"
rg -q --fixed-strings 'test "$devtool_rc" -eq 0' "$wrapper"
rg -q --fixed-strings 'official finish returned rc=$devtool_rc' "$wrapper"
rg -q --fixed-strings 'expected one generated patch for source HEAD' "$helper"
rg -q --fixed-strings 'canonical finish scaffold exists' "$helper"
rg -q --fixed-strings 'canonical patch copy is not byte-identical' "$helper"
rg -q --fixed-strings 'recipes-graphics/filament/files/*.patch' "$helper"
rg -q --fixed-strings 'filament patch requires the existing filament-vk bbappend' "$helper"

status_fixture='flutter-auto: /workspace/state/build/workspace/sources/flutter-auto-reconcile'
status_match=$(printf '%s\n' "$status_fixture" |
    sed -n \
        -e 's#^\([^:][^:]*\): /workspace/state/build/workspace/sources/flutter-auto-reconcile$#\1#p' \
        -e 's#^\([^:][^:]*\): /workspace/state/build/workspace/sources/flutter-auto-reconcile .*#\1#p')
test "$status_match" = flutter-auto
status_fixture='flutter-auto: /workspace/state/build/workspace/sources/flutter-auto-reconcile active'
status_match=$(printf '%s\n' "$status_fixture" |
    sed -n \
        -e 's#^\([^:][^:]*\): /workspace/state/build/workspace/sources/flutter-auto-reconcile$#\1#p' \
        -e 's#^\([^:][^:]*\): /workspace/state/build/workspace/sources/flutter-auto-reconcile .*#\1#p')
test "$status_match" = flutter-auto

if bash "$helper" /wrong/source layers/meta-fluorite-trial/recipes-graphics/toyota/files/x.patch \
    layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend >/dev/null 2>&1; then
    echo 'devtool finish contract test: FAIL wrong source accepted' >&2
    exit 1
fi

if bash "$helper" /wrong/source layers/meta-fluorite-trial/recipes-graphics/filament/files/x.patch \
    layers/meta-fluorite-trial/recipes-graphics/filament/filament-vk_1.54.3.bbappend >/dev/null 2>&1; then
    echo 'devtool finish contract test: FAIL wrong Filament source accepted' >&2
    exit 1
fi

printf '%s\n' 'devtool finish contract test: PASS'
