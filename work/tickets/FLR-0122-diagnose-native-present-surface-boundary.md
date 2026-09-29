# FLR-0122 — diagnose the native present and surface-composition boundary

- Status: Waiting
- Priority: High
- Owner: Mini authoritative runtime + Mac persistent Devtool diagnostic roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0121](FLR-0121-align-dart-camera-payload-with-native-v2-contract.md), [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-13-flr0122.md`

## Work unit

Identify the first divergence between a native Filament frame that has a
ready renderable and a QMP-visible 3D pixel in the self-made blue-cube
fixture. This ticket is diagnostic only: it does not claim a production-scene
fix, change lighting/materials, or mix in scene-transition behavior.

## Problem

FLR-0121 removed the Dart/native camera API-generation mismatch. In the fresh
Mini image, the fixture reached `SHAPE_READY renderable=true`, Vulkan queue
submit returned `result=0`, and no coredump occurred. The 2D HUD remained
visible, but the QMP central 3D region was uniform black. The existing runtime
markers do not yet establish whether the rendered result reached
`vkQueuePresentKHR`, a Wayland buffer attach/commit, the expected child-surface
geometry, or the QMP-visible layer.

### Purpose

Separate native render-command completion from present/WSI and compositor
visibility with the smallest evidence set, reusing the fixed Mini build,
single QEMU, and official QMP capture/teardown harness.

### Success measure

The first failing process step is identified with paired evidence, or the
remaining ambiguity is explicitly recorded as UNKNOWN and split into a new
ticket. No source patch is made until the failing step and its owner are
evidence-backed.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Shape and queue submit succeed while 3D pixels stay black | FLR-0121 status and QMP analyses |
| Where | Native Filament frame, Vulkan WSI, Wayland child surface, compositor/QMP path | effective source, bounded runtime markers, QMP region |
| When | After native readiness and first fixture frame | timestamped fixture log |
| Who | Filament view, Vulkan/Wayland integration, compositor and capture roles | source ownership and runtime process map |
| How | Compare paired frame/present/surface events with the same QMP region | one controlled fixture run |

### Priority selection

- Compared strata: camera payload, geometry/material creation, render/submit,
  present/WSI, Wayland surface composition, and QMP capture region.
- Selected focus: present/WSI and surface visibility, because FLR-0121
  directly cleared the camera channel boundary while shape and submit already
  succeed.
- Selection evidence: FLR-0121 QMP central region `0/248000` with
  `renderable=true` and submit `result=0`; historical FLR-0042 proves that the
  project can produce visible fixture pixels through a controlled surface.

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| 1 | scene camera and shape payload | native entity/renderable ready | `SHAPE_READY renderable=true` | FLR-0121 fixture log |
| 2 | frame request | begin/render/end markers paired | begin/end markers exist but draw completion is not yet fully correlated | FLR-0121 fixture log |
| 3 | recorded command buffer | queue submit and present return | queue submit returned `0`; present boundary is not yet proven | FLR-0121 fixture log |
| 4 | presented native buffer | Wayland attach/damage/commit on expected child surface | UNKNOWN | bounded runtime trace |
| 5 | compositor output | nonzero 3D pixels in `[300,250,620,400]` | `0/248000`, uniform black | QMP early/late analyses |

### Problem point

The first confirmed gap is between successful native queue submission and the
expected visible QMP region. The exact sub-step—render output, Vulkan present,
Wayland buffer handoff, compositor stacking, or capture-layer selection—is
UNKNOWN until the bounded trace is collected.

### Ideal condition

The same fixture run produces ordered native frame, queue-present return,
Wayland buffer attach/commit, and QMP central-region nonzero pixels, with no
coredump or residual process.

### Current condition — Facts

- The camera channel errors are absent after FLR-0121.
- The native shape is marked `renderable=true`.
- Vulkan queue submit returns `result=0`.
- QMP sees the 2D HUD but the central 3D region is uniform black.
- QMP teardown is clean; there are no residual QEMU/runqemu/flutter-auto
  targets or QMP socket.
- The accepted runtime launch was performed as the `agl-driver` role with one
  `flutter-auto` process. A prior root launch was retained only as an invalid
  diagnostic comparison, not as acceptance evidence.
- The same valid runtime log contains `FLR0026_VK_END_FRAME_BEGIN` and a
  successful queue submit, but no `FLR0026_RENDERER_COMMIT_ENQUEUE`,
  `FLR0026_VK_COMMIT_BEGIN`, `FLR0026_VK_PRESENT_BOUNDARY_*`, or
  `FLUORITE_VK_PRESENT_*` marker.
- The stripped image binary contains the renderer/commit/present marker
  strings. Their absence in the bounded runtime log is therefore not explained
  by missing instrumentation alone.
- The Mini effective `flutter-auto` source is the v2.0-style
  `ViewTarget::DrawFrame` implementation. It contains the software frame-loop
  start and unconditional `wl_surface_commit`, but it does not contain the
  newer `FLR0026_FRAME_BEGIN/END` markers present in the persistent Mac
  Devtool source.
- The Mini effective Filament source statically calls
  `mSwapChain->commit(driver)` from `FRenderer::endFrame`, and the Vulkan
  driver statically calls `swapChain->present(*this)` from `commit`. This makes
  the missing runtime commit/present markers a meaningful unresolved boundary,
  subject to confirming that the running binary matches this work tree.
- The persistent Mac Devtool native source and Mini effective
  `view_target.cc` are not the same source snapshot. Their recorded SHA-256
  values are `66b4345c01a2f078c065440a646031a5e64308ea09bcabee906a4a8bc491d6c1`
  and `4c9a5e6fdfca9b2c014a054c89825a3afe6598422dd0bb259b432029dd2fb9d8`,
  respectively. The Mac source is on the persistent Devtool diagnostic branch;
  the Mini source is based on upstream `v2.0` plus the layer patch stack.
- The historical visible blue cube in FLR-0042 came from the C++ native
  minimal-geometry fixture. FLR-0121 instead exercises the Dart Example Demo
  fixture path, so the historical native-cube PASS does not prove this Dart
  creation path.

### Gap

The current Dart fixture's frame path is not correlated from `ViewTarget` frame
entry through Filament `endFrame`, renderer commit, Vulkan present, and
Wayland/QMP pixels. The exact first missing step remains UNKNOWN, and source
provenance must be reconciled before a native patch is selected.

### Impact

Further camera, light, or production-scene patches would be low-value and may
mask the actual display boundary. 3D success cannot be claimed.

### Point of occurrence

After queue submit and before a QMP-visible 3D pixel; sub-step UNKNOWN.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| A. The Dart fixture does not enter the native ViewTarget draw/endFrame path | shape and engine command activity exist, but renderer commit/present markers do not appear | add only a source-owned entry/return correlation after source provenance is aligned | LEADING / UNPROVEN | valid FLR-0122 agl-driver run |
| B. The renderer frame reaches submit but commit/present is skipped or uses a different path | submit/end-frame-related markers exist, but renderer/Vulkan commit markers do not | compare the exact linked binary path with the effective source and trace the bounded call seam | OPEN | valid FLR-0122 agl-driver run |
| C. Native buffer is presented but Wayland/compositor handoff or stacking hides it | present and attach/commit exist, but QMP central region remains black | correlate protocol/geometry only after present is proven | OPEN | QMP late region |
| D. QMP central region is not the native surface | native surface pixels appear elsewhere or geometry differs from `[300,250,620,400]` | capture full-frame region map and compare surface geometry | OPEN | QMP full-frame analysis |

### Confirmed root cause

UNKNOWN. The ticket must not promote a successful queue submit or a black
capture into a root-cause claim.

### Minimal countermeasure

First add no product change. Reconcile the Mac persistent Devtool source with
the Mini recipe's effective native source and confirm the linked binary
provenance. Then collect only the bounded ViewTarget/endFrame/commit markers
needed to select A, B, C, or D. If a source-owned process step is identified,
create a separate implementation ticket and use the official Mac Devtool patch
flow there.

## Scope

### In scope

- Effective source/recipe/patch inspection for existing frame, Vulkan present,
  Wayland, and surface-geometry markers.
- One fresh run of the already-built fixture image using the official
  runqemu/QMP harness.
- Minimal guest log, coredump, process, QMP-only screenshot, pixel-region, and
  teardown evidence.
- A decision on the first divergence and a follow-up ticket if needed.

### Out of scope

- Production Sequoia scene, light/material A/B, or scene-transition behavior.
- New camera API, random delay, broad logging, or multiple simultaneous QEMU.
- Hand-editing generated patches or changing the canonical layer before the
  failing process step is identified.

## Success criteria

- [x] Existing markers and effective source path are mapped before any patch;
  the source mismatch and missing runtime commit/present markers are recorded.
- [x] One QMP-only fixture run captures full-frame and central-region metrics;
  exactly one QEMU is launched and cleanly stopped by negotiated QMP quit.
- [x] Paired evidence records the remaining first-divergence ambiguity and
  splits the next comparison into FLR-0123; the exact first source-owned step
  remains UNKNOWN.
- [x] No unsupported camera channel error or coredump is introduced in the
  accepted `agl-driver` run.
- [x] Working log, ticket, evidence IDs, and failure/success observations are
  committed locally; no push is performed.

## Visual evidence

- QMP-only screenshot: `$EVIDENCE_ROOT/flr0113-authoritative/flr0122-36d976a-agldriver/qemu/fixture-qmp-late.ppm`
- Image content: 2D HUD is visible; the designated 3D central region is black.
- Run ID / image identity: `flr0122-36d976a-agldriver`; exact Mini-built
  kernel/rootfs hashes are recorded in FLR-0121 and its working log.
- Pixel result: central region `0/248000`, no edges/chromatic pixels, luma
  `[0,0]`; region SHA-256
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.

## Hypotheses

1. The Dart fixture does not enter the native ViewTarget draw/endFrame path
   (A).
2. The renderer frame reaches submit but commit/present is skipped or takes a
   different path (B).
3. The native buffer is presented but not visible through Wayland/compositor
   handoff or stacking (C).
4. The capture region or layer identity is wrong (D).

## PDCA

### Plan

- Read effective source, recipe patch order, and existing marker definitions.
- Select the minimum bounded runtime probes; do not collect unrelated logs.
- Run one official QEMU fixture, capture QMP early/late plus the required
  marker window, and terminate through QMP.
- Choose the first failing process step; open a new implementation ticket only
  after the diagnosis is evidence-backed.

### Do

- Working-log links only. Raw command output remains in the Mini evidence
  directory.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Source/marker map | complete before patch | Mini source/Filament map complete; Mac/Mini native source mismatch found | working log; Mini work tree | PASS WITH OPEN MISMATCH |
| Single QEMU/QMP run | clean start, capture, quit | one accepted `agl-driver` run; QMP capture and negotiated quit PASS | Mini evidence | PASS |
| First divergence | identified or UNKNOWN split | submit and end-frame-related activity observed; renderer commit/present absent; exact first step UNKNOWN | working log/ticket | UNKNOWN |
| 3D pixel acceptance | nonzero geometry in `[300,250,620,400]` | `0/248000`, uniform black; 2D HUD visible | QMP late analysis | FAIL |

### Act

- Standardize the minimum marker set and continue the source-provenance
  comparison in FLR-0123. No behavior patch is selected from this ticket.

## Decision log

- 2026-09-13: FLR-0121 cleared the camera API-generation error but not the
  3D pixels; present/surface diagnosis is now a separate work unit.
- 2026-09-13: The accepted `agl-driver` run confirmed the 2D/HUD path,
  renderable shape, and queue submit, but no renderer commit or Vulkan present
  marker. Static inspection found that the persistent Mac Devtool native source
  and Mini effective native source are different snapshots. The historical
  FLR-0042 visible cube is a separate C++ native fixture, not this Dart fixture
  path. Root cause remains UNKNOWN; reconcile source provenance before patching.

## Unknowns

- Whether `vkQueuePresentKHR` returns for this current fixture run.
- Whether a Wayland buffer is attached/damaged/committed for the native child
  surface.
- Whether the child surface is above the parent and matches the QMP region.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:
