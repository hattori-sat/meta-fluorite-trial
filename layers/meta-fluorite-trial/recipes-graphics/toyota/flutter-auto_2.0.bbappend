# flutter-auto_2.0.bbappend
# FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
# Fluorite validation uses the Vulkan backend so Filament and flutter-auto
# exercise the same path as the target application.
PACKAGECONFIG:append = " backend-wayland-vulkan"
PACKAGECONFIG:remove = " backend-wayland-egl"

# Filament view plugin は有効のままにする。
PACKAGECONFIG:append = " filament-view"


# FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# SRC_URI += " \
#   file://0001-drop-GEN_MIPMAPPABLE.patch \
# "

PACKAGECONFIG[filament-view] = "\
    -DBUILD_PLUGIN_FILAMENT_VIEW=ON \
    -DFILAMENT_INCLUDE_DIR=${STAGING_INCDIR}/filament \
    -DFILAMENT_LINK_LIBRARIES_DIR=${STAGING_LIBDIR}/filament, \
    -DBUILD_PLUGIN_FILAMENT_VIEW=OFF, filament-vk curl vulkan-loader"

# SRC_URI:append = " \
#    file://0001-filament-view-use-filament-imageio-include.patch \
#"
#


FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI:append = " \
    file://0002-wayland-vulkan-drop-vk-detail.patch \
    file://0003-agl-shell-register-normal-windows.patch \
    file://0004-fluorite-normal-defer-registration-until-configured.patch \
    file://0005-flutter-auto-restore-agl-shell-bind-for-bg-and-panels.patch \
    file://0006-fluorite-normal-default-activation-area-to-configured-size.patch \
    file://0007-wayland-apply-output-buffer-scale-to-surface.patch \
    file://0009-filament-view-fix-loaded-noninstanced-asset-reuse.patch \
"

do_configure:prepend() {
    f="${S}/ivi-homescreen-plugins/plugins/filament_view/CMakeLists.txt"
    if [ -f "$f" ]; then
        sed -i '/libvkshaders\.a/d' "$f"
    fi
}
