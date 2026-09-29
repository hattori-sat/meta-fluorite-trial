# FLR-0276 — restore bounded production model-payload control

- Status: Done
- Priority: High
- Owner: production asset loading / current scene-stage diagnostic controls
- Depends on: [FLR-0275](FLR-0275-isolate-production-payload-visibility.md)
- Working log: `work/logs/2026-09-24-flr0276.md`

## Problem

FLR-0275 showed that the current scene-stage patch stack unconditionally loads
the production model list. The attempted payload A/B used a stale model-skip
name, so it was invalid and the guest hit OOM before a visual verdict. A valid
bounded control must be used against the current Devtool baseline before
production payload visibility can be measured.

## Facts

- Current patch `0278` calls `setUpLoadingModels()` unconditionally.
- Current environment controls are split into skybox and indirect-light
  selectors; the old aggregate environment marker is not emitted.
- FLR-0275-0002 ended with a kernel OOM kill of `flutter-auto` and an invalid
  all-black QMP frame.
- The fixed qemuboot profile supplies `-m 2048`; the runtime harness accepted
  an explicit `--memory-mb 4096` override for this diagnostic. This is not a
  product-memory claim.
- The current persistent Devtool source already contains the model
  limit/match implementation. No new source patch is required for this ticket;
  the defect was use of stale runtime control names.
- The current controls selected one model and suppressed the requested skybox,
  indirect-light, and light payloads. The process then faulted with SIGSEGV,
  not OOM; FLR-0277 owns that boundary.

## Hypotheses

1. Restoring a bounded model limit will remove the OOM ambiguity and allow a
   valid payload comparison. PASS for model selection; production later
   SIGSEGVed.
2. Even one selected model may remain zero-chroma or crash; the remaining
   boundary is now production frame-event/render safety, not an unbounded
   payload assumption. PASS as a diagnostic split.
3. The current source already implements the model-loading API. PASS; no
   reimplementation was needed.

## Success criteria

- Use the existing Mac Podman Devtool container and current recipe-applied
  source baseline.
- Run the bounded A/B with the harness memory override at 4096 MiB; this is a
  runtime diagnostic setting, not a product-memory claim.
- Confirm the existing Mac Podman Devtool source baseline; do not create a
  source patch when the control is already present.
- Reuse the already transferred layer commit and fixed Mini build/TMPDIR; no
  image rebuild is needed for this command/harness-only experiment.
- Run one QMP-only bounded A/B with the actual current control names, record
  model selection, process/core state, ROI metrics, and teardown. The pure
  fixture remains alive and chromatic; production SIGSEGV is explicitly
  recorded as the next boundary rather than misclassified as black 3D.
- Keep route/input and full production visual acceptance out of this ticket.

## Verification plan

1. Inspect current Devtool status/source and the current model-loading API.
2. Use the existing `FLR0026_NATIVE_MODEL_LIMIT` control with a limit of one,
   plus the current skybox/indirect-light control names.
3. Launch one QEMU with a small model limit and the current skybox/indirect
   light control names; capture bounded runtime markers and QMP frames.
4. Close this ticket with visual evidence and create the next ticket for the
   first surviving production render boundary.

## Visual evidence

Done. The bounded control selected one model and removed the prior OOM
ambiguity. Production still needs FLR-0277 to survive the frame-event path;
the same-QEMU pure fixture produced positive colored QMP geometry.
