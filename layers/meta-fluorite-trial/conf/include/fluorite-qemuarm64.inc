require conf/include/fluorite-common.inc

# Default to the same Vulkan-first strategy used on the Raspberry Pi target.
# Set QEMU_USE_SWIFTSHADER = "1" in local.conf when guest-visible Vulkan is not
# sufficient for Fluorite validation.
QEMU_USE_SWIFTSHADER ?= "0"

IMAGE_INSTALL:append = "${@oe.utils.conditional('QEMU_USE_SWIFTSHADER', '1', ' swiftshader', '', d)}"
