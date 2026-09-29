SUMMARY = "Fluorite runtime debugging tools"
DESCRIPTION = "Reproducible runtime diagnostics for the Fluorite validation image."
LICENSE = "MIT"

inherit packagegroup

# Keep the diagnostic image self-contained instead of relying only on an
# AGL image feature that may change when the surrounding image profile moves.
# The -dbg packages are limited to the graphics/runtime stack under test; the
# image does not enable debug symbols for every package in the distribution.
RDEPENDS:${PN} = " \
    gdb \
    gdbserver \
    strace \
    perf \
    elfutils \
    binutils \
    systemd \
    clang \
    clang-dbg \
    mesa-dbg \
    flutter-auto-dbg \
    flutter-engine-dbg \
    filament-vk-dbg \
"
