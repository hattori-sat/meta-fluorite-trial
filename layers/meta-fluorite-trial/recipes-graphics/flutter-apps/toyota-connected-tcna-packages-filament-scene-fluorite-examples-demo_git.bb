SUMMARY = "Fluorite Filament scene examples demo"
DESCRIPTION = "Project-owned Fluorite demo recipe for AGL Flutter images."
LICENSE = "BSD-3-Clause"
LIC_FILES_CHKSUM = "file://LICENSE;md5=d73cf6ba84211d8b7fd0d2865b678fe8"

SRCREV = "2626d1757f18e438f4095e38e413eb40eab40b6d"
SRC_URI = "git://github.com/toyota-connected/tcna-packages.git;branch=v2.0;protocol=https;lfs=0 \
           file://0004-filament_scene-omit-native-unsupported-root-cameras.patch \
           file://0007-filament_scene-v2-scene-camera-adapter.patch \
           file://0008-filament_scene-v2-skip-camera-ecs-init.patch \
           file://0009-filament_scene-v2-normalize-shape-material-payload.patch \
           file://0011-filament_scene-normalize-frame-event-map.patch \
           file://0012-filament_scene-accept-native-frame-timing.patch \
           file://0013-filament_scene-camera-native-compat.patch \
           file://0014-filament_scene-throttle-planetarium-frame-commands.patch \
           file://0015-filament_scene-restore-root-camera-ecs-registration.patch \
           file://0016-filament_scene-minimal-3d-fixture-devtool.patch \
           file://0017-filament_scene-minimal-3d-fixture-camera-devtool.patch \
           file://0018-filament_scene-dolly-camera-offset-devtool.patch \
           file://0019-filament_scene-aim-fixture-camera-at-cube-devtool.patch \
           file://0020-filament_scene-minimal-3d-fixture-unlit-devtool.patch \
           file://0021-filament_scene-minimal-3d-fixture-emissive-lit-devtool.patch \
           file://0022-filament_scene-diagnostic-flutter-3d-mock-devtool.patch \
           file://0023-filament_scene-diagnostic-flutter-only-mock-devtool.patch \
           file://0024-filament_scene-diagnostic-flutter-mock-self-contained-devtool.patch \
           file://0027-filament_scene-diagnostic-native-only-final-devtool.patch \
           file://0028-filament_scene-minimal-3d-fixture-unlit-final-devtool.patch \
           file://0029-filament_scene-use-packaged-unlit-material-devtool.patch \
           file://0030-filament_scene-bind-texture-for-unlit-fixture-devtool.patch \
           file://0031-filament_scene-use-emissive-blue-native-fixture-devtool.patch \
           file://0032-filament_scene-rotate-emissive-blue-native-fixture-devtool.patch \
           file://0033-filament_scene-restore-production-scene-devtool.patch \
           file://0034-filament_scene-detach-cameras-until-activation-devtool.patch \
           file://0035-filament_scene-planetarium-camera-radians-devtool.patch \
           file://0036-diag-production-scene-known-good-indirect-light-devtool.patch \
           file://0037-filament_scene-install-frame-event-handler-after-readiness.patch \
           file://0038-diag-add-proven-cube-to-production-shape-path-devtool.patch \
           file://0039-diag-log-playground-scene-activation-devtool.patch \
           file://0040-diag-trace-camera-activation-request-devtool.patch \
           file://0042-fix-bind-dart-scene-cameras-to-native-view-devtool.patch \
           file://0043-fix-send-orbit-point-as-camera-target-devtool.patch \
           file://0044-test-isolate-proven-native-3d-fixture-devtool.patch \
           file://0045-test-use-active-playground-camera-for-fixture-devtool.patch \
           file://0046-test-match-known-good-fixture-camera-devtool.patch \
           file://0047-diag-reproduce-known-good-minimal-fixture-input-devtool.patch \
           file://0048-fix-activate-isolated-fixture-camera-devtool.patch \
           file://0049-diag-restore-first-frame-camera-selection-devtool.patch \
           file://0050-test-restore-known-good-native-fixture-scene-devtool.patch \
           file://0051-test-restore-production-scene-devtool.patch \
           file://0053-test-restore-self-made-3d-fixture-wiring-devtool.patch \
           file://0054-filament_scene-adapt-camera-to-native-v2-contract-devtool.patch \
           file://0056-filament_scene-align-dart-light-color-wire-format-devtool.patch \
           file://0057-filament_scene-compare-self-made-cube-unlit-material-devtool.patch \
           file://0058-filament_scene-compare-self-made-cube-culling-devtool.patch \
           file://0059-filament_scene-bind-dart-unlit-base-map-devtool.patch \
           file://0060-test-send-planetarium-shapes-through-native-creation-devtool.patch \
           file://0061-filament_scene-align-camera-world-eye-devtool.patch \
           file://0062-filament_scene-place-planetarium-light-world-devtool.patch \
           file://0063-filament_scene-use-unlit-planetarium-material-devtool.patch \
           file://0175-filament-scene-detach-cameras-until-activation-devtool.patch \
           file://0001-fix-restore-production-default-indirect-light-devtool.patch \
           file://0064-flr0226-transparent-material-parent-devtool.patch \
           file://0065-flr0227-isolate-menuanchor-hover-devtool.patch \
           file://0066-flr0234-scenes-hover-overlay-transparent-devtool.patch \
           file://0067-flr0235-static-scenes-surface-devtool.patch \
           file://0068-flr0236-activate-planetarium-scene-devtool.patch \
           file://0069-flr0237-isolate-planetarium-overlay-devtool.patch \
           file://0070-flr0238-isolate-marker-only-parent-setstate-devtool.patch \
           file://0071-flr0239-isolate-no-setState-tap-devtool.patch \
           file://0072-flr0240-mount-scene-subtree-devtool.patch \
           file://0073-flr0241-isolate-planetarium-lifecycle-callbacks-devtool.patch \
           file://0074-flr0242-isolate-generic-stateful-sceneview-mount-devtool.patch \
           file://0075-flr0243-isolate-plain-child-replacement-devtool.patch \
           file://0076-flr0244-isolate-builder-rebuild-from-child-identity-devtool.patch \
           file://0077-flr0245-isolate-builder-from-platform-view-composition-devtool.patch \
           file://0078-flr0246-mount-planetarium-directly-without-builder-devtool.patch \
           file://0079-flr0247-trace-planetarium-readiness-callback-devtool.patch \
           file://0080-flr0248-trace-readiness-method-channel-boundary-devtool.patch \
           file://0081-flr0249-start-readiness-after-platform-view-devtool.patch \
           file://0082-flr0251-revert-readiness-scheduling-ab-devtool.patch \
           file://0083-flr0252-restore-production-scene-payload-devtool.patch \
           file://0084-flr0253-restore-readiness-after-platform-view-devtool.patch \
           file://0085-flr0255-defer-readiness-poll-until-platform-view-devtool.patch \
           file://0086-flr0256-trace-platform-view-created-callback-devtool.patch \
           file://0087-flr0272-restore-native-root-camera-contract-devtool.patch \
           file://0088-flr0272-restore-proven-scene-camera-contract-devtool.patch \
           file://0089-flr0272-trace-dart-camera-payload-devtool.patch \
           file://0090-flr0272-restore-root-camera-activation-contract-devtool.patch \
           file://0091-flr0274-restore-initial-playground-camera-and-planetarium-route-devtool.patch \
           file://config.toml \
           file://pubspec.lock \
           "

S = "${WORKDIR}/git"
PUBSPEC_APPNAME = "fluorite_examples_demo"
FLUTTER_APPLICATION_INSTALL_SUFFIX = "toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo"
FLUTTER_APPLICATION_PATH = "packages/filament_scene/example"
PUBSPEC_IGNORE_LOCKFILE = "0"

inherit flutter-app

# meta-flutter archives the pub cache after do_patch and before do_configure.
# Install the project lock at that earlier boundary so the archive and the
# later offline compile enforce the same dependency graph.
python do_patch:append() {
    import os
    import shutil

    workdir = d.getVar("WORKDIR")
    app_root = os.path.join(d.getVar("S"), d.getVar("FLUTTER_APPLICATION_PATH"))
    shutil.copyfile(
        os.path.join(workdir, "pubspec.lock"),
        os.path.join(app_root, "pubspec.lock"),
    )

    # Force meta-flutter to recalculate its archive identity when an existing
    # WORKDIR marker was created before this recipe lock was installed. The
    # value names a path that is deliberately not created.
    archive_marker = os.path.join(workdir, "PUB_CACHE_ARCHIVE")
    refresh_path = os.path.join(workdir, ".fluorite-pub-cache-archive-refresh")
    with open(archive_marker, "w") as marker:
        marker.write(refresh_path)
}

do_install:append() {
    install -m 0644 ${WORKDIR}/config.toml \
        ${D}${FLUTTER_INSTALL_DIR}/${FLUTTER_SDK_VERSION}/${FLUTTER_RUNTIME_MODE}/config.toml
}
