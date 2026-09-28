# FLR-0335 evidence — no-GDB production present/fault comparison

- Date: 2026-09-28
- Ticket: [FLR-0335](../tickets/FLR-0335-compare-present-without-gdb.md)
- Run ID: `flr0335-0001`
- Raw evidence: `$EVIDENCE_ROOT/flr0335-0001/qemu` (Mini PC only)
- Exact image source revision: UNKNOWN; no source/build changes were made.
- Rootfs SHA-256:
  `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Qemuboot SHA-256:
  `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- QEMU memory: 6144 MiB; same fixed Mini build/TMPDIR as FLR-0334; one QEMU.
- No Devtool, BitBake, patch, recipe, source, or image build ran.

## Comparison and runtime boundary

- The same Sequoia Example Demo diagnostic environment as FLR-0334 was
  launched directly without GDB. The bounded log reported guest uptime
  `284.16` seconds when collected. The prior GDB run lasted 11m07 without a
  fault; this single pair supports a debugger/timing hypothesis but does not
  prove GDB caused the difference.
- Bounded app-log counts:
  - `FLR0026_SCENE_STAGE_DRAW_END=19`
  - `FLR0026_VK_QUEUE_PRESENT_BEGIN=1`
  - `FLUORITE_VK_PRESENT_CALL_BEGIN=1`
  - `FLUORITE_VK_QUEUE_PRESENT_ENTER=1`
  - `FLUORITE_VK_QUEUE_PRESENT_RETURN=0`
  - `FLUORITE_VK_PRESENT_DONE=0`
  - `FLUORITE_NATIVE_WAYLAND_COMMIT=19`
- The selected app log ended at queue-present begin. The guest kernel journal
  then recorded a page fault about one second later:

  ```text
  BUG: unable to handle page fault for address: 00000000098f6750
  #PF: supervisor read access in user mode
  #PF: error_code(0x0000) - not-present page
  Oops: 0000 [#1] PREEMPT SMP NOPTI
  CPU: 2 PID: 683 Comm: FEngine::loop
  RIP: 0033:0x7fb02fe44541
  RSP: 002b:00007fb0098f6750
  CR2: 00000000098f6750
  ```

- The no-coredump result is `coredump_matches=0`. The parent `flutter-auto`
  survived; faulting TID 683 was absent from its thread set after the Oops.
- A bounded post-fault GDB attach to the surviving parent mapped the RIP to
  `/usr/lib/libLLVM.so.18.1`, symbol
  `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)+1`. GDB disassembly at
  the reported byte showed `iret`; the preceding kernel `Code` bytes were
  `ff <cf> 83 ...`. This is consistent with the historical one-byte-offset
  signature, but the post-fault attach did not capture the vanished worker's
  live stack or prove that `isOrdered` caused the fault.
- Historical comparison: FLR-0105 captured a normal `isOrdered` entry in an
  LLVM InstCombine stack and a later `isOrdered+1` Oops in another
  `FEngine::loop` thread. FLR-0107 observed both Gallivm `LLVMRunPasses` calls
  return normally before a later Oops. FLR-0308/0309 reproduced the fault
  with one model and with zero-intensity light. The producer and causality
  remain UNKNOWN.

## QMP visual evidence

- Baseline, 1280×800, HUD not yet launched:
  `qmp-0335-before-app.ppm`, SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Pre-fault full frame:
  `qmp-0335-run-full.ppm`, SHA-256
  `79e01b42663958f2b4abd6e60c538fb7a14e7bf4bf8f80d4bd0f0969e96d0bbe`.
- Post-fault full frame:
  `qmp-0335-post-fault-full.ppm`, same SHA-256 as the pre-fault frame.
- Both eight-frame QMP sequences contain one unique hash, equal to the
  corresponding full frame. The native vehicle ROI `(440,220,400,360)` was
  `0/144000` changed and zero chromatic pixels. The HUD ROI `(0,0,240,220)`
  changed `6423` pixels, of which `2265` were chromatic. The right/main region
  changes were confined to the Scenes button.
- The frame visibly contains the 2D telemetry HUD and Scenes button, but no
  vehicle or other 3D pixels. The screenshot is QMP framebuffer evidence, not
  a host display-window capture.
- The user's separate square image is the static embedded
  `HeadLights_Emission` texture from the GLB (derived-artifact SHA-256
  `87fa31842d2e6e97aeefdb29de38e8e070619607ef93fda071915d6856362546`). It
  contains red emissive texels; it is not this QMP frame and does not prove
  runtime sampling.
- Historical FLR-0070 p9 separately recorded HUD pixels `3961/100000` and
  candidate 3D changes `5510/223200`. FLR-0071's three follow-up conditions
  were all native-black, and p9's complete identity was not retained. Treat
  p9 as a historical, non-reproduced positive observation, not the current
  acceptance baseline.

## Teardown and file hashes

- The recorded guest app PID was stopped through serial-exec only after its
  `comm` matched `flutter-auto`; result: `flutter_processes=0` and
  `FLR0335_APP_STOP_PASS`.
- QMP teardown: `qmp=PASS capabilities=negotiated quit=accepted`;
  `cleanup=PASS residual_targets=0 residual_qmp=0`.
- Final exact process check: no QEMU, runqemu, or flutter-auto targets; QMP
  socket absent.
- `serial-0335-launch.output` SHA-256:
  `ce556c300cf8504a04c0c798eb03de8e778eb1cc65c00cca22574d8c12d7208a`.
- `serial-0335-log-slice-1.output` SHA-256:
  `a93caa460bccd9b482461734541580f5336520013848dc3bc6652950b8630f3a`.
- `serial-0335-log-slice-2.output` SHA-256:
  `5c09ff68117399bc3446a8908c3bb9a0fca5137fba66c5e1bb9cbcbfb503c1a7`.
- `serial-0335-fault-snapshot.output` SHA-256:
  `d9fe1f107d81499cb9816b23f9d3e5fdf77edd85f03365334ce4ac22d76a9353`.
- `serial-0335-postfault-rip-map.output` SHA-256:
  `c750c4207250202e31c2b1990eb179739187d4f82ce6fc96b0bc690df952e549`.
- `serial-0335-stop-app.output` SHA-256:
  `1a63a9c3bf640406d26609f2f7e5a5552bc412b723234cee1a6fd39e27859e35`.

## Verdict

The no-GDB run reproduced the known FEngine page-fault/present boundary earlier
than the prior GDB run. The signature matches older `isOrdered+1` observations,
but the module/symbol location is not a root-cause proof. HUD is visible;
production 3D remains absent from QMP. The static emissive texture exists and
its gltfio binding reaches ready/applied state, so a missing file or missing
binding is not currently the leading explanation. Actual shader sampling,
fragment output, and fault causality remain UNKNOWN. No source or image fix is
justified by this run alone.
