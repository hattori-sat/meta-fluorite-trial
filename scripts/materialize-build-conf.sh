#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/materialize-build-conf.sh \
    --target raspberrypi4-64|qemux86-64 \
    --agl-root /absolute/agl/root \
    --project-root /absolute/meta-fluorite-trial \
    --output-dir /absolute/build/directory [--write --source-identity-verified]

Validates a sanitized baseline configuration. Without --write it is a dry run.
With --write it also requires an explicit assertion that the source manifest and
external-layer revisions were verified outside this script. It creates
conf/local.conf and conf/bblayers.conf only when neither destination file exists.
It never syncs source, starts BitBake, or deletes data.
EOF
}

target=
agl_root=
project_root=
output_dir=
write=0
source_identity_verified=0

while test "$#" -gt 0; do
    case "$1" in
        --target)
            test "$#" -ge 2 || { usage >&2; exit 2; }
            target=$2
            shift 2
            ;;
        --agl-root)
            test "$#" -ge 2 || { usage >&2; exit 2; }
            agl_root=$2
            shift 2
            ;;
        --output-dir)
            test "$#" -ge 2 || { usage >&2; exit 2; }
            output_dir=$2
            shift 2
            ;;
        --project-root)
            test "$#" -ge 2 || { usage >&2; exit 2; }
            project_root=$2
            shift 2
            ;;
        --write)
            write=1
            shift
            ;;
        --source-identity-verified)
            source_identity_verified=1
            shift
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
done

case "$target" in
    raspberrypi4-64|qemux86-64) ;;
    *) echo "build-conf: target MISSING or unsupported" >&2; exit 2 ;;
esac

case "$agl_root" in
    /*) ;;
    *) echo "build-conf: --agl-root must be an absolute path" >&2; exit 2 ;;
esac

case "$output_dir" in
    /*) ;;
    *) echo "build-conf: --output-dir must be an absolute path" >&2; exit 2 ;;
esac

if test -z "$project_root"; then
    project_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fi
case "$project_root" in
    /*) ;;
    *) echo "build-conf: --project-root must be an absolute path" >&2; exit 2 ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
template_dir="$repository_root/conf/$target"

for source_file in "$template_dir/local.conf.template" "$template_dir/bblayers.conf.template"; do
    if ! test -r "$source_file"; then
        echo "build-conf: baseline template MISSING" >&2
        exit 1
    fi
done

for required_path in \
    "$agl_root/meta-agl" \
    "$agl_root/external/poky" \
    "$project_root/layers/meta-fluorite-trial/conf/layer.conf" \
    "$agl_root/meta-vulkan/conf/layer.conf"; do
    if ! test -e "$required_path"; then
        echo "build-conf: required AGL source/layer MISSING" >&2
        exit 1
    fi
done

if test "$target" = raspberrypi4-64 && ! test -r "$output_dir/workspace/conf/layer.conf"; then
    echo "build-conf: captured Raspberry Pi BBLAYERS workspace is MISSING" >&2
    exit 1
fi

if test -e "$output_dir/conf" || test -L "$output_dir/conf"; then
    echo "build-conf: destination configuration already exists; refusing overwrite" >&2
    exit 1
fi

if test "$write" -eq 0; then
    echo "build-conf: PASS (dry-run structure check; source revision identity UNKNOWN)"
    echo "build-conf: verify fixed manifest/external revisions, then rerun with --write --source-identity-verified"
    exit 0
fi

if test "$source_identity_verified" -ne 1; then
    echo "build-conf: --write requires --source-identity-verified" >&2
    exit 1
fi

mkdir -p "$output_dir"
temporary_conf=$(mktemp -d "$output_dir/.fluorite-conf.XXXXXX")
cleanup_temporary_conf() {
    rm -f -- "$temporary_conf/local.conf" "$temporary_conf/bblayers.conf"
    rmdir -- "$temporary_conf" 2>/dev/null || true
}
trap cleanup_temporary_conf EXIT HUP INT TERM

AGL_ROOT_VALUE=$agl_root AGL_BUILD_DIR_VALUE=$output_dir PROJECT_ROOT_VALUE=$project_root perl -pe \
    's/\@AGL_ROOT\@/$ENV{AGL_ROOT_VALUE}/g; s/\@AGL_BUILD_DIR\@/$ENV{AGL_BUILD_DIR_VALUE}/g; s/\@PROJECT_ROOT\@/$ENV{PROJECT_ROOT_VALUE}/g' \
    "$template_dir/local.conf.template" >"$temporary_conf/local.conf"

AGL_ROOT_VALUE=$agl_root AGL_BUILD_DIR_VALUE=$output_dir PROJECT_ROOT_VALUE=$project_root perl -pe \
    's/\@AGL_ROOT\@/$ENV{AGL_ROOT_VALUE}/g; s/\@AGL_BUILD_DIR\@/$ENV{AGL_BUILD_DIR_VALUE}/g; s/\@PROJECT_ROOT\@/$ENV{PROJECT_ROOT_VALUE}/g' \
    "$template_dir/bblayers.conf.template" >"$temporary_conf/bblayers.conf"

mv -- "$temporary_conf" "$output_dir/conf"
trap - EXIT HUP INT TERM

echo "build-conf: PASS (created local.conf and bblayers.conf; no build started)"
