# FLR-0392 — make the Podman Devtool rebase loop deterministic

- Status: Inbox
- Priority: High
- Created: 2026-10-01
- Discovered during: [FLR-0391](FLR-0391-apply-constant-lit-material-to-sequoia.md)

## Objective

Make the fixed-container Devtool component-rebase workflow complete
deterministically after component reset, workspace registration, and bounded
timeouts. Preserve the standard Yocto sequence: commit the Devtool source,
run official `devtool update-recipe`, verify the generated patch, then commit
the layer change. Do not add a new container, volume, source tree, build tree,
TMPDIR, or index lock.

## Facts

- On FLR-0391's first helper call, `devtool reset --no-clean` moved the source
  tree to the standard workspace attic; the helper then checked the obsolete
  pre-reset path.
- The retry reached `devtool add` and BitBake reported duplicate
  `BBFILE_COLLECTIONS`. The fixed BBLAYERS file contained both
  `/workspace/state/build/workspace` and the symlink alias
  `/tmp/fluorite-bitbake-control/workspace`, which resolve to the same
  directory and load the same `workspacelayer` collection.
- The pinned Yocto `edit_bblayers_conf()` strips trailing separators but
  compares workspace entries as path strings. Its Devtool configuration uses
  the canonical path while the Podman wrapper adds the alias.
- The bounded wrapper timeout stopped its direct command but left child shell,
  `recipetool`, and BitBake server processes; exact recorded children were
  terminated and a subsequent exact-PID check was clear.

## Scope and hypotheses

1. Resolve the active source location after reset from Devtool status and use
   the exact existing attic path rather than a pre-reset path.
2. Use one consistent workspace path in both `devtool.conf` and BBLAYERS so
   Yocto does not load the same workspace layer collection twice.
3. Manage the Devtool process group on timeout and preserve the first useful
   error output and exit status; do not leave children behind or repeat a
   300-second loop without a clear failure point.

The likely common improvement point is the existing split-component rebase
helper and Podman wrapper contract. Keep the fix minimal and prove each
failure mode with focused regression tests before changing the production
material workflow.

## Success criteria

- A reset/retry test proves the helper follows the source tree into the attic
  and preserves the exact committed source SHA.
- A config test proves the workspace collection appears exactly once even
  when the fixed control directory is a symlink to the state bind.
- A timeout test proves the exact command process group is terminated, its
  result is reported as timeout, and no child remains.
- Existing source-commit → official `devtool update-recipe` output → layer
  patch byte-identity checks still pass.
- Existing persistent Podman container/state/TMPDIR are reused; no caches or
  workspaces are deleted; no index-local lock is introduced.
