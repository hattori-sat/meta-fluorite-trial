# FLR-0123 — compare native and Dart fixture entry paths on the current image

- Status: Waiting
- Priority: High
- Owner: Mini authoritative runtime + QMP evidence roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0122](FLR-0122-diagnose-native-present-surface-boundary.md), [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-13-flr0123.md`

## Work unit

Compare the historical C++ native minimal-geometry fixture with the current
Dart Example Demo blue-cube fixture on the same current Mini image. Use one
controlled native-control run, the existing fixed QMP region, and the official
teardown path. Do not change source in this ticket.

## Problem

FLR-0122 found that the current Dart fixture reaches shape readiness and Vulkan
queue submit but its QMP 3D region remains uniform black. FLR-0042 previously
showed visible blue-cube pixels from a C++ native fixture. The two results are
not comparable until the known-good native entry path is checked against the
same current image. A preflight source scan is required before launching a
control so an absent environment-variable handler is not mistaken for a
runtime result.

## Success measure

The native-control result is classified with QMP-only pixels and bounded
runtime evidence:

- native control visible: common image/Vulkan/Wayland/QMP path is alive and
  the remaining failure is isolated to the Dart fixture entry path;
- native control black: current image or native frame/present behavior has
  regressed, so Dart-specific changes are deferred;
- otherwise: the result is explicitly UNKNOWN and split again.

## Facts

- Current Dart fixture baseline: `SHAPE_READY renderable=true`, successful
  Vulkan queue submit, no coredump, 2D HUD visible, and central region
  `[300,250,620,400]` at `0/248000` changed pixels.
- FLR-0042's positive result came from the C++ native minimal-geometry fixture,
  not from the current Dart creation payload.
- The fixed Mini image, build directory, TMPDIR, QEMU profile, and QMP region
  are reused. No second persistent build or container is created.
- The current Mini effective `flutter-auto` source does not contain the
  `NATIVE_MINIMAL_GEOMETRY` or `NATIVE_PURE_FIXTURE` control implementation,
  and the deployed binary does not contain the corresponding setup markers.
- Therefore a QEMU run with only those environment variables would be a
  no-op and cannot classify the native-control path.

## Inferences

- A visible native control on the current image would falsify a global
  compositor/QMP failure and focus the next ticket on Dart-to-ViewTarget
  frame initiation or scene binding.
- A black native control would make the image/native frame or present boundary
  the priority and prevent another Dart patch from masking it.
- Because the current image lacks the native-control implementation, neither
  outcome can be obtained from this image without a source change.

## Hypotheses / UNKNOWN

1. The current C++ native control would produce visible 3D pixels if its
   Devtool-generated implementation were present.
2. The current image source/patch reconciliation removed the control, so the
   historical comparison cannot be replayed yet.
3. UNKNOWN whether the restored control and current Dart fixture will share
   the same surface and frame path until the control is rebuilt.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Native control versus Dart cube has different pixel outcomes | QMP central/full-frame analysis |
| Where | Native fixture code path versus Dart scene creation/ViewTarget path | bounded launch variables and source map |
| When | Same current image, after guest-ready and before teardown | timestamped runtime evidence |
| Who | Native plugin/Filament path versus Dart scene integration | process and marker roles |
| How | One native-control launch using the fixed QMP harness | evidence directory |

## PDCA

### Plan

1. Confirm no QEMU or flutter-auto remains from the prior run.
2. Perform the source-availability preflight. If the control implementation is
   absent, stop without launching QEMU and hand off to FLR-0124.
3. If present, launch exactly one current-image native minimal-geometry control
   with the existing official runqemu/QMP harness and bounded diagnostic
   environment.
4. Capture early/late QMP-only frames and the minimum runtime status.
5. Quit through negotiated QMP, verify zero residual targets/socket, classify
   the native-control result, and only then choose a separate source ticket.

### Do

- Source-availability preflight completed: **FAIL**; the current effective
  source and deployed binary do not contain the native-control implementation.
- QEMU was intentionally **NOT RUN** because an environment-variable no-op
  would not be evidence.
- No source patch, Devtool operation, build, or image change was made in this
  ticket.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Current image identity | exact kernel/rootfs recorded | known from FLR-0121; control not present | FLR-0121 / Mini source scan | BLOCKED BY SOURCE |
| Native control implementation | setup code and marker strings present | absent from current effective source and binary | Mini source scan | FAIL |
| Native control runtime | one process, no coredump, bounded markers | intentionally not run | this ticket log | NOT RUN |
| Native control pixels | central region classified as visible or black | cannot classify before implementation exists | this ticket log | UNKNOWN |
| Teardown | negotiated QMP quit, zero residual targets/socket | no QEMU launched | this ticket log | NOT APPLICABLE |

### Act

- Restore a current-image native control through the official Devtool source
  workflow in FLR-0124, then rerun this comparison as a new ticket.
- Do not infer a global image or compositor failure from this skipped no-op.

## Evidence locations

- `$EVIDENCE_ROOT/flr0113-authoritative/flr0123-native-control/qemu`
- Working log: `work/logs/2026-09-13-flr0123.md`

## Unknowns

- Whether the current image still reproduces FLR-0042's native C++ cube.
- Whether the positive native fixture used a different source/patch provenance
  than the current Mini image.
- Whether the native control uses the same child surface and QMP region.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:
