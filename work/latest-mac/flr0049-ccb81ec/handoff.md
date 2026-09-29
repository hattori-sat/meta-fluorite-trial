# FLR-0049 latest Mac handoff

## Current state

- Feature branch commit: `be1a271` (`diag: probe ARGB Wayland composition`).
- Latest Mini PC rootfs: `mini-rootfs-20260908090413/agl-ivi-image-flutter-qemux86-64.rootfs-20260908090413.ext4`.
- Rootfs SHA-256: `46cbaea463998ee486b73e93542833ef8dde22415be170ece6a55610de61d12b`.
- QMP is the only screen evidence source. Captured resolution is 1280x800.
- Combined Flutter HUD plus production 3D is not yet proven. The latest valid
  native Sequoia 3D-only evidence is the alpha-clear video below.
- The 0200 ARGB probe shows that an ARGB SHM child reveals the Flutter parent
  around an opaque red rectangle. Native Vulkan alpha remains UNKNOWN because
  the same run entered `started=false` before stable Sequoia scene insertion.

## Videos

- Native Sequoia 3D-only result:
  `alpha-clear-20260908/qmp-flr0049-alpha-clear.mp4`
- Explicit launch, immediate present mode, 2D HUD:
  `mac-qemu-present-immediate-20260908/qmp-flr0049-present-immediate-explicit-launch.mp4`
- Explicit launch, FIFO, 2D HUD and later known llvmpipe/LLVM Oops:
  `fifo-explicit-20260908/qmp-flr0049-fifo-explicit.mp4`
- Sequoia-controlled launch before model-scene insertion:
  `sequoia-controlled-20260908/qmp-flr0049-sequoia-controlled.mp4`
- First-failure sync boundary:
  `sync-boundary-r3-20260908/qmp-flr0049-sync-boundary-r3.mp4`
- Unlinked-fence causal probe (diagnostic flag only):
  `unlinked-fence-probe-20260908/qmp-flr0049-unlinked-fence-probe.mp4`
- Command enqueue/execute trace:
  `fence-command-trace-20260908/qmp-flr0049-fence-command-trace.mp4`
- Normal frame-callback path without alpha-clear loop:
  `clean-frame-loop-20260908/qmp-flr0049-clean-frame-loop.mp4`
- Synchronous flush diagnostic (not a production fix):
  `native-sync-present-20260908/qmp-flr0049-native-sync-present.mp4`
- ARGB child over Flutter parent:
  `argb-composition-20260908/qmp-flr0049-argb-composition.mp4`
- ARGB child over native surface A/B:
  `argb-above-native-20260908/qmp-flr0049-argb-above-native.mp4`

## Reproduction contract

1. Reuse the persistent Mac Devtool container and the fixed Mini PC build/TMPDIR.
2. Edit only the persistent Devtool source through the Mac-side copy workflow;
   generate the registered Yocto patch with official `devtool finish`.
3. Commit the layer change in the `meta-fluorite-trial` repository, create a
   Git bundle, and send that bundle to the fixed build receiver.
4. Run the authoritative BitBake image build on the Mini PC; do not create a
   second TMPDIR or clean `downloads`, `sstate-cache`, or the fixed TMPDIR.
5. Boot one QEMU at a time with snapshot rootfs and QMP socket. Booting
   `applaunchd`/compositor is not enough: explicitly launch the installed
   Fluorite bundle as `agl-driver` with `XDG_RUNTIME_DIR=/run/user/1001` and
   `WAYLAND_DISPLAY=wayland-0`.
6. Capture every case through QMP, encode the frame sequence to MP4 on the Mac,
   copy the final PPM/PNG and runtime markers beside the video, then end QEMU
   with QMP `quit` and record the no-residual-process check.

## Next action

Keep FLR-0049 In Progress. The first native rendering boundary is now
`createFenceR` enqueue without bounded-run execution/linkage, followed by
FrameSkipper skipping every frame. Inspect the plugin/Filament thread and
flush ownership before selecting a production patch. The normal frame-callback
path reproduces the same boundary, while `NATIVE_SYNC_PRESENT` blocks before
its completion marker. The above/below A/B still shows that native and Flutter
pixels are mutually hidden, so HUD-only or native-only frames are not
combined-render success.

The 0200 ARGB control now shows parent transparency is working for SHM child
content. Native Vulkan alpha is still UNKNOWN because this run stopped at
`started=false` before stable Sequoia insertion. Resolve the frame/fence stop
boundary, then repeat the native/Flutter composition test.
