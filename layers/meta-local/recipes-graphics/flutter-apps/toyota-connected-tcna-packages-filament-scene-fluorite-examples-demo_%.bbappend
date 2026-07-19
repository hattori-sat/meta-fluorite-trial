FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://config.toml \
"

# flutter-app class always runs `flutter pub get --enforce-lockfile --offline` in do_compile.
# Ensure pubspec.lock exists in source root even when upstream doesn't ship it.
FLUTTER_PREBUILD_CMD = "if [ ! -f pubspec.lock ]; then dart pub --suppress-analytics --directory . get --offline --example || dart pub --suppress-analytics --directory . get --offline; fi"

do_install:append() {
    install -m 0644 ${WORKDIR}/config.toml \
        ${D}${FLUTTER_INSTALL_DIR}/${FLUTTER_SDK_VERSION}/${FLUTTER_RUNTIME_MODE}/config.toml
}
