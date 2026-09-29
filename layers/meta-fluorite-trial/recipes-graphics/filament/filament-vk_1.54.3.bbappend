# meta-fluorite-trial/recipes-graphics/filament/filament-vk_1.54.3.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# PV = "1.69.4"
# SRCREV  = "847d657ad5538053ee2e009cc855c5de53d5bb58"
PV = "1.65.4"
SRCREV = "2a86c0c60ecce9443fc34631570e924721b20b40"

#SRC_URI:remove = "git://github.com/google/filament.git;protocol=https;branch=release"
#SRC_URI:prepend = "git://github.com/google/filament.git;protocol=https;tag=v1.54.3 "
# SRCREV = ""


# meta-fluorite-trial/recipes-graphics/filament/filament-vk_1.54.3.bbappend


# meta-fluorite-trial/recipes-graphics/filament/filament-vk_1.54.3.bbappend
# TEMP: drop all patches from meta-vulkan filament-vk recipe

SRC_URI:remove = " \
  file://0001-error-ignoring-return-value-of-function-declared-wit.patch \
  file://0002-disable-backend-tests.patch \
  file://0003-install-required-files.patch \
  file://0004-move-include-contents-to-include-filament.patch \
  file://0005-move-libraries-so-they-install.patch \
  file://0006-return-shader-type-mobile-for-linux-vulkan.patch \
"

SRC_URI:append = " \
    file://0100-disable-backend-tests-1.69.4.patch \
    file://0101-enable-cross-imageio-deps-1.69.4.patch \
    file://0102-install-required-files-1.69.4.patch \
    file://0103-return-shader-type-mobile-for-linux-vulkan-1.69.4.patch \
    file://0104-filament-vulkan-present-diagnostics-devtool.patch \
    file://0105-filament-vulkan-readback-diagnostics-devtool.patch \
    file://0139-filament-vulkan-readback-completion-devtool.patch \
    file://0140-filament-vulkan-readback-dispatch-devtool.patch \
    file://0141-filament-readpixels-dispatch-devtool.patch \
    file://0142-filament-readpixels-logger-devtool.patch \
    file://0143-filament-readpixels-dispatcher-devtool.patch \
    file://0144-filament-vulkan-readback-buffer-devtool.patch \
    file://0145-filament-vulkan-readback-compile-fix-devtool.patch \
    file://0117-filament-vulkan-wayland-surface-identity-devtool.patch \
    file://0118-filament-vulkan-portable-handle-diagnostics-devtool.patch \
    file://0119-filament-vulkan-format-fix-devtool.patch \
   file://0123-filament-vulkan-present-substeps-devtool.patch \
    file://0125-diag-select-vulkan-present-mode-devtool.patch \
    file://0126-filament-vulkan-present-semaphore-wait-devtool.patch \
    file://0127-filament-vulkan-queue-idle-present-devtool.patch \
    file://0128-filament-vulkan-acquire-semaphore-wait-devtool.patch \
    file://0129-filament-vulkan-present-fence-diagnostics-devtool.patch \
    file://0130-filament-vulkan-present-fence-diagnostics-fix-devtool.patch \
    file://0131-filament-vulkan-queue-idle-fence-probe-devtool.patch \
    file://0132-filament-vulkan-present-layout-probe-devtool.patch \
    file://0133-filament-enable-target-bluegl-devtool.patch \
    file://0134-filament-skip-bluegl-tests-target-devtool.patch \
    file://0146-filament-vulkan-submit-fence-trace-devtool.patch \
    file://0147-filament-vulkan-swapchain-sync-init-devtool.patch \
    file://0148-filament-vulkan-readback-skip-devtool.patch \
    file://0149-filament-vulkan-sync-trace-devtool.patch \
    file://0150-filament-vulkan-sync-trace-format-devtool.patch \
    file://0151-filament-vulkan-swapchain-boundary-trace-devtool.patch \
    file://0152-filament-vulkan-driver-frame-handoff-trace-devtool.patch \
    file://0153-filament-frame-skip-status-devtool.patch \
    file://0154-filament-vulkan-frame-fence-linkage-trace-devtool.patch \
    file://0155-filament-driver-command-enqueue-trace-devtool.patch \
    file://0156-filament-command-stream-execution-trace-devtool.patch \
    file://0157-filament-command-enqueue-address-trace-devtool.patch \
    file://0158-filament-command-queue-boundary-trace-devtool.patch \
    file://0159-filament-command-stream-all-trace-devtool.patch \
    file://0160-filament-descriptor-texture-trace-devtool.patch \
    file://0161-filament-sampler-creation-trace-devtool.patch \
    file://0162-filament-mixed-filter-sampler-fallback-devtool.patch \
    file://0163-filament-vulkan-pipeline-creation-trace-devtool.patch \
    file://0164-filament-vulkan-unlinked-fence-ready-devtool.patch \
    file://0170-filament-vulkan-transparent-alpha-devtool.patch \
    file://0001-diag-trace-Vulkan-output-target-and-readback-source.patch \
    file://0171-filament-vulkan-target-trace-compile-fix-devtool.patch \
    file://0172-filament-vulkan-draw2-target-trace-devtool.patch \
    file://0173-filament-vulkan-target-content-probe-devtool.patch \
        file://0174-filament-vulkan-target-content-probe-compile-fix-devtool.patch \
        file://0175-filament-vulkan-target-probe-queue-sync-devtool.patch \
        file://0176-filament-vulkan-target-probe-nonblocking-devtool.patch \
        file://0180-filament-driver-lifecycle-trace-devtool.patch \
        file://0181-filament-command-queue-lifecycle-trace-devtool.patch \
        file://0182-diag-trace-Vulkan-present-call-boundary-devtool.patch \
        file://0183-diag-trace-Vulkan-queue-present-return-devtool.patch \
        file://0184-diag-trace-submit-present-semaphore-ownership-devtool.patch \
        file://0185-diag-add-neutral-Vulkan-fence-status-marker-devtool.patch \
        file://0186-diag-trace-effective-Vulkan-pipeline-inputs-devtool.patch \
        file://0187-diag-trace-render-pass-execute-seam-devtool.patch \
        file://0245-diag-trace-native-swapchain-pixels-devtool.patch \
        file://0246-fix-remove-unused-swapchain-probe-capture-devtool.patch \
        file://0247-diag-trace-native-Vulkan-pipeline-state-contract-devtool.patch \
        file://0248-diag-trace-native-vertex-buffer-boundary-devtool.patch \
"

EXTRA_OECMAKE:append:class-target = " -DFILAMENT_ENABLE_LTO=OFF"

# Build the alternate OpenGL/EGL backend for a runtime A/B. Vulkan remains the
# application default; FLR0026_FILAMENT_BACKEND=OPENGL selects the diagnostic
# path through the existing Devtool-generated 0091 backend override patch.
PACKAGECONFIG:append = " opengl"



do_install:append:class-target () {
    install -d ${D}${includedir}/filament

    # Make filament sub-headers visible under /usr/include/filament/*
    for d in backend camutils filamat filameshio geometry gltfio ibl image imageio ktxreader math mathio tsl utils viewer; do
        if [ -d ${D}${includedir}/$d ]; then
            cp -a ${D}${includedir}/$d ${D}${includedir}/filament/
        fi
    done

    # Ensure imageio headers are available in both expected include roots.
    install -d ${D}${includedir}/imageio
    install -d ${D}${includedir}/filament/imageio
    for h in ${S}/libs/imageio/include/imageio/*.h; do
        [ -f "$h" ] || continue
        install -m 0644 "$h" ${D}${includedir}/imageio/
        install -m 0644 "$h" ${D}${includedir}/filament/imageio/
    done

    # Force-stage static libs linked by flutter-auto.
install -d ${D}${libdir}/filament
    for n in libvkshaders.a libtinyexr.a; do
        p="$(find ${B} ${S} -name $n 2>/dev/null | head -n1 || true)"
        if [ -n "$p" ]; then
            install -m 0644 "$p" ${D}${libdir}/filament/
        fi
    done    


install -d ${D}${includedir}/filament/filament

for h in ${D}${includedir}/filament/*.h; do
        [ -f "$h" ] || continue
        install -m 0644 "$h" ${D}${includedir}/filament/filament/
    done
}

SRC_URI:append = " file://0260-diag-trace-vulkan-readback-payload-devtool.patch"
SRC_URI:append = " file://0261-diag-trace-vulkan-readback-roi-alpha-devtool.patch"

SRC_URI:append = " file://0270-diag-trace-current-swapchain-image-identity-devtool.patch"

SRC_URI:append = " file://0271-diag-use-vulkan-image-accessor-devtool.patch"
SRC_URI:append = " file://0272-diag-trace-gltfio-emissive-binding-devtool.patch"
