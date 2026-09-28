#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/run-mac-devtool.sh <modify|finish|component-reset|component-add|update-recipe|status> [arguments]

The first invocation creates one persistent Compose container. Subsequent
invocations start and exec in that same container and reuse its named volumes.
This wrapper is patch-only and never builds an image recipe.
EOF
}

fail() {
    echo "mac-devtool: $1" >&2
    exit 1
}

operation=${1:-}
shift || true
case "$operation" in
    modify)
        test "$#" -eq 1 || { usage >&2; exit 2; }
        recipe=$1
        ;;
    finish)
        test "$#" -eq 2 || { usage >&2; exit 2; }
        recipe=$1
        destination=$2
        case "$destination" in
            /workspace/project|/workspace/project/*) ;;
            *) fail "finish destination must be inside /workspace/project" ;;
        esac
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
            /workspace/build/*|/workspace/project/*) ;;
            *) fail "component-add source must be inside /workspace/build or /workspace/project" ;;
        esac
        ;;
    update-recipe)
        test "$#" -ge 2 -a "$#" -le 4 || { usage >&2; exit 2; }
        recipe=$1
        append_layer=$2
        case "$append_layer" in
            /workspace/build/*|/workspace/project/*) ;;
            *) fail "update-recipe append layer must be inside /workspace/build or /workspace/project" ;;
        esac
        if test "$#" -ge 3; then
            test "$3" = --force-patch-refresh || fail "unsupported update-recipe option: $3"
        fi
        if test "$#" -eq 4; then
            case "$4" in
                ''|*[!0-9a-fA-F]*) fail "initial revision must be hexadecimal" ;;
            esac
        fi
        ;;
    status)
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

repository_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
project_root=${FLUORITE_MAC_PROJECT_ROOT:-$repository_root}
agl_root=${FLUORITE_MAC_AGL_ROOT:-${HOME:-}/work/agl-trout-mac}
compose_file=${FLUORITE_MAC_DOCKER_COMPOSE_FILE:-$repository_root/compose.mac-devtool.yaml}
compose_project=${FLUORITE_MAC_DOCKER_COMPOSE_PROJECT:-fluorite-mac-devtool}
container_name=${FLUORITE_MAC_DOCKER_CONTAINER:-fluorite-mac-devtool}
image=${FLUORITE_MAC_DEVTOOL_IMAGE:-fluorite-yocto-devtool:22.04}
docker_uid=${FLUORITE_MAC_DOCKER_UID:-$(id -u)}
docker_gid=${FLUORITE_MAC_DOCKER_GID:-$(id -g)}
build_volume=${FLUORITE_MAC_DOCKER_BUILD_VOLUME:-fluorite-mac-devtool-build}
dl_volume=${FLUORITE_MAC_DOCKER_DL_VOLUME:-fluorite-mac-devtool-downloads}
sstate_volume=${FLUORITE_MAC_DOCKER_SSTATE_VOLUME:-fluorite-mac-devtool-sstate-cache}
tmp_volume=${FLUORITE_MAC_DOCKER_TMP_VOLUME:-fluorite-mac-devtool-tmp}

case "$docker_uid:$docker_gid" in
    ''|*[!0-9:]*) fail "Docker UID/GID must be numeric" ;;
esac
for docker_name in "$compose_project" "$container_name" "$build_volume" "$dl_volume" "$sstate_volume" "$tmp_volume"; do
    case "$docker_name" in
        ''|*[!a-zA-Z0-9_.-]*) fail "unsupported Docker name: $docker_name" ;;
    esac
done

validate_path() {
    path_name=$1
    path_value=$2
    test "${path_value#/}" != "$path_value" || fail "$path_name must be absolute"
    case "$path_value" in
        /mnt/yocto/*|*/build-flourite*|*/flourite/tmp*|*/flourite/downloads*|*/flourite/sstate-cache*)
            fail "$path_name points at a mini-PC build path" ;;
    esac
}

validate_path project_root "$project_root"
validate_path agl_root "$agl_root"
test -d "$project_root" || fail "Mac project root is missing: $project_root"
test -r "$agl_root/external/poky/oe-init-build-env" || fail "Mac AGL source is missing: $agl_root"
test -r "$compose_file" || fail "Compose file is missing: $compose_file"
bash "$project_root/scripts/assert-canonical-repository.sh" >/dev/null || fail "Mac project root is not canonical"
docker image inspect "$image" >/dev/null 2>&1 || fail "Docker image is missing: $image"

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

export FLUORITE_MAC_PROJECT_ROOT="$project_root"
export FLUORITE_MAC_AGL_ROOT="$agl_root"
export FLUORITE_MAC_DOCKER_COMPOSE_FILE="$compose_file"
export FLUORITE_MAC_DOCKER_COMPOSE_PROJECT="$compose_project"
export FLUORITE_MAC_DOCKER_CONTAINER="$container_name"
export FLUORITE_MAC_DEVTOOL_IMAGE="$image"
export FLUORITE_MAC_DOCKER_UID="$docker_uid"
export FLUORITE_MAC_DOCKER_GID="$docker_gid"
export FLUORITE_MAC_DOCKER_BUILD_VOLUME="$build_volume"
export FLUORITE_MAC_DOCKER_DL_VOLUME="$dl_volume"
export FLUORITE_MAC_DOCKER_SSTATE_VOLUME="$sstate_volume"
export FLUORITE_MAC_DOCKER_TMP_VOLUME="$tmp_volume"

compose=(docker compose -f "$compose_file" -p "$compose_project")

if ! docker container inspect "$container_name" >/dev/null 2>&1; then
    "${compose[@]}" up -d --no-build devtool
else
    check_label() {
        label=$1
        expected=$2
        actual=$(docker inspect -f "{{index .Config.Labels \"$label\"}}" "$container_name" 2>/dev/null || true)
        test "$actual" = "$expected" || fail "existing container contract mismatch for $label"
    }
    check_label com.fluorite.mac-devtool.contract 1
    check_label com.fluorite.mac-devtool.project-root "$project_root"
    check_label com.fluorite.mac-devtool.agl-root "$agl_root"
    check_label com.fluorite.mac-devtool.image "$image"
    check_label com.fluorite.mac-devtool.uid "$docker_uid"
    check_label com.fluorite.mac-devtool.gid "$docker_gid"
    check_label com.fluorite.mac-devtool.build-volume "$build_volume"
    check_label com.fluorite.mac-devtool.dl-volume "$dl_volume"
    check_label com.fluorite.mac-devtool.sstate-volume "$sstate_volume"
    check_label com.fluorite.mac-devtool.tmp-volume "$tmp_volume"
    running=$(docker inspect -f '{{.State.Running}}' "$container_name")
    test "$running" = true || "${compose[@]}" start devtool
fi

for _ in {1..60}; do
    if docker exec "$container_name" test -f /tmp/fluorite-devtool-ready >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
docker exec "$container_name" test -f /tmp/fluorite-devtool-ready || fail "persistent Devtool container did not become ready"

exec "${compose[@]}" exec -T --user "$docker_uid:$docker_gid" devtool \
    /bin/bash -lc 'source "$BITBAKE_ENV_SCRIPT" "$BUILD_DIR" >/dev/null; exec /usr/local/bin/fluorite-run-devtool "$@"' \
    bash "$operation" "$@"
