# FLR-0334 — GDB under-run evidence

- Date: 2026-09-28
- Ticket: [FLR-0334](../tickets/FLR-0334-symbolize-production-fengine-render-fault.md)
- Raw evidence directory: `$EVIDENCE_ROOT/flr0334-0001/qemu` (Mini PC only)
- Repository HEAD at the beginning of this unit: `72674c7`; exact layer
  revision used to build the retained image is UNKNOWN.
- Rootfs SHA-256:
  `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- QEMU boot-config SHA-256:
  `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- QEMU memory: 6144 MiB. Same fixed Mini build/TMPDIR and one QEMU; no build
  or source changes.
- Launch-to-interrupt elapsed time: 11m07. The previous fault was reported at
  guest monotonic 598.075730 seconds; this run exceeded that point.

## QMP visual evidence

- Baseline full frame: `qmp-0334-before-app.ppm`, SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Full production diagnostic frame, 1280×800:
  `qmp-0334-gdb-run-full.ppm`, SHA-256
  `7e632afa9091b9f23552e9ac14538141ec275c39eb7871195007da43e5df73ac`.
- Visual result: HUD and Scenes control visible; vehicle region black.
- Video sequence: `qmp-0334-gdb-video/frame-00000.ppm` through
  `frame-00007.ppm`; eight files, one unique hash, equal to the full-frame
  hash above.

## Runtime / debugger evidence

- Sequoia GLB load completed. Emissive texture index 6 was initially queued
  while not ready; the later marker reported ready and applied binding.
- The diagnostic unlit magenta PaintColor override was applied, but the QMP
  vehicle ROI remained black.
- Last bounded runtime marker was
  `FLR0026_VK_QUEUE_PRESENT_BEGIN`; no matching present-return/result marker
  was recorded.
- No SIGSEGV or user-mode page-fault marker occurred during the 11m07 GDB run.
- The intentional SIGINT stopped the inferior. The captured snapshot showed
  main thread `nanosleep`, Wayland `wl_display_poll`, and FEngine/llvmpipe
  Mesa `cnd_wait` frames. These are idle/wait stacks, not a fault backtrace.
- Guest GDB output hash before shutdown:
  `47851c20df55d5cb3630a064888ca979fc278f3ddebd82c9b6d9bf037896acfb`.
- Bounded extracts in the Mini evidence directory:
  - `serial-0334-gdb-interrupt.output` —
    `823fe460f90b792e315d84ef8698f356d94d7ff5a1bc9d70f8c0ebfa75795727`
  - `serial-0334-gdb-output-slice-6.output` —
    `67b223a943678d26df5ffa0cab775216a32c805a9078ec034c2275948a163c3f`
- The full guest `/run` log was not persisted before QEMU shutdown; only the
  bounded GDB extracts remain. No faulting RIP/module can be named.

## Image interpretation

The user's 1024×1024 `HeadLights_Emission` image is the static emissive
texture asset from the Sequoia GLB, not a runtime QMP frame. It demonstrates
that the asset contains red emissive texels, not that Filament sampled them
or displayed the Sequoia. Runtime markers prove texture readiness/binding only;
shader sampling and visible pixels remain UNKNOWN.

## Cleanup

- `qemu-runtime-harness.sh qmp-quit`:
  `qmp=PASS capabilities=negotiated quit=accepted`;
  `cleanup=PASS residual_targets=0 residual_qmp=0`.
- QMP socket absent after teardown. No QEMU/app remains from this unit.
