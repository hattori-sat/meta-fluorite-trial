# FLR-0351 Plan — validate Mini handoff before receiver update

## Goal and scope

Make the fixed Mini Git-bundle handoff fail closed before it can move the
receiver `HEAD`, index, or worktree. Validate the effective BitBake `TMPDIR`
against the existing fixed role value and complete every receiver precondition
before `git fetch` or `git checkout`.

This is a handoff-safety prerequisite for FLR-0350, not a Fluorite runtime
result. FLR-0350 remains the only 3D/runtime gate and resumes after this
precondition is proven. No product layer, recipe, image, QEMU process, build
TMPDIR, receiver, or container is created or changed by this ticket's local
implementation tests.

## Evidence and decision

### Facts

- The canonical repository guard passes on
  `feature-flr-0351-mini-handoff-preflight`, based on the current verified
  feature head `7124123`; `dev-fluorite-demo` is a stale ancestor and is not a
  safe base for this ticket.
- The existing receiver helper checks a literal `TMPDIR = ...` line in
  `conf/local.conf` only after bundle fetch and detached checkout.
- The fixed build's `local.conf` has zero active `TMPDIR` assignments.
- On the Mini, a bounded target-less `bitbake -e` succeeded, reported the
  effective form `TOPDIR/tmp`, and matched the `TOPDIR` inferred from the
  saved FLR-0335 runqemu command. No BitBake process remained after the query.
- The saved QEMU kernel, rootfs, and qemuboot inputs resolve under `TOPDIR`
  but outside `TOPDIR/tmp`. This is an artifact-location fact only; it does
  not establish a different effective `TMPDIR` or the original deploy path.
- Exploratory failures were contained: querying unavailable recipe/image
  targets returned a provider error; a CLI-help probe queried `bitbake` outside
  the sourced environment and returned 127. Those attempts left no BitBake
  process, changed no receiver state, and are recorded in the working log.

### Inference

The exact literal grep is not an effective-configuration check, and because it
runs after checkout it can reject a handoff after mutating the receiver.

### Hypotheses and alternatives

1. **Chosen: query effective configuration with target-less `bitbake -e`**
   before receiver mutation; compare its resolved `TOPDIR` and `TMPDIR` with
   the fixed role arguments. The exact CLI form succeeded on the pinned Mini
   build and the BitBake process exited cleanly. This costs a metadata parse
   per handoff but avoids assumptions about include files and defaults.
2. **Rejected: parse `local.conf`/included files or infer `TOPDIR/tmp` in the
   helper.** This is faster but can miss BitBake overrides, environment
   expansion, and included configuration; the current failure already shows
   why a literal grep is not authoritative.
3. **Rejected: infer TMPDIR from QEMU artifact paths.** The saved runqemu inputs
   are outside the effective TMPDIR, so artifact location is not a reliable
   proxy for BitBake's effective value.

## Implementation steps

1. Move FLR-0350 to `Waiting` with the handoff dependency and make FLR-0351 the
   sole `In Progress` ticket; retain one active ticket.
2. In `scripts/reuse-mini-build-receiver.sh`, validate fixed directories,
   receiver cleanliness, no active BitBake process, receiver layer
   configuration, effective `TOPDIR`, and effective `TMPDIR` before any Git
   receiver mutation. Require all existing receiver/build/TMPDIR role values;
   remove historical hard-coded fallbacks. Find the OE initialization script
   by walking ancestors of the existing build directory and fail if sourcing
   it fails; do not create a new build/TMPDIR. Use the documented
   `bitbake -e -T 5` global environment query with a hard 120-second client
   bound and a bounded idle-process check.
3. Keep bundle verification before mutation, then fetch and detach-checkout
   only after every preflight succeeds. Verify exact tip and final clean state.
4. Add focused integration tests using temporary local Git repositories and
   a fake SSH/BitBake environment. Prove missing roles stop before SSH,
   initialization/query/TMPDIR failures leave `HEAD`, `FETCH_HEAD`, index,
   and worktree unchanged, and valid TMPDIR updates to exactly the bundle tip.
   Do not rely solely on source-order grep tests.
5. Run focused tests, shell syntax, privacy/checkpoint, `git diff --check`,
   and `make verify`. Self-review mutation ordering and failure cleanup.
6. Commit locally on this feature branch. Do not push. If the existing local
   handoff roles are available, use only the documented bundle helper for the
   authorized Mini handoff; otherwise stop before transfer and record the
   missing role configuration rather than guessing paths.

## Acceptance criteria

- A rejected preflight leaves receiver `HEAD`, `FETCH_HEAD`, index, and
  non-evidence worktree status unchanged.
- A valid handoff reaches the exact requested full commit SHA and leaves the
  receiver clean outside its existing evidence directory.
- All TMPDIR/build/layer/process checks happen before fetch/checkout.
- No new receiver, build directory, TMPDIR, container, image build, or QEMU
  run is created in this ticket.
- Local verification, privacy, and one-In-Progress checkpoint pass; commit is
  local only.

## Risk and impact

- **Build time:** one bounded metadata parse per bundle handoff; no build task.
- **Runtime/packaging:** no product change.
- **Integration:** the helper must source the same OE environment as the fixed
  build. Exact target-less query and clean BitBake exit were observed on the
  Mini; the integration test will model both success and query failure.
- **3D goal:** no rendering conclusion. FLR-0350 still requires one bounded
  Mini QEMU attempt with QMP-only visual evidence after handoff is safe.
