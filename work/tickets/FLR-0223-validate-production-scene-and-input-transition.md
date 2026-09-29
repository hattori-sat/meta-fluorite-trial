# FLR-0223 — validate production scene and QEMU input transition

- Status: Done
- Priority: High
- Owner: Example Demo production scene, QEMU input, and display evidence role
- Created: 2026-09-20
- Predecessor: FLR-0221

## Objective

Determine whether the released Fluorite Example Demo production scene can
produce real 3D pixels and whether QEMU input transitions to another scene
while the 2D HUD remains visible. Use the existing readback-to-SHM path only
as a diagnostic display control; do not claim native WSI is fixed here.

## Success criteria

- The initial production scene produces a non-uniform QMP 3D ROI with the HUD.
- A QEMU input event activates the visible `Scenes` control.
- At least one scene transition produces a distinct QMP frame with 3D pixels,
  or the first failing production-scene boundary is identified with evidence.
- Every state has a QMP-only screenshot, ROI metrics, runtime slice, and hash.

## Facts

- The self-made native fixture produces chromatic native target pixels.
- The readback-to-SHM bridge displays those pixels in QMP with the HUD.
- Native-only QMP remains black and is tracked separately by FLR-0222.
- The fixed QEMU image, build, TMPDIR, and receiver must be reused.

## Hypotheses

1. The production scene readback contains real non-uniform geometry and the
   bridge will display it.
2. The released production scene produces uniform/empty readback because its
   camera, material, light, or model path is incomplete.
3. QEMU input reaches the 2D Flutter layer but not the scene navigation route.

## Plan / Do / Check / Act

### Plan

- Launch the released Example Demo without minimal-fixture overrides, with
  `FLUORITE_NATIVE_READBACK_TO_SHM=1` and bounded traces.
- Capture initial QMP screenshot and ROI/readback markers.
- Send one QMP mouse click to the visible Scenes button and capture the next
  stable frame; do not use global input or process kills.
- Stop at the first failing transition and split a new ticket if a source
  change is needed.

### Do

- Reused the fixed Mini PC image/build/TMPDIR/receiver and one QEMU instance.
- Started the released Example Demo with the diagnostic readback-to-SHM bridge
  and bounded Wayland/Vulkan/scene traces.
- Captured QMP-only initial and post-input screenshots, ROI metrics, runtime
  slices, and SHA-256 indexes.
- Sent a scaled absolute QMP tablet click to the visible `Scenes` control after
  recording and rejecting the malformed/device-specific input attempts.
- Stopped QEMU through QMP and verified no residual target remained.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Production readback | non-uniform geometry | `nonzero_pixels=248000`, `chromatic_pixels=0` | PASS: first production-scene boundary is uniform readback |
| Initial QMP frame | 2D HUD plus 3D | QMP bridge ROI `nonzero=100800`, `chromatic=100800`; HUD ROI positive | PASS: diagnostic bridge is visible, not native WSI proof |
| Scenes input | route changes | QMP accepted scaled click, but pointer left `wl_surface@14` and entered `wl_surface@39`; no route marker | FAIL: input is captured by native surface before Flutter route |
| Transition frame | distinct 3D scene or first failing boundary | post-click QMP hash changed to `83b474a...`; HUD disappeared and no scene transition marker appeared | PASS: first input/composition boundary identified |
| Teardown | QMP quit and no residual targets | `qmp=PASS`, `cleanup=PASS`, `residual_targets=0`, `residual_qmp=0` | PASS |

### Act

The diagnostic bridge is retained as a control, but production readback is
uniform. Native-only WSI restoration remains FLR-0222. Input routing is split
to FLR-0224 because the QMP pointer enters the native surface and the Flutter
HUD disappears before a scene route transition is observed.

## Evidence

- New evidence root: `$EVIDENCE_ROOT/FLR-0223/`
- QMP-only screenshot and artifact hash index are required before closure.

## Evidence summary

- Evidence root: `$EVIDENCE_ROOT/FLR-0223/`
- Initial QMP screenshot: `q/flr0223-initial.ppm`, SHA-256
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
- Post-click QMP screenshot: `q/flr0223-after-scenes-click.ppm`, SHA-256
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- Initial native readback: `chromatic_pixels=0`; diagnostic bridge ROI was
  `100800` chromatic pixels.
- Post-click pointer evidence: `wl_pointer.enter(... wl_surface@39 ...)`.
- Runtime selected log and all artifact hashes are in the evidence root.

## UNKNOWN

- The exact production asset/camera/light stage responsible for the uniform
  readback remains unresolved and is outside this ticket's first-boundary
  result.
- Whether clearing native-surface input coverage restores Flutter routing is
  owned by FLR-0224.
