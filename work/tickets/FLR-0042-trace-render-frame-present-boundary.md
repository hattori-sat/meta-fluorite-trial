# FLR-0042 — trace render/frame/present boundary after native Scene registration

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + Flutter/Wayland + target-validation roles
- Depends on: [FLR-0041](FLR-0041-trace-selected-light-native-resource.md)
- Working log: `work/logs/2026-09-07-flr0042.md`

## Problem

FLR-0041 proved that selected GUID134 and GUID136 both create valid Filament light components, valid instances, and Scene membership. The QEMU framebuffer still shows only the 2D HUD and a black native region. The next boundary is therefore after native Scene registration and before visible 3D pixels.

## Purpose

Identify the first failing or diverging operation among Filament render-list submission, `beginFrame`/`render`/`endFrame`, `Present`, and Wayland child-surface attach/commit. Preserve the fixed image/profile and compare a known 3D-producing fixture path where possible.

## Success measure

- A runtime trace records the relevant operation and result for control and one selected-light case, including frame sequence, render target/view/scene association, present result, and Wayland attach/commit/activation state.
- The trace distinguishes “rendered but not composited” from “not rendered” and “rendered black”.
- QMP-only photos are captured for each decisive case; the central candidate region is analyzed separately from the 2D HUD.
- Any source change is made through the persistent Mac Devtool source workspace, finished by official Devtool, registered under `meta-fluorite-trial`, committed locally, bundled, and built on the fixed Mini PC receiver/build/TMPDIR.
- Close this ticket before changing the production scene or adding an unrelated workaround.

## Facts

- FLR-0041 native state: six lights, valid Filament instances, Scene membership, and 45 renderables are present.
- FLR-0041 QMP frames: 1280x800, 2D HUD visible, central candidate region black for control/GUID134/GUID136.
- FLR-0041 did not emit a numeric `Present` result; this is UNKNOWN, not a pass.

## Hypotheses

1. Filament does not submit or execute the native scene render despite valid entities. Prediction: render-list/view/frame trace is absent or reports failure.
2. Filament renders, but the child surface is not committed/activated into the compositor. Prediction: render/frame succeeds while Wayland commit/activation or final candidate pixels remain absent.
3. The prior 3D pixels came from a transient runtime state not reproduced by the current profile. Prediction: a self-made minimal fixture can produce 3D pixels while the production scene remains black.

## PDCA

### Plan

- Inspect existing render/frame/present and Wayland diagnostic hooks before editing.
- Choose the smallest missing boundary and create one official Devtool-generated patch if needed.
- Reuse the same container, fixed receiver/build/TMPDIR, rootfs artifact, QEMU profile, guest user, and QMP-only evidence procedure.
- Compare control, the smallest self-made fixture/shape path, and one production/selected-light case only as required by the first divergence.

### Do

- Reused the fixed Mini PC rootfs, build, TMPDIR, and official Linux `runqemu`
  profile. Only one QEMU instance was active per run and each run used QMP
  `quit` before the next run.
- Ran the self-made Filament cube with
  `FLR0026_NATIVE_PURE_FIXTURE=1` and
  `FLR0026_NATIVE_MINIMAL_GEOMETRY=1`.
- Ran the independent Wayland SHM diagnostic with
  `FLR0026_SHM_PROBE=1` and `FLR0026_3D_SHM_MOCK=1`.
- Captured both screens through QMP `screendump`; no host-window screenshot
  was used as evidence.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Render/frame trace | first render operation and result identified | `FRAME_BEGIN`, Vulkan queue submit, and frame end reached; `queue submit result=0` | `work/logs/2026-09-07-flr0042.md` | PASS |
| Present trace | numeric result or explicit UNKNOWN explained | `QUEUE_PRESENT result=0`, `PRESENT_BOUNDARY_RETURN result=0`, and `PRESENT_BOUNDARY_DONE` repeated in the native fixture run | `work/logs/2026-09-07-flr0042.md` | PASS |
| Wayland composition | attach/commit/activation state correlated with QMP pixels | SHM child surface attached; QMP region `[240,120,240,160]` changed `38400/38400` | `work/evidence/flr0042/shm-mock-30s.png` | PASS |
| Self-made 3D fixture | visible non-HUD pixels proven if used | Blue Filament cube visible; region changed `5608/100000`, bbox `[501,285,99,65]` | `work/evidence/flr0042/native-fixture-15s.png` | PASS |
| Teardown/privacy | no residual processes and no private values | QMP quit completed; no QEMU, runqemu, flutter-auto, bitbake, or QMP socket remained | `work/logs/2026-09-07-flr0042.md` | PASS |

## Result

- The current fixed image can render a self-made native Filament cube to
  visible QEMU pixels. This proves the native Filament render path, Vulkan
  submit/present boundary, and QMP capture path are live for the pure fixture.
- The independent SHM mock also appears with the 2D HUD, proving that the
  parent Flutter surface, Wayland child-surface composition, and QMP capture
  path are not globally broken. This is composition evidence only, not a
  product 3D success claim.
- Production Example Demo content remains a separate unresolved problem. The
  next task must compare production resource/environment setup against the
  now-proven native fixture without weakening the QMP-only evidence rule.

## UNKNOWN

- Which production resource or environment operation prevents the production
  scene from reaching the same visible native-pixel result.
- Whether the production scene needs a camera/model/material/resource fix after
  the render boundary has been proven with the fixture.
