# FLR-0208 — repair the fixed Devtool full-source baseline

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto patch workflow roles
- Created: 2026-09-20
- Predecessor: [FLR-0207](FLR-0207-inspect-live-wayland-shm-buffer-bytes.md)
- Working log: `work/logs/2026-09-20-flr0208.md`

## Work unit

Restore the existing fixed Mac Devtool source tree from the current Mini
recipe-effective source and make its source Git baseline include the complete
source. This is a workflow repair, not a 3D implementation.

## Facts

- Fixed Mac source Git `HEAD=5de74d...` contains only three tree entries while
  the worktree has about 966 files and marks many tracked files deleted.
- `plugins/filament_view/core/scene/view_target.h` is absent from the Mac
  worktree and absent from that HEAD.
- The Mini post-`do_patch` effective source Git has 478 tracked files and
  contains `view_target.h` and `view_target.cc`.
- The current helper's baseline commit uses `git add -u`, which cannot add a
  complete untracked baseline.

## Success criteria

- [x] Restore the same fixed Mac source path from the Mini effective source;
  do not create a second source tree, container, volume, or TMPDIR.
- [x] Change the baseline helper to stage the complete source deterministically
  with `git add -A` and an explicit full-tree check.
- [x] Create a full-source baseline commit through the Devtool wrapper.
- [x] Generate a no-op official patch or equivalent diff check proving the
  baseline is stable before any 3D source edit.
- [x] Commit the workflow repair locally and record all hashes.

## Hypotheses

1. H1: the partial source Git baseline is the direct cause of the apparent
   Devtool/meta patch drift.
2. H2: recipe registration alone is sufficient and the partial source Git is
   harmless.

H1 is currently favored because HEAD does not contain the header required by
the current source, while the Mini effective source is complete.

## Plan / Do / Check / Act

### Plan

1. Restore the fixed source path from the Mini effective source without
   changing the active recipe.
2. Repair and verify the baseline helper.
3. Commit the complete source baseline through the existing Devtool source
   Git, then run the official source diff gate.

### Do

- Restored missing source files from the Mini post-`do_patch` worktree into the
  same fixed Mac source path with `rsync --ignore-existing`. Existing files
  were not overwritten. One content-stale file was saved as evidence before
  being refreshed from the Mini effective source.
- Imported the Mini source Git history into the fixed state with bundle SHA-256
  `dc84274fc5839c48ca5cc13a74ab58670adc5cfcd8716943fe40c980418bf9e2`.
- Repaired the baseline helper to use `git add -A`, recover a partial HEAD by
  rebuilding only the index, exclude Devtool root Quilt metadata, and retain
  submodule gitlinks without recursing into an unavailable submodule.
- Created source baseline commit `95dc7cef4d7871b7614689e1c30af43e2f880b95`.
- Recovered the existing sdbus submodule metadata and object history with
  bundle SHA-256
  `57d88d0d2ac4bc482e63c129cb2e6e94b264b2edbd50c60c1775e58f6e2d3a38`.
- Re-registered the same source path with `modify --no-extract`; the official
  finish path then completed its standard clean/parse lifecycle and removed
  the temporary workspace recipe. No new source patch was generated because
  the baseline was unchanged.

### Check

- Fixed source Git reports `HEAD=95dc7cef4d7871b7614689e1c30af43e2f880b95`,
  `tree=478`, `index=478`, and clean status.
- The missing header is present at
  `plugins/filament_view/core/scene/view_target.h`.
- The pre-refresh Mac file evidence is
  `work/evidence/FLR-0208-mac-scene_text_deserializer.cc.before`, SHA-256
  `d1bf335a12655c7dbdd34bb6d9fb1475822a38249f9f46c7dcbc738eac8ecdab`.
- The refreshed effective file SHA-256 is
  `bb64306a363db640b95ed0292c10aa3ddfd1ce46aaaa2fbd133e8597edb70956`.
- Devtool status was restored to exactly one `flutter-auto` source before
  finish and was empty after successful no-op finish, as expected.
- The fixed finish layer retained the existing four patch artifacts; no
  baseline-sized patch was produced.

### Act

Closed FLR-0208 and opened FLR-0209 for a current-source visible SHM cube
fallback. The native Vulkan WSI repair remains a separate hypothesis.

## UNKNOWN

- Whether every file in the Mini post-patch worktree is required by the
  current Mac Devtool source recipe; the restore will be checked against the
  effective source tree and the next official patch gate.
