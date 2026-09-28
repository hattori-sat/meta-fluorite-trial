# FLR-0349 — audit Fluorite 3D countermeasure effectiveness and regressions

- Status: Done
- Priority: High
- Owner: runtime evidence synthesis / production rendering / QMP acceptance roles
- Created: 2026-09-28
- Predecessors: [FLR-0345](FLR-0345-retrospective-3d-visibility-checklist.md), [FLR-0347](FLR-0347-retest-empty-log-arm-poll-on-exact-image.md)
- Follow-up: [FLR-0348](FLR-0348-watch-lavapipe-signal-without-fence-type.md)
- Working log: [2026-09-28 FLR-0349 working log](../logs/2026-09-28-flr0349.md)

## Purpose

Update the earlier historical checklist with measured effects from the latest
runtime and workflow gates. Separate fixes, positive controls, failed
interventions, diagnostic improvements, and confirmed versus unproven
regressions. Select one next bounded action without rerunning QEMU or changing
the product image.

## Acceptance checklist

- [x] State the current production screen result separately from the 2D HUD.
- [x] Link positive QMP evidence for same-frame 2D HUD plus self-made 3D.
- [x] Record the tested countermeasure, its measurable effect, and whether it
      fixed product behavior or only isolated a boundary.
- [x] Distinguish the proven readback-mode regression from the unproven
      historical-production regression.
- [x] Classify the supplied Photo 1 as resource evidence, not runtime screen
      evidence, using the prior hash/provenance record.
- [x] Identify the next-plan carry-over defect and update FLR-0348 from the
      exact Mesa wait condition.
- [x] Preserve QMP screenshot/video references and image/run identity.
- [x] Verify repository privacy, internal links, ticket checkpoints, and
      documentation diff; no QEMU, build, or product-source change.

## Current capability checklist

| Capability | Latest attributable evidence | Status | Interpretation |
| --- | --- | --- | --- |
| Flutter 2D HUD and metrics reach QMP | FLR-0347 full frame: HUD, CPU/GPU/FPS metrics, and Scenes control visible | PASS | Establishes the 2D path only |
| Self-made native 3D and HUD compose together | FLR-0235 and FLR-0271 QMP controls; FLR-0321 reports 119,716/144,000 chromatic fixture pixels with HUD | PASS, fixture only | Falsifies a universal QMP/Wayland inability to show 2D+3D |
| Production Sequoia is visible in the current image | FLR-0347 run flr0347-0001; exact lower ROI 768,000/768,000 black in all eight frames | FAIL | Current production image still shows HUD without visible Sequoia |
| Production Sequoia plus HUD is repeatable and correctly colored | Historical FLR-0070 p9 candidate only; not repeated with matched source/image/profile | UNKNOWN | Not acceptance; the current image/profile has not passed |
| Sequoia appears with HUD disabled on the exact current image | No such run in FLR-0347 or FLR-0348 | UNKNOWN | Neither hidden-behind-HUD nor no-HUD visibility has been established |

## Countermeasure and effect checklist

| Symptom / boundary | Countermeasure or control | Measured effect | Verdict |
| --- | --- | --- | --- |
| Pointer movement could repaint the 2D surface white while native fixture pixels were visible | FLR-0235 replaced the stateful hover button with a static clickable surface | HUD stayed at 2,845 chromatic pixels and the native fixture at 24,178 chromatic pixels through the tested motion sequence | Effective for that pointer-motion regression; not production Sequoia acceptance |
| Readback mode produced a full-black QMP frame | FLR-0268 ran a same-image SHM-only control versus readback mode | SHM-only restored HUD plus 24,178 chromatic fixture pixels; the readback-mode case remained black even though source readback and buffer-release markers were positive | Readback-mode-specific visibility/composition regression is demonstrated; do not generalize it to every 3D path |
| Production framing selected a distant camera | FLR-0274's 0091 camera-selection patch | Effective camera changed to the local Playground view, but QMP remained at 0 chromatic production pixels | Camera correction took effect but was insufficient to restore visible Sequoia |
| PaintColor override branch did not match | FLR-0324 changed the name comparison to content equality | Corrected predicate and magenta override markers fired; production ROI still had 0/144,000 chromatic pixels | Real code defect fixed; no visible-production fix demonstrated |
| Missing or incorrect emissive/light/material path was suspected | FLR-0314/0316/0321 and FLR-0324 used bounded material, texture, emissive, and fixture controls | Fixture renders in color; Sequoia asset/binding markers are positive, but current production pixels remain absent; the static texture atlas is not a framebuffer | Light-only or missing-texture root cause is not established; shader/target output remains unresolved |
| FLR-0344 arm check failed ambiguously on an empty GDB transcript | FLR-0346 added an empty-log-aware deterministic helper and regression test | FLR-0347 waited 44 polls, retained the GDB transcript, and exposed the concrete missing-type error instead of the old missing-state result | Effective observability improvement; no product-render change |
| QEMU evidence and cleanup could be mistaken or incomplete | FLR-0347 pinned image hashes, captured QMP full-frame PNG plus eight frames, counted a fixed ROI, and checked teardown | All frames were identical; the lower ROI was black; zero app/QEMU/socket leftovers were independently confirmed | Evidence and cleanup controls worked; they prove the production failure, not a fix |

## Facts

- FLR-0347 used the exact FLR-0335 kernel/rootfs/qemuboot identity and one
  Mini-hosted QEMU run. Present entered and did not return; the QMP lower 3D
  ROI was uniformly black in the still and all eight frames.
- The corrected arm helper waited 44 cycles. GDB read signaled=false and
  fence=null, created the signal watch, then failed to create the typed fence
  watch because pipe_fence_handle debug type information was unavailable.
  Therefore the bounded writer interval never ran.
- FLR-0342's hash-matched Mesa source/binary evidence says the wait continues
  while both signaled is false and fence is null. Either field changing can
  release it.
- FLR-0268 demonstrates a black result in the readback mode while a same-image
  SHM-only control showed both the HUD and a chromatic fixture.
- FLR-0345 records that FLR-0070 p9's historical Sequoia/HUD candidate was
  unstable, lacked its raw frame at the recorded evidence location, and used
  a different rootfs/profile from the current run.
- FLR-0321/0345 identify Photo 1 as the static Sequoia GLB emissive texture
  atlas. It establishes that texture color data exists, not that a runtime
  shader sampled it or that QMP displayed the car.

## Regression verdict

- **Proven, limited scope:** the experimental readback mode fails to preserve
  visible output in the tested case, while the same-image SHM-only fixture
  control succeeds. This is not evidence that ordinary QMP composition or
  every fixture/production route is broken.
- **Plausible, not proven:** historical Sequoia-positive evidence and the
  current production-black result differ, but rootfs, source/configuration,
  launch profile, and repeatability are not a matched A/B. The old raw p9
  frame is unavailable for re-analysis.
- **Current status:** 2D is visible; a fixture can compose 2D+3D; production
  Sequoia plus HUD is not currently visible. Whether removing the HUD exposes
  production pixels is UNKNOWN. Therefore 3D acceptance is not complete.

## Problem analysis and next action

The latest established production divergence is a Present-enter/no-return
wait with both release predicates initially false/null, followed by no visible
production pixels. This is a boundary correlation, not a proven root cause.
The initial FLR-0348 signal-only plan omitted the fence-pointer condition
already recorded in FLR-0342, so it could produce an incomplete observation.

**Selected next action:** FLR-0348 will first contract-test a type-independent
GDB watch of both the signal bit and the raw-address fence-pointer storage,
then use the existing bundle-to-Mini route for exactly one same-image runtime
run. Capture the full QMP frame/video, both watch outcomes, fixed-ROI pixels,
and teardown. No image rebuild is needed for a debugger-script-only change.

Do not mix HUD-off, camera, Light, texture, and material changes into that run.
If either wait condition changes or the wait returns while the production ROI
stays black, open a distinct ticket for the next measured render/surface
boundary; test the exact-image HUD-off hypothesis separately only if evidence
still supports it.

## Visual evidence

- Current negative QMP frame: [FLR-0347 full-frame PNG](../evidence/FLR-0347-qmp-run-0001.png), SHA-256
  4b2d48306e24e04ff3634340d338512799fc2c8ebd066b82666151d8b9862b81.
  The upper HUD is visible; the lower fixed ROI is black.
- Current eight-frame QMP video: [FLR-0347 sequence](../evidence/FLR-0347-qmp-run-0001-sequence.mp4), SHA-256
  331c38be1e7bcca8aff38fad5cdabff18556071808764f1f0f1a2b120040741d.
- Positive fixture controls: [FLR-0235 combined HUD and native fixture](FLR-0235-replace-material-hover-button.md) and
  [FLR-0271 continuous QMP fixture plus HUD](FLR-0271-trace-readback-child-surface-visibility.md).
- Image identity, run timestamp, full hashes, pixel analysis, and teardown:
  [FLR-0347 runtime record](FLR-0347-retest-empty-log-arm-poll-on-exact-image.md).
- No new screenshot/video was generated in this retrospective.

## Plan / Do / Check / Act

### Plan

1. Reuse FLR-0345's bounded intervention matrix rather than rereading unrelated
   historical logs.
2. Compare the exact FLR-0347 QMP/GDB result with positive fixture controls,
   the same-image readback control, camera/material interventions, and the
   source-level Mesa wait condition.
3. Classify each outcome as product fix, diagnostic improvement, positive
   control, regression, or UNKNOWN.
4. Update FLR-0348 to cover both source-proven wait-release predicates and
   run documentation privacy/link/checkpoint/whitespace validation.

### Do

- Read FLR-0235, FLR-0268, FLR-0271, FLR-0273/0274, FLR-0314/0316/0321/0323/0324,
  FLR-0342/0345/0346/0347/0348 and their bounded evidence summaries.
- Reconciled present and historical pixel evidence; retained the difference
  between fixture output, production output, static texture data, and QMP.
- Updated FLR-0348 and its working-log handoff to watch both wait predicates.
- No QEMU, Mini mutation, BitBake, build, Devtool, image, or product-source
  operation was performed.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Evidence-linked checklist | Each intervention has a measured effect and scoped verdict | Recorded above, linked to primary tickets | This ticket and FLR-0347/0345/0268/0324 | PASS |
| Regression classification | Separate proven path regression from unmatched historical comparison | Readback-only regression proven; overall historical production regression plausible, not proven | FLR-0268 and FLR-0345 | PASS |
| Wait-condition handoff | Both source-level release predicates reflected in next test | FLR-0348 now requires signal plus type-independent fence-pointer watch | FLR-0342 and revised FLR-0348 | PASS |
| Runtime change | No additional run or build during retrospective | None performed | Working log | PASS |
| Repository gates | Canonical/privacy/links/checkpoints/diff pass | See working log | Working log | PASS |

### Act

- Close this retrospective after its repository checks. Keep FLR-0348 as the
  single active runtime unit with the corrected two-predicate contract.
- Do not mark Fluorite complete: production Sequoia plus the 2D HUD remains
  absent from the latest exact-image QMP evidence.

## UNKNOWN

- Which wait-release predicate changes in the runtime and its writer/stack.
- Whether the Lavapipe wait causes the black production ROI or is only
  correlated with it.
- Whether production Sequoia pixels exist beneath the HUD on the exact current
  image; no exact-image HUD-off run has been captured.
- Which matched source/image/profile delta explains the historical
  Sequoia-positive versus current-black comparison.
- Whether the current production material, lighting, or shader output is
  independently correct once the present boundary is resolved.

## PDCA checker

- Status: PASS
- Checked by: canonical, privacy, link, checkpoint, whitespace, and file-size gates
- Findings: documentation evidence and links are recorded; no product/runtime success is claimed
