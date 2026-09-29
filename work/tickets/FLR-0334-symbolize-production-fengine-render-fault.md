# FLR-0334 — symbolize the production FEngine render fault

- Status: Waiting
- Priority: High
- Owner: FEngine render-thread / llvmpipe / GDB runtime roles
- Created: 2026-09-28
- Predecessor: [FLR-0333](FLR-0333-trace-vulkan-present-return-page-fault.md)
- Working log: `work/logs/2026-09-28-flr0334.md`
- Evidence: [GDB no-fault run](../evidence/FLR-0334-gdb-under-run-2026-09-28.md)

## Objective

Capture the production Example Demo's FEngine user-mode fault while the
faulting thread still exists, then map its instruction address to a loaded
module and symbol. Determine whether it is the same thread blocked in
`vkQueuePresentKHR` or a separate scene/render worker. Do not infer a
texture or lighting defect from the black QMP frame.

## Success criteria

- Reuse the exact FLR-0333 image identity, Mini receiver/build/TMPDIR, and one
  QEMU at a time; do not rebuild unless this ticket later proves a source
  change is required.
- Start the production diagnostic profile under GDB (or attach before the
  first model-add/frame boundary), stop on SIGSEGV, and capture
  `thread apply all bt`, registers, loaded shared-library ranges, and the
  mapping for the faulting RIP.
- Correlate the faulting TID and timestamp with the present begin/return and
  scene-add/render markers.
- Capture QMP-only full frame and a bounded frame sequence; record whether
  HUD pixels continue changing and whether any vehicle pixels appear.
- Stop the recorded app and QEMU cleanly; preserve exact evidence hashes.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0333 reproduced `vkQueuePresentKHR` begin without a return marker and a
  user-mode page fault in an `FEngine::loop` thread.
- GDB was present in the image, but the post-fault attach could not see the
  faulting thread; no matching coredump was listed.
- Surviving FEngine and llvmpipe workers were waiting in Mesa
  `cnd_wait`; QMP's eight production frames were identical.
- A same-image pure native cube fixture did return from queue-present, but its
  front-on camera did not show depth.
- Under GDB, the same diagnostic profile ran for 11m07 after launch, beyond
  the predecessor's 598-second guest-monotonic page-fault point. No SIGSEGV
  occurred; GDB was stopped by a deliberate SIGINT after the runtime became
  visually and log-wise quiescent.
- The bounded GDB stop snapshot showed the main `flutter-auto` thread in
  `nanosleep`, a Wayland client thread in `wl_display_poll`, and FEngine/
  llvmpipe workers waiting in Mesa `cnd_wait`. These are post-SIGINT stacks,
  not fault stacks. No present-return marker was recorded.
- The Sequoia GLB loaded. Its emissive binding trace moved from
  `texture_ready=false`/queued to `texture_ready=true`/applied; this proves
  the asset/binding path reached readiness, not that a shader sampled it or
  emitted a screen pixel.
- QMP showed the HUD/Scenes control and a black vehicle region. The eight-frame
  sequence had one unique full-frame hash.

### Hypotheses

1. A production model/material/scene resource triggers a user-space fault in
   the llvmpipe or shader execution path. Prediction: GDB maps the faulting RIP
   into Mesa/LLVM or a graphics runtime module.
2. Concurrent production scene insertion or resource lifetime misuse faults
   an FEngine worker while a different worker is waiting in present. Prediction:
   GDB shows distinct thread stacks and the fault maps to application/Filament
   code or an invalid resource access near scene insertion.
3. A production-specific WSI/semaphore interaction blocks present while an
   unrelated worker faults. Prediction: the present-owning TID is alive and
   blocked in the Vulkan/WSI stack when the other TID receives SIGSEGV.

### UNKNOWN

- Faulting module, symbol, instruction, and owning thread.
- Whether the missing present return and the page fault share one causal path.
- Whether production material/texture data is reached by the GPU pipeline.
- Whether GDB changes scheduling enough to suppress or delay the predecessor
  fault.
- Whether the absent present-return marker means the API call remained active
  or the render loop stopped requesting further frames.

## Plan / PDCA

1. Verify canonical repository, active ticket, fixed build/image identity, and
   that no QEMU or app remains.
2. Reuse the existing diagnostic profile under GDB, with no source or image
   changes.
3. Capture bounded GDB and QMP evidence, then stop after the predecessor fault
   point has been exceeded without a SIGSEGV.
4. Compare against FLR-0335's no-GDB control before deciding whether another
   symbolication attempt is justified.

## FLR-0334 result and handoff

- Status is Waiting, not Done: the fault was not reproduced, so there is no
  faulting RIP/module to symbolize.
- FLR-0335's no-GDB control later reproduced the fault at guest uptime
  284.16 seconds. Its post-fault GDB map resolved RIP to
  `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered+1`, but the faulting TID had
  already disappeared, so no live stack was captured. FLR-0334 remains
  Waiting for a fault-time execution context, not for symbol mapping alone.
- FLR-0336 checks whether the retained image supports a bounded, low-perturbation
  kernel page-fault trace. Reuse the same image; do not change Light, camera,
  texture, material, scene behavior, or system settings.
- The attached `HeadLights_Emission` image is a static emissive texture from
  the Sequoia asset, not a runtime QMP screenshot. The red texels describe
  emission data but do not prove runtime sampling or display.

## Stop conditions

- No Light, camera, texture, material, model-count, or scene-ownership patch
  until the faulting stack is mapped.
- Do not repeat the historical no-wait A/B or start a second concurrent QEMU.
- If GDB instrumentation prevents startup or changes the failure timing,
  record that result and do not call it a production fix.
