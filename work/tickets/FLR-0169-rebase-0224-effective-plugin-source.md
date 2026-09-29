# FLR-0169 — rebase 0224 on the effective post-0226 plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0168](FLR-0168-rebase-0226-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0169.md`

## Work unit

Reconcile `0224-reconcile-async-indirect-light-snapshot-with-current-plugin-api-devtool.patch`
with the effective `ivi-homescreen-plugins` source after 0226. Use the fixed
Mac Devtool source and the official component-scoped `update-recipe` path.

## Problem

Mini `do_patch` passed 0226 but stopped at 0224 hunk 1 / line 54. The old 0224
patch expects older `GetStrand`/raw callback context, while the effective source
uses current `getStrand()` and `getSystem()` APIs.

## Success criteria

- [x] Record the exact 0224 failure and bounded task output.
- [x] Confirm the effective target source identity from the fixed Mini TMPDIR.
- [x] Remove the duplicate Devtool registration for the shared source path.
- [x] Import the effective source into the existing fixed Mac Devtool tree and
  commit the baseline through the source Git wrapper.
- [x] Edit only the intended async snapshot change and commit it through the
  source Git wrapper.
- [x] Generate one official component-scoped patch and replace the stale 0224.
- [x] Commit layer/lock/ticket/log, hand off one bundle, and prove Mini
  `do_patch` advances beyond 0224.

## Facts

- Initial corrected 0226 run used canonical commit `3b1a347` and passed 0226;
  it stopped at 0224 hunk 1 / line 54. Evidence is
  `$RECEIVER/evidence/flr0168/do_patch-flr0168.stdout`.
- The effective Mini `indirect_light_system.cc` SHA-256 is
  `022839b0128e5236e80ba97abf96bc887fb803b611bc64122703acfb92788845`.
- Before cleanup, `devtool status` showed both `fluorite-plugins` and
  `flutter-auto` registered to the same source path. The stale `flutter-auto`
  entry was removed with official `devtool reset --no-clean`; source Git was
  preserved.
- Effective baseline commit: `50251efce49724cb7115d96986b8a3708dbe1a2d`.
- Source change commit: `71c8fd6b6a0ee8c21df99f5e6a2eff3c1e230eca`.
- Official `update-recipe` generated the replacement patch with SHA-256
  `3533061e07e86674a46725f624e12873d713b9f565ded94eef468a5324a66f81`.
- The committed bundle was handed off through the fixed receiver. Mini
  `do_patch` applied 0224 and advanced to 0229; 0229 is a separate source
  rebase boundary now owned by a follow-up ticket.

## Inferences

- The old 0224 failure was stale context, not proof that the async snapshot
  change is invalid.
- The one-recipe/one-source invariant is required before `update-recipe` so the
  selected workspace recipe is deterministic.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0224 has stale context | regenerated official patch applies after 0226 | Mini still fails at the same 0224 context |
| H2: duplicate registration caused recipe ambiguity | reset leaves one active recipe and official generation is stable | status still shows multiple recipes for the source |
| H3: copied async values are API-compatible | patch passes and later compile accepts it | compile rejects the current API usage |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | Rebase 0224 async indirect-light snapshot |
| Where | Fixed Mac Devtool source and canonical meta-fluorite-trial layer |
| When | After corrected 0226, before compile/image/QEMU |
| Who | Plugin source, Devtool, and Mini BitBake roles |
| How | one-to-one status → effective baseline → official update-recipe → do_patch |

## PDCA

### Plan

1. Keep one fixed container, source tree, receiver, build, and TMPDIR.
2. Enforce one active Devtool recipe per source path.
3. Generate 0224 from the effective post-0226 source and run only the bounded
   Mini patch gate.

### Do

- Removed the stale duplicate `flutter-auto` registration with official
  `devtool reset --no-clean`; the source tree and committed source history were
  preserved.
- Imported the Mini effective target into the same fixed Mac source tree and
  committed the baseline as `50251ef...`.
- Edited only the current-API async snapshot logic and committed it as
  `71c8fd6...`.
- Official component rebase passed, validated registration, replaced 0224, and
  refreshed the baseline lock.

### Check

- Generated patch contains only the intended `indirect_light_system.cc` change;
  Mini revalidation passed through 0224 and stopped at the 0229 boundary.
- The wrapper now rejects multiple active recipes for one source path before
  `component-reset`/`update-recipe`.
- The source commit wrapper stages with `git add .` only after proving exactly
  one expected changed path.

### Act

- The fixed Mini gate passed 0224 and stopped at the independent 0229
  context boundary. Move the reusable gate improvement to FLR-0170 and do not
  start compile, image, or QEMU from this ticket.
- Do not start compile, image, or QEMU until the complete patch stack applies.

## Evidence

- Initial failure: `$RECEIVER/evidence/flr0168/do_patch-flr0168.stdout`.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3150418`.
- Official replacement patch:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0224-reconcile-async-indirect-light-snapshot-with-current-plugin-api-devtool.patch`.
- Mini result: `do_patch` passed 0224 and stopped at 0229 hunk 2; the bounded
  output and exact task log remain under the fixed receiver evidence role.
