#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/run-podman-devtool.sh <modify|finish|finish-source|component-reset|component-add|update-recipe|recipe-task|source-git-repair|source-git-orphan-baseline|prune-stale-filament-workspace|source-git-stash|source-git-stash-pop|source-git-status|source-git-diff-check|source-git-log|source-git-revision|source-git-commit|source-git-commit-all|source-git-commit-baseline|source-git-branch|source-git-ensure-branch|source-git-repoint-branch|devtool-status|status> [arguments]

modify accepts either <recipe> or --no-extract <recipe> <srctree>, where the
existing source tree must be inside the fixed Devtool workspace or project.

Uses one persistent Podman container and one fixed host state directory mounted
at /workspace/state. The source/build/download/sstate state stays in that bind;
Yocto's TMPDIR and BitBake control socket use fixed container-local Linux paths
because macOS shared filesystems do not provide Yocto's case-sensitive/FIFO/
Unix-socket contract. The wrapper repairs stale ownership before the non-root
Devtool operation. It never creates named volumes, initializes a Podman
machine, creates a per-ticket source/build/TMPDIR, or deletes state.
EOF
}

fail() {
    echo "podman-devtool: $1" >&2
    exit 1
}

operation=${1:-}
shift || true
focused_no_extract=0
case "$operation" in
    modify)
        case "$#" in
            1)
                recipe=$1
                ;;
            3)
                test "$1" = --no-extract || { usage >&2; exit 2; }
                focused_no_extract=1
                recipe=$2
                source_tree=$3
                case "$source_tree" in
                    /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*|/workspace/project/*) ;;
                    *) fail "modify source must be inside the fixed workspace or /workspace/project" ;;
                esac
                ;;
            *)
                usage >&2
                exit 2
                ;;
        esac
        ;;
    finish)
        test "$#" -ge 2 -a "$#" -le 3 || { usage >&2; exit 2; }
        recipe=$1
        destination=$2
        if test "$#" -eq 3; then
            test "$3" = --force-patch-refresh || fail "unsupported finish option: $3"
        fi
        case "$destination" in
            /workspace/state/build/workspace/finish-layer) ;;
            /workspace/project|/workspace/project/*)
                fail "direct finish into the canonical project layer is forbidden; use finish-fluorite-devtool-patch.sh" ;;
            *) fail "finish destination must be the fixed finish layer" ;;
        esac
        ;;
    finish-source)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        destination=$2
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "finish-source source must be inside the fixed Devtool source workspace" ;;
        esac
        test "$destination" = /workspace/state/build/workspace/finish-layer || \
            fail "finish-source destination must be the fixed finish layer"
        ;;
    component-reset)
        test "$#" -eq 1 || { usage >&2; exit 2; }
        recipe=$1
        ;;
    component-add)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=$1
        source_tree=$2
        case "$source_tree" in
            /workspace/state/build/*|/workspace/project/*) ;;
            *) fail "component-add source must be inside /workspace/state/build or /workspace/project" ;;
        esac
        ;;
    update-recipe)
        test "$#" -ge 2 -a "$#" -le 3 || { usage >&2; exit 2; }
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
    recipe-task)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=$1
        task=$2
        case "$task" in
            do_patch|patch) task=patch ;;
            do_configure|configure) task=configure ;;
            *) fail "only do_patch and do_configure are allowed in the Mac recipe gate" ;;
        esac
        ;;
    source-git-status|source-git-diff-check|source-git-log|source-git-revision)
        test "$#" -eq 1 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        ;;
    source-git-repair)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        bundle_file=$2
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        test "$bundle_file" = /workspace/state/build/workspace/filament-vk-source-head.bundle || \
            fail "source Git repair requires the fixed Filament source bundle"
        ;;
    source-git-orphan-baseline)
        test "$#" -eq 3 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        branch_name=$2
        commit_message=$3
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git orphan baseline path must be inside the fixed source workspace" ;;
        esac
        case "$branch_name" in
            ''|-*|*[!a-zA-Z0-9._-]*) fail "source Git baseline branch must be a simple name" ;;
        esac
        case "$commit_message" in
            ''|-*|*$'\n'*) fail "source Git baseline commit message must be one non-option line" ;;
        esac
        ;;
    prune-stale-filament-workspace)
        test "$#" -eq 0 || { usage >&2; exit 2; }
        recipe=
        ;;
    source-git-stash|source-git-stash-pop)
        test "$#" -eq 1 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        ;;
    source-git-commit)
        test "$#" -eq 3 || { usage >&2; exit 2; }
        recipe=
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
    source-git-commit-all)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        commit_message=$2
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        case "$commit_message" in
            ''|-*|*$'\n'*) fail "source Git commit message must be one non-option line" ;;
        esac
        ;;
    source-git-commit-baseline)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=
        source_tree=$1
        commit_message=$2
        case "$source_tree" in
            /workspace/state/build/workspace/sources/*|/workspace/state/build/workspace/attic/sources/*) ;;
            *) fail "source Git path must be inside the fixed Devtool source workspace" ;;
        esac
        case "$commit_message" in
            ''|-*|*$'\n'*) fail "source Git commit message must be one non-option line" ;;
        esac
        ;;
    source-git-branch|source-git-ensure-branch|source-git-repoint-branch)
        test "$#" -eq 3 || { usage >&2; exit 2; }
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
    status)
        test "$#" -eq 0 || { usage >&2; exit 2; }
        recipe=
        ;;
    devtool-status)
        test "$#" -eq 0 || { usage >&2; exit 2; }
        recipe=
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

case "$recipe" in
    agl-ivi-image-*|core-image-*) fail "image recipes are forbidden on the Mac" ;;
esac

command -v podman >/dev/null 2>&1 || fail "podman is not installed"
podman info >/dev/null 2>&1 || fail "Podman backend/socket unavailable; start it outside this project"
podman_rootless=$(podman info --format '{{.Host.Security.Rootless}}')
test "$podman_rootless" = false || fail "Podman rootful connection is required for state-bind ownership"

repository_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
project_root=${FLUORITE_MAC_PROJECT_ROOT:-$repository_root}
agl_root=${FLUORITE_MAC_AGL_ROOT:-${HOME:-}/work/agl-trout-mac}
container_name=${FLUORITE_MAC_PODMAN_CONTAINER:-fluorite-mac-devtool}
image=${FLUORITE_MAC_PODMAN_IMAGE:-fluorite-yocto-devtool:22.04}
podman_uid=${FLUORITE_MAC_DEVTOOL_UID:-${FLUORITE_MAC_PODMAN_UID:-${FLUORITE_MAC_DOCKER_UID:-$(id -u)}}}
podman_gid=${FLUORITE_MAC_DEVTOOL_GID:-${FLUORITE_MAC_PODMAN_GID:-${FLUORITE_MAC_DOCKER_GID:-$(id -g)}}}
state_root=${FLUORITE_MAC_DEVTOOL_STATE_ROOT:-/tmp/fluorite-mac-devtool-state}
finish_layer_template=$repository_root/tools/yocto-devtool/finish-layer
workspace_layer_template=$repository_root/tools/yocto-devtool/workspace-layer/conf/layer.conf
finish_layer_state=$state_root/build/workspace/finish-layer
container_tmp=/workspace/tmp
bitbake_control=/tmp/fluorite-bitbake-control
repair_state=${FLUORITE_MAC_DEVTOOL_REPAIR_STATE:-auto}
devtool_timeout=${FLUORITE_MAC_DEVTOOL_TIMEOUT_SECONDS:-300}
bitbake_response_timeout=${FLUORITE_MAC_BITBAKE_RESPONSE_TIMEOUT_SECONDS:-180}
bitbake_python_overlay=/workspace/project/tools/yocto-devtool/bitbake-client-timeout
recipe_profile=${FLUORITE_MAC_DEVTOOL_RECIPE_PROFILE:-auto}

case "$repair_state" in
    auto|always) ;;
    *) fail "FLUORITE_MAC_DEVTOOL_REPAIR_STATE must be auto or always" ;;
esac
case "$devtool_timeout" in
    ''|*[!0-9]*) fail "FLUORITE_MAC_DEVTOOL_TIMEOUT_SECONDS must be numeric" ;;
esac
test "$devtool_timeout" -ge 60 -a "$devtool_timeout" -le 1800 || \
    fail "FLUORITE_MAC_DEVTOOL_TIMEOUT_SECONDS must be between 60 and 1800"
case "$bitbake_response_timeout" in
    ''|*[!0-9]*) fail "FLUORITE_MAC_BITBAKE_RESPONSE_TIMEOUT_SECONDS must be numeric" ;;
esac
test "$bitbake_response_timeout" -ge 60 -a "$bitbake_response_timeout" -le 1800 || \
    fail "FLUORITE_MAC_BITBAKE_RESPONSE_TIMEOUT_SECONDS must be between 60 and 1800"
case "$recipe_profile" in
    auto|focused|full) ;;
    *) fail "FLUORITE_MAC_DEVTOOL_RECIPE_PROFILE must be auto, focused, or full" ;;
esac

case "$podman_uid:$podman_gid" in
    ''|*[!0-9:]*) fail "Podman UID/GID must be numeric" ;;
esac
for name in "$container_name"; do
    case "$name" in
        ''|*[!a-zA-Z0-9_.-]*) fail "unsupported Podman name: $name" ;;
    esac
done
case "$project_root" in
    /mnt/yocto/*|*/build-flourite*|*/flourite/tmp*|*/flourite/downloads*|*/flourite/sstate-cache*)
        fail "project root points at a build-host path" ;;
esac
test "${project_root#/}" != "$project_root" || fail "project root must be absolute"
test "${agl_root#/}" != "$agl_root" || fail "AGL root must be absolute"
test "${state_root#/}" != "$state_root" || fail "state root must be absolute"
test -d "$project_root" || fail "project root is missing"
test -r "$agl_root/external/poky/oe-init-build-env" || fail "Mac AGL source is missing"
test -r "$project_root/scripts/assert-canonical-repository.sh" || fail "canonical guard is missing from project root"
test -r "$workspace_layer_template" || fail "workspace layer template is missing"
test -r "$repository_root/tools/yocto-devtool/bitbake-client-timeout/sitecustomize.py" || \
    fail "BitBake response-timeout shim is missing"
bash "$project_root/scripts/assert-canonical-repository.sh" >/dev/null || fail "project root is not canonical"
podman image exists "$image" >/dev/null 2>&1 || fail "Podman image is missing: $image"

# macOS exposes /tmp through /private/tmp. Canonicalize the existing bind root
# before comparing it with the container contract label; otherwise the same
# bind is falsely rejected as a different state root on every invocation.
mkdir -p "$state_root"
state_root=$(CDPATH= cd -- "$state_root" && pwd -P)
mkdir -p "$state_root/build" "$state_root/downloads" "$state_root/sstate-cache"

state_device=$(stat -f '%d' "$state_root/build")
for state_path in "$state_root/downloads" "$state_root/sstate-cache"; do
    test "$(stat -f '%d' "$state_path")" = "$state_device" || \
        fail "state paths must share one host filesystem: $state_path"
done

operation_lock=${FLUORITE_MAC_DEVTOOL_OPERATION_LOCK:-/tmp/fluorite-mac-devtool-operation.lock}
case "$operation_lock" in
    /tmp/fluorite-mac-devtool-operation.lock) ;;
    *) fail "operation lock must use the fixed /tmp path" ;;
esac

acquire_operation_lock() {
    while ! mkdir "$operation_lock" 2>/dev/null; do
        lock_pid=
        if test -r "$operation_lock/pid"; then
            read -r lock_pid < "$operation_lock/pid" || true
        fi
        case "$lock_pid" in
            ''|*[!0-9]*) ;;
            *)
                if ! kill -0 "$lock_pid" 2>/dev/null; then
                    rm -f "$operation_lock/pid"
                    rmdir "$operation_lock" 2>/dev/null || true
                fi
                ;;
        esac
        test -d "$operation_lock" || continue
        sleep 1
    done
    printf '%s\n' "$$" > "$operation_lock/pid"
}

release_operation_lock() {
    rm -f "$operation_lock/pid"
    rmdir "$operation_lock" 2>/dev/null || true
}

acquire_operation_lock
trap release_operation_lock EXIT

if ! podman container exists "$container_name"; then
    podman create --name "$container_name" --init \
        --label com.fluorite.mac-devtool.contract=1 \
        --label "com.fluorite.mac-devtool.project-root=$project_root" \
        --label "com.fluorite.mac-devtool.agl-root=$agl_root" \
        --label "com.fluorite.mac-devtool.image=$image" \
        --label "com.fluorite.mac-devtool.uid=$podman_uid" \
        --label "com.fluorite.mac-devtool.gid=$podman_gid" \
        --label "com.fluorite.mac-devtool.state-root=$state_root" \
        --label com.fluorite.mac-devtool.selinux=disabled \
        --label com.fluorite.mac-devtool.tmpdir=container-tmpfs \
        --security-opt label=disable \
        --tmpfs "$container_tmp:rw,size=3g" \
        -e AGL_ROOT=/workspace/agl -e BUILD_DIR=/workspace/state/build \
        -e DL_DIR=/workspace/state/downloads -e SSTATE_DIR=/workspace/state/sstate-cache \
        -e TMPDIR="$container_tmp" \
        -e BITBAKE_ENV_SCRIPT=/workspace/agl/external/poky/oe-init-build-env \
        -e AGL_SETUP_SCRIPT=/workspace/agl/meta-agl/scripts/aglsetup.sh \
        -e AGL_SETUP_MACHINE=qemux86-64 \
        -e 'EXTRA_BBLAYERS=/workspace/project/layers/meta-fluorite-trial /workspace/agl/meta-vulkan' \
        -e DEVTOOL_UID="$podman_uid" -e DEVTOOL_GID="$podman_gid" -e HOME=/tmp \
        -v "$project_root:/workspace/project:rw" \
        -v "$agl_root:/workspace/agl:ro" \
        -v "$state_root:/workspace/state:rw" \
        "$image" sleep infinity >/dev/null
else
    for pair in \
        com.fluorite.mac-devtool.contract=1 \
        "com.fluorite.mac-devtool.project-root=$project_root" \
        "com.fluorite.mac-devtool.agl-root=$agl_root" \
        "com.fluorite.mac-devtool.image=$image" \
        "com.fluorite.mac-devtool.uid=$podman_uid" \
        "com.fluorite.mac-devtool.gid=$podman_gid" \
        "com.fluorite.mac-devtool.state-root=$state_root" \
        com.fluorite.mac-devtool.selinux=disabled \
        com.fluorite.mac-devtool.tmpdir=container-tmpfs; do
        label=${pair%%=*}
        expected=${pair#*=}
        actual=$(podman inspect --format "{{index .Config.Labels \"$label\"}}" "$container_name")
        test "$actual" = "$expected" || fail "existing container contract mismatch for $label"
    done
fi

running=$(podman inspect --format '{{.State.Running}}' "$container_name")
test "$running" = true || podman start "$container_name" >/dev/null

for _ in {1..60}; do
    podman exec "$container_name" test -f /tmp/fluorite-devtool-ready >/dev/null 2>&1 && break
    sleep 1
done
podman exec "$container_name" test -f /tmp/fluorite-devtool-ready || fail "persistent Podman Devtool container did not become ready"

# A timed-out Devtool can leave its BitBake server behind even when the host
# wrapper has exited. Do not reconnect to that state silently: report the
# exact residual processes and require bounded cleanup before another task.
stale_devtool_processes=$(podman exec "$container_name" sh -lc \
    "ps -eo pid=,ppid=,args= | grep -E '(/scripts/devtool|run-devtool|bitbake-server)' | grep -v grep || true")
test -z "$stale_devtool_processes" || {
    printf '%s\n' "$stale_devtool_processes" >&2
    fail "stale Devtool/BitBake processes remain; clean only these recorded PIDs before retry"
}

# A status check must be bounded and observational.  The persistent downloads
# tree can contain thousands of files, so do not trigger the ownership repair
# scan or rewrite BitBake configuration merely to answer whether the existing
# container and binds are usable.  Real Devtool operations continue through
# the repair path below.
if test "$operation" = status; then
    podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
        TMPDIR="$container_tmp" \
        /bin/bash -lc '
        set -eu
        test -d /workspace/project && test -r /workspace/project && test -w /workspace/project
        test -d /workspace/agl && test -r /workspace/agl && test ! -w /workspace/agl
        for state_dir in /workspace/state/build /workspace/state/downloads /workspace/state/sstate-cache; do
            test -d "$state_dir" && test -r "$state_dir" && test -w "$state_dir"
        done
        test -d "$TMPDIR" && test -r "$TMPDIR" && test -w "$TMPDIR"
        # The /workspace/tmp tmpfs is recreated on container restart. Recreate
        # its disposable work directory before the FIFO probe so status remains
        # valid while the bind-mounted Yocto state stays untouched.
        mkdir -p "$TMPDIR/work"
        test -d "$TMPDIR/work" && test -r "$TMPDIR/work" && test -w "$TMPDIR/work"
        test "$(findmnt -T "$TMPDIR" -no fstype)" = tmpfs
        fifo_probe="$TMPDIR/work/.fluorite-devtool-status-fifo-probe"
        rm -f "$fifo_probe"
        mkfifo "$fifo_probe"
        test -p "$fifo_probe"
        rm -f "$fifo_probe"
        copy_probe="$TMPDIR/.fluorite-devtool-status-copy-probe"
        rm -rf "$copy_probe"
        mkdir -p "$copy_probe/source/nested" "$copy_probe/destination"
        printf "%s\n" probe >"$copy_probe/source/nested/file"
        cp -afl --preserve=xattr "$copy_probe/source"/* "$copy_probe/destination"/
        test -f "$copy_probe/destination/nested/file"
        rm -rf "$copy_probe"
        printf "%s\n" "status=PASS project=rw agl=ro state-bind=rw tmpdir=state-bind-ownership-fifo-xattr=PASS repair=deferred"
    '
    exit 0
fi

focused_recipe=toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo
focused_profile=0
if test "$recipe_profile" != full; then
    case "$recipe" in
        "$focused_recipe") focused_profile=1 ;;
    esac
    if test "$operation" = finish-source; then
        case "$source_tree" in
            /workspace/state/build/workspace/sources/$focused_recipe|\
            /workspace/state/build/workspace/attic/sources/$focused_recipe.*)
                focused_profile=1
                ;;
        esac
    fi
fi
# finish-source operates on an already prepared Git tree, so it has the same
# narrow metadata requirement as modify --no-extract. Avoid expanding the
# provider graph and unrelated stale bbappends during official patch finish.
if test "$focused_profile" -eq 1 && test "$operation" = finish-source; then
    focused_no_extract=1
fi

active_bitbake_control=$bitbake_control
if test "$focused_profile" -eq 1; then
    # Devtool only needs the target recipe's metadata for modify/finish. Keep
    # the normal source and state binds, mask unrelated dynamic bbappends, and
    # add the target recipe without replacing the layer-provided BBFILES. The
    # provider list is required for native task dependencies such as
    # quilt-native. TMPDIR remains the single fixed /workspace/tmp bind; this
    # is a control directory, not another work tree.
    active_bitbake_control=/tmp/fluorite-bitbake-focused-control
    podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
        BUILD_DIR=/workspace/state/build \
        FOCUSED_RECIPE="$focused_recipe" \
        FOCUSED_NO_EXTRACT="$focused_no_extract" \
        FOCUSED_CONTROL="$active_bitbake_control" \
        /bin/bash -lc '
        set -eu
        rm -rf "$FOCUSED_CONTROL/cache"
        mkdir -p "$FOCUSED_CONTROL/conf"
        rm -f "$FOCUSED_CONTROL/conf/local.conf" \
            "$FOCUSED_CONTROL/conf/bblayers.conf" \
            "$FOCUSED_CONTROL/conf/devtool.conf" \
            "$FOCUSED_CONTROL/workspace" \
            "$FOCUSED_CONTROL/bitbake.lock" \
            "$FOCUSED_CONTROL/bitbake.sock" \
            "$FOCUSED_CONTROL/bitbake-cookerdaemon.log"
        cp -p "$BUILD_DIR/conf/local.conf" "$FOCUSED_CONTROL/conf/local.conf"
        sed -i -E \
            "/^[[:space:]]*require conf\\/include\\/agl-(demo|app-framework|kuksa-val|netboot|pipewire|selinux)\\.inc[[:space:]]*$/d; \
             /^[[:space:]]*(DL_DIR|SSTATE_DIR|TMPDIR)[[:space:]]*=/d" \
            "$FOCUSED_CONTROL/conf/local.conf"
        {
            printf "\\n# Managed by fluorite Mac focused Devtool profile.\\n"
            printf "DL_DIR = \\\"/workspace/state/downloads\\\"\\n"
            printf "SSTATE_DIR = \\\"/workspace/state/sstate-cache\\\"\\n"
            printf "TMPDIR = \\\"/workspace/tmp\\\"\\n"
            if test "$FOCUSED_NO_EXTRACT" -eq 1; then
                # --no-extract only parses the target recipe and reuses an
                # already prepared Git tree; do not expand the provider graph.
                printf "BBFILES = \\\"/workspace/project/layers/meta-fluorite-trial/recipes-graphics/flutter-apps/%s_git.bb\\\"\\n" "$FOCUSED_RECIPE"
            else
                # Normal extraction needs the layer-provided provider list
                # (including quilt-native), so add rather than replace it.
                printf "BBFILES += \\\"/workspace/project/layers/meta-fluorite-trial/recipes-graphics/flutter-apps/%s_git.bb\\\"\\n" "$FOCUSED_RECIPE"
            fi
            printf "BBMASK += \\\"/workspace/agl/.*/dynamic-layers/.*\\\\.bbappend$\\\"\\n"
        } >>"$FOCUSED_CONTROL/conf/local.conf"
        cat >"$FOCUSED_CONTROL/conf/bblayers.conf" <<'EOF'
BBLAYERS = " \
  /workspace/agl/external/poky/meta \
  /workspace/agl/external/poky/meta-poky \
  /workspace/agl/external/meta-openembedded/meta-oe \
  /workspace/agl/external/meta-openembedded/meta-python \
  /workspace/agl/meta-agl/meta-agl-core \
  /workspace/agl/meta-agl/meta-agl-bsp \
  /workspace/agl/meta-agl/meta-agl-flutter \
  /workspace/agl/external/meta-flutter \
  /workspace/agl/external/meta-clang \
  /workspace/agl/meta-vulkan \
  /workspace/project/layers/meta-fluorite-trial \
  /workspace/state/build/workspace \
  "
EOF
        printf "[General]\\nworkspace_path = /workspace/state/build/workspace\\n" \
            >"$FOCUSED_CONTROL/conf/devtool.conf"
        ln -s "$BUILD_DIR/workspace" "$FOCUSED_CONTROL/workspace"
        '
fi

if { test "$operation" = finish || test "$operation" = finish-source; } &&
    test "$destination" = /workspace/state/build/workspace/finish-layer; then
    test -r "$finish_layer_template/conf/layer.conf" || fail "fixed finish layer template is missing"
    test -r "$finish_layer_template/recipes-graphics/filament/filament-vk_1.65.4.bb" || \
        fail "fixed finish layer recipe template is missing"
    mkdir -p "$finish_layer_state/conf" "$finish_layer_state/recipes-graphics/filament"
    cp -p "$finish_layer_template/conf/layer.conf" "$finish_layer_state/conf/layer.conf"
    cp -p "$finish_layer_template/recipes-graphics/filament/filament-vk_1.65.4.bb" \
        "$finish_layer_state/recipes-graphics/filament/filament-vk_1.65.4.bb"
fi

# The state bind contains entries left by a root-owned legacy wrapper. BitBake
# needs to create FIFOs below TMPDIR as the host UID, so repair only ownership
# of the fixed state tree before the non-root operation. No files are deleted.
podman exec "$container_name" env \
    BUILD_DIR=/workspace/state/build \
    DL_DIR=/workspace/state/downloads \
    SSTATE_DIR=/workspace/state/sstate-cache \
    TMPDIR="$container_tmp" \
    WORKSPACE_LAYER_TEMPLATE=/workspace/project/tools/yocto-devtool/workspace-layer/conf/layer.conf \
    REPAIR_STATE="$repair_state" \
    OWNER_MARKER="/workspace/state/.fluorite-devtool-owner-${podman_uid}-${podman_gid}" \
    /bin/bash -lc '
    set -eu
    mkdir -p "$TMPDIR/work"
    chown "$DEVTOOL_UID:$DEVTOOL_GID" "$TMPDIR/work"
    marker_owner=
    if test -e "$OWNER_MARKER"; then
        marker_owner=$(cat "$OWNER_MARKER" 2>/dev/null || true)
    fi
    if test "$REPAIR_STATE" = always || test "$marker_owner" != "$DEVTOOL_UID:$DEVTOOL_GID"; then
        for state_dir in "$BUILD_DIR" "$DL_DIR" "$SSTATE_DIR" "$TMPDIR"; do
            find "$state_dir" -ignore_readdir_race -xdev \( -type d -o -type f \) \
                \( ! -user "$DEVTOOL_UID" -o ! -group "$DEVTOOL_GID" \) \
                -exec /bin/bash -c '\''
                    uid=$1
                    gid=$2
                    shift 2
                    for path do
                        test -e "$path" || continue
                        chown "$uid:$gid" "$path"
                    done
                '\'' bash "$DEVTOOL_UID" "$DEVTOOL_GID" {} +
        done
        printf "%s\n" "$DEVTOOL_UID:$DEVTOOL_GID" >"$OWNER_MARKER"
    fi

    while IFS= read -r native_bin; do
        for tool in quilt libtool libtoolize; do
            if test -f "$native_bin/$tool" && test ! -x "$native_bin/$tool"; then
                chmod u+x "$native_bin/$tool"
            fi
        done
    done < <(find "$TMPDIR/work" -xdev -type d -path "*/recipe-sysroot-native/usr/bin" -print)

    # Podman restarts preserve the mounted source/recipe state but can leave
    # the standard Devtool workspace layer only in an obsolete control copy.
    # Restore the single missing metadata file from the tracked Yocto-standard
    # template; never add the legacy control workspace as a second BBLAYER.
    workspace_conf="$BUILD_DIR/workspace/conf"
    mkdir -p "$workspace_conf"
    if test ! -r "$workspace_conf/layer.conf"; then
        test -r "$WORKSPACE_LAYER_TEMPLATE" || {
            echo "workspace layer template is missing: $WORKSPACE_LAYER_TEMPLATE" >&2
            exit 1
        }
        cp -p "$WORKSPACE_LAYER_TEMPLATE" "$workspace_conf/layer.conf"
    fi
    chown "$DEVTOOL_UID:$DEVTOOL_GID" "$workspace_conf" "$workspace_conf/layer.conf"
'

podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
    TMPDIR="$container_tmp" \
    /bin/bash -lc '
    test -d /workspace/project && test -r /workspace/project && test -w /workspace/project
    test -d /workspace/agl && test -r /workspace/agl && test ! -w /workspace/agl
    for state_dir in /workspace/state/build /workspace/state/downloads /workspace/state/sstate-cache; do
        test -d "$state_dir" && test -r "$state_dir" && test -w "$state_dir"
    done
    test -d "$TMPDIR" && test -r "$TMPDIR" && test -w "$TMPDIR"
    test -d "$TMPDIR/work" && test -r "$TMPDIR/work" && test -w "$TMPDIR/work"
    test "$(findmnt -T "$TMPDIR" -no fstype)" = tmpfs
    fifo_probe="$TMPDIR/work/.fluorite-devtool-fifo-probe"
    rm -f "$fifo_probe"
    mkfifo "$fifo_probe"
    test -p "$fifo_probe"
    rm -f "$fifo_probe"
    copy_probe=/workspace/state/.fluorite-devtool-copy-probe
    rm -rf "$copy_probe"
    mkdir -p "$copy_probe/source/nested" "$copy_probe/destination"
    printf "%s\n" "probe" >"$copy_probe/source/nested/file"
    cp -afl --preserve=xattr "$copy_probe/source"/* "$copy_probe/destination"/
    test -f "$copy_probe/destination/nested/file"
    rm -rf "$copy_probe"
    printf "%s\n" "mount-permission=PASS project=rw agl=ro state-bind=rw tmpdir=state-bind-ownership-fifo-xattr=PASS"
'

# Reassert the fixed state paths for an already-created container. Remove only
# managed assignments/comments and append the current contract once.
podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
    BUILD_DIR=/workspace/state/build \
    DL_DIR=/workspace/state/downloads \
    SSTATE_DIR=/workspace/state/sstate-cache \
    TMPDIR="$container_tmp" \
    /bin/bash -lc '
        if test -r "$BUILD_DIR/conf/local.conf"; then
            sed -i -E \
                "/^[[:space:]]*(DL_DIR|SSTATE_DIR|TMPDIR)[[:space:]]*=/d; /^[[:space:]]*# Managed by fluorite-yocto-devtool\\. Keep Yocto state (in one persistent bind-mounted directory|in the fixed Podman contract)\\.?[[:space:]]*$/d" \
                "$BUILD_DIR/conf/local.conf"
            {
                printf "\\n# Managed by fluorite-yocto-devtool. Keep Yocto state in the fixed Podman contract.\\n"
                printf "DL_DIR = \\\"%s\\\"\\n" "$DL_DIR"
                printf "SSTATE_DIR = \\\"%s\\\"\\n" "$SSTATE_DIR"
                printf "TMPDIR = \\\"%s\\\"\\n" "$TMPDIR"
            } >>"$BUILD_DIR/conf/local.conf"
        fi
    '

# BitBake derives its local control socket from the build directory. Keep the
# actual build/config/workspace bind-mounted, but provide one fixed
# container-local control directory so the socket is created on Linux overlayfs.
podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
    BUILD_DIR=/workspace/state/build \
    BITBAKE_CONTROL_DIR="$bitbake_control" \
    /bin/bash -lc '
        set -eu
        mkdir -p "$BITBAKE_CONTROL_DIR/conf"
        # Normalize the persistent build configuration before exposing it via
        # the control-directory symlink. Editing the symlink path with sed -i
        # would replace only the symlink and leave the bind-mounted state stale.
        sed -i \
            -e "\|/workspace/state/build/workspace|d" \
            -e "\|$BITBAKE_CONTROL_DIR/workspace|d" \
            "$BUILD_DIR/conf/bblayers.conf"
        printf "\\nBBLAYERS += \\\" %s/workspace \\\"\\n" "$BITBAKE_CONTROL_DIR" >> \
            "$BUILD_DIR/conf/bblayers.conf"
        ln -sfn "$BUILD_DIR/conf/bblayers.conf" "$BITBAKE_CONTROL_DIR/conf/bblayers.conf"
        ln -sfn "$BUILD_DIR/conf/local.conf" "$BITBAKE_CONTROL_DIR/conf/local.conf"
        ln -sfn "$BUILD_DIR/workspace" "$BITBAKE_CONTROL_DIR/workspace"
        if test ! -r "$BITBAKE_CONTROL_DIR/conf/devtool.conf"; then
            printf "[General]\\nworkspace_path = %s\\n" "$BUILD_DIR/workspace" >"$BITBAKE_CONTROL_DIR/conf/devtool.conf"
        fi
    '

if test "$operation" = recipe-task; then
    if ! podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
        TMPDIR="$container_tmp" \
        /bin/bash -lc '
            set -eu
            probe="$TMPDIR/.fluorite-devtool-xattr-probe"
            rm -rf "$probe"
            mkdir -p "$probe/source/nested" "$probe/destination"
            printf "%s\\n" probe >"$probe/source/nested/file"
            cp -afl --preserve=xattr "$probe/source"/* "$probe/destination"/
            rm -rf "$probe"
        '; then
        fail "Mac recipe task gate requires TMPDIR xattr support; run the authoritative task on the Mini PC"
    fi
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
        DL_DIR=/workspace/state/downloads \
        SSTATE_DIR=/workspace/state/sstate-cache \
        TMPDIR="$container_tmp" \
        BUILDDIR="$active_bitbake_control" \
        PYTHONPATH="$bitbake_python_overlay" \
        FLUORITE_BITBAKE_CLIENT_RESPONSE_TIMEOUT="$bitbake_response_timeout" \
        RECIPE="$recipe" TASK="$task" \
        /bin/bash -lc 'source "$BITBAKE_ENV_SCRIPT" "$BUILDDIR" >/dev/null; exec bitbake -c "$TASK" -f "$RECIPE"'
fi

if test "$operation" = source-git-repair; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        bundle_file=$2
        alt="$source_tree/.git/objects/info/alternates"
        backup="$alt.legacy"
        main_ref="$source_tree/.git/refs/heads/main"
        main_backup="$source_tree/.git/main-ref.legacy"
        release_ref="$source_tree/.git/refs/heads/release"
        release_backup="$source_tree/.git/release-ref.legacy"
        packed_refs="$source_tree/.git/packed-refs"
        packed_backup="$source_tree/.git/packed-refs.legacy"
        test -d "$source_tree/.git" || {
            echo "source Git metadata is missing: $source_tree/.git" >&2
            exit 1
        }
        test -r "$bundle_file" || {
            echo "source Git repair bundle is missing: $bundle_file" >&2
            exit 1
        }
        test ! -e "$backup" || {
            echo "source Git repair backup already exists: $backup" >&2
            exit 1
        }
        test ! -e "$main_backup" || {
            echo "source Git main-ref backup already exists: $main_backup" >&2
            exit 1
        }
        test ! -e "$release_backup" || {
            echo "source Git release-ref backup already exists: $release_backup" >&2
            exit 1
        }
        test ! -e "$packed_backup" || {
            echo "source Git packed-refs backup already exists: $packed_backup" >&2
            exit 1
        }
        if test -e "$main_ref"; then
            mv -- "$main_ref" "$main_backup"
        fi
        if test -e "$release_ref"; then
            mv -- "$release_ref" "$release_backup"
        fi
        if test -e "$packed_refs"; then
            mv -- "$packed_refs" "$packed_backup"
        fi
        if test -e "$alt"; then
            mv -- "$alt" "$backup"
        fi
        restore=1
        restore_alt() {
            if test "$restore" -eq 1 && test -e "$packed_backup"; then
                mv -- "$packed_backup" "$packed_refs"
            fi
            if test "$restore" -eq 1 && test -e "$release_backup"; then
                mv -- "$release_backup" "$release_ref"
            fi
            if test "$restore" -eq 1 && test -e "$main_backup"; then
                mv -- "$main_backup" "$main_ref"
            fi
            if test "$restore" -eq 1 && test -e "$backup"; then
                mv -- "$backup" "$alt"
            fi
        }
        trap restore_alt EXIT
        git -C "$source_tree" fetch --no-tags "$bundle_file" \
            HEAD:refs/remotes/fluorite/source-head \
            refs/heads/main:refs/remotes/fluorite/source-main
        git -C "$source_tree" cat-file -e refs/remotes/fluorite/source-head^{commit}
        git -C "$source_tree" cat-file -e refs/remotes/fluorite/source-head^{tree}
        git -C "$source_tree" cat-file -e refs/remotes/fluorite/source-main^{commit}
        if test -e "$release_backup"; then
            mv -- "$release_backup" "$release_ref"
        fi
        if test -e "$main_backup"; then
            mv -- "$main_backup" "$main_ref"
        fi
        git -C "$source_tree" cat-file -e HEAD^{commit}
        git -C "$source_tree" cat-file -e HEAD^{tree}
        git -C "$source_tree" diff --check
        git -C "$source_tree" status --short --branch
        rm -f -- "$backup"
        restore=0
        trap - EXIT
        printf "%s\n" "source-git-repair=PASS source=$source_tree bundle=$bundle_file"
        ' bash "$source_tree" "$bundle_file"
fi

if test "$operation" = source-git-orphan-baseline; then
    exec podman exec -i --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -s -- "$source_tree" "$branch_name" "$commit_message" <<'CONTAINER_SCRIPT'
set -eu
source_tree=$1
branch_name=$2
commit_message=$3

test -d "$source_tree/.git" || {
    echo "source Git metadata is missing: $source_tree/.git" >&2
    exit 1
}
test -z "$(git -C "$source_tree" -c submodule.recurse=false status --porcelain --untracked-files=all --ignore-submodules=all)" || {
    echo "source Git tree must be clean before orphan baseline creation" >&2
    exit 1
}
git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name" && {
    echo "source Git baseline branch already exists: $branch_name" >&2
    exit 1
}
old_branch=$(git -C "$source_tree" branch --show-current)
old_head=$(git -C "$source_tree" rev-parse --verify HEAD^{commit})

# Keep the old branch as an auditable archive. The new branch deliberately has
# no parent: its single commit is a complete snapshot of the effective source,
# so a missing historical object cannot affect the next official Devtool diff.
git -C "$source_tree" checkout --orphan "$branch_name" >/dev/null
git -C "$source_tree" -c submodule.recurse=false add -A
# The effective upstream snapshot contains pre-existing whitespace and EOF
# diagnostics. They are source data, not a baseline-integrity failure; the
# project change gate checks only generated patch diffs later in the workflow.
staged_tree_files=$(git -C "$source_tree" -c submodule.recurse=false diff --cached --name-only | awk 'NF {count++} END {print count + 0}')
test "$staged_tree_files" -ge 100 || {
    echo "source Git orphan baseline is unexpectedly partial: staged=$staged_tree_files" >&2
    exit 1
}
git -C "$source_tree" -c user.name="Fluorite Devtool" \
    -c user.email="fluorite-devtool@example.invalid" \
    commit -m "$commit_message" >/dev/null
new_head=$(git -C "$source_tree" rev-parse --verify HEAD^{commit})

# Verify only the active new baseline. The archived branch is intentionally
# retained even though its historical objects are known to be incomplete.
missing_objects=$(git -C "$source_tree" rev-list --objects "$new_head" | \
    awk '{print $1}' | \
    git -C "$source_tree" cat-file --batch-check='%(objectname) %(objecttype)' | \
    awk '$2 == "missing" {print $1}')
test -z "$missing_objects" || {
    echo "active source Git orphan baseline has missing objects:" >&2
    printf '%s\n' "$missing_objects" >&2
    exit 1
}
git -C "$source_tree" diff --check --quiet
git -C "$source_tree" status --short --branch
printf '%s\n' "source-git-orphan-baseline=PASS old_branch=$old_branch old_head=$old_head branch=$branch_name baseline=$new_head files=$staged_tree_files"
CONTAINER_SCRIPT
fi

if test "$operation" = prune-stale-filament-workspace; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        attic=/workspace/state/build/workspace/attic/filament-vk
        append=/workspace/state/build/workspace/appends/filament-vk_1.54.3.bbappend
        removed=0
        if test -e "$attic"; then
            test -d "$attic" || {
                echo "stale Filament attic is not a directory: $attic" >&2
                exit 1
            }
        expected_files="
7aed257f3f29dce4a5797862af0879cfa04265c5ab053b061371501f1dd2c04f  filament-vk/0001-diag-probe-production-target-pixels.patch
eec91bc004aafa630db922fa1a16cf538cb02698a9ebcc3ad00dc4c8973e2381  filament-vk/0001-diag-trace-draw2-Vulkan-output-target.patch
b65aa258ffd2d7fa4bca5c66c5c0eb5fdce8778891c9f148cceaddb33519fb69  filament-vk/0001-fix-capture-target-probe-constants.patch
"
        while read -r expected relative; do
            test -n "$expected" || continue
            path="$attic/$relative"
            test -f "$path" || {
                echo "stale attic file is missing: $path" >&2
                exit 1
            }
            actual=$(sha256sum "$path" | cut -d " " -f1)
            test "$actual" = "$expected" || {
                echo "stale attic hash mismatch: $path" >&2
                exit 1
            }
        done <<EOF
$expected_files
EOF
            rm -rf -- "$attic"
            test ! -e "$attic"
            removed=1
        fi
        if test -e "$append"; then
            test -f "$append" || {
                echo "stale Filament append is not a file: $append" >&2
                exit 1
            }
            actual=$(sha256sum "$append" | cut -d " " -f1)
            test "$actual" = 68d37c8de745a7487b097b63cbd92384f849451f9ad6bf53efc6296cfb762bbf || {
                echo "stale Filament append hash mismatch: $append" >&2
                exit 1
            }
            rm -f -- "$append"
            test ! -e "$append"
            removed=1
        fi
        test "$removed" -eq 1 || {
            echo "no stale Filament workspace metadata found" >&2
            exit 1
        }
        printf "%s\n" "prune-stale-filament-workspace=PASS"
        '
fi

if test "$operation" = source-git-stash; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        message="fluorite-old-patched-baseline"
        test -d "$source_tree/.git" || exit 1
        test -z "$(git -C "$source_tree" status --porcelain)" && {
            echo "source Git tree is already clean: $source_tree" >&2
            exit 1
        }
        git -C "$source_tree" stash push --include-untracked -m "$message" >/dev/null
        git -C "$source_tree" status --porcelain
        git -C "$source_tree" stash list | head -1 | grep -Fq "$message"
        printf "%s\n" "source-git-stash=PASS source=$source_tree"
        ' bash "$source_tree"
fi

if test "$operation" = source-git-stash-pop; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        message="fluorite-old-patched-baseline"
        test -d "$source_tree/.git" || exit 1
        top_stash=$(git -C "$source_tree" stash list --format='%H %s' | head -1)
        printf '%s\n' "$top_stash" | grep -Fq " $message" || {
            echo "expected source Git stash is not at the top of the stack" >&2
            exit 1
        }
        stash_oid=${top_stash%% *}
        git -C "$source_tree" stash pop >/dev/null
        git -C "$source_tree" stash list --format='%H %s' | grep -Fq "$stash_oid " && {
            echo "source Git stash object was not removed after pop" >&2
            exit 1
        }
        printf "%s\n" "source-git-stash-pop=PASS source=$source_tree stash=$stash_oid"
        ' bash "$source_tree"
fi

if test "$operation" = source-git-status; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        git -C "$source_tree" -c submodule.recurse=false status --short --branch --ignore-submodules=all
fi

if test "$operation" = source-git-diff-check; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        git -C "$source_tree" -c submodule.recurse=false diff --check --ignore-submodules=all
fi

if test "$operation" = source-git-log; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        git -C "$source_tree" --no-pager log -8 --oneline --decorate
fi

if test "$operation" = source-git-revision; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        git -C "$source_tree" rev-parse --verify HEAD^{commit}
fi

if test "$operation" = source-git-commit; then
    exec podman exec -i --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -s -- "$source_tree" "$source_path" "$commit_message" <<'CONTAINER_SCRIPT'
set -eu
source_tree=$1
source_path=$2
commit_message=$3
changed=$(git -C "$source_tree" -c submodule.recurse=false status --porcelain --untracked-files=all --ignore-submodules=all)
changed_count=$(printf '%s\n' "$changed" | awk 'NF { count++ } END { print count + 0 }')
test "$changed_count" -eq 1 || {
    echo "source Git commit requires exactly one changed path" >&2
    exit 1
}
changed_path=$(printf '%s\n' "$changed" | sed -n '1s/^.. //p')
test "$changed_path" = "$source_path" || {
    echo "source Git commit changed path does not match the requested file" >&2
    exit 1
}
git -C "$source_tree" -c submodule.recurse=false diff --check --ignore-submodules=all
git -C "$source_tree" -c submodule.recurse=false add -u --
untracked=$(git -C "$source_tree" -c submodule.recurse=false ls-files --others --exclude-standard)
if test -n "$untracked"; then
    git -C "$source_tree" -c submodule.recurse=false add -- $untracked
fi
staged=$(git -C "$source_tree" -c submodule.recurse=false diff --cached --name-only)
test "$staged" = "$source_path" || {
    echo "source Git add . staged an unexpected path" >&2
    exit 1
}
git -C "$source_tree" -c submodule.recurse=false diff --cached --check --ignore-submodules=all
git -C "$source_tree" -c submodule.recurse=false -c user.name="Fluorite Devtool" \
    -c user.email="fluorite-devtool@example.invalid" \
    commit -m "$commit_message"
CONTAINER_SCRIPT
fi

if test "$operation" = source-git-commit-all; then
    exec podman exec -i --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -s -- "$source_tree" "$commit_message" <<'CONTAINER_SCRIPT'
set -eu
source_tree=$1
commit_message=$2
test -z "$(git -C "$source_tree" diff --cached --name-only)" || {
    echo "source Git index is already staged; refusing multi-file commit" >&2
    exit 1
}
git -C "$source_tree" -c submodule.recurse=false diff --check --ignore-submodules=all
git -C "$source_tree" -c submodule.recurse=false add -u --
untracked=$(git -C "$source_tree" -c submodule.recurse=false ls-files --others --exclude-standard)
if test -n "$untracked"; then
    git -C "$source_tree" -c submodule.recurse=false add -- $untracked
fi
staged=$(git -C "$source_tree" -c submodule.recurse=false diff --cached --name-only)
test -n "$staged" || {
    echo "source Git add . staged no source changes" >&2
    exit 1
}
git -C "$source_tree" -c submodule.recurse=false diff --cached --check --ignore-submodules=all
git -C "$source_tree" -c submodule.recurse=false -c user.name="Fluorite Devtool" \
    -c user.email="fluorite-devtool@example.invalid" \
    commit -m "$commit_message"
CONTAINER_SCRIPT
fi

if test "$operation" = source-git-commit-baseline; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        commit_message=$2
        test -z "$(git -C "$source_tree" diff --cached --name-only)" || {
            echo "source Git index is already staged; refusing baseline commit" >&2
            exit 1
        }
        git -C "$source_tree" -c submodule.recurse=false diff --check --ignore-submodules=all
        baseline_tree_files=$(git -C "$source_tree" -c submodule.recurse=false ls-tree -r --name-only HEAD | awk "NF {count++} END {print count + 0}")
        if test "$baseline_tree_files" -lt 100; then
            # The old helper could leave a full index attached to a partial
            # HEAD. Rebuild only the index in that recovery case; source files
            # remain untouched and are staged by the complete add below.
            submodule_gitlink=$(git -C "$source_tree" ls-files --stage -- plugins/common/sdbus/third_party/sdbus-cpp | cut -d" " -f2)
            git -C "$source_tree" read-tree --empty
        fi
        # A Devtool baseline must describe the complete effective source, not
        # only paths that were already tracked by a previous partial commit.
        # `git add -u` silently preserves a partial tree and makes the next
        # official update-recipe diff depend on accidental source history.
        # The Devtool root-level Quilt `patches/series` is workspace metadata,
        # not source. Keep it out of the source-Git baseline while retaining
        # any tracked component paths named `patches` below the source root.
        git -C "$source_tree" -c submodule.recurse=false add -u --
        untracked=$(git -C "$source_tree" -c submodule.recurse=false ls-files --others --exclude-standard)
        if test -n "$untracked"; then
            git -C "$source_tree" -c submodule.recurse=false add -- $untracked
        fi
        if test "$baseline_tree_files" -lt 100 && test -n "${submodule_gitlink:-}"; then
            git -C "$source_tree" update-index --add --cacheinfo 160000 "$submodule_gitlink" plugins/common/sdbus/third_party/sdbus-cpp
        fi
        git -C "$source_tree" -c submodule.recurse=false diff --cached --check --ignore-submodules=all
        staged_tree_files=$(git -C "$source_tree" -c submodule.recurse=false diff --cached --name-only | awk "NF {count++} END {print count + 0}")
        if test "$baseline_tree_files" -lt 100 && test "$staged_tree_files" -lt 100; then
            echo "source Git baseline remains partial: HEAD=$baseline_tree_files staged=$staged_tree_files" >&2
            exit 1
        fi
        git -C "$source_tree" -c submodule.recurse=false -c user.name="Fluorite Devtool" \
            -c user.email="fluorite-devtool@example.invalid" \
            commit -m "$commit_message"
    ' bash "$source_tree" "$commit_message"
fi

if test "$operation" = source-git-branch; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        branch_name=$2
        revision=$3
        if git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name"; then
            echo "source Git branch already exists: $branch_name" >&2
            exit 1
        fi
        exec git -C "$source_tree" checkout -b "$branch_name" "$revision"
    ' bash "$source_tree" "$branch_name" "$revision"
fi

if test "$operation" = source-git-repoint-branch; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        branch_name=$2
        revision=$3
        current=$(git -C "$source_tree" branch --show-current)
        test "$current" != "$branch_name" || {
            echo "source Git cannot repoint the checked-out branch: $branch_name" >&2
            exit 1
        }
        git -C "$source_tree" rev-parse --verify "$revision^{commit}" >/dev/null
        git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name" || {
            echo "source Git branch is missing: $branch_name" >&2
            exit 1
        }
        git -C "$source_tree" branch -f "$branch_name" "$revision"
        expected=$(git -C "$source_tree" rev-parse --verify "$revision^{commit}")
        actual=$(git -C "$source_tree" rev-parse --verify "refs/heads/$branch_name^{commit}")
        test "$actual" = "$expected"
        printf "%s\n" "source-git-repoint-branch=PASS branch=$branch_name revision=$expected"
    ' bash "$source_tree" "$branch_name" "$revision"
fi

if test "$operation" = source-git-ensure-branch; then
    exec podman exec --user "$podman_uid:$podman_gid" "$container_name" \
        /bin/bash -lc '
        set -eu
        source_tree=$1
        branch_name=$2
        revision=$3
        test -z "$(git -C "$source_tree" status --porcelain)" || {
            echo "source Git tree is dirty: $source_tree" >&2
            exit 1
        }
        expected=$(git -C "$source_tree" rev-parse --verify "$revision^{commit}")
        if git -C "$source_tree" show-ref --verify --quiet "refs/heads/$branch_name"; then
            actual=$(git -C "$source_tree" rev-parse --verify "refs/heads/$branch_name^{commit}")
            test "$actual" = "$expected" || {
                echo "source Git branch points at a different revision: $branch_name" >&2
                exit 1
            }
            git -C "$source_tree" checkout --quiet "$branch_name"
        else
            git -C "$source_tree" checkout --quiet -b "$branch_name" "$expected"
        fi
        test "$(git -C "$source_tree" rev-parse HEAD)" = "$expected"
        printf "%s\n" "source-git-ensure-branch=PASS branch=$branch_name revision=$expected"
    ' bash "$source_tree" "$branch_name" "$revision"
fi

if test "$operation" = finish-source; then
    exec podman exec -i --user "$podman_uid:$podman_gid" "$container_name" env \
        DL_DIR=/workspace/state/downloads \
        SSTATE_DIR=/workspace/state/sstate-cache \
        TMPDIR="$container_tmp" \
        BUILDDIR="$active_bitbake_control" \
        DEVTOOL_TIMEOUT_SECONDS="$devtool_timeout" \
        DEVTOOL_FINISH_NO_CLEAN="$focused_profile" \
        PYTHONPATH="$bitbake_python_overlay" \
        FLUORITE_BITBAKE_CLIENT_RESPONSE_TIMEOUT="$bitbake_response_timeout" \
        /bin/bash -lc 'source "$BITBAKE_ENV_SCRIPT" "$BUILDDIR" >/dev/null; exec timeout --foreground --signal=TERM --kill-after=15s "$DEVTOOL_TIMEOUT_SECONDS" /bin/bash -s -- "$@"' \
        bash "$source_tree" "$destination" <<'CONTAINER_SCRIPT'
set -eu
source_tree=$1
destination=$2

status_output=$(devtool status)
# `devtool status` prints only `recipe: source` for a clean source, while
# some Yocto versions append fields after the path. Accept both shapes but
# never a path-prefix collision. Keep the two expressions separate because
# the host macOS sed does not provide the GNU `\|` extension.
recipe_matches=$(printf '%s\n' "$status_output" | sed -n \
    -e "s#^\\([^:][^:]*\\): ${source_tree}\$#\\1#p" \
    -e "s#^\\([^:][^:]*\\): ${source_tree} .*#\\1#p")
recipe_count=$(printf '%s\n' "$recipe_matches" | awk 'NF {count++} END {print count + 0}')
test "$recipe_count" -eq 1 || {
    echo "finish-source: FAIL expected one active recipe for $source_tree, found $recipe_count" >&2
    printf '%s\n' "$status_output" | sed -n '/^[^:][^:]*: \/workspace\//p' >&2
    exit 1
}
recipe=$recipe_matches
source_head=$(git -C "$source_tree" rev-parse --verify HEAD^{commit})
test -z "$(git -C "$source_tree" status --porcelain)" || {
    echo "finish-source: FAIL source tree is dirty" >&2
    exit 1
}
printf '%s\n' "finish-source=START recipe=$recipe source_head=$source_head destination=$destination"
devtool_rc=0
set +e
if test "${DEVTOOL_FINISH_NO_CLEAN:-0}" = 1; then
    (devtool finish --no-clean "$recipe" "$destination" --mode patch)
else
    (devtool finish "$recipe" "$destination" --mode patch)
fi
devtool_rc=$?
set -e
test "$devtool_rc" -eq 0 || {
    echo "finish-source: FAIL official finish returned rc=$devtool_rc" >&2
    exit "$devtool_rc"
}
generated_matches=$(find "$destination" -type f -name '*.patch' -print | while IFS= read -r patch_file; do
    if grep -q --fixed-strings "From $source_head " "$patch_file"; then
        printf '%s\n' "$patch_file"
    fi
done)
generated_count=$(printf '%s\n' "$generated_matches" | awk 'NF {count++} END {print count + 0}')
test "$generated_count" -le 1 || {
    echo "finish-source: FAIL official finish generated $generated_count patches for source HEAD $source_head" >&2
    exit 1
}
generated_label=${generated_matches:-none}
printf '%s\n' "finish-source=PASS recipe=$recipe source_head=$source_head destination=$destination devtool_rc=$devtool_rc generated_count=$generated_count generated=$generated_label"
CONTAINER_SCRIPT
fi

exec podman exec --user "$podman_uid:$podman_gid" "$container_name" env \
    DL_DIR=/workspace/state/downloads \
    SSTATE_DIR=/workspace/state/sstate-cache \
    TMPDIR="$container_tmp" \
    BUILDDIR="$active_bitbake_control" \
    DEVTOOL_TIMEOUT_SECONDS="$devtool_timeout" \
    PYTHONPATH="$bitbake_python_overlay" \
    FLUORITE_BITBAKE_CLIENT_RESPONSE_TIMEOUT="$bitbake_response_timeout" \
    /bin/bash -lc 'source "$BITBAKE_ENV_SCRIPT" "$BUILDDIR" >/dev/null; exec timeout --foreground --signal=TERM --kill-after=15s "$DEVTOOL_TIMEOUT_SECONDS" /workspace/project/tools/yocto-devtool/run-devtool.sh "$@"' \
    bash "$operation" "$@"
