# flutter-auto_2.0.bbappend
# FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
# Fluorite validation uses the Vulkan backend; the EGL A/B was diagnostic only
# and did not change Filament's native renderer (it fell back to Vulkan).
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
# Keep Mac Devtool and Mini BitBake on the same resolved v2.0 source pair.
# The authoritative Mini build records these revisions in its effective
# recipe environment; pin them in this project layer so the patch context is
# deterministic even when the external meta-flutter checkout is older.
HOMESCREEN_COMMIT = "dd6d9224de807e24f0f9150e5a2e4ee1b896ac3c"
PLUGINS_COMMIT = "2163242e9973336153871ed63b34bb5ed8282145"

# The pinned plugin source contains sdbus-cpp as a Git submodule. Fetch the
# plugin component recursively so its CMakeLists.txt is present at configure
# time; preserve the repository, protocol, branch, source name, destination,
# and pinned revision.
SRC_URI:remove = "git://github.com/toyota-connected/ivi-homescreen-plugins.git;protocol=https;branch=v2.0;name=plugins;destsuffix=${S}/ivi-homescreen-plugins"
SRC_URI:append = " gitsm://github.com/toyota-connected/ivi-homescreen-plugins.git;protocol=https;branch=v2.0;name=plugins;destsuffix=${S}/ivi-homescreen-plugins"

# The upstream v2.0 source refactored Camera from
# core/scene/camera/camera.cc into core/components/derived/camera.cc. The
# historical patch only initialized a field on the removed Camera class and
# cannot apply to the resolved source. Remove that obsolete recipe item; keep
# the current source revision and all later patches unchanged.
SRC_URI:remove = "file://0002-fix-initialize-custom-camera-base-mode.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " \
    file://0002-wayland-vulkan-drop-vk-detail.patch \
    file://0220-reconcile-parent-alpha-and-AGL-normal-source-current-devtool.patch \
    file://0221-reconcile-visible-default-light-with-current-plugin-api-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0222-reconcile-nanosecond-frame-timing-with-current-plugin-source-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0223-reconcile-transparent-swapchain-with-current-plugin-api-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0004-fluorite-normal-defer-registration-until-configured.patch \
    file://0005-flutter-auto-restore-agl-shell-bind-for-bg-and-panels.patch \
    file://0006-fluorite-normal-default-activation-area-to-configured-size.patch \
    file://0007-wayland-apply-output-buffer-scale-to-surface.patch \
    file://0230-filament-view-refresh-loaded-noninstanced-asset-reuse-current-plugin-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0010-filament-view-register-default-light-before-component.patch \
    file://0013-filament-view-start-wayland-frame-callback.patch \
    file://0014-filament-view-show-default-render-layers.patch \
    file://0226-unify-post-renderable-shape-insertion-and-readiness-trace-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0025-filament-view-place-surface-above-parent.patch \
    file://0032-filament-texture-loader-skip-invalid-mipmap.patch \
    file://0028-filament-view-transparent-clear.patch \
    file://0038-filament-view-do-not-block-platform-registration-on-scene-load.patch \
    file://0039-filament-view-remove-obsolete-async-scene-load-promise.patch \
    file://0040-filament-view-do-not-block-platform-registration-on-ecs-init.patch \
    file://0224-reconcile-async-indirect-light-snapshot-with-current-plugin-api-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0174-filament-view-restore-queued-noninstanced-model-assets-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0181-diag-isolate-scene-default-indirect-light-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0182-diag-trace-hdr-indirect-light-stages-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0183-diag-limit-production-model-load-plan-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0184-diag-select-production-model-asset-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0227-defer-async-model-source-release-current-plugin-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0229-diag-isolate-explicit-light-contribution-current-plugin-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0203-diag-allow-XDG-fluorite-launch-without-AGL-bind-devtool.patch \
    file://0207-diag-optionally-attach-default-indirect-light-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0231-fix-wait-for-ecs-systems-before-channel-setup-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0232-register-filament-camera-api-before-fixture-init-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0233-diag-add-native-control-fields-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0234-diag-add-native-minimal-geometry-control-devtool.patch;patchdir=ivi-homescreen-plugins \
    file://0237-diag-add-opaque-ViewTarget-probe-devtool.patch;patchdir=ivi-homescreen-plugins \
"

do_configure:prepend() {
    f="${S}/ivi-homescreen-plugins/plugins/filament_view/CMakeLists.txt"
    if [ -f "$f" ]; then
        sed -i '/libvkshaders\.a/d' "$f"
    fi
}

# Keep the software-renderer quality reduction in QEMU validation only. The
# patch targets the current nested plugin source and is never used by target
# images.
SRC_URI:append:qemux86-64 = " file://0228-filament-view-use-lowest-qemu-quality-current-plugin-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append:qemuarm64 = " file://0228-filament-view-use-lowest-qemu-quality-current-plugin-devtool.patch;patchdir=ivi-homescreen-plugins"

# Generated against the effective source after the existing patch stack;
# register it after that stack so the diagnostic context remains valid.
SRC_URI:append = " file://0001-diag-trace-effective-ViewTarget-frame-boundary.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0242-diag-set-explicit-local-fixture-camera-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0243-diag-trace-effective-ViewTarget-scene-contract-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0244-diag-trace-native-fixture-renderable-contract-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0248-fix-native-fixture-color-on-active-material-instance-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0249-diag-hardcoded-native-material-color-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0250-diag-mark-native-material-branch-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0251-fix-restore-pure-fixture-camera-projection-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0252-fix-software-frame-promise-deadlock-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0253-fix-drain-initial-viewtarget-messages-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0254-diag-trace-viewtarget-c-api-bootstrap-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0255-diag-trace-viewtarget-system-handlers-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0256-diag-trace-viewtarget-registration-messages-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0257-fix-defer-viewtarget-messages-until-ecs-init-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0258-fix-pass-ecs-manager-pointer-to-deferred-route-helper-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0259-diag-readback-direct-fixture-swapchain-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0262-fix-filament-wayland-child-surface-position-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0263-diag-add-current-pure-native-fixture-control-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0264-diag-gate-native-swapchain-opacity-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0265-diag-gate-wayland-child-surface-commit-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0266-diag-gate-wayland-child-stacking-direction-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0267-diag-visible-shm-cube-fallback-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0268-fix-visible-shm-cube-position-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0270-diag-publish-native-readback-through-visible-shm-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0272-diag-allow-flutter-input-through-native-surface-devtool.patch;patchdir=ivi-homescreen-plugins"
SRC_URI:append = " file://0273-diag-gate-output-enter-pixel-ratio-metrics-devtool.patch"
SRC_URI += "file://0001-FLR-0231-gate-button-up-event-delivery.patch \
            file://0002-FLR-0233-gate-pointer-motion-event-delivery.patch \
            "

SRC_URI:append = " file://0274-flr0248-trace-native-readiness-method-call-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0275-flr0257-trace-platform-view-create-result-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0276-flr0258-trace-platform-view-handler-return-devtool.patch"

SRC_URI:append = " file://0277-flr0259-remove-synchronous-platform-view-drain-wait-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0278-diag-reintroduce-production-scene-stage-isolation-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0279-diag-trace-current-production-scene-stages-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0280-flr0266-diag-trace-readback-shm-ownership-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0281-flr0267-fix-readback-shm-buffer-release-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0282-flr0270-separate-readback-shm-pool-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0283-flr0272-guard-scene-setup-enqueue-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0284-flr0277-diag-skip-frame-event-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0285-flr0280-diag-model-content-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0286-flr0282-attach-primary-production-model-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0287-flr0285-bounded-production-camera-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0288-flr0285-apply-production-camera-before-draw-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0289-preserve-native-fixture-camera.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0290-reapply-native-fixture-camera.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0291-flr0285-probe-beginframe-failure-state-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0292-flr0285-probe-model-in-diagnostic-scene-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0293-flr0285-probe-direct-lights-in-diagnostic-scene-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0294-flr0285-probe-production-culling-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0295-flr0286-opt-in-lit-fixture-light-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0296-flr0289-opt-in-translucent-diagnostic-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0297-flr0302-trace-production-world-transform-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0298-flr0303-fix-transform-probe-api-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0299-flr0304-probe-production-camera-culling-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0305-flr0305-add-production-default-scene-light-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0306-flr0306-trace-production-material-output-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0307-flr0307-probe-production-emissive-output-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0309-flr0309-probe-zero-intensity-production-light-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0310-flr0310-probe-production-light-order-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0311-flr0311-trace-production-asset-boundary-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0315-flr0315-target-production-body-emissive-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0316-flr0316-probe-production-base-color-output-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0317-flr0317-trace-paintcolor-override-predicate-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0318-flr0318-skip-primary-scene-attach-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0323-flr0323-trace-paintcolor-predicate-operands-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0324-flr0324-fix-paintcolor-string-comparison-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0325-flr0325-trace-post-override-material-output-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0326-flr0326-add-opt-in-production-unlit-output-probe-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0327-flr0332-trace-nav-surface-frame-trigger-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0330-flr0371-lit-parameter-rgb-assignment-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0331-flr0383-sequoia-known-unlit-material-devtool.patch;patchdir=ivi-homescreen-plugins"

SRC_URI:append = " file://0332-flr0385-sequoia-known-lit-material-devtool.patch;patchdir=ivi-homescreen-plugins"
