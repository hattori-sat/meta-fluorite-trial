# FLR-0369 — current-image LIT fixture with hardcoded material color

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / direct guest SSH / manual Flutter / QMP evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0368 current-image UNLIT control](FLR-0368-manual-unlit-fixture-control.md)
- LIT negative baseline: [FLR-0367 manual LIT replay](FLR-0367-replay-manual-known-good-fixture-on-current-image.md)
- Working log: [FLR-0369 working log](../logs/2026-09-30-flr0369.md)

## Objective

Determine whether the current-image LIT fixture's black native ROI is caused
by its dynamic `materialParams.color` input. Reuse the FLR-0367 direct manual
LIT profile and current pinned image; add only the existing
`FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1` runtime flag. Do not edit scripts,
source, recipes, patches, or the image.

## Facts

- FLR-0367 used the current rootfs and LIT fixture with
  `hardcoded=false source=parameter`; HUD and successful draw/present activity
  were present, but native ROI was black.
- FLR-0368 used the same rootfs and fixture geometry with the LIT opt-in
  removed. UNLIT geometry and HUD were both visible in QMP, with 119,716 native
  chromatic pixels and 2,845 HUD chromatic pixels.
- Patch 0249's existing flag changes only the native fixture material source
  from `materialParams.color` to constant blue
  `vec3(0.05, 0.45, 1.0)`. FLR-0154 tested the flag on an older source/image
  lineage and remained black; that historical negative does not decide the
  current image after later fixture changes.
- FLR-0286 proves the LIT fixture can render chromatic geometry with HUD on an
  older rootfs. Production Sequoia remains a separate unresolved path.

## Hypotheses

1. If LIT plus hardcoded blue produces native pixels, the dynamic material
   parameter path is the distinguishing failure in FLR-0367.
2. If it remains black while UNLIT is visible, the failure is after that color
   expression or in the combined LIT/SUN path; the next split must distinguish
   LIT shading from light setup before source changes.

## Procedure / success criteria

- Verify canonical repository, sole active ticket, exact current image hashes,
  free QEMU slot, guest/bundle/Wayland readiness, and no stale Flutter process.
- Manually SSH to the guest as the recorded runtime user and execute the
  existing FLR-0367 Flutter command/profile. Add only
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1`; keep
  `FLUORITE_NATIVE_FIXTURE_LIGHT=1` and all other runtime inputs fixed.
- Confirm `hardcoded=true shading=lit source=constant`, fixture geometry and
  camera setup; capture a full QMP frame and the same fixed HUD/native ROIs.
  Capture selected marker counts/hashes rather than transferring a repeated
  full runtime log.
- Stop the exact recorded app PID immediately after the decisive QMP capture.
  Do not wait for further frame counts while transferring/converting evidence.
  Stop QEMU and independently verify PIDs, QMP socket, and ports absent/free.
- Preserve QMP PNG/short sequence, measurements, hashes, selected runtime
  markers, failures, and teardown result in this ticket and its working log.
- No script/source/recipe/patch/build changes in this task.

## Impact

- Build-time and packaging: none.
- Runtime: one bounded manual fixture run.
- Integration risk: low; one existing diagnostic environment variable only.

## Plan / Do / Check / Act

### Plan

Compare directly against FLR-0367 and FLR-0368 on the identical current image.
The hardcoded-color flag is the sole changed variable relative to the LIT
negative baseline.

### Do

- Pending preflight, then one direct manual guest launch.

### Check

| Gate | Actual | Result |
| --- | --- | --- |
| Canonical repository / sole active ticket / QEMU preflight | Pending | PENDING |
| Manual Flutter and LIT+constant branch markers | Pending | PENDING |
| QMP full frame and fixed ROI pixel evidence | Pending | PENDING |
| Immediate exact-app and QEMU teardown verification | Pending | PENDING |

### Act

- If constant-color LIT renders, isolate the dynamic parameter assignment
  path next; only then decide whether a minimal source patch is justified.
- If it stays black, do not call the material parameter the cause. Plan the
  next single-variable LIT-versus-light split from the actual source contract.
- Keep production Sequoia and combined product acceptance open until its own
  recognizable same-frame QMP evidence passes.

## UNKNOWN

- Whether the hardcoded color branch produces pixels in the current image's
  LIT fixture.
- If it remains black, whether LIT shading or SUN/light interaction is the
  more specific failing component.
