#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/rebase-fluorite-devtool-component.sh \
  <ticket> <recipe> <container-source-path> <baseline-commit> <source-commit> \
  <canonical-patch-file> <canonical-bbappend-file> [patchdir] [--replace-canonical]

Re-registers one split component from an effective-source baseline, generates
one official Yocto Devtool patch for the source commit, copies it unchanged to
meta-fluorite-trial, registers it once, and refreshes the authorized layer
baseline lock. The operation reuses the fixed Podman container/state and does
not create a ticket-specific source tree, volume, TMPDIR, or local index file.
EOF
    exit 2
}

fail() {
    echo "fluorite-component-rebase: $1" >&2
    exit 1
}

test "$#" -ge 7 -a "$#" -le 9 || usage
ticket=$1
recipe=$2
source_tree=$3
baseline_commit=$4
source_commit=$5
canonical_patch=$6
canonical_bbappend=$7
patchdir=${8:-ivi-homescreen-plugins}
replace_canonical=0
if test "$#" -eq 9; then
    test "$9" = --replace-canonical || usage
    replace_canonical=1
fi

case "$ticket" in
    ''|*[!A-Za-z0-9._-]*) fail "ticket must be a simple identifier" ;;
esac
case "$recipe" in
    ''|*[!A-Za-z0-9._+-]*) fail "recipe must be a simple name" ;;
esac
case "$source_tree" in
    /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
    *) fail "source path must be inside the fixed Devtool source workspace" ;;
esac
if ! [[ "$baseline_commit" =~ ^[0-9a-fA-F]{40}$ ]] ||
    ! [[ "$source_commit" =~ ^[0-9a-fA-F]{40}$ ]]; then
    fail "baseline and source commits must be full 40-character SHA-1 values"
fi
case "$canonical_patch" in
    layers/meta-fluorite-trial/recipes-graphics/toyota/files/*.patch) ;;
    *) fail "patch must be under meta-fluorite-trial/recipes-graphics/toyota/files" ;;
esac
case "$canonical_bbappend" in
    layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_*.bbappend) ;;
    *) fail "bbappend must be the existing flutter-auto bbappend" ;
esac
case "$patchdir" in
    ''|/*|*..*|*[!A-Za-z0-9._/-]*) fail "patchdir must be a relative safe path" ;;
esac

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
wrapper="$repo_root/scripts/run-podman-devtool.sh"
state_root=${FLUORITE_MAC_DEVTOOL_STATE_ROOT:-/tmp/fluorite-mac-devtool-state}
generated_root="$state_root/build/workspace/appends/$recipe"
finish_root="$state_root/build/workspace/finish-layer"

bash "$repo_root/scripts/assert-canonical-repository.sh" >/dev/null || \
    fail "canonical repository check failed"
test -x "$wrapper" || fail "Podman Devtool wrapper is not executable"
test -f "$repo_root/$canonical_bbappend" || fail "canonical bbappend is missing"
test -d "$state_root/build/workspace" || fail "fixed Devtool workspace is missing"

run_step() {
    step=$1
    shift
    step_output=
    if ! step_output=$("$@" 2>&1); then
        printf '%s\n' "$step_output" | awk '
            /ERROR|FAIL|error:|failed|dirty|mismatch|No recipe|No such recipe|not found/ {
                print
                shown++
            }
            shown >= 40 { exit }
        ' >&2
        fail "$step failed"
    fi
}

run_step status "$wrapper" devtool-status
component_recipe=fluorite-plugins
test "$recipe" = "$component_recipe" || \
    fail "source rebase requires component recipe $component_recipe; outer recipe is only the canonical bbappend target"
registered_component_count=$(printf '%s\n' "$step_output" | awk -v source="$source_tree" \
    '$1 == "fluorite-plugins:" && $2 == source { count++ } END { print count + 0 }')
same_source_count=$(printf '%s\n' "$step_output" | awk -v source="$source_tree" \
    '$2 == source { count++ } END { print count + 0 }')
test "$same_source_count" -eq 1 || \
    test "$same_source_count" -eq 0 || \
    fail "source path has multiple active Devtool recipes; reset duplicates before rebase"
active_count=$(printf '%s\n' "$step_output" | awk -v recipe="$recipe" \
    '$1 == recipe ":" { count++ } END { print count + 0 }')
test "$active_count" -le 1 || fail "target component has multiple active Devtool registrations"
if test "$same_source_count" -eq 1; then
    test "$registered_component_count" -eq 1 || \
        fail "source path is registered to an unexpected component"
else
    test "$active_count" -eq 0 || \
        fail "target component is registered to a different source path"
fi
if test "$active_count" -eq 1; then
    run_step component-reset "$wrapper" component-reset "$recipe"
fi

run_step source-status "$wrapper" source-git-status "$source_tree"
dirty_lines=$(printf '%s\n' "$step_output" | awk '
    /^mkfifo: cannot create fifo / { next }
    /^mount-permission=/ { next }
    /^## / { next }
    NF { print }
')
test -z "$dirty_lines" || fail "source tree is dirty; stash or commit it before rebase"

baseline_branch="devtool-${ticket}-baseline"
source_branch="devtool-${ticket}-source"
run_step baseline-branch "$wrapper" source-git-ensure-branch \
    "$source_tree" "$baseline_branch" "$baseline_commit"
run_step component-add "$wrapper" component-add "$recipe" "$source_tree"
workspace_bbappend="$state_root/build/workspace/appends/${recipe}.bbappend"
test -r "$workspace_bbappend" || fail "Devtool workspace bbappend is missing: $workspace_bbappend"
initial_rev_line=$(rg --fixed-strings "# initial_rev .: $baseline_commit" "$workspace_bbappend" || true)
test -n "$initial_rev_line" || fail "Devtool component-add did not record the requested baseline in $workspace_bbappend"
test "$(printf '%s\n' "$initial_rev_line" | wc -l | tr -d ' ')" -eq 1 || \
    fail "Devtool workspace bbappend has duplicate baseline records: $workspace_bbappend"
run_step source-branch "$wrapper" source-git-ensure-branch \
    "$source_tree" "$source_branch" "$source_commit"
run_step update-recipe "$wrapper" update-recipe "$recipe" \
    /workspace/state/build/workspace --force-patch-refresh

matches=()
for generated_root in "$generated_root" "$finish_root"; do
    test -d "$generated_root" || continue
    while IFS= read -r generated; do
        if rg -q --fixed-strings "From $source_commit " "$generated"; then
            matches+=("$generated")
        fi
    done < <(find "$generated_root" -type f -name '*.patch' -print | LC_ALL=C sort)
done
test "${#matches[@]}" -eq 1 || {
    printf '%s\n' "${matches[@]}" >&2
    fail "expected exactly one generated patch in append/finish output for source commit $source_commit"
}
patch_name=${canonical_patch##*/}
registration_line="file://$patch_name;patchdir=$patchdir"
bbappend_file="$repo_root/$canonical_bbappend"
registration_matches() {
    rg -F "$registration_line" "$bbappend_file" || true
}
assert_unique_registration_lines() {
    local matches duplicates
    matches=$(registration_matches)
    test -n "$matches" || fail "canonical patch registration is missing"
    duplicates=$(printf '%s\n' "$matches" | LC_ALL=C sort | uniq -d)
    test -z "$duplicates" || fail "canonical patch registration has duplicate lines"
}
if rg -q --fixed-strings "$patch_name" "$bbappend_file"; then
    rg -q --fixed-strings "$registration_line" "$bbappend_file" || \
        fail "canonical patch name exists with a different registration"
    registration_needs_append=0
    assert_unique_registration_lines
else
    registration_needs_append=1
fi

generated_patch=${matches[0]}
test -s "$generated_patch" || fail "generated patch is empty"

target="$repo_root/$canonical_patch"
previous_patch_sha=
if test -e "$target"; then
    if ! cmp -s "$generated_patch" "$target"; then
        test "$replace_canonical" -eq 1 || \
            fail "existing canonical patch differs; refusing overwrite (pass --replace-canonical for an intentional rebase)"
        previous_patch_sha=$(shasum -a 256 "$target" | awk '{print $1}')
        cp -p "$generated_patch" "$target"
    fi
else
    cp -p "$generated_patch" "$target"
fi
cmp -s "$generated_patch" "$target" || fail "canonical patch copy is not byte-identical"

if test "$registration_needs_append" -eq 1; then
    printf '\nSRC_URI:append = " file://%s;patchdir=%s"\n' "$patch_name" "$patchdir" >> "$bbappend_file"
fi
assert_unique_registration_lines

python3 "$repo_root/scripts/refresh-project-layer-baseline.py" >/dev/null
patch_sha=$(shasum -a 256 "$target" | awk '{print $1}')
printf '%s\n' \
    "component-rebase=PASS ticket=$ticket recipe=$recipe baseline=$baseline_commit source=$source_commit" \
    "generated=$(basename "$generated_patch") canonical=$canonical_patch sha256=$patch_sha" \
    "registration=PASS bbappend=$canonical_bbappend patchdir=$patchdir baseline-lock=REFRESHED"
if test -n "$previous_patch_sha"; then
    printf '%s\n' "canonical-replaced=PASS previous-sha256=$previous_patch_sha"
fi
