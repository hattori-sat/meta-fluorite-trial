require conf/include/fluorite-common.inc

# qemux86-64 is the preferred QEMU validation target because the AGL Mesa
# configuration already enables the software Vulkan path there. SwiftShader
# remains available as an opt-in fallback.
QEMU_USE_SWIFTSHADER ?= "0"

IMAGE_INSTALL:append = "${@oe.utils.conditional('QEMU_USE_SWIFTSHADER', '1', ' swiftshader', '', d)}"
