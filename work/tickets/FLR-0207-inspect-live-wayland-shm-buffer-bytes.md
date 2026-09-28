# FLR-0207 — inspect live Wayland SHM buffer bytes

- Status: Done
- Priority: High
- Owner: Runtime gdb/proc analysis + QEMU evidence roles
- Created: 2026-09-19
- Predecessor: [FLR-0206](FLR-0206-trace-vulkan-wayland-shm-buffer-content.md)
- Working log: `work/logs/2026-09-19-flr0207.md`

## Work unit

Read the live `memfd:mesa-shared` mappings from the running `flutter-auto`
process after Vulkan present. This distinguishes a zero/stale WSI buffer from
a non-zero buffer that disappears during compositor composition.

## Facts

- FLR-0206 observed five 4096000-byte `mesa-shared` pools and `MAP_SHARED`
  mappings, but syscall tracing cannot observe ordinary stores through mmap.
- QMP central and wide 3D regions remain uniformly black while driver readback
  is non-zero.
- The guest includes `gdb`, `strace`, and `coredumpctl`.

## Hypotheses

1. H1: the presented `memfd:mesa-shared` mapping contains non-zero pixels;
   compositor import or parent-frame composition is the missing boundary.
2. H2: the presented mapping is zero/stale while the driver readback uses a
   different target; the WSI copy/present path is the missing boundary.

## Success criteria

- [x] Use one existing-image QEMU run and one fixture process.
- [x] Capture `/proc/<pid>/maps` and gdb byte samples for shared Mesa mappings
  after present.
- [x] Pair the memory evidence with QMP central/wide ROI results.
- [x] Stop the app and QMP-quit with zero residual targets.

## Plan / Do / Check / Act

### Plan

1. Reuse the FLR-0204 rootfs without a source or layer change.
2. Launch the fixture, locate `memfd:mesa-shared`, and attach gdb briefly after
   the first present marker.
3. Read bounded samples from each 4096000-byte mapping and capture QMP.

### Do

- Reused the FLR-0204 rootfs and ran exactly one QEMU instance at
  `qemu-live-shm-20260919`.
- The fixture process had ten live `rw-s` `memfd:mesa-shared` mappings. Eight
  sampled mapping starts were all zero; the remaining two contained only
  `00 00 00 80` alpha bytes and no RGB bytes.
- Saved the bounded gdb evidence to the Mini evidence directory.

### Check

- gdb evidence: `/mnt/yocto/flourite-receivers/flr0023-835a04e/evidence/FLR-0207/qemu-live-shm-20260919/gdb-live.txt`, SHA-256
  `0d95e1cd134f011863adf12b1570961a3fa697beb744a9715a77a4b6a8e7dac8`.
- QMP frame: `live-shm-final.ppm`, SHA-256
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- QMP central ROI `[300,250,620,400]`: `0/248000` changed pixels.
  Wide ROI `[180,180,920,560]`: `0/515200` changed pixels.
- QMP reported three video frames; app stop and QMP quit both passed with
  `residual_targets=0` and `residual_qmp=0`.

### Act

The observed mapping bytes falsify H1 for the displayed SHM buffers. The
native Vulkan WSI/SHM transfer path remains the first missing boundary. A
separate visible SHM fallback will be tested only after the Devtool source
baseline is repaired.

## UNKNOWN

- Which shared mapping corresponds to the exact `wl_buffer` attached by the
  current Vulkan present remains UNKNOWN; all sampled presentable mappings
  nevertheless lacked RGB content.

## Follow-up

The fixed Mac Devtool source Git was found to have an invalid partial HEAD
(only three tree entries while the Mini effective source has 478). FLR-0208
owns repair of that baseline before the next source edit.
