# FLR-0393 — replay the known-positive constant LIT/SUN fixture on the FLR-0391 image

- Status: In Progress
- Priority: High
- Created: 2026-10-01
- Work unit: One bounded runtime control; no source, patch, or image change
- Predecessor: [FLR-0391 Sequoia constant-LIT trial](FLR-0391-apply-constant-lit-material-to-sequoia.md)
- Positive control: [FLR-0369 constant LIT/SUN fixture](FLR-0369-lit-hardcoded-material-control.md), [FLR-0371 3.32.5 LIT/SUN fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Candidate rootfs SHA-256: `54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690`
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate qemuboot SHA-256: `58ef9a59af7df24be48b221f252fd7b604e5d968e61766af83b7cf7b8ae5b5f7`
- Layer source commit: `2c531a8ddce315ab958629d082586ffe85e69c21` (patch 0333)
- Branch: `feature-flr-0393-current-image-fixture-control`, based on the exact FLR-0391 candidate branch; local only, no push
- Working log: [FLR-0393 working log](../logs/2026-10-01-flr0393.md)
- Evidence manifest: [FLR-0393 QMP evidence](../evidence/FLR-0393-0001.md) (created after the run)

## Problem and purpose

FLR-0391's constant LIT material reached Sequoia READY/BOUND=24 and the known
SUN setup, but a live QMP frame contained no Sequoia pixels while the second
Vulkan present was unmatched and `FEngine::loop` recorded an Oops. This does
not tell whether the current image's general native 3D path still works or the
failure is specific to production Sequoia setup.

On the exact FLR-0391 rootfs, replay the already-proven self-made constant
LIT/SUN fixture with the CPU/GPU HUD. This is a control-path discriminator, not
production Sequoia acceptance and not a new material implementation.

## Evidence basis and competing explanations

- FLR-0369 on its pinned image showed the constant LIT/SUN fixture and HUD in
  one QMP frame: native ROI 119716/144000 chromatic; 242 present-boundary
  completions. The exact material branch uses
  `vec3(0.05, 0.45, 1.0)`.
- FLR-0371 on Example Demo 3.32.5 showed the fixture plus HUD and 146
  successful presents on rootfs `949921c…`; its parameterized material
  branch differs from this constant-source control.
- FLR-0389 ran a fixture control on rootfs `ff0f801c…`, but produced no
  healthy live visual verdict. It is not the exact newer FLR-0391 image.
- FLR-0391's candidate rootfs includes patch 0333, which changes only the
  opt-in Sequoia material source. This ticket does not set that Sequoia-only
  override; the existing fixture code path and HUD are held as the positive
  control.

| Hypothesis | Prediction on this exact image |
| --- | --- |
| General native 3D and HUD path remains healthy; fault is Sequoia-specific | Constant-blue fixture pixels, HUD, and repeated successful presents appear together |
| Current-image shared renderer/present path is unhealthy | Fixture also lacks QMP pixels or reproduces unmatched present/Oops |

The result classifies the next boundary; neither outcome alone proves the
root cause of the Sequoia path.

## Stratification — 4W1H excluding Why

| Dimension | Scope |
| --- | --- |
| What | Known-positive constant LIT/SUN diagnostic geometry and CPU/GPU HUD |
| Where | Exact FLR-0391 Mini image, Example Demo 3.32.5, existing runqemu/QMP path |
| When | One manual app launch, bounded to 60 seconds; QMP capture at the first successful present |
| Who | Mini BitBake/image role (no rebuild), guest Flutter role, QMP evidence role |
| How | Historical fixture flags, no Sequoia selector/override, full-frame QMP plus fixed native/HUD ROIs |

**Problem point under test:** whether a known-positive native fixture can pass
through draw and repeated present to visible QMP pixels on the exact image that
showed Sequoia READY/BOUND but black output.

## Ideal condition and current gap

- **Ideal:** at least eight successful fixture draw/present boundaries; a
  recognizable dark-blue native 3D face and the CPU/GPU HUD in the same live
  QMP frame; no unmatched present/Oops; exact QEMU teardown.
- **Current facts:** FLR-0391 captured HUD/Scenes but zero pixels in the
  Sequoia ROI, with 2 present begins / 1 return / 0 present-done, Oops #2, and
  app status 124.
- **Gap:** no valid positive-control result exists for the exact rootfs
  `54da69d…`.
- **Confirmed root cause:** UNKNOWN. FLR-0366's GDB run caught no signal and
  did not prove the invalid access; FLR-0339's partial stack reached a
  Lavapipe sync wait but did not capture the caller. Do not repeat a broad
  all-thread dump here.

## Plan / Do / Check / Act

### Plan

- Reuse the exact already-built rootfs/kernel/qemuboot and the official Mini
  QEMU harness; no BitBake, bundle, new TMPDIR, or image copy.
- Preflight one QEMU slot, hashes, ports, QMP path, guest Wayland session,
  installed Example Demo bundle, and zero stale `flutter-auto`.
- Manually launch one app as `agl-driver` with the existing fixture controls:
  `FLUORITE_NATIVE_PURE_FIXTURE=1`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`,
  `FLUORITE_NATIVE_FIXTURE_LIGHT=1`, and
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1`.
- Leave `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE` and
  `FLR0305_PRODUCTION_SCENE_LIGHT` unset. Do not add high-volume traces,
  legacy `FLR0026_*` switches, or change camera, model assets, or UI.
- Capture full QMP still/eight-frame short video at the first successful
  present while the exact PID is live. Then record repeated-present health,
  app status, and only focused kernel/core markers.
- If launch/identity/present gates fail, retain the bounded failure and stop
  this ticket after one attempt; do not retry the same sequence.

### Do

- Working-log links only; see [FLR-0393 working log](../logs/2026-10-01-flr0393.md).

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image and process preflight | Exact hashes; zero stale QEMU/app; guest session ready | Pending | PENDING |
| Fixture contract | Constant LIT material, SUN, 8 vertices/36 indices, local camera | Pending | PENDING |
| Native 3D + HUD | Full QMP frame shows both, with separate ROI metrics | Pending | PENDING |
| Present health | At least eight successful returns; no unmatched present/Oops | Pending | PENDING |
| Capture liveness | Same PID/UID/start before and after QMP still/video | Pending | PENDING |
| Teardown | Owned QMP quit; zero processes/socket/ports | Pending | PENDING |

### Act

- If fixture+HUD succeeds, keep FLR-0391 Waiting and create a new Sequoia-only
  follow-up using the exact same image/control profile; do not call the
  fixture result production acceptance.
- If the fixture fails or Oopses, prioritize the shared draw/present boundary
  using existing FLR-0339/0366 evidence and only the first newly observed
  divergence; do not re-scan textures or alter camera/light.

## Visual evidence

- QMP-only screenshot/video and pixel metrics: pending; see the evidence
  manifest after execution.

## Unknowns

- Whether the constant fixture still emits visible pixels on the exact
  FLR-0391 image.
- Whether repeated present health differs between the self-made fixture and
  production Sequoia on this image.
- Whether any shared present fault causes the black Sequoia result; correlation
  alone will not establish causality.

## PDCA checker

- Status: NOT CHECKED
- Checked by: pending runtime and cleanup evidence
- Findings: one bounded control run remains.
