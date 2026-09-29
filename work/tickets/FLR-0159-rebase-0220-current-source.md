# FLR-0159 — rebase 0220 against the resolved current source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto source baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0158](FLR-0158-reconcile-current-flutter-auto-patch-stack.md)
- Working log: `work/logs/2026-09-15-flr0159.md`

## Work unit

Reconcile the existing `0220` parent-alpha/AGL-normal patch with the resolved
current `flutter-auto` source using the persistent Mac Devtool workspace and
official Yocto patch-generation operations. Preserve the behavior under test,
the current source identity, the `0002` removal, and FLR-0156's unchanged
`0251` camera patch.

## Problem

After FLR-0158 removed the proven-obsolete `0002` recipe item, the fixed Mini
`do_patch` reached `0220` and failed. The current source is based on
`SRCREV_homescreen=dd6d9224de807e24f0f9150e5a2e4ee1b896ac3c` and
`SRCREV_plugins=2163242e9973336153871ed63b34bb5ed8282145`, while `0220`
was generated against an older source preimage. Its Vulkan barrier hunk and
Wayland window hunk do not apply. Removing `0220` without evidence could
reintroduce the exact parent-alpha/AGL-normal composition defect being
investigated.

## Success criteria

- [x] Record the current source revision and the exact `0220` preimage mismatch
  using bounded source/patch evidence.
- [x] Compare two official reconciliation paths: pinning the historical source
  versus importing the resolved current source into the persistent Devtool
  baseline and regenerating the behavior-preserving patch. Select one with
  build-time, runtime, packaging, and integration risk recorded.
- [x] Use Yocto Devtool `modify`/`update-recipe` or `finish --mode patch` as
  applicable; do not hand-edit the `0220` patch hunk.
- [x] Register only the unchanged official output in `meta-fluorite-trial`,
  keep `0002` removed and `0251` byte-identical, and commit the layer state.
- [ ] Prove resolved patch order and pass one fixed-Mini `flutter-auto do_patch`
  gate before resuming FLR-0158 or starting compile/image/QEMU.

## Facts

- FLR-0158's bounded Mini preflight found `0002` count 0 and `0251` count 1.
- The fixed Mini `do_patch` stopped at `0220` with hunk 3 failure in
  `shell/backend/wayland_vulkan/wayland_vulkan.cc` and hunk 1 failure in
  `shell/wayland/window.cc`.
- The exact raw task log is outside Git at
  `$RECEIVER/evidence/flr0158/do_patch-h1.log`; no compile, image, or QEMU
  started after this failure.
- The resolved source Git HEAD is
  `dd6d9224de807e24f0f9150e5a2e4ee1b896ac3c`. The aggregate `SRCREV=INVALID`
  remains an attribution UNKNOWN, while the component revisions are available
  in the raw recipe environment.
- The current `window.cc` already has `m_output_index`, but its constructor
  still registers `WINDOW_NORMAL` as a no-op and sends background/panel calls
  to output `0`. The current Vulkan preimage uses
  `VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT`, while `0220` expects `0`.
- `0220` adds behavior for parent-alpha clearing and AGL normal/output
  registration. That behavior is not proven redundant.
- The current-source Devtool baseline was imported into the existing
  `flutter-auto-reconcile` workspace from common ancestor
  `bc85acbad58b61da5fbfa97926c267ddb8e07abc`; the source behavior commit is
  `4d1f0c04da1eb18735eec8def1aec37c68c6c5ab`.
- Official Devtool finish generated one patch for source HEAD
  `4d1f0c04da1eb18735eec8def1aec37c68c6c5ab`. The canonical replacement patch
  is registered once, has SHA-256
  `3ef3f61321c361b3ea894efa2ae2e4e2e6b8ab555de7d5dfc77a6dc1eecacead`, and the
  old 0220 patch file is removed from the layer.
- The bundle handoff reached the fixed receiver at `e003c11...`; the bounded
  Mini preflight resolved the current 0220 once, the obsolete 0002 zero times,
  and 0251 once, in that order.
- The single fixed-Mini `do_patch` run applied 0220 and stopped at the next
  independent patch, 0221, in the nested `ivi-homescreen-plugins` component.
  No compile, image build, or QEMU started.

## Inferences

- The 0220 failure is a source-baseline/context mismatch, not evidence that
  parent-alpha or AGL-normal behavior is unnecessary.
- Pinning the old source may make the old patch apply, but it would discard the
  resolved current source and risks invalidating the current camera/plugin
  contract. Current-source rebase is the lower integration-risk path if it can
  be represented by official Devtool output.
- The exact source component boundary is currently UNKNOWN: the root
  `flutter-auto` tree owns `0220`, while FLR-0156's `0251` targets the nested
  `ivi-homescreen-plugins` component.
- The current-source rebase preserves the current root source and changes only
  the four 0220 behavior files. Pinning has lower immediate patch work but
  higher source/runtime integration risk; H1 is selected.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0220 is behavior-preserving but stale-context | current-source Devtool rebase regenerates one patch with the same parent-alpha/AGL-normal intent and the next `do_patch` advances beyond 0220 | regenerated output drops required behavior or still fails against the resolved source |
| H2: the recipe must use the historical source baseline | pinning the source revision makes the unchanged patch stack apply without losing required current behavior | current source or later patches remain required, or a historical pin causes later failures |
| H3: 0220 contains independent obsolete pieces | bounded source comparison proves one or more behavior branches already exist and can be removed only after evidence | current source lacks the branches and runtime composition depends on them |

## UNKNOWN

- Whether the resolved source can be materialized in the existing persistent
  Devtool workspace without replacing or duplicating state is UNKNOWN.
- Whether later patches after 0220 have additional source-baseline mismatches is
  UNKNOWN until the first corrected gate advances.
- `SRCREV=INVALID` is not yet attributable to one recipe/provider cause.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Rebase the 0220 behavior onto the resolved current flutter-auto source |
| Where | Mac persistent Devtool source/state and canonical layer patch registration |
| When | After FLR-0158's 0002 boundary and before compile/image/QEMU |
| Who | Yocto source-baseline role, Mac Devtool role, Mini BitBake role |
| How | bounded comparison, official Devtool generation, one fixed Mini do_patch gate |

## PDCA

### Plan

1. Use the exact Mini source identity and 0220 failure as the baseline record.
2. Compare historical pin versus current-source Devtool rebase; select the
   smallest behavior-preserving official path.
3. Reuse the persistent Podman container/state and existing source workspace;
   do not create a ticket-specific volume, TMPDIR, or source copy.
4. Register the generated patch unchanged, commit, bundle to the fixed Mini
   receiver, and run only the bounded recipe preflight and `do_patch` gate.

### Do

- Created after FLR-0158's one bounded `do_patch` run advanced past `0002` and
  stopped at the independent `0220` source-context mismatch.
- Imported the current root source from the fixed Mini TMPDIR using a single
  bounded Git-diff artifact after Git bundle generation proved empty under the
  source's alternate-object layout. No duplicate TMPDIR or source directory
  was created.
- Created the source baseline on branch
  `devtool-flr0159-0220-current-baseline`, registered it with official
  `modify --no-extract`, edited only the four source files, and committed
  source behavior as `4d1f0c04da1eb18735eec8def1aec37c68c6c5ab`.
- Fixed the Devtool wrapper's end-of-line recipe status matcher and added a
  macOS-compatible contract test. The test passes.
- Generated the replacement with official `devtool finish --mode patch` via
  the bounded helper, copied it byte-for-byte, moved its registration to the
  original 0220 order position, and removed the stale patch file.

### Check

- PASS for this work unit: the current-source 0220 patch is registered once,
  the Mini preflight resolves it in the expected order, and the one bounded
  `do_patch` run advances beyond 0220. The next failure is 0221 and is tracked
  separately as FLR-0160.

### Act

- Mark this 0220 unit Done and keep FLR-0158/FLR-0156 Waiting. FLR-0160 owns
  the next 0221/current-plugin boundary; do not compile, build an image, or
  start QEMU until the remaining patch gates pass.

## Evidence

- FLR-0158 ticket/log for the preceding `0002` reconciliation.
- Raw Mini task evidence: `$RECEIVER/evidence/flr0158/do_patch-h1.log`
- Raw Mini preflight: `$RECEIVER/evidence/flr0159/recipe-env-after-rebase.log`
- Raw Mini task summary: `$RECEIVER/evidence/flr0159/do_patch-current-0220.summary`
- Raw Mini task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3138799`
- Next patch boundary: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
