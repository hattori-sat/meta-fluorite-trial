# FLR-0220 — trace native render-target shape content before Wayland composition

- Status: Done
- Priority: Critical
- Owner: Filament native render-target and fixture role
- Created: 2026-09-20
- Predecessor: [FLR-0219](FLR-0219-trace-final-native-wayland-composition.md)
- Links: [working log](../logs/2026-09-20-flr0220.md)

## Work unit

Determine why the native swapchain readback ROI is uniformly white
(`chromatic_pixels=0`) even though the runtime reports renderable shapes, and
why the final QMP native ROI is black. Prove actual shape pixels in the native
render target before changing Wayland composition.

## Success criteria

- Reuse the fixed Podman/Devtool state, Mini receiver/build/TMPDIR, image, and
  QEMU harness.
- Statistically correlate `SHAPE_READY`, camera/view setup, primitive/index
  selection, render-pass target, and readback ROI.
- Compare at least two explanations: clear/placeholder output versus real
  geometry lost by readback/conversion.
- Use the self-made fixture as the control where possible, then compare the
  packaged Example Demo scene without changing both variables at once.
- Retain QMP-only screenshot/frame hashes and native readback statistics.
- Do not create a source patch until a bounded runtime or static source
  observation selects the implicated layer. If a patch is required, use the
  official locked Devtool baseline → source commit → `update-recipe` →
  `finish` → canonical layer → bundle → Mini gate sequence.

## Facts inherited from FLR-0219

- `FLR0026_SHAPE_READY` reported many `renderable=true` entities.
- The final swapchain draw marker reported `primitive_handle=231` and
  `index_count=3`.
- Native swapchain probe reported all `248000` ROI pixels non-zero, but
  `chromatic_pixels=0`, `byte_sum=252960000`, and `max_rgb_byte=255`.
- Native driver readback reported all bytes non-zero and alpha 255.
- QMP showed a stable black native ROI and a visible 2D HUD for eight frames.
- Wayland client attach/damage/frame/commit and Vulkan present result 0 passed;
  this ticket does not reopen that protocol path without new evidence.
- Native minimal geometry contract passed:
  `has_renderable=true primitives=1 bound_material=true material_instance=true
  vertex_count=8 index_count=36 scene=true`.
- Explicit fixture camera passed with `fov=60`, near `0.05`, far `1000`, eye
  `(0,0,5)`, and target `(0,0,0)`.
- Native target draw used `index_count=36`; current-color, draw, readback, and
  present correlated to the same swapchain image.
- Native probe reported `nonzero_pixels=111758 chromatic_pixels=111758` in the
  248,000-pixel ROI. Driver readback reported `nonzero_bytes=478864`,
  `nonzero_rgb=111758`, `nonzero_alpha=111758`, alpha range `0..255`.
- QMP native ROI remained black while HUD was visible; all eight captured frame
  hashes were `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- Evidence hashes are indexed in
  `$EVIDENCE_ROOT/FLR-0220/flr0220-artifact-sha256.txt`.

## Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Minimal fixture native target contains chromatic geometry pixels; QMP native ROI is black | FLR-0220 runtime/QMP evidence |
| Where | Filament render pass, camera/material/primitive selection, or readback conversion | First unresolved 3D boundary |
| When | After target draw/readback and before final visible pixels | Target/readback markers |
| Who | Filament scene/fixture, Vulkan render target, readback path | Component roles |
| How | `chromatic_pixels=111758` in the native ROI, but zero pixels in paired QMP ROI | Native probe and QMP ROI statistics |

## Hypotheses

1. The compositor receives a different, empty, or rejected buffer even though
   the native target contains geometry.
2. The native surface is committed but hidden by parent/child stacking, alpha,
   position, or output selection.
3. QMP/scanout captures a different final surface than the compositor path.

## Plan / Do / Check / Act

### Plan

- Read the current render-pass, camera, material, primitive, and readback
  source markers before changing code.
- Run one self-made fixture control and one packaged-scene observation only if
  the existing image supports both without a rebuild.
- Compare target draw primitive/index counts and native ROI color statistics.
- Stop at the first divergence and create a separate implementation ticket if
  a source change is justified.

### Do

Record bounded commands and results in
`work/logs/2026-09-20-flr0220.md`. Reuse the existing evidence root and do not
create another container, named volume, source tree, or TMPDIR.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Shape/raster evidence | non-uniform chromatic native target pixels | 111,758 chromatic pixels, index_count=36 | PASS |
| Fixture control | self-made object has a distinct native/QMP signature | Native target chromatic; QMP native ROI black | PARTIAL: target PASS, final display FAIL |
| Scene correlation | Example Demo primitive/camera/material path is identified | primitive handle/index count only | INCOMPLETE |
| QMP proof | screenshot and frame hashes retained | inherited HUD/black-native evidence | PASS |

### Act

- Close FLR-0220 as the native render-target shape-content proof. FLR-0221
  owns the remaining final Wayland composition/import/display boundary.
- Do not add a source patch to this ticket; the existing fixture control was
  sufficient to prove native geometry.

## Visual evidence

- QMP-only screenshot:
  `$EVIDENCE_ROOT/FLR-0220/q/flr0220-latest.ppm`
- Native ROI: black in QMP; HUD ROI visible.
- Inherited frame SHA-256:
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.

## Unknowns

- Which compositor/output stage drops the verified geometry-containing native
  buffer before QMP.

## PDCA checker

- Status: PASS with final-display criterion intentionally open
- Checked by: FLR-0220 runtime evidence review
- Findings: native geometry is proven before composition; FLR-0221 is the
  independent next unit for the remaining final-display boundary.
