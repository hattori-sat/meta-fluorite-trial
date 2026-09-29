# FLR-0168 — rebase 0226 on the effective post-0225 plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0167](FLR-0167-rebase-0223-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0168.md`

## Work unit

Reconcile `0226-unify-post-renderable-shape-insertion-and-readiness-trace-devtool.patch`
with the effective `ivi-homescreen-plugins` source after 0225. Reuse the fixed
Mac Podman Devtool source and official component-scoped `update-recipe`; do not
hand-edit the generated patch.

## Problem

The corrected 0223 patch applies on Mini, but the next patch boundary, 0226,
fails at its only hunk around `ShapeSystem::addShapeToScene`. The old patch
expects `GetGuid()` and an older source context, while the effective source
uses `getGuid()` and the current scene insertion path.

## Success criteria

- [x] Record the exact 0226 failure and bounded task output.
- [x] Import the effective post-0225 target source into the existing fixed Mac
  Devtool source tree and commit that baseline through its source Git wrapper.
- [x] Edit only the intended post-build scene insertion/readiness trace change
  and commit it through the Devtool source Git wrapper.
- [x] Generate one official component-scoped patch and register it unchanged.
- [x] Commit the layer/lock, hand off one bundle, and prove Mini `do_patch`
  advances beyond 0226.
- [ ] Run compile/image/QEMU only after the complete patch stack gate passes.

## Facts

- Mini `do_patch` using canonical commit `0c738e2` passed through 0223 and
  stopped at 0226 hunk 1 at line 156; the bounded output is
  `$RECEIVER/evidence/flr0167/do_patch-flr0167.stdout`.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3147852`.
- The stale 0226 patch expected `shape->GetGuid()` and pre-build
  `filamentScene->addEntity(oEntity)`. The effective source uses
  `shape->getGuid()` and the current post-0225 body.
- The Mini effective target file was copied to the existing fixed Mac Devtool
  source tree and has SHA-256
  `621d758a2bf0851b7ed18bfc9cea9fc8e4f2505d443a73dca5e177db2142021b`.
- The effective baseline was committed in the Devtool source Git as
  `86e90374322b94c823d58938b513b7a15c9041f2`; the intended change was then
  committed as `6a162ae6ab9df768581b8161535a56e2ed39efb0`.
- Official component rebase generated one patch and replaced the old
  canonical 0226 with SHA-256
  `97323c0d428fbecc008a284f48e09489a122bcdebba7e3174d2fb8a494e9cfe6`.
- Commit `3b1a347c3ab6e97f39b6b25d49ebc9b3295467e8` was handed off with bundle
  SHA-256 `5b65f0908539313f17c094295b4a09950c96fb2f37fa1794fef6234337d6eee9`.
- Mini `do_patch` passed 0226 and stopped at 0224 hunk 1 / line 54 in
  `indirect_light_system.cc`; bounded output SHA-256 is
  `ab51b1d1de383d123ca6e1171065c96f1d73c566dd08965df4b506e387cb370d`.

## Inferences

- The 0226 failure is another stale patch-context boundary, not evidence that
  the intended shape readiness change is semantically invalid.
- The effective-source import method is now repeatable across 0222, 0223, and
  this 0226 boundary when the Mini source is treated as the post-patch truth.
- A separate fixed-workspace audit found duplicate active Devtool registrations
  for the same source path; the stale `flutter-auto` registration was removed
  with `devtool reset --no-clean`, leaving one component registration.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0226 has stale source context | regenerated official patch applies after 0223/0226 predecessor state | regenerated patch still fails at the same context |
| H2: post-0225 source is divergent or partial | imported Mini target differs from the fixed Devtool baseline after copy | byte identity or clean patch gate fails |
| H3: the readiness trace calls an unavailable current API | `do_patch` passes but later compile rejects `_rcm->hasComponent` or the trace call | compile accepts the generated source |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | Rebase 0226 post-renderable insertion/readiness trace |
| Where | Fixed Mac Devtool source and canonical meta-fluorite-trial layer |
| When | After corrected 0223 passes, before compile/image/QEMU |
| Who | Plugin source, Devtool, and Mini BitBake roles |
| How | bounded failure → effective-source import → official update-recipe → fixed do_patch |

## PDCA

### Plan

1. Preserve the single fixed Devtool container/source state and Mini
   receiver/build/TMPDIR.
2. Use the post-0225 target file from the Mini patch workspace as the effective
   baseline.
3. Edit only the 0226 intended change in the existing Devtool source, commit it
   through the wrapper, and generate the official patch.
4. Commit the canonical layer/lock/ticket/log, hand off one bundle, and rerun
   only the bounded Mini patch gate.

### Do

- Reused `fluorite-mac-devtool`, its fixed state bind, and the existing source
  path; no new container, volume, source tree, TMPDIR, or index file was made.
- Imported the Mini effective `shape_system.cc` and committed the baseline
  through `source-git-commit-baseline`.
- Applied the intended change with the current `getGuid()` API and committed
  only that file through `source-git-commit`.
- Ran the official component-scoped rebase with explicit replacement after
  registration validation; it passed and refreshed the baseline lock.

### Check

- Official generation output: `component-rebase=PASS` for FLR-0168.
- Generated source commit: `6a162ae6...`; baseline: `86e90374...`.
- Mini revalidation passed 0226 and advanced to 0224; the next boundary is
  tracked separately in FLR-0169.

### Act

- Closed 0226 after the corrected Mini patch gate advanced to 0224. FLR-0169
  owns the next boundary and must retain the one-recipe/one-source invariant.

## Evidence

- Initial 0226 failure: `$RECEIVER/evidence/flr0167/do_patch-flr0167.stdout`.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3147852`.
- Regenerated canonical patch:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0226-unify-post-renderable-shape-insertion-and-readiness-trace-devtool.patch`.
- Corrected Mini gate:
  `$RECEIVER/evidence/flr0168/do_patch-flr0168.stdout`.
