# FLR-0221 — trace composition of the native geometry buffer

- Status: Done
- Priority: Critical
- Owner: Wayland WSI, compositor, and QEMU scanout roles
- Created: 2026-09-20
- Predecessor: FLR-0220

## Objective

Determine why the native swapchain image proven to contain geometry is
presented and committed successfully but does not appear in the QMP final
frame. Keep this ticket limited to the final composition/import/display
boundary; do not reopen the already-closed native geometry contract.

## Success criteria

- Identify the first boundary after the geometry-containing native image where
  pixels become empty, hidden, or unrelated to the QMP frame.
- Retain one QMP-only screenshot, bounded runtime evidence, and artifact hashes.
- If a source correction is required, create a separate implementation ticket
  and use the locked official Devtool flow from the current effective source
  baseline.

## Facts

- FLR-0220 proved the minimal fixture contract, local camera, indexed draw
  (`index_count=36`), and `111758` chromatic native ROI pixels.
- The same image handle was correlated through current color, draw, readback,
  and present.
- Wayland attach/damage/frame/commit and Vulkan present returned success.
- The paired QMP native ROI remained black while the 2D HUD remained visible.
- In the same QEMU and minimal fixture, enabling the existing
  `FLUORITE_NATIVE_READBACK_TO_SHM=1` bridge produced a QMP native ROI with
  `100800` nonzero and `100800` chromatic pixels.
- The native-only A/B produced a QMP native ROI with `0` nonzero and `0`
  chromatic pixels, while the HUD remained visible.
- Bridge QMP screenshot SHA-256:
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
- Native-only QMP screenshot SHA-256:
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- The first launch attempt failed with status 127 because the recorded bundle
  path was stale. Guest path inspection found the hyphenated package path; the
  corrected launch passed. Both outcomes are retained in the evidence root.
- QMP quit and residual-process cleanup passed.

## Inferences

- The native Filament draw path is no longer the first unresolved boundary.
- A successful Wayland commit alone does not prove that the committed buffer is
  the buffer imported by the compositor or captured by QMP.
- The visible SHM bridge can display the same native geometry data, so the
  compositor and QMP path are not globally unable to display 3D pixels.

## Hypotheses

1. WSI export/import selects a different, empty, or rejected buffer.
2. The native surface is committed but hidden by parent/child stacking, alpha,
   position, or output selection.
3. QMP captures a different final surface than the compositor path.

## Plan / Do / Check / Act

### Plan

- Run one fixed-image A/B using the existing native readback-to-visible-SHM
  diagnostic control, without rebuilding first.
- Compare native probe, Wayland protocol, compositor bounded logs, visible-SHM
  ROI, and QMP ROI in the same run.
- Stop at the first divergence; do not patch a source layer from correlation
  alone.

### Do

Completed with the existing fixed receiver, build/TMPDIR, and QEMU harness;
no new container, named volume, source tree, or TMPDIR was created.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Native geometry input | chromatic native ROI | inherited from FLR-0220 | PASS |
| WSI/Wayland transfer | same non-empty content reaches compositor | native-only remains black; SHM bridge is chromatic | PARTIAL |
| Final QMP display | native geometry visible with HUD | bridge PASS; native-only FAIL | SPLIT |
| Teardown | QMP quit and no residual QEMU | QMP/cleanup PASS | PASS |

### Act

Close FLR-0221 as the A/B boundary proof. FLR-0222 owns restoring native-only
3D display without the diagnostic bridge. Any code change gets its own ticket
and official Devtool rebase/patch evidence.

## Evidence

- Predecessor evidence:
  `$EVIDENCE_ROOT/FLR-0220/flr0220-artifact-sha256.txt`
- New evidence root: `$EVIDENCE_ROOT/FLR-0221/`
- QMP-only screenshots and the artifact hash index are retained before closure.

## UNKNOWN

- Which native WSI/export/import or surface-selection field differs from the
  working SHM bridge path.
- Whether the native-only extent/format path is consistent with the bridge
  path at the compositor boundary.
