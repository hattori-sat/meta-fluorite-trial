# ivi-homescreen_2.0.bbappend
# Keep backend selection aligned with flutter-auto.
PACKAGECONFIG:append = " backend-wayland-vulkan"
PACKAGECONFIG:remove = " backend-wayland-egl"

# Match Vulkan-Hpp API used in current toolchain (same fix as flutter-auto).
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI:append = " file://0002-wayland-vulkan-drop-vk-detail.patch"
