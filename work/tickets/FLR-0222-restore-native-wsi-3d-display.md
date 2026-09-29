# FLR-0222 — restore native WSI 3D display without the diagnostic bridge

- Status: Waiting
- Priority: Critical
- Owner: native WSI/export/import and surface-selection role
- Created: 2026-09-20
- Predecessor: FLR-0221

## Objective

Make the verified native geometry visible in the normal native-only QMP frame,
without relying on `FLUORITE_NATIVE_READBACK_TO_SHM`. Keep the existing SHM
bridge as a control only; it is not the production fix.

## Success criteria

- Native-only QMP shows the same 3D geometry and 2D HUD in one frame.
- The native and bridge paths expose consistent extent, format, buffer/surface
  identity, and commit/output-selection evidence.
- Any source change is produced from the current effective Devtool baseline,
  applied through the official recipe flow, and verified on the fixed Mini
  image with QMP-only evidence.

## Facts

- FLR-0220 proves `111758` chromatic pixels in the native render target.
- FLR-0221 proves the SHM bridge displays `100800` chromatic pixels in QMP.
- FLR-0221 native-only QMP remains `0` chromatic pixels with the HUD visible.
- With `FLUORITE_NATIVE_VISIBLE_SHM_CUBE=1` but without the readback bridge,
  the initialization roundtrip changed the fallback extent to `1280x800`, and
  the native target still reported `111758` chromatic pixels. QMP pixels
  outside the SHM child region remained zero, so extent initialization alone
  did not prove native WSI visibility.
- QMP teardown and fixed-image reuse are deterministic; no new container,
  source tree, build directory, or TMPDIR is allowed.

## Hypotheses

1. Native WSI export/import or compositor import selects an empty/different
   buffer even though Filament renders into the verified image.
2. Native-only surface extent/format/layout or alpha differs from the working
   SHM bridge and causes the compositor to omit the geometry.
3. Native surface role/stacking/output selection differs from the SHM control.

The extent-only discriminator is now lower priority: the SHM initialization
roundtrip changes `1280x720` to `1280x800`, but the visible pixels are still
only the SHM child and not independently verified native WSI content.

## Plan / Do / Check / Act

### Plan

- Compare native-only and bridge runtime markers for image identity, extent,
  format, layout, surface, and output selection.
- Locate the first divergence with bounded logs before editing source.
- If a patch is required, use the current Devtool source commit, commit source
  first, run `devtool update-recipe`, register only the generated patch in
  `meta-fluorite-trial`, then bundle to Mini and run do_patch/do_compile/image.

### Do

Completed the extent-only runtime discriminator. It did not produce a native
WSI pixel proof, so the production correction remains open.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Native target geometry | chromatic native pixels | `111758` | PASS |
| Bridge control | chromatic QMP ROI | `100800` | PASS |
| Native-only QMP | chromatic QMP ROI | `0` in FLR-0221 | FAIL |
| Extent-only discriminator | native pixels outside SHM child | `0`; chosen extent `1280x800` | FALSIFIED |
| Production correction | native-only QMP geometry | UNKNOWN | NOT CHECKED |

### Act

Do not close until native-only QMP contains the geometry and the result is
recorded with a QMP-only screenshot, bounded logs, and hashes.

## Evidence

- Predecessor A/B evidence:
  `$EVIDENCE_ROOT/FLR-0221/flr0221-artifact-sha256.txt`
- New evidence root: `$EVIDENCE_ROOT/FLR-0222/`

## UNKNOWN

- The exact native WSI/compositor field that differs from the bridge path.
- Whether the correction belongs in Flutter surface setup, Filament native
  target setup, or compositor/output selection.

## Pause reason

Native-only QMP restoration remains open, but production-scene and input
transition behavior can be verified independently through the already-proven
readback-to-SHM control. FLR-0223 owns that separate validation unit.
