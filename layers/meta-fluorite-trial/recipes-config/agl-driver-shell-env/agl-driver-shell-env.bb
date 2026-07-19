SUMMARY = "Default shell environment for agl-driver"
DESCRIPTION = "Installs default shell environment for agl-driver via /etc/profile.d"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://agl-driver-env.sh"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${sysconfdir}/profile.d
    install -m 0644 ${WORKDIR}/agl-driver-env.sh ${D}${sysconfdir}/profile.d/agl-driver-env.sh
}

FILES:${PN} = "${sysconfdir}/profile.d/agl-driver-env.sh"
