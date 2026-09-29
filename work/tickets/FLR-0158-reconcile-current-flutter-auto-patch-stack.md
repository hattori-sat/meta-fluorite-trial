# FLR-0158 — reconcile current flutter-auto patch stack baseline

- Status: Waiting
- Blocked by: FLR-0159 rebase 0220 against the resolved current source
- Priority: High
- Owner: Yocto flutter-auto recipe + Devtool baseline role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0156](FLR-0156-restore-pure-fixture-camera-projection.md)
- Working log: `work/logs/2026-09-15-flr0158.md`

## Work unit

Reconcile the current `flutter-auto` source layout with its existing Yocto
patch stack so the registered FLR-0156 camera patch can reach `do_patch`
without hand-editing a generated patch or silently changing the current
source. Preserve one Mini build/TMPDIR and the exact receiver tip.

## Problem

Mini `bitbake -c do_patch -f flutter-auto` stopped at the first existing patch,
`0002-fix-initialize-custom-camera-base-mode.patch`, with `No file to patch`.
The resolved source Git tree contains
`plugins/filament_view/core/components/derived/camera.cc`, while that patch
targets the older
`plugins/filament_view/core/scene/camera/camera.cc` path. The active recipe
source revision is not pinned (`SRCREV=INVALID` in the resolved environment),
so the current v2.0 source layout and historical patch stack have diverged.

## Success criteria

- [ ] Compare the current source revision, the `0002` patch intent, and later
  camera patches to determine whether the old patch is already represented or
  requires an official source-baseline update.
- [ ] Choose and document one official Yocto path (`devtool` baseline import,
  `update-recipe`, or a minimal recipe metadata correction) without editing
  any patch hunk by hand.
- [ ] Make the smallest layer/source change needed for the existing patch
  stack to apply, then prove the resolved patch order with Mini `do_patch`.
- [ ] Keep FLR-0156's `0251` patch unchanged and retain its exact source/layer
  identity; do not start compile/full image/QEMU until `do_patch` is clean.

## Facts

- FLR-0156 bundle handoff passed to the fixed receiver tip
  `8149bcd1d35545c7978e8b77cf605386f1966775`.
- Mini resolved `PN="flutter-auto"`, `PV="2.0"`, `MACHINE="qemux86-64"`,
  `DISTRO="poky-agl"`, and the fixed role `$BUILD_TMPDIR`.
- Resolved `SRC_URI` contains the FLR-0156 patch once at order position 214,
  after the historical camera/material diagnostics.
- The first failing patch is `0002-fix-initialize-custom-camera-base-mode.patch`;
  its header targets `plugins/filament_view/core/scene/camera/camera.cc`.
- The current source Git tree is at a v2.0 commit whose matching camera source
  file is under `plugins/filament_view/core/components/derived/camera.cc`.
- The failed task left only quilt `.pc/` and `patches/` entries in the fixed
  TMPDIR source tree; no new build/TMPDIR/receiver was created.
- After removing only `0002`, the fixed Mini preflight resolved `0002` at count
  0 and `0251` at count 1.
- The next fixed Mini `do_patch` stopped at `0220`: hunk 3 in
  `shell/backend/wayland_vulkan/wayland_vulkan.cc` and hunk 1 in
  `shell/wayland/window.cc` failed. No compile, image build, or QEMU started.
- The resolved source identities are `SRCREV_homescreen=dd6d9224...` and
  `SRCREV_plugins=2163242...`; aggregate `SRCREV=INVALID` remains an
  attribution UNKNOWN. The source Git HEAD is `dd6d9224...`.
- The current Camera constructor has no `mode_` or `eCustomCameraMode_`
  symbols; the old path and symbols are referenced only by `0002` in the
  resolved patch stack. Later camera patches target `view_target.cc` and do not
  depend on the removed constructor.

## Inferences

- The first divergence is the historical patch stack versus current source
  layout, before the new camera projection patch is reached.
- Repeating forced `do_patch` cannot fix this and may preserve misleading quilt
  state; the baseline or source revision must be reconciled first.
- Removing only the obsolete `0002` item is the smallest correction for the
  first boundary, but it does not reconcile the later `0220` source-base
  mismatch. Further source/patch rebase work is a separate ticket.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: `0002` is obsolete because its camera-base behavior is already present in the current source or later patches | current source and later patch history contain the behavior, so removing/replacing only the obsolete recipe entry through an official recipe update lets the remaining stack apply | current source lacks the behavior and later patches depend on `0002`'s exact change |
| H2: the recipe must use the historical source revision matching its patch stack | a pinned historical source revision restores the expected path and the unchanged patch stack applies | the historical revision still lacks the path or breaks later patches |
| H3: the source baseline needs Devtool import/rebase while retaining current source | official Devtool baseline import yields a clean source commit and generated layer patch without hand-edited hunks | Devtool cannot represent the baseline or generated patch changes unrelated source |

## UNKNOWN

- Whether `0002` is redundant, source-revision-specific, or required by later
  patches is not yet proven.
- The correct minimal recipe/source boundary is UNKNOWN until the patch body,
  current camera implementation, and later patch dependencies are compared.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | make the existing flutter-auto patch stack apply to its declared source |
| Where | Mini resolved recipe/source and the Mac Devtool baseline workflow |
| When | before FLR-0156 `do_patch`, compile, image, or QMP validation |
| Who | Yocto recipe/source role and Mac Devtool handoff role |
| How | bounded source/patch comparison, official Devtool/recipe operation, one fixed Mini gate |

## PDCA

### Plan

1. Inspect the `0002` body, current camera source, and later patch references
   without modifying the fixed Mini source or patch files.
2. Compare at least two official reconciliation paths and select the smallest
   one that preserves the current source identity and FLR-0156 patch.
3. Apply the selected source/recipe change through the Mac Devtool/layer flow,
   bundle it to the same receiver, and rerun only `do_patch`.

### Do

- Ticket created after FLR-0156's bounded Mini `do_patch` failure identified an
  old camera path in `0002` versus the current source layout.
- Compared the current source constructor, path history, `0002` body, and later
  patch targets. Selected the H1 recipe-metadata correction and added only
  `SRC_URI:remove` for the obsolete `0002`; FLR-0156's `0251` remains unchanged.
- The H1 metadata bundle reached the fixed receiver at `b7fef3f8...`.
- The bounded preflight passed with `0002` absent and `0251` present once. The
  following single `do_patch` run failed at `0220`; raw evidence is under
  `$RECEIVER/evidence/flr0158/`.

### Check

- H1 metadata, bundle, bounded recipe preflight, and one fixed-Mini `do_patch`
  gate are complete. The gate stops at `0220`, so FLR-0159 owns the rebase.

## Decision

- H1 selected. The old patch is obsolete after the source refactor; do not pin
  a historical source or manufacture a replacement hunk. The next gate is
  recipe parse/order confirmation followed by one fixed-TMPDIR `do_patch`.

### Act

- Keep FLR-0156 Waiting and stop before compile/image/QEMU. Resume this ticket
  only after FLR-0159 produces a clean current-source patch boundary.

## Evidence

- FLR-0156 raw env and task logs: `$RECEIVER/evidence/flr0156/`
- FLR-0156 ticket: [camera projection repair](FLR-0156-restore-pure-fixture-camera-projection.md)
