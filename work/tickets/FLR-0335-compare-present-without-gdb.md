# FLR-0335 — compare production present behavior with and without GDB

- Status: Done
- Priority: High
- Owner: production Example Demo / FEngine / runtime-evidence roles
- Created: 2026-09-28
- Predecessor: [FLR-0334](FLR-0334-symbolize-production-fengine-render-fault.md)
- Working log: `work/logs/2026-09-28-flr0335.md`
- Evidence: [no-GDB present/fault comparison](../evidence/FLR-0335-no-gdb-present-fault-2026-09-28.md)

## Objective

Test whether GDB changes the production render/present behavior. Replay the
same fixed image and same Sequoia diagnostic profile without GDB, long enough
to exceed the predecessor's 598-second fault point. Decide whether the prior
FEngine fault is repeatable or debugger/timing-sensitive. Do not change any
source, Light, camera, texture, material, or scene behavior.

## Success criteria

- Reuse the exact FLR-0334 rootfs, qemuboot, kernel, Mini build, and TMPDIR;
  no Devtool, BitBake, patch, or image build.
- Start only one QEMU through the established Mini harness and use a unique
  evidence directory for this ticket; never create a second TMPDIR.
- Launch the exact FLR-0334 environment/profile directly, without GDB. Keep
  every other launch variable unchanged.
- Observe for 720 seconds, or stop early when the same page-fault boundary is
  captured with enough evidence to compare against FLR-0334. Do not keep a
  faulted run alive merely to satisfy the timer.
- Compare process survival, `FLR0026_VK_QUEUE_PRESENT_BEGIN`/return markers,
  QMP vehicle/HUD pixels, and any page fault against FLR-0334.
- Stop only the recorded app PID after confirming `/proc/<pid>/comm`, then
  QMP-quit the single VM and verify zero residual targets/socket.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0333 reported a user-mode FEngine page fault at guest monotonic
  598.075730 seconds and no queue-present return marker.
- FLR-0334 ran the same diagnostic profile under GDB for 11m07 but recorded
  no SIGSEGV. The controlled stop showed waiting FEngine/llvmpipe stacks and
  one static QMP frame.
- FLR-0334's Sequoia emissive texture reached `texture_ready=true` and applied
  binding markers; shader sampling/display is still unproven.
- The exact FLR-0334 image/profile ran without GDB. At guest uptime 284.16 s,
  one queue-present attempt had no return marker and an `FEngine::loop` worker
  faulted. The 720-second observation target was not reached because the
  discriminating fault occurred first.
- Kernel RIP `0x7fb02fe44541` maps post-fault to
  `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered(Predicate)+1`. The faulting
  worker TID was already absent when GDB attached to the surviving parent.
- This matches the historical `isOrdered+1` signature in FLR-0103/0105/0106/
  0107 and the later FLR-0308/0309 fault matrix. Those records did not prove
  that LLVM's ordinary `isOrdered` call caused the Oops.
- FLR-0319/0320 prove the embedded `HeadLights_Emission` resource exists and
  gltfio queues then applies its `emissiveMap` binding when ready. Sampling
  into visible fragment output remains UNKNOWN.

### Hypotheses

1. GDB changes scheduling or timing and suppresses/delays the fault. Prediction:
   the no-GDB run reaches a fault or a different present boundary within the
   bounded 720-second observation.
2. The fault is nondeterministic or tied to the previous runtime state rather
   than debugger instrumentation. Prediction: the no-GDB run also stays alive
   without fault while the vehicle ROI remains black.
3. The missing present-return marker is associated with a one-frame/quiescent
   render loop rather than a long-blocked `vkQueuePresentKHR`. Prediction:
   QMP remains byte-identical and subsequent draw/present markers do not recur.

### Result

- The no-GDB run reproduced the FEngine page-fault boundary before 720 seconds.
  This completes the comparison unit; it does not claim that GDB alone caused
  the timing difference. One run per condition is insufficient to separate a
  debugger scheduling effect from runtime nondeterminism.
- QMP showed the HUD and Scenes control, but the vehicle region was uniformly
  black before and after the fault. Eight frames before and eight after had
  one unique hash per sequence; the post-fault frame matched the pre-fault
  frame.
- FLR-0335 is an evidence-unit PASS for reproducing/classifying the no-GDB
  boundary. The requested 720-second duration was not reached. Production 3D
  remains NOT PROVEN; no source, recipe, or image change was made.
- The user's square `HeadLights_Emission` image is the static 1024×1024 GLB
  emissive texture, not a QMP runtime frame. Separately, FLR-0070 p9 once
  captured HUD plus non-black production Sequoia pixels, but FLR-0071 did not
  reproduce them and the original p9 launch identity was incomplete. Neither
  image is a stable current baseline.
- FLR-0336 owns a low-perturbation capture of the recurring page-fault
  execution context. It must first check existing guest trace support and must
  not repeat the already-completed texture/light or LLVM symbol-only probes.

### UNKNOWN

- Whether GDB alone changed failure timing or the fault is nondeterministic.
- Whether the app requests more frames after the first production present.
- Whether a coredump is produced by the existing image configuration.
- Whether the missing present-return marker and the FEngine fault share one
  causal path.

## Plan / PDCA

1. Verify canonical repo, single active ticket, no residual QEMU/app, exact
   image hashes, and existing free-space/build state.
2. Launch one QEMU from the same fixed Mini build/TMPDIR and same image; run
   the exact diagnostic profile without GDB.
3. Capture full-screen QMP plus a bounded frame sequence; inspect only selected
   present, asset, fault, OOM, and coredump markers.
4. Compare to FLR-0334 and select one next diagnostic boundary. Do not patch
   unless a runtime stack/evidence identifies a specific code defect.

## Stop conditions

- Do not alter scene/material/light/camera settings or rebuild the image.
- Do not create another QEMU, build directory, receiver, or TMPDIR.
- Do not claim the red static texture image is proof of runtime 3D display.
- If process/resource behavior diverges or image hashes do not match, stop and
  record UNKNOWN rather than comparing unlike runs.
