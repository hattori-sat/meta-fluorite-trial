#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/finish-fluorite-devtool-patch.sh \
  <container-source-path> <canonical-patch-file> <canonical-bbappend-file>

Resolves the active Devtool recipe from the source path, runs official
devtool finish into the one fixed finish layer, selects the patch for the
exact source HEAD, copies it byte-for-byte, and registers it once in the
existing meta-fluorite-trial bbappend. It never finishes directly into the
canonical project layer.
EOF
    exit 2
}

fail() {
    echo "fluorite-finish: $1" >&2
    exit 1
}

test "$#" -eq 3 || usage
source_tree=$1
canonical_patch=$2
canonical_bbappend=$3

case "$source_tree" in
    /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
    *) fail "source path must be inside the fixed Devtool source workspace" ;;
esac
patchdir=
registration_mode=bbappend
case "$canonical_patch" in
    layers/meta-fluorite-trial/recipes-graphics/toyota/files/*.patch)
        case "$canonical_bbappend" in
            layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_*.bbappend) ;;
            *) fail "toyota patch requires the existing flutter-auto bbappend" ;;
        esac
        patchdir=ivi-homescreen-plugins
        ;;
    layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/*.patch)
        case "$canonical_bbappend" in
            layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo_git.bb) ;;
            *) fail "Flutter app patch requires the existing app recipe" ;;
        esac
        registration_mode=recipe
        ;;
    layers/meta-fluorite-trial/recipes-graphics/filament/files/*.patch)
        case "$canonical_bbappend" in
            layers/meta-fluorite-trial/recipes-graphics/filament/filament-vk_*.bbappend) ;;
            *) fail "filament patch requires the existing filament-vk bbappend" ;;
        esac
        ;;
    *) fail "patch must be under a supported meta-fluorite-trial recipe files directory" ;;
esac

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
bash "$repo_root/scripts/assert-canonical-repository.sh" >/dev/null || \
    fail "canonical repository check failed"

test -f "$repo_root/$canonical_bbappend" || fail "canonical bbappend is missing"
canonical_scaffold="$repo_root/layers/meta-fluorite-trial/recipes-fluorite-plugins"
if test -e "$canonical_scaffold" &&
    find "$canonical_scaffold" -type f -print -quit | grep -q .; then
    fail "canonical finish scaffold exists; remove only the recorded stale scaffold before retry"
fi

patch_name=${canonical_patch##*/}
if test -n "$patchdir"; then
    registration="SRC_URI:append = \" file://$patch_name;patchdir=$patchdir\""
elif test "$registration_mode" = recipe; then
    registration="file://$patch_name"
else
    registration="SRC_URI:append = \" file://$patch_name\""
fi
if rg -q --fixed-strings "$patch_name" "$repo_root/$canonical_bbappend" &&
    ! rg -q --fixed-strings "$registration" "$repo_root/$canonical_bbappend"; then
    fail "canonical bbappend already names $patch_name with a different registration"
fi

state_root=${FLUORITE_MAC_DEVTOOL_STATE_ROOT:-/tmp/fluorite-mac-devtool-state}
test -d "$state_root" || fail "fixed Devtool state root is missing"
state_root=$(CDPATH= cd -- "$state_root" && pwd -P)
finish_layer_host="$state_root/build/workspace/finish-layer"
test -d "$finish_layer_host" || fail "fixed finish layer is missing"

source_head=$(FLUORITE_MAC_PROJECT_ROOT="$repo_root" \
    "$repo_root/scripts/run-podman-devtool.sh" source-git-revision "$source_tree" | \
    grep -E '^[0-9a-fA-F]{40}$' | tail -n 1)
case "$source_head" in
    [0-9a-fA-F][0-9a-fA-F]*) ;;
    *) fail "source Git did not report a commit" ;;
esac

finish_output=
if ! finish_output=$(FLUORITE_MAC_PROJECT_ROOT="$repo_root" \
    "$repo_root/scripts/run-podman-devtool.sh" finish-source \
    "$source_tree" /workspace/state/build/workspace/finish-layer 2>&1); then
    # `devtool finish` removes the active workspace registration after a
    # successful handoff. If this helper is retried after that point, reuse
    # only an existing finish-layer patch for the exact same source HEAD;
    # never regenerate or hand-author a patch in the fallback.
    candidates=()
    while IFS= read -r patch_file; do
        if rg -q --fixed-strings "From $source_head " "$patch_file"; then
            candidates+=("$patch_file")
        fi
    done < <(find "$finish_layer_host" -type f -name '*.patch' -print | LC_ALL=C sort)
    if test "${#candidates[@]}" -ne 1; then
        printf '%s\n' "$finish_output" | awk '
            /finish-source=|ERROR:|FAIL|No recipe|No such recipe|not found/ { print; shown++ }
            shown >= 40 { exit }
        ' >&2
        fail "official Devtool finish failed and no unique prior finish patch exists for source HEAD $source_head"
    fi
    generated_patch=${candidates[0]}
    printf '%s\n' "finish-source=REUSE source_head=$source_head generated=$generated_patch reason=active-registration-absent-after-prior-finish" >&2
else
    parsed_source_head=$(printf '%s\n' "$finish_output" | sed -n \
        's/^finish-source=START recipe=[^ ]* source_head=\([0-9a-fA-F][0-9a-fA-F]*\) destination=.*/\1/p' | sed -n '1p')
    test "$parsed_source_head" = "$source_head" || \
        fail "official finish source HEAD changed during handoff"
    source_head=$parsed_source_head
fi

if test -z "${generated_patch:-}"; then
    candidates=()
    while IFS= read -r patch_file; do
        if rg -q --fixed-strings "From $source_head " "$patch_file"; then
            candidates+=("$patch_file")
        fi
    done < <(find "$finish_layer_host" -type f -name '*.patch' -print | LC_ALL=C sort)
    test "${#candidates[@]}" -eq 1 || \
        fail "expected one generated patch for source HEAD $source_head, found ${#candidates[@]}"
    generated_patch=${candidates[0]}
fi
test -s "$generated_patch" || fail "generated patch is empty"

target="$repo_root/$canonical_patch"
if test -e "$target"; then
    cmp -s "$generated_patch" "$target" || fail "existing canonical patch differs from generated output"
else
    cp -p "$generated_patch" "$target"
fi
cmp -s "$generated_patch" "$target" || fail "canonical patch copy is not byte-identical"

bbappend_file="$repo_root/$canonical_bbappend"
if rg -q --fixed-strings "$patch_name" "$bbappend_file"; then
    rg -q --fixed-strings "$registration" "$bbappend_file" ||
        fail "canonical patch name is present but its exact registration is missing"
elif test "$registration_mode" = recipe; then
    tmp_recipe="${bbappend_file}.tmp.$$"
    awk -v registration="$registration" '
        !inserted && $0 ~ /file:\/\/config\.toml/ {
            printf "           %s \\\n", registration
            inserted = 1
        }
        { print }
        END {
            if (!inserted) exit 2
        }
    ' "$bbappend_file" > "$tmp_recipe" || {
        rm -f "$tmp_recipe"
        fail "could not insert generated patch into the app recipe SRC_URI"
    }
    mv "$tmp_recipe" "$bbappend_file"
else
    printf '\n%s\n' "$registration" >> "$bbappend_file"
fi

if find "$canonical_scaffold" -type f -print -quit 2>/dev/null | grep -q .; then
    fail "finish created a canonical recipe scaffold; operation is rejected"
fi

patch_sha=$(shasum -a 256 "$target" | awk '{print $1}')
printf '%s\n' "finish-source=PASS source_head=$source_head generated=$(basename "$generated_patch") canonical=$canonical_patch sha256=$patch_sha"
printf '%s\n' "registration=PASS bbappend=$canonical_bbappend patchdir=${patchdir:-none}"
