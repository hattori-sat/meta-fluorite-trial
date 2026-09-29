#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "fluorite-devtool: $1" >&2
    exit 1
}

test "$#" -ge 1 || fail "operation is required"
operation=$1
shift

case "$operation" in
    modify)
        case "$#" in
            1)
                recipe=$1
                ;;
            3)
                test "$1" = --no-extract || fail "unsupported modify option"
                recipe=$2
                source_tree=$3
                case "$source_tree" in
                    /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*|/workspace/project/*) ;;
                    *) fail "modify source must be inside the fixed workspace or /workspace/project" ;;
                esac
                ;;
            *) fail "modify requires a recipe or --no-extract recipe source tree" ;;
        esac
        ;;
    finish)
        test "$#" -ge 2 -a "$#" -le 3 || fail "finish requires recipe, destination layer, and optional patch refresh"
        recipe=$1
        destination=$2
        if test "$#" -eq 3; then
            test "$3" = --force-patch-refresh || fail "unsupported finish option: $3"
        fi
        case "$destination" in
            /workspace/project|/workspace/project/*|/workspace/state/build/workspace/finish-layer) ;;
            *) fail "finish destination must be inside /workspace/project or the fixed finish layer" ;;
        esac
        ;;
    component-reset)
        test "$#" -eq 1 || fail "component-reset requires exactly one recipe"
        recipe=$1
        ;;
    component-add)
        test "$#" -eq 2 || fail "component-add requires recipe and source tree"
        recipe=$1
        source_tree=$2
        case "$source_tree" in
                    /workspace/state/build/*|/workspace/project/*) ;;
                    *) fail "component-add source must be inside /workspace/state/build or /workspace/project" ;;
        esac
        ;;
    update-recipe)
        test "$#" -ge 2 -a "$#" -le 3 || fail "update-recipe requires recipe, append layer, and optional refresh"
        recipe=$1
        append_layer=$2
        case "$append_layer" in
            /workspace/state/build/*|/workspace/project/*) ;;
            *) fail "update-recipe append layer must be inside /workspace/state/build or /workspace/project" ;;
        esac
        if test "$#" -ge 3; then
            case "$3" in
                --force-patch-refresh) ;;
                *) fail "unsupported update-recipe option: $3" ;;
            esac
        fi
        ;;
    status|devtool-status)
        test "$#" -eq 0 || fail "status takes no arguments"
        recipe=
        ;;
    source-git-status|source-git-diff-check|source-git-log|source-git-revision)
        test "$#" -eq 1 || fail "$operation requires a source tree"
        source_tree=$1
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        ;;
    source-git-commit)
        test "$#" -eq 3 || fail "source-git-commit requires source tree, file, and message"
        source_tree=$1
        source_path=$2
        commit_message=$3
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        case "$source_path" in
            ''|/*|../*|*/../*|*/*/../*) fail "source Git file must be a relative path without traversal" ;;
        esac
        case "$commit_message" in
            ''|-*|*$'\n'*) fail "source Git commit message must be one non-option line" ;;
        esac
        ;;
    source-git-ensure-branch)
        test "$#" -eq 3 || fail "source-git-ensure-branch requires source tree, branch, and revision"
        source_tree=$1
        branch_name=$2
        revision=$3
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed source workspace" ;;
        esac
        case "$branch_name" in
            ''|-*|*[!a-zA-Z0-9._-]*) fail "source Git branch must be a simple non-option name" ;;
        esac
        case "$revision" in
            ''|*[!0-9a-fA-F]*) fail "source Git revision must be hexadecimal" ;;
        esac
        ;;
    source-git-branch)
        test "$#" -eq 3 || fail "source-git-branch requires source tree, branch, and revision"
        recipe=
        source_tree=$1
        branch_name=$2
        revision=$3
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        case "$branch_name" in
            ''|-*|*[!a-zA-Z0-9._-]*) fail "source Git branch must be a simple non-option name" ;;
        esac
        case "$revision" in
            ''|*[!0-9a-fA-F]*) fail "source Git revision must be hexadecimal" ;;
        esac
        ;;
    *) fail "only devtool and bounded source Git operations are allowed" ;;
esac

case "$recipe" in
    agl-ivi-image-*|core-image-*) fail "image recipes are forbidden in the Mac container" ;;
esac

command -v devtool >/dev/null 2>&1 || fail "devtool is not available; source the pinned Yocto environment"
if test "$operation" = finish; then
    if test "$#" -eq 3; then
        exec devtool finish --force-patch-refresh "$recipe" "$destination" --mode patch
    fi
    exec devtool finish "$recipe" "$destination" --mode patch
fi
if test "$operation" = component-reset; then
    exec devtool reset --no-clean "$recipe"
fi
if test "$operation" = component-add; then
    exec devtool add "$recipe" "$source_tree"
fi
if test "$operation" = devtool-status; then
    exec devtool status
fi
if test "$operation" = update-recipe; then
    if test "$#" -eq 3; then
        exec devtool update-recipe "$recipe" --mode patch --append "$append_layer" --no-remove --force-patch-refresh
    fi
    exec devtool update-recipe "$recipe" --mode patch --append "$append_layer" --no-remove
fi
if test "$operation" = source-git-status; then
    exec git -C "$source_tree" status --short --branch
fi
if test "$operation" = source-git-diff-check; then
    exec git -C "$source_tree" diff --check
fi
if test "$operation" = source-git-log; then
    exec git -C "$source_tree" --no-pager log -8 --oneline --decorate
fi
if test "$operation" = source-git-revision; then
    exec git -C "$source_tree" rev-parse --verify HEAD^{commit}
fi
if test "$operation" = source-git-commit; then
    set -- "$source_tree" "$source_path" "$commit_message"
    exec /bin/bash -lc '
        set -eu
        source_tree=$1
        source_path=$2
        commit_message=$3
        changed=$(git -C "$source_tree" status --porcelain --untracked-files=all)
        changed_count=$(printf "%s\n" "$changed" | awk "NF { count++ } END { print count + 0 }")
        test "$changed_count" -eq 1 || {
            echo "source Git commit requires exactly one changed path" >&2
            exit 1
        }
        changed_path=$(printf "%s\n" "$changed" | sed -n "1s/^.. //p")
        test "$changed_path" = "$source_path" || {
            echo "source Git commit changed path does not match the requested file" >&2
            exit 1
        }
        git -C "$source_tree" diff --check
        git -C "$source_tree" add .
        staged=$(git -C "$source_tree" diff --cached --name-only)
        test "$staged" = "$source_path" || {
            echo "source Git add . staged an unexpected path" >&2
            exit 1
        }
        git -C "$source_tree" diff --cached --check
        git -C "$1" -c user.name="Fluorite Devtool" \
            -c user.email="fluorite-devtool@example.invalid" \
            commit -m "$commit_message"
    ' bash "$@"
fi
if test "$operation" = source-git-branch; then
    if git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name"; then
        fail "source Git branch already exists: $branch_name"
    fi
    exec git -C "$source_tree" checkout -b "$branch_name" "$revision"
fi
if test "$operation" = source-git-ensure-branch; then
    test -z "$(git -C "$source_tree" status --porcelain)" || fail "source Git tree is dirty"
    expected=$(git -C "$source_tree" rev-parse --verify "$revision^{commit}")
    if git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name"; then
        actual=$(git -C "$source_tree" rev-parse --verify "refs/heads/$branch_name^{commit}")
        test "$actual" = "$expected" || fail "source Git branch points at a different revision: $branch_name"
        git -C "$source_tree" checkout --quiet "$branch_name"
    else
        git -C "$source_tree" checkout --quiet -b "$branch_name" "$expected"
    fi
    test "$(git -C "$source_tree" rev-parse HEAD)" = "$expected"
    printf '%s\n' "source-git-ensure-branch=PASS branch=$branch_name revision=$expected"
    exit 0
fi
exec devtool "$operation" "$@"
