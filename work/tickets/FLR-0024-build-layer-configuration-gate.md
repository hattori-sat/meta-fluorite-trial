# FLR-0024 — authoritative Yocto build-layer configuration gate

- Status: Next
- Priority: High
- Owner: build-host role + Yocto integration role
- Depends on: FLR-0019, FLR-0022
- External publication: none

## Problem

The existing mini-PC build directory is not currently proven to be an AGL
Fluorite build environment. Its inspected `bblayers.conf` lists only base Poky
layers, while the FLR-0019 candidate requires AGL, project, and external Vulkan
layers. A successful parse or build from the wrong layer graph would be a false
positive for synchronization.

## Goal

Create a separate, recipe-scoped validation build directory using the pinned AGL
setup flow and the imported candidate worktree. Preserve the existing dirty
checkout and existing `downloads`, `sstate-cache`, and `tmp` roles.

## Success criteria

- [x] Existing build directory remains unchanged and its dirty checkout is
  preserved.
- [x] Pinned AGL `aglsetup.sh` creates a separate build directory.
- [x] `bitbake-layers show-layers` includes the expected AGL, project, and
  external Vulkan layers at recorded revisions.
- [x] `bitbake -e` proves the target recipe, `SRC_URI`, `FILESPATH`, and patch
  order from the candidate worktree.
- [x] Only recipe-scoped `parse`, `patch`, `compile`, `install`, `package`, or
  `populate_sysroot` tasks are run on Mac/Docker.
- [x] No full image build, `cleanall`, `cleansstate`, cache deletion, reset, or
  checkout of the dirty canonical branch occurs.

## Facts

- FLR-0019's clean candidate is available as an imported mini-PC feature ref
  and a clean detached worktree.
- The existing build directory's visible `bblayers.conf` contains only base
  Poky layers.
- A first `bitbake -e` attempt against that existing directory waited in
  BitBake config update without producing effective recipe output and was
  stopped by exact-PID termination of the process started for the check.
- A separate r2 AGL build resolved the AGL, project, and Vulkan layers; the
  demo recipe parsed with zero errors, and `bitbake -e` resolved the active
  Devtool-generated fixture patch and project `FILESPATH`.
- The demo recipe `do_patch` completed with 104 tasks attempted and all
  succeeded. The post-task source contained the fixture functions and cube
  identifier.
- The generated candidate configuration still did not include `vulkan` in
  effective `DISTRO_FEATURES`; a temporary `bitbake -R` append resolved it,
  but no persistent configuration change was made.

## Hypotheses

1. The existing build directory is a stale or observer-only Poky configuration;
   the target recipes are absent because the AGL/project layers are not in its
   layer graph.
2. The correct AGL setup exists elsewhere on the host, but the build directory
   was initialized with the wrong environment script or wrong source root.
3. Even after the layer gate passes, the runtime 3D failure remains a separate
   Flutter/Filament/Wayland boundary and must not be conflated with this gate.

## Verification sequence

1. Record the pinned AGL manifest and source revision without `repo sync`.
2. Run the official setup script into a new build directory with explicit
   source, build, download, sstate, and tmp roles.
3. Inspect layer names/revisions and the effective target recipe variables.
4. Run only the candidate recipe's parse/patch task, then stop before any image
   task. Record logs and hashes in a new evidence file.
5. Hand the verified layer graph and revision manifest to the build stage.

## UNKNOWN

- The exact AGL setup arguments and layer revisions used to create the existing
  `/mnt/yocto/flourite` directory.
- Whether the existing downloads and sstate cache are compatible with the
  clean candidate worktree.
- Whether the correct setup can complete without refreshing moving upstream
  refs; no `repo sync` is authorized by this ticket.
- The recipe `do_compile` task remains UNKNOWN; only parse, metadata
  evaluation, and `do_patch` are proven for the Devtool-generated fixture.
- The persistent configuration ownership for enabling the project common
  include and Vulkan feature in the production build remains UNKNOWN.
