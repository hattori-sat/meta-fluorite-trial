# FLR-0393 — replay the known-positive constant LIT/SUN fixture on the FLR-0391 image

- Status: Waiting
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
| When | One manual app launch; observer failed at its 30-second deadline before the roughly 52-second first present |
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

- The guest used `/usr/bin/timeout 60`; the constant LIT branch marker
  appeared. The standard `serial-exec` live gate failed with
  `completion-marker-not-observed`; its implementation has a fixed 30-second
  command deadline. Focused final counts were 7 present begins, 6 successful
  returns, and 0 present-boundary completions. The wrapper recorded exit status
  124 at its 60-second limit; no coredump was found.
- The guest BusyBox `dmesg` rejected `--ctime`, so no kernel-fault verdict is
  claimed. QMP still/eight frames were captured only after the app exited;
  the black frame is forensic-only, not a live-render verdict. The official
  QMP quit and postflight passed.
- Focused app output was not persisted outside the guest snapshot before
  teardown. This retention gap is explicit in the evidence manifest.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image and process preflight | Exact hashes; zero stale QEMU/app; guest session ready | PASS | PASS |
| Fixture contract | Constant LIT branch reached; geometry marker contract not independently verified | Partial / UNKNOWN | PARTIAL |
| Native 3D + HUD | Full live QMP frame shows both, with separate ROI metrics | No live capture; post-exit frame black | UNKNOWN |
| Present health | At least eight successful returns; no unmatched present/Oops | 7 begins / 6 returns / 0 done; timeout 124 | FAIL |
| Capture liveness | Same PID/UID/start before and after QMP still/video | App had exited before QMP capture | FAIL |
| Teardown | Owned QMP quit; zero processes/socket/ports | Official harness and forwarded-port checks passed | PASS |

### Act

- FLR-0393 is Waiting because its 30-second serial observer cannot observe the
  roughly 52-second first present under the 60-second app cap. This is an
  observer/process-window mismatch, not a valid visual negative. FLR-0394 owns
  one direct-SSH live capture with a 180-second app cap, appended-log waiting,
  QMP still/video while the exact PID is live, and focused evidence persisted
  to the Mini host before teardown.
- Do not repeat the same serial-exec gate, rescan textures, or change camera or
  light. FLR-0391 remains Waiting until a valid live QMP frame narrows the
  production Sequoia boundary.

## Visual evidence

- See [FLR-0393 evidence manifest](../evidence/FLR-0393-0001.md). Its
  post-exit black frame is explicitly not a fixture-render verdict.

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
