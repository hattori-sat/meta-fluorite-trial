# FLR-0110 evidence — low-memory production GDB observation (2026-09-12)

## Outcome

The guest debugger procedure is now bounded enough to observe the production
process without an OOM kill. Automatic shared-library loading and broad
remote symbol transfer caused the first low-memory attempt to time out; adding
the guest `sysroot=/`, disabling `auto-solib-add`, and removing the shared
library inventory from the command produced a usable bounded result.

This ticket validates the debugger harness only. It does not fix or classify
the production present/WSI owner.

## Fixed control

- Receiver role: `$RECEIVER`
- Build role: `$BUILD_DIR`
- TMPDIR role: `$BUILD_TMPDIR`
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- One QEMU was used and all runtime evidence is under
  `$RECEIVER/evidence/flr0110-r1/`.

## Runtime gates

- QEMU start: PASS.
- Guest SSH ready: PASS.
- Normal production launch: PASS; exactly one `flutter-auto` PID 628 was
  selected and its maps contained `libvulkan_lvp.so` and `libflutter_engine.so`.
- Pre-attach QMP capture: PASS, 1280x800, native candidate `0/223200`, HUD
  `1294/100000`; PPM SHA-256
  `2c679a5e4320c2654d3f10e42ae0bddf11e97ce5f463709e71829060768c6e45`.
- GDB r1: procedure partial. It kept the target alive and produced no OOM,
  but omitted `sysroot`, so GDB transferred many libraries from the target and
  timed out with client RC `124` before usable thread output.
- GDB r2: PASS. `sysroot=/`, `solib-absolute-prefix=/`,
  `solib-search-path=/usr/lib:/lib`, and `auto-solib-add off` yielded client
  RC `0`; target RSS was `1124892` kB before and `1124892` kB after, and no
  OOM marker was present.
- GDB r2 selected candidate thread IDs 25, 30, 26, 23, and 1. Threads 25 and
  30 (`FEngine::loop`), 26 (`llvmpipe-0`), and 23 (`JobSystem::loop`) all
  exposed usable PCs in `__futex_abstimed_wait_common64`; thread 1 was in
  `__GI___clock_nanosleep`. This is a stopped-time state snapshot, not proof
  that any one thread owns the missing queue-present return.
- Post-detach QMP capture: PASS, native candidate `0/223200`, HUD
  `1199/100000`; PPM SHA-256
  `65be5580550c1f5839c36ea8fe04edb91d87d5b0af6428fa0e4336bd2c03ed68`.
- QMP quit: PASS; residual targets and QMP sockets: `0/0`.

## Failed observations retained

- The first QEMU start command used a malformed rootfs SHA argument and was
  rejected by preflight before QEMU start. The corrected invocation passed;
  no second QEMU was started.
- The first low-memory GDB command still used remote library transfer and
  timed out. This is retained as a debugger procedure failure, not as a
  product result.

## Conclusion

FLR-0110 is complete as a debugger-resource unit. The reproducible procedure
is: verify the normal Vulkan-bearing PID, capture QMP, attach gdbserver, use a
foreground GDB client with `sysroot=/` and `auto-solib-add off`, request only
selected candidate threads, detach, capture QMP again, and issue QMP quit.
FLR-0109 resumes the present/WSI owner investigation with this procedure.
