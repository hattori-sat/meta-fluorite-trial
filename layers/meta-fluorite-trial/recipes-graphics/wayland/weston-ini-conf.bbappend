FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
FILESEXTRAPATHS:prepend:qemux86-64 := "${THISDIR}/files/qemux86-64:"

SRC_URI:append = " file://grpc-proxy.cfg"
