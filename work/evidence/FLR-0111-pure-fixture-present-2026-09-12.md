# FLR-0111 evidence — pure fixture present comparison (2026-09-12)

## Outcome

The self-made pure native fixture is a positive control on the same fixed
debug image: it produces nonzero native 3D QMP pixels and repeatedly returns
from queue present with `result=0` followed by `PRESENT_DONE`. The production
run in FLR-0109 remains native-black and has no recorded queue-present return.
This separates the fixture's render/present path from the production failure,
but it is not a production fix.

## Facts

- The authoritative runtime was QEMU on the build host, using the existing
  receiver, build, and TMPDIR roles. The QEMU command record resolves the
  fixed kernel, rootfs, qemuboot profile, and `qmp.sock` under the existing
  FLR-0111 evidence directory.
- The fixture was launched as exactly one `/usr/bin/flutter-auto` with:
  `FLUORITE_NATIVE_PURE_FIXTURE=1`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLUORITE_SCENE_PASS_TRACE=1`,
  `FLUORITE_PRESENT_TRACE=1`, and
  `FLUORITE_DRIVER_LIFECYCLE_TRACE=1`.
- The first fixture run selected PID 636 and showed
  `/usr/lib/libvulkan_lvp.so` in its maps. Its launch record contains repeated
  `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0` and
  `FLUORITE_VK_PRESENT_DONE` pairs after
  `FLUORITE_VK_QUEUE_PRESENT_ENTER`/`FLR0026_VK_QUEUE_PRESENT_BEGIN`.
- QMP-only `fixture-late.ppm` is 1280x800, SHA-256
  `5d5a512876a0dca7a8a760a7001230990484bdbec701a654849a0e6ea1509045`.
  The native candidate changed `41,750/223,200` pixels with bounding box
  `[501,278,278,162]`; the HUD candidate changed `6,148/100,000` pixels with
  bounding box `[200,113,400,237]`.
- Six QMP frame captures were retained under the same evidence directory. Their
  SHA-256 values are:
  `frame-00000.ppm=6d74ce36b4a76e643b5fcd5c273f515d4caed078c8562203f40de6f7ef245034`,
  `frame-00001.ppm=073321f165c0c3b55ae18dc6eb48e1df314c0c6276779eafd3eb12de9ffb2d89`,
  `frame-00002.ppm=b28a18a3f085369ee8d3b2e73c2ac09263aa4abdcd9e45ccf33efd093a06f8d3`,
  `frame-00003.ppm=fc4680a26ff7f77cb190017f3e22410a0fb75fffd561f48ee64c3f174ecb0636`,
  `frame-00004.ppm=31176335d0691e1ee9cb0232334705692c9223b9935448a2711a8bfca3e7a9c4`,
  `frame-00005.ppm=7543c083c03383f0096e421673d7874ebd5bd3bd1ff6ecbb78941976f44aba94`.
  No display-window screenshot was used as evidence.
- QMP-only `fixture-after-gdb.ppm` is 1280x800, SHA-256
  `6505d03d54491182b20b28cff1881510f570845f7762c496605d5eaecbb768f3`.
  It still changed `41,750/223,200` native pixels and `6,149/100,000` HUD
  pixels, so the bounded debugger did not remove the fixture's visible output.
- The first GDB attempt was intentionally retained as a procedure failure:
  manually loading `libvulkan_lvp.so` exceeded the 20-second bound and
  returned `124`. It is not a product result.
- The corrected low-memory GDB attempt used `-nh -nx`,
  `sysroot=/`, `solib-absolute-prefix=/`,
  `solib-search-path=/usr/lib:/lib`, `debug-file-directory`, and
  `auto-solib-add off`. It returned `0`, kept PID 636 alive, and observed 40
  threads without OOM or target loss.
- In that bounded fixture snapshot, the FEngine threads were in either
  `poll` through `libwayland-client.so.0` or glibc futex/condition waits; the
  top four frames did not contain a `libvulkan_lvp.so` frame. Because symbols
  were deliberately not loaded and only four frames were requested, the
  absence of a deeper Mesa frame is not treated as proof that no Mesa wait
  exists.
- A second identical QEMU/fixture run was started with new serial/SSH/telnet
  ports in the same evidence directory. Start, guest-ready, one-process
  launch, `libvulkan_lvp.so` mapping, and repeated present returns passed for
  PID 640. Its deeper GDB/QMP completion and teardown remain pending.
- An initial attempt to contact the guest through the Mac loopback was
  rejected because QEMU's loopback ports belong to the build host. The
  corrected nested build-host-to-guest route succeeded. This is recorded as a
  procedure issue, not a product failure.
- The first fixture QEMU run ended with QMP capabilities/quit accepted and
  `residual_targets=0 residual_qmp=0`. The second run is not yet classified
  as cleanly terminated because the remote cleanup call was rejected by the
  execution approval service's usage limit.

## Inferences

- The production-only missing queue-present return is not explained by the
  generic presence of lavapipe, Wayland, Flutter worker threads, or the
  fixed QEMU profile: the same stack reaches visible native output and
  returns from present in the fixture.
- The FLR-0109 r12 observation of FEngine threads in symbolized
  `lvp_pipe_sync_wait_locked`/`lp_cs_tpool_worker` remains the highest-ranked
  production-side boundary. The fixture control weakens the hypothesis that
  this is an unavoidable normal lavapipe idle state.
- The strongest current distinction is input/path-specific: production scene
  state or production command/resource synchronization reaches a different
  present contract than the pure fixture. The exact violated semaphore,
  fence, command stream, or compositor contract is not yet proven.

## Hypotheses to test next

1. Production's shaded scene/resource path leaves a submission or semaphore
   state that the fixture does not create, so lavapipe waits for work that is
   never completed.
2. Production and fixture use different surface/composition ownership after
   the same native draw boundary; production's native pixels may be hidden or
   its present path may be entered from a different thread.
3. The known `FEngine::loop` OOPS is concurrent with, or corrupts, the
   production synchronization state. Causality remains UNKNOWN.

## UNKNOWN

- The exact production semaphore/fence/command that the Mesa wait observes.
- Whether the production OOPS is causal.
- The complete deep fixture stack for the second run and a synchronized
  fixture stack at a present marker.
- Whether the production native surface is rendered but later hidden by
  composition in the full scene. Existing production QMP evidence proves
  only that the native candidate is black while the HUD is visible.
- Whether a source patch can restore production output. No source patch is
  justified by this control result alone.

## Verification status

- Fixture QMP native pixels: **PASS**.
- Fixture queue-present return/done markers: **PASS**.
- Fixture low-memory GDB without OOM: **PASS**.
- Fixture comparison to production: **diagnostic PASS; production fix NOT
  PROVEN**.
- First-run QMP teardown: **PASS**.
- Second-run deep GDB and QMP teardown: **PENDING** because the remote
  execution approval limit prevented the final bounded collection/cleanup.
