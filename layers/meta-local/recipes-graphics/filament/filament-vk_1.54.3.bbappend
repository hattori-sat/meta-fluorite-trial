# meta-local/recipes-graphics/filament/filament-vk_1.54.3.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# PV = "1.69.4"
# SRCREV  = "847d657ad5538053ee2e009cc855c5de53d5bb58"
PV = "1.65.4"
SRCREV = "2a86c0c60ecce9443fc34631570e924721b20b40"

#SRC_URI:remove = "git://github.com/google/filament.git;protocol=https;branch=release"
#SRC_URI:prepend = "git://github.com/google/filament.git;protocol=https;tag=v1.54.3 "
# SRCREV = ""


# meta-local/recipes-graphics/filament/filament-vk_1.54.3.bbappend


# meta-local/recipes-graphics/filament/filament-vk_1.54.3.bbappend
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
"

EXTRA_OECMAKE:append:class-target = " -DFILAMENT_ENABLE_LTO=OFF"



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
