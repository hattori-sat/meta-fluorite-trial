# Shared image additions used by Fluorite validation builds.

IMAGE_INSTALL:append = " \
    packagegroup-fluorite-demo \
    ivi-homescreen \
    agl-shell-activator \
    window-management-client-grpc \
    vulkan-loader \
    mesa-vulkan-drivers \
    vulkan-tools \
"

DISTRO_FEATURES:append = " vulkan"

# Keep debug/coredump tooling aligned with the current Raspberry Pi bring-up.
require conf/include/agl-devel.inc
