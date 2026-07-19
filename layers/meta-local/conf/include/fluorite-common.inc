# Shared image additions used by Fluorite validation builds.

IMAGE_INSTALL:append = " \
    packagegroup-toyota-connected-tcna-packages \
    ivi-homescreen \
    agl-shell-activator \
    window-management-client-grpc \
    vulkan-loader \
    mesa-vulkan-drivers \
    vulkan-tools \
    vkcube \
"

DISTRO_FEATURES:append = " vulkan"

# Keep debug/coredump tooling aligned with the current Raspberry Pi bring-up.
require conf/include/agl-devel.inc
