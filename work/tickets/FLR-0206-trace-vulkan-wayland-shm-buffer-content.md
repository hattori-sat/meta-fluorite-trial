# FLR-0206 — trace Vulkan to Wayland SHM buffer content

- Status: Done
- Priority: High
- Owner: Runtime syscall/debug analysis + QEMU evidence roles
- Created: 2026-09-19
- Predecessor: [FLR-0205](FLR-0205-observe-wayland-native-buffer-import-release.md)
- Working log: `work/logs/2026-09-19-flr0206.md`

## Work unit

Determine whether the native `wl_shm` buffer attached by Vulkan Wayland WSI
contains rendered pixels before the compositor receives it. This is a runtime
observation unit and does not change the source or image.

## Facts

- The client creates a 1280×800 `wl_shm` buffer from a 4 MiB pool and attaches
  it to the native child surface.
- The client sends `damage`, `frame`, and `commit`; Vulkan queue present returns
  0 and native driver readback is non-zero.
- QMP remains 2D-only and the compositor journal has no matching error.

## Hypotheses

1. H1: the WSI SHM pool is mapped and receives non-zero writes, but the
   compositor does not import/composite the buffer.
2. H2: the WSI presents an SHM buffer whose mapped contents are zero or stale;
   driver readback is from a different render target.

## Success criteria

- [x] Capture bounded `strace`/`/proc` evidence for SHM creation, mapping, and
  writes during one fixture run.
- [x] Pair the syscall evidence with QMP central/wide ROI results.
- [x] Preserve the evidence and cleanly QMP-quit with zero residual targets.

## Plan / Do / Check / Act

### Plan

1. Reuse the existing FLR-0204 image; do not rebuild.
2. Run one QEMU session and one fixture under a bounded syscall trace.
3. Inspect only `memfd_create`, `ftruncate`, `mmap`, `munmap`, and writes to
   the Wayland SHM pool, then compare QMP pixels.

### Do

One existing-image QEMU run launched the fixture under bounded `strace`. The
trace captured five `memfd_create("mesa-shared")` calls, five
`ftruncate(...,4096000)` calls, and `MAP_SHARED` mappings for 1280×800×4-byte
buffers. The trace was saved as a compressed artifact; no source or layer
change was made.

### Check

QMP final SHA is `b133eeb9...c05147`; central and wide 3D ROIs both remained
zero. The strace archive SHA is
`54c0d1d3da2c098d4cfdb9d2510f9830f983c7ace7876b9a92e3316c30541051`, and the
summary SHA is
`596be993ba7980a9ad0017c5b5705786f847d00a6d39eda76033052bbc94cd88`.
QMP teardown passed with zero residual targets and QMP.

### Act

Syscall evidence proves the SHM allocation and mapping but cannot prove the
contents. FLR-0207 owns direct gdb/proc byte inspection.

## UNKNOWN

- Whether the guest image includes `strace` and permits attaching to the
  `agl-driver` process.
- Whether a file-descriptor write is visible when the WSI uses `mmap`.
