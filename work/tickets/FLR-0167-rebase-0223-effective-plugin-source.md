# FLR-0167 — rebase 0223 on the effective post-0222 plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0167.md`

## Work unit

Reconcile `0223-reconcile-transparent-swapchain-with-current-plugin-api-devtool.patch`
with the effective `ivi-homescreen-plugins` source after 0222. Use the existing
fixed Mac Devtool source and official component-scoped `update-recipe`; do not
hand-edit the generated patch.

## Problem

The corrected 0222 patch now applies on Mini, but the next patch boundary,
0223, fails at its only hunk around `InitializeFilamentInternals`. The old
0223 patch expects `const auto engine`, while the effective source uses the
current `_engine` member.

## Success criteria

- [x] Record the exact 0223 failure and bounded task log.
- [x] Compare the failed hunk with the effective post-0222 source.
- [x] Confirm the fixed Mac Devtool source and Mini effective source identity.
- [x] Edit only the transparent swapchain call from the effective baseline.
- [x] Generate one official component-scoped patch and register it unchanged.
- [x] Commit the layer/lock, hand off the bundle, and prove Mini `do_patch`
  advances beyond 0223.

## Facts

- Corrected 0222 passed on Mini. The corrected 0223 patch also passed; the
  next first failure is 0226, with one hunk failing at line 156 and no later
  hunk.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3145820`.
- Bounded output: `$RECEIVER/evidence/flr0160/do_patch-flr0160-corrected.stdout`.
- Corrected 0223 bounded output: `$RECEIVER/evidence/flr0167/do_patch-flr0167.stdout`;
  SHA-256 `362d5559704b4d3be99577d464656a5ef0c286f03d55f682095b7ae71749170e`.
- Exact next task log: `log.do_patch.3147852`; first failing patch 0226,
  hunk line 156.
- The 0223 patch changes
  `createSwapChain(&native_window_)` to use
  `filament::SwapChain::CONFIG_TRANSPARENT`, but its context expects an older
  `const auto engine` spelling.
- After 0222, the Mini and fixed Mac Devtool target file both have SHA-256
  `3a4224b84ed63f31e68e0b08a076e04dce8ff1195e86d5b9cf78dfc0e68327ab`.
- No compile, image build, or QEMU was started after the corrected 0223 gate;
  those remain outside this patch-stack boundary.

## Inferences

- 0222's effective-source baseline method is validated: the same target file
  exists byte-for-byte on Mac and Mini after 0222.
- 0223 was an independent stale-context patch and was regenerated from the
  existing post-0222 Devtool source history. The same method advanced the
  stack through 0223 and exposed 0226 as the next independent stale-context
  patch.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0223 has stale source context | effective source has `_engine` and official rebase produces one transparent swapchain patch | effective source already contains transparent configuration |
| H2: 0222 left a partial or corrupt source | Mac/Mini post-0222 hashes differ or target contains partial hunk | hashes match exactly |
| H3: the transparent API is unavailable | source headers or build API reject the official call | the change is generated and later `do_patch` passes 0223 |

## PDCA

### Plan

1. Preserve the single fixed Devtool source/state and fixed Mini build.
2. Use the post-0222 source commit as the effective baseline.
3. Edit only the 0223 swapchain configuration, commit through the Devtool
   wrapper, and generate the official patch.
4. Commit canonical patch/lock, hand off one bundle, and rerun only the
   bounded preflight and `do_patch` gate.

### Do

- Read the exact 0223 failure and compared the only failed hunk with the Mini
  source. The context mismatch is `const auto engine` versus `_engine`.
- Confirmed the existing fixed Mac Devtool source is already byte-identical to
  the Mini post-0222 source. The common effective baseline is source commit
  `956b5e44...`.

### Check

- The 0223 source edit was committed through the wrapper as
  `9e690ddc56d1ab950bbbf8d9a361fb0e5fc59c55` from effective baseline
  `956b5e44...`.
- Official standard `update-recipe` generated one patch with SHA-256
  `73e07fde5bb4048659d3a3f4f1503b61fcd35632adaf9f86df8350cfa478ccdb`.
  Registration validation and baseline lock refresh passed; the generated
  diff contains only the transparent swapchain call change.
- The corrected 0223 patch was handed off in bundle
  `7cf0bc3ed80e264cf791d9f0c9a26370fc1e4040bfb35cae440b76319a3d2b05` and
  Mini `do_patch` passed 0223 before stopping at 0226. Compile, image build,
  QEMU, and 3D pixel acceptance remain out of scope until the remaining patch
  stack is reconciled.

### Act

- Closed 0223 after the corrected Mini `do_patch` gate advanced to 0226.
  FLR-0168 owns the next boundary; it must import the post-0225 effective
  source into the same fixed Devtool workspace before editing.

## Evidence

- Fixed-Mini corrected 0222 task output:
  `$RECEIVER/evidence/flr0160/do_patch-flr0160-corrected.stdout`
- Exact 0223 task log:
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3145820`
- Effective target identity: SHA-256
  `3a4224b84ed63f31e68e0b08a076e04dce8ff1195e86d5b9cf78dfc0e68327ab` on both
  fixed Mac Devtool source and Mini post-0222 source.
- Regenerated canonical 0223 patch:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0223-reconcile-transparent-swapchain-with-current-plugin-api-devtool.patch`
- Mini corrected 0223 gate:
  `$RECEIVER/evidence/flr0167/do_patch-flr0167.stdout`.
