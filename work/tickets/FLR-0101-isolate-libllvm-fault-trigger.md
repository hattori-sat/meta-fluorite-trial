# FLR-0101 — isolate the production input that triggers the libLLVM fault

- Status: Done
- Priority: High
- Owner: Fluorite production scene/resource boundary
- Created: 2026-09-12
- Depends on: [FLR-0100](FLR-0100-vk-present-return-boundary.md), [FLR-0099](FLR-0099-draw-to-native-output-boundary.md)
- Working log: `work/logs/2026-09-12-flr0101.md`

## Work unit

Find the smallest production input or scene stage that changes the current
image from the self-made fixture's successful native 3D output to the
`FEngine::loop` / `libLLVM.so.18.1` fault observed after queue-present entry.
Use the already deployed diagnostic controls as runtime-only A/B variables.
Run one variable at a time, keep the fixed image and QMP contract, and do not
change present, fence, semaphore, or compositor semantics before the trigger
is isolated.

The current work uses neutral ticket/evidence/receiver names. Existing
historical diagnostic environment variables in the deployed image may be
reused only as read-only controls for this A/B; no new legacy namespace,
directory, receiver, TMPDIR, marker, or environment variable may be created.

## Success criteria

- Establish a full-production control and one minimal variant with the same
  image, one QEMU at a time, and QMP-only evidence.
- Vary exactly one existing scene/resource selector per comparison, beginning
  with the smallest model-load boundary that can distinguish full production
  content from the known successful fixture.
- Record for each variant: process count, marker boundary, Oops/fault state,
  native/HUD pixel counts, QMP frame hashes, and teardown state.
- Identify the smallest trigger, or explicitly retain UNKNOWN and name the
  next narrow seam. A source patch is out of scope until this criterion is
  met.
- Preserve failed invocations and clean up QEMU through QMP.

## Out of scope

- No source or image patch.
- No changes to Vulkan present/fence/semaphore behavior, Wayland composition,
  light/material semantics, or route behavior.
- No cache deletion, new container, new QEMU run directory, or global process
  kill.
- No edits to historical FLR-0026 tickets, logs, evidence, or patch names.

## Facts

- FLR-0099's self-made fixture returned from `vkQueuePresentKHR` and produced
  `41,750/223,200` native pixels on the fixed image.
- FLR-0099's recovered full production scene reached visible target draws but
  remained native-black and had no queue-present return.
- FLR-0100 reproduced a guest userspace fault in `FEngine::loop` at the
  already-known `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered` offset boundary.
- Historical evidence shows that reduced model/environment conditions once
  produced visible production 3D, but those older conditions are not a verdict
  for the current image and must be replayed only as explicitly named A/B
  variants.
- The valid current-image control (`control-r4`) ran one `agl-compositor` and
  one `flutter-auto`, reached the visible swapchain draw and present-entry
  markers, remained at `0/223200` native pixels with HUD pixels present, and
  had no queue-present return marker. QMP capture and QMP teardown both passed.
- The valid model/resource reductions did not move that boundary:
  `model-match-sequoia-r1` selected 17 assets, `model-limit-1-r1` selected one
  asset, `environment-skip-r1` kept the scene setup while skipping the
  environment stage, and `model-skip-r1` loaded zero model assets. Each kept
  the same one-compositor/one-app process shape, native pixels at zero, and
  present-entry without a return marker; each had six identical QMP video
  frames and clean QMP teardown.
- `scene-content-skip-r1` did not emit its requested skip marker and still
  reported the full scene state, so it is not an effective A/B condition. Its
  non-identical QMP frames are retained as evidence but are not used as a
  product conclusion.
- `scene-render-skip-r1` completed QMP capture and teardown, but serial
  extraction missed its completion marker and no runtime markers were
  retained. Its QMP image remained native-black with HUD pixels, so the run is
  classified as an invalid stimulus/result rather than a trigger verdict.

## Inferences

- A runtime-only reduction is safer and more informative than another
  synchronization patch: it can show whether production scene input is a
  trigger while preserving the successful fixture control.
- The first useful cut is model/resource content because the fixture and full
  production differ most strongly there, and existing selectors can reduce
  that input without rebuilding the image.
- The effective model and environment reductions did not change the first
  observed boundary. This weakens the hypothesis that the number of loaded
  models or the environment stage alone triggers the current fault, but it
  does not prove that all scene content is irrelevant because the scene-content
  selector was not effective in this run.
- The current marker set is too late to distinguish the last successful scene
  command-recording operation from the userspace fault after queue-present
  entry. The next narrow seam is source-level instrumentation around the
  production scene draw/command-recording path, not another present or fence
  workaround.

## Hypotheses

1. A production model/resource selection triggers the invalid state. Prediction:
   a one-model or one-asset variant avoids the Oops and may return from present.
2. The aggregate production scene, rather than one model, triggers the fault.
   Prediction: the one-model variant still faults, while a scene/content
   suppression variant reaches a successful present boundary.
3. The fault is independent of scene content and is caused by a common
   current-image/runtime condition. Prediction: the self-made fixture also
   faults under the same ready condition, or no content reduction changes the
   boundary.

## UNKNOWN

- The smallest model/material/light/pipeline input that triggers the fault.
- Whether an Oops-free reduced variant produces actual native 3D pixels or
  only restores present completion.
- Whether the final fix belongs in application resource handling, Filament,
  Mesa/llvmpipe, or the image/runtime configuration.
- Whether the current `scene-content` and `scene-render` selectors can be
  made effective without changing production semantics; this is outside this
  runtime-only matrix because both current runs were invalid as A/B evidence.

## Plan / Do / Check / Act

### Plan

1. Verify canonical state, fixed image identity, one-QEMU preflight, and zero
   residual targets.
2. Run the recovered production control with the existing ready condition.
3. Run one model/resource reduction variant with every other input unchanged.
4. Compare marker order, Oops state, QMP native/HUD pixels, and teardown.
5. Select the next one-variable cut or, if the trigger is proven, open a
   separate source-patch ticket using Mac Devtool.

### Do

1. Reused the fixed image, build/TMPDIR, receiver, QEMU run alias, ports, and
   one-QEMU-at-a-time contract for all cases under
   `$RECEIVER/evidence/flr0101-libllvm-trigger/`.
2. Ran the recovered production control `control-r4`.
3. Ran one-variable runtime reductions: `model-match-sequoia-r1`,
   `model-limit-1-r1`, `environment-skip-r1`, and `model-skip-r1`.
4. Retained the failed/invalid orchestration and extraction attempts:
   `control/`, `control-r2/`, `control-r3/`, `scene-content-skip-r1/`, and
   `scene-render-skip-r1/`.
5. Captured QMP before/early/late frames and six-frame QMP samples for every
   valid case, then stopped QEMU through QMP and checked residual processes
   and sockets.

### Check

The valid control and four effective reduction cases all reached the same
present-entry-without-return boundary, with native pixels `0/223200`, HUD
pixels retained, no guest Oops in the selected runtime output, and
`cleanup=PASS residual_targets=0 residual_qmp=0`. The two scene-stage cases
did not provide valid internal runtime evidence and remain explicitly
excluded from trigger claims. Full per-case hashes and marker excerpts are in
`work/evidence/FLR-0101-libllvm-trigger-2026-09-12.md`.

### Act

Close this runtime-selector matrix as an evidence unit with the trigger still
UNKNOWN. Do not patch present, fence, semaphore, compositor, or scene
semantics from this result. Open FLR-0102 for neutral source instrumentation
at the production scene draw/command-recording seam, using the persistent Mac
Devtool source and the existing Mini authoritative build/evidence flow.
