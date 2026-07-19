FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-grpc-proxy-start-server-after-shell-registration.patch \
    file://0002-grpc-proxy-send-ready-after-binding.patch \
    file://0003-desktop-defer-pending-resolution-until-background-exists.patch \
    file://0004-layout-fallback-to-default-output-before-background.patch \
    file://0005-shell-defer-pending-surfaces-until-background-exists.patch \
    file://0006-shell-allow-black-curtain-as-background-fallback.patch \
    file://0007-layout-promote-hidden-desktop-surface-on-activation.patch \
    file://0008-desktop-allow-black-curtain-for-pending-resolution.patch \
"
