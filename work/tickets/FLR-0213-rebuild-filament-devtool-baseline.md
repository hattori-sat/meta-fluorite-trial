# FLR-0213 — rebuild complete Filament Devtool baseline

- Status: Done
- Priority: High
- Owner: Mac Podman Devtool source-history role
- Created: 2026-09-20
- Predecessor: [FLR-0211](FLR-0211-reconcile-shm-geometry-and-native-wsi.md)

## Goal

Restore a traversable, complete Git baseline for the existing effective
`filament-vk` source so the next WSI source change can follow the deterministic
Yocto Devtool lifecycle: existing recipe patches → source commit → official
`devtool update-recipe`/`finish` → untouched layer patch → Mini bundle.

## Success criteria

- Reuse the fixed Podman container and fixed source workspace; create no new
  container, named volume, source tree, TMPDIR, or `index.local`.
- Keep the effective source tree complete and clean after repair.
- `git fsck` reports no missing commit/tree/blob reachable from the active
  source branch, and `git log` reaches the baseline without an object error.
- Register the source once as the `filament-vk` Devtool component with a
  baseline revision representing the current recipe-patched source.
- Prove that a later WSI edit can be committed as a child of that baseline and
  produce exactly one official Devtool patch. This ticket need not build the
  WSI fix.

## Facts

- Fixed source path inside the container:
  `/workspace/state/build/workspace/sources/filament-vk`.
- Before repair, the source branch was `devtool-flr0155-vk-source` at
  `4c3a4f2220217ea6a76eba67b8de27b30c25e41d`; the working tree is clean.
- `git log` fails because parent commit
  `27f57649c921d1ccc6dc5d009c30fc72b43a592a` is missing.
- `git fsck --full --no-reflogs` reports missing commit `27f57649...` and
  missing trees `36a60c99...` and `fc523ad0...` linked from existing Devtool
  diagnostic commits.
- The expected repair bundle
  `/workspace/state/build/workspace/filament-vk-source-head.bundle` is absent.
- The current worktree is still a full effective source tree; the failure is
  source Git ancestry, not evidence that current files are absent.

## Hypotheses

1. The old Devtool source history was copied incompletely while its effective
   worktree and layer patches survived; rebuilding a new baseline from the
   current effective source will remove the broken ancestry.
2. The missing objects may exist in another local alternate or Git store;
   search before rebuilding so recoverable history is not discarded.
3. The source registration is stale or absent, so official Devtool
   re-registration must be part of repair rather than merely adding a commit
   to the broken branch.

## Plan / Do / Check / Act

### Plan

1. Preserve the current source tree and inspect local alternates/refs for the
   missing objects.
2. If unrecoverable, create a complete effective-source baseline through the
   fixed Devtool workflow without hand-authoring a layer patch.
3. Register `filament-vk` once, verify baseline metadata and Git traversal,
   then hand the WSI change back to FLR-0211.

### Do

- Podman machine/container recovery passed: `fluorite-mac-devtool` is running
  and the wrapper reports `mount-permission=PASS` with the fixed state bind.
- `devtool status` currently lists only `fluorite-plugins`; the Filament source
  branch exists but is not a clean active component registration.
- The existing repair-bundle operation correctly refused because the fixed
  Filament bundle is absent. No source file or layer patch changed.
- The fixed source tree was preserved and a new orphan baseline branch was
  created without deleting the old branch:
  `devtool-flr0213-baseline` at
  `2990e692ea88b47c3dda61780a4ec08dd33cf7ec`.
- The baseline commit contains 47,877 tracked files. The source tree is clean.
- `devtool reset --no-clean filament-vk` removed the stale active registration.
  `devtool add` correctly refused to reuse the existing Devtool-marked source
  directory, so the official `devtool modify --no-extract filament-vk
  <source>` path was used to reconnect the complete source without deleting it.
- The fixed workspace append now records the new baseline as
  `initial_rev .: 2990e692ea88b47c3dda61780a4ec08dd33cf7ec`.
- Official `devtool update-recipe filament-vk --mode patch --append
  /workspace/state/build/workspace --no-remove` completed with no source
  change and generated zero patches, proving the clean parent gate. The
  workspace append's `initial_rev` is authoritative for this Yocto release.

### Check

- Pre-repair source status: clean at `4c3a4f222...`.
- Pre-repair history check: FAIL at the missing parent/tree boundary.
- No WSI source edit or generated patch has started under this ticket.
- Active baseline check: PASS. `git log -1` reaches `2990e692...`, the active
  tree has 47,877 files, and `git status` reports zero entries.
- `git fsck --connectivity-only HEAD` reports no missing objects for the active
  baseline. Full repository fsck still reports dangling commits from the
  archived `devtool-flr0155-vk-source` branch; those are retained for audit and
  are not reachable from the active branch.
- Devtool status lists both `filament-vk` and `fluorite-plugins`, with
  `filament-vk` pointing at the repaired source path.
- The no-source-change official update-recipe gate passed with zero generated
  Filament patches and the expected baseline revision.

### Act

Keep the repaired baseline active and hand the actual WSI child edit to
FLR-0211. That ticket must commit the source change with `git add` and `git
commit`, then use the official Devtool update/finish flow. The generated patch
must be copied unchanged into the canonical layer and only then sent to the
Mini as a bundle.

## UNKNOWN

- Whether another local alternate can supply the old missing objects. This is
  no longer required for the active baseline because the old branch is kept as
  an audit archive and the effective source snapshot is complete.
- The child-edit criterion is PASS: FLR-0211 source commit
  `1fd22efd9acd0b80c7bd2c670cf17e25fd796b8a` produced exactly one official
  Devtool patch with SHA-256
  `6392a5dbdde06d2cd6d38a8701ae543d30a68bdf753e8b4ad43fc2e4ba3f4805`.
