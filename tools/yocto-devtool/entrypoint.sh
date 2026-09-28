#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "fluorite-devtool: $1" >&2
    exit 1
}

: "${AGL_ROOT:=/workspace/agl}"
: "${BUILD_DIR:=/workspace/build}"
: "${DL_DIR:=/yocto-cache/downloads}"
: "${SSTATE_DIR:=/yocto-cache/sstate-cache}"
: "${TMPDIR:=/yocto-cache/tmp}"
: "${DEVTOOL_UID:=1000}"
: "${DEVTOOL_GID:=1000}"
: "${BBSERVER:=}"
: "${AGL_SETUP_SCRIPT:=}"
: "${AGL_SETUP_MACHINE:=qemux86-64}"
: "${AGL_SETUP_FEATURES:=agl-demo agl-app-framework agl-flutter agl-kuksa-val agl-netboot agl-pipewire agl-selinux}"
: "${EXTRA_BBLAYERS:=}"
: "${HOME:=/tmp}"

for required_dir in "$AGL_ROOT" "$BUILD_DIR" "$DL_DIR" "$SSTATE_DIR" "$TMPDIR"; do
    test -d "$required_dir" || fail "required mount is missing: $required_dir"
done

export BBSERVER DL_DIR SSTATE_DIR TMPDIR HOME

if test "$(id -u)" -eq 0; then
    chown "$DEVTOOL_UID:$DEVTOOL_GID" "$BUILD_DIR" "$DL_DIR" "$SSTATE_DIR" "$TMPDIR"
fi

environment_sourced=0
if test -n "$AGL_SETUP_SCRIPT" && ! test -r "$BUILD_DIR/conf/local.conf"; then
    test -r "$AGL_SETUP_SCRIPT" || fail "AGL_SETUP_SCRIPT is not readable"
    set +u
    source "$AGL_SETUP_SCRIPT" --machine "$AGL_SETUP_MACHINE" \
        --build "$BUILD_DIR" $AGL_SETUP_FEATURES
    set -u
    environment_sourced=1
fi

if test "$environment_sourced" -eq 0 && test -n "${BITBAKE_ENV_SCRIPT:-}"; then
    test -r "$BITBAKE_ENV_SCRIPT" || fail "BITBAKE_ENV_SCRIPT is not readable"
    set +u
    source "$BITBAKE_ENV_SCRIPT" "$BUILD_DIR"
    set -u
fi

if test -r "$BUILD_DIR/conf/bblayers.conf" && test -n "$EXTRA_BBLAYERS"; then
    # A previous Docker wrapper appended the historical self-install checkout.
    # Keep the fixed external/meta-flutter layer created by aglsetup and
    # remove only those stale paths before reusing the bind-mounted state.
    sed -i '\|/workspace/agl/self-install/meta-flutter|d' \
        "$BUILD_DIR/conf/bblayers.conf"
    for layer in $EXTRA_BBLAYERS; do
        if ! grep -Fq "${layer}" "$BUILD_DIR/conf/bblayers.conf"; then
            printf '\nBBLAYERS += " %s "\n' "$layer" >>"$BUILD_DIR/conf/bblayers.conf"
        fi
    done
fi

if test -r "$BUILD_DIR/conf/local.conf" && ! grep -Eq '^DISTRO_FEATURES:append.*vulkan' "$BUILD_DIR/conf/local.conf"; then
    printf '\nDISTRO_FEATURES:append = " vulkan"\n' >>"$BUILD_DIR/conf/local.conf"
fi

if test -r "$BUILD_DIR/conf/local.conf"; then
    sed -i -E '/^[[:space:]]*(DL_DIR|SSTATE_DIR|TMPDIR)[[:space:]]*=/d' \
        "$BUILD_DIR/conf/local.conf"
    {
        printf '\n# Managed by fluorite-yocto-devtool. Keep Yocto state in one persistent bind-mounted directory.\n'
        printf 'DL_DIR = "%s"\n' "$DL_DIR"
        printf 'SSTATE_DIR = "%s"\n' "$SSTATE_DIR"
        printf 'TMPDIR = "%s"\n' "$TMPDIR"
    } >>"$BUILD_DIR/conf/local.conf"
fi

touch /tmp/fluorite-devtool-ready
if test "$#" -eq 0; then
    exec bash
fi
exec "$@"
