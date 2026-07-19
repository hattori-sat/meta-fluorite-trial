# FLR-0021 — Align active layer topology with fixed manifest

Status: Inbox

## Problem

The active Mini PC qemux86 build includes `meta-vulkan` correctly, but uses a different `meta-flutter` checkout than the fixed manifest and project provenance records.

## Facts

- `meta-vulkan` is cloned from `https://github.com/jwinarske/meta-vulkan.git` at locked revision `a1389ab...` and appears in `bitbake-layers show-layers` as `vulkan-layer` priority 12.
- The active `bblayers.conf` adds both `${METADIR}/meta-local` and `${METADIR}/meta-vulkan`.
- The fixed AGL manifest pins `external/meta-flutter` to `67d7a4d...`.
- The active qemux86 build instead uses `self-install/meta-flutter` at `b6e338a...`, with a dirty `conf/include/common.inc`.
- The active `self-install/meta-flutter` changes Flutter pub lockfile behavior and build logic relative to the fixed `external/meta-flutter` checkout.
- Effective metadata is otherwise coherent: `BB_VERSION=2.8.1`, `DISTRO=poky-agl`, `DISTRO_VERSION=20.0.4`, `MACHINE=qemux86-64`, and the expected `/mnt/yocto/flourite-qemux86-64` cache roots.

## Inference

The missing-layer hypothesis for `meta-vulkan` is refuted. The active layer topology is not a canonical fixed-manifest build, so the Flutter worker hang and prior image failures cannot yet be attributed to Fluorite source changes.

## Smallest next action

Compare a clean fixed-manifest build using `external/meta-flutter` against the current `self-install/meta-flutter` topology, without deleting caches. Record recipe/task signatures before any long image build.
