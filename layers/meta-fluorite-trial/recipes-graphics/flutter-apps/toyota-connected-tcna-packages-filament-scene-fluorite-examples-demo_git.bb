SUMMARY = "Fluorite Filament scene examples demo"
DESCRIPTION = "Project-owned Fluorite demo recipe for AGL Flutter images."
LICENSE = "BSD-3-Clause"
LIC_FILES_CHKSUM = "file://LICENSE;md5=d73cf9ba84211d8b7fd0d2865b678fe4"

SRCREV = "2626d1757f18e438f4095e38e413eb40eab40b6d"
SRC_URI = " \
    git://github.com/toyota-connected/tcna-packages.git;branch=v2.0;protocol=https;lfs=0 \
    file://0001-filament_scene-reduce-startup-camera-contention-on-r.patch \
    file://0002-filament_scene-limit-startup-to-playground.patch \
    file://0003-filament_scene-minimize-startup-scene-for-pi.patch \
    file://config.toml \
"

S = "${WORKDIR}/git"
PUBSPEC_APPNAME = "fluorite_examples_demo"
FLUTTER_APPLICATION_INSTALL_SUFFIX = "toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo"
FLUTTER_APPLICATION_PATH = "packages/filament_scene/example"
PUBSPEC_IGNORE_LOCKFILE = "1"

inherit flutter-app

do_install:append() {
    install -m 0644 ${WORKDIR}/config.toml \
        ${D}${FLUTTER_INSTALL_DIR}/${FLUTTER_SDK_VERSION}/${FLUTTER_RUNTIME_MODE}/config.toml
}
