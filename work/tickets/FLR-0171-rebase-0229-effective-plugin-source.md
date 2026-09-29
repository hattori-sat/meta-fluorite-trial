# FLR-0171 — rebase 0229 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0170](FLR-0170-deterministic-mini-recipe-patch-gate.md)
- Working log: `work/logs/2026-09-15-flr0171.md`

## Work unit

Rebase `0229-diag-isolate-explicit-light-contribution-current-plugin-devtool.patch`
on the exact effective source after the patches through 0224. Use the fixed Mac
Podman Devtool source and the deterministic Mini recipe patch gate.

## Problem

The fixed Mini patch gate applies the corrected stack through 0224, then 0229
fails at hunk 2 in `plugins/filament_view/core/systems/derived/light_system.cc`.
Hunk 1 succeeds with fuzz 2, so the existing patch has stale context against
the current effective source and must be regenerated through Devtool.

## Success criteria

- [x] Capture the exact effective 0229 target source and hash from the fixed
  Mini TMPDIR.
- [x] Verify one active Devtool recipe for the selected source path.
- [x] Import the effective source as a baseline through the source Git wrapper.
- [x] Apply only the intended 0229 diagnostic change and commit it through the
  wrapper's `git add .` → staged-path check → `git commit` sequence.
- [x] Generate one official component-scoped Devtool patch and register it in
  `meta-fluorite-trial` without hand-editing the generated patch.
- [x] Hand off one local commit and run the deterministic Mini recipe gate.
- [x] Prove Mini `do_patch` applies 0229 and advances to the next boundary.

## Facts

- FLR-0170's deterministic gate passed preflight and reproduced the 0229
  boundary with bounded output.
- The selected task log is `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3162127`.
- No compile, image, QEMU, or runtime claim follows from this patch failure.
- The effective target `light_system.cc` SHA-256 is
  `dd42080f7dc94bfc8c1a522e17ae899d16ef7daf276a1ecfdd0308df6e009ae3`.
- The official component rebase used baseline
  `ff065c98d2c5babe99e9cf95cc323cf26778451c` and source commit
  `4808e4f30cb16c375594cd74cc5a404c4f32e997`.
- The generated canonical 0229 patch SHA-256 is
  `ab9c26fa4e794a167451fc5826bbf1b781a6efc1bbe360faf21a073ec7b58f95`.
- The bundle handoff reached receiver revision `5993e700...`; Mini
  `do_patch` applied 0229 and stopped at 0231 hunk 1 in
  `filament_view_plugin.cc`.

## Inferences

- 0229 is the next independent stale-context boundary after the successful
  0224 rebase.
- The patch-generation workflow is now reusable; this ticket should contain
  only the source rebase and its application proof.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0229 has stale context | an official patch from the effective source applies after 0224 | regenerated patch fails at the same hunk |
| H2: one-to-one Devtool registration is sufficient | status has one recipe for the source path and update-recipe is stable | duplicate registration remains |
| H3: diagnostic change remains API-compatible | do_patch advances beyond 0229 and compile is the next gate | do_patch advances but compile rejects the current API |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0229 light diagnostic patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0224, before compile/image/QEMU |
| Who | plugin source, Devtool, and Mini BitBake roles |
| How | effective source → source commit → official update-recipe → recipe gate |

## PDCA

### Plan

1. Read the 0229 task log and inspect only the target source/function.
2. Import the exact effective source into the fixed Devtool component baseline.
3. Recreate the intended diagnostic change, generate the official patch, and
   run one Mini recipe gate.

### Do

- Imported the exact effective source file from the fixed Mini TMPDIR and
  committed the baseline through the source Git wrapper.
- Created the intended environment-gated direct-light diagnostic change and
  committed it through the wrapper's guarded `git add .` sequence.
- Official component rebase passed, replaced the stale 0229 patch, and refreshed
  the baseline lock. The helper also handled the valid post-reset unregistered
  component state.

### Check

- The generated patch changes only `light_system.cc`, uses current lower-case
  APIs, and preserves the intended diagnostic behavior.
- Mini application proof passed for 0229. The first remaining boundary is
  0231 and is owned by FLR-0172.
- Compile/image/QEMU remain intentionally unstarted.

### Act

- Commit the canonical patch and wrapper improvements, hand off one bundle, and
  run the deterministic Mini recipe gate once. Completed; the next source
  boundary is split to FLR-0172.

## UNKNOWN

- The exact 0229 effective source semantics after preceding patches are
  now recorded by the imported target hash and source baseline.
- Whether the diagnostic change fixes the runtime light state is UNKNOWN and
  belongs to a later compile/runtime ticket.

## Evidence

- Predecessor gate summary: fixed receiver evidence role for FLR-0170.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3162127`.
- Official component rebase: `component-rebase=PASS`; canonical registration
  and baseline lock refresh both passed.
- Bundle SHA-256: `f71e26475fec76ebd8c132863e65fb94ed52b5a68e2a624cee655db72117147b`.
- Mini gate summary SHA-256: `5c2f10998d33790661a05f50e1b5b3b73e4d4411628d0c5707a7636721ced5ba`.
- Bounded failure SHA-256: `d3a3a10a49f95cdc241da548ff08c67aaa0531b8325d4cef14f9cf1d8f53a1c7`.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3169194`.
- Result: `0229=PASS`, `0231 hunk 1=FAIL`; compile/image/QEMU/3D were not run.
