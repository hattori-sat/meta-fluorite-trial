# FLR-0390 — bind the fixed Podman Devtool container to the current repository

- Status: Done
- Priority: High
- Created: 2026-10-01
- Predecessor: [FLR-0389 same-image LIT fixture replay](FLR-0389-replay-lit-fixture-correct-marker-current-image.md)
- Branch: `feature-flr-0388-direct-sequoia-lit-runtime` (existing checkout; no source change in this ticket)
- Plan: [FLR-0390 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0390-rebind-podman-project.md)
- Working log: [FLR-0390 working log](../logs/2026-10-01-flr0390.md)

## Objective

Repair the single existing Podman Devtool container's `/workspace/project`
bind so it points to the current canonical `meta-fluorite-trial` checkout,
while preserving its fixed AGL and state binds and all existing
`/workspace/tmp` contents. Reuse the current Podman machine, image, container
name, state root, and one TMPDIR. Do not change Fluorite source, layer patches,
recipes, or Yocto build artifacts in this ticket.

## Facts

- `bash scripts/assert-canonical-repository.sh` passes in the current checkout.
- `scripts/run-podman-devtool.sh status` fails closed at the existing
  container's `project-root` label.
- The fixed-name container is running, but its project bind is a separate,
  clean clone on branch `devtool-flr-0371-mount`, HEAD `a3e7799`; its Git common
  directory is not the current checkout. The old clone will remain untouched.
- The AGL bind and fixed state bind match their configured role paths. The
  container uses the expected `fluorite-yocto-devtool:22.04` image. There are
  no Devtool or BitBake processes in the container.
- `/workspace/tmp` is one 3-GiB container tmpfs with 637620 KiB used (about
  623 MiB). The fixed state filesystem has 22458908 KiB free. The single
  preservation-archive path is absent and GNU tar is available in the
  container.
- `FLUORITE_MAC_PROJECT_ROOT` is unset, so a stale shell override does not
  explain the bind mismatch.

## Inference

The existing container's project bind is the first failing contract. Keeping
it would make Devtool resolve recipe metadata from a separate historical
checkout rather than the current feature checkout. The fixed state and AGL
binds do not need to move.

## Competing explanations

1. **Only the project bind is stale.** Recreating the same named container
   through the documented Podman wrapper will attach the current checkout;
   the state/AGL labels remain unchanged and restored TMPDIR passes an archive
   comparison.
2. **The shell selects a stale project path.** An explicit current-root
   setting would make the existing container contract match. This is
   falsified because the environment override is unset and the mount itself
   points to a different Git common directory.
3. **Other Devtool state is active or bound elsewhere.** A live process or
   state/AGL mismatch would make container replacement unsafe. Read-only
   process and mount checks currently falsify this explanation; repeat them
   immediately before the stop.

## Success criteria

1. Before replacement, verify the exact container name/image, no active
   Devtool/BitBake process, fixed state and AGL binds, archive absence, and
   sufficient state-filesystem space. Preserve the old project clone.
2. Archive the existing `/workspace/tmp` contents under one fixed filename in
   the already-mounted state root; record its SHA-256 and entry count.
3. Stop and remove only the recorded fixed-name container. Recreate it through
   `scripts/run-podman-devtool.sh status` with the same Podman machine, image,
   name, AGL bind, state bind, and one 3-GiB `/workspace/tmp` tmpfs. No second
   container, machine, volume, TMPDIR, or build directory may remain.
4. Restore TMPDIR from the archive and require GNU tar compare to pass before
   removing the archive. The old clone and persistent state bind remain
   unchanged.
5. The container project bind equals the current canonical checkout; the
   canonical guard and two consecutive read-only wrapper `status` checks pass.
6. Update `docs/environment.md`, this ticket, the working log, and `TASKS.md`
   with the evidence. No product source/build changes occur.

## Impact and risk

- **Build-time:** no BitBake or image build; status probes are bounded.
- **Packaging/runtime:** none; this ticket does not change the product image.
- **State:** the container ID changes once because a bind mount cannot be
  edited in place. Its fixed state/AGL mounts and image are reused; current
  TMPDIR is archived/restored and compared before the archive is removed.
- **Integration risk:** if the archive, recreate, restore, or wrapper check
  fails, keep the archive and stop. Do not proceed to Devtool source edits or
  create a second container.

## Plan / Do / Check / Act

### Plan

- Recheck all safety preconditions immediately before the one-container
  rebind.
- Preserve and verify TMPDIR, then let the official Podman wrapper recreate
  the fixed container using the current repository path.
- Prove bind, state, TMPDIR, and wrapper identity before starting the separate
  Sequoia material task.

### Do

- Saved `/workspace/tmp` into one archive on the fixed state bind before
  stopping the container. Archive SHA-256:
  `340e7ce3a38e266b8c0ca9e59e3a0add28c5424e836f5a0dd5fcb0a0de9bc637`; size
  `652574720` bytes; `8404` entries; archive readback passed.
- Stopped and removed only the old fixed-name container. Recreated it through
  the documented Podman wrapper with the same image, state and AGL binds and
  current project bind. Container ID changed from `00db13334986` to
  `88e0bdcd2b8e`; image ID remained `3db2dc9e27c5`.
- Restored the archive into the same 3-GiB `/workspace/tmp` tmpfs. GNU tar
  compare passed; used space returned to `637620` KiB. Wrapper status passed
  twice, and Devtool status listed exactly one `fluorite-plugins` source.
- The preservation archive was removed only after restore comparison and
  wrapper checks passed. The old clone and fixed persistent state were not
  modified.

### Check

- PASS: the current checkout is the `/workspace/project` bind; AGL/state
  binds and image identity match; the sole fixed container and Podman machine
  remain; TMPDIR restored and tar-compare passed; two wrapper status checks
  and one Devtool status check passed. No BitBake server remained after the
  status command. No source/build/image change occurred.

### Act

- The earlier follow-up statement that the parameterized Sequoia material was
  already the known-positive material was incorrect. FLR-0369's same-image
  control identifies constant-source LIT/SUN as the current-image positive;
  patch 0332 still uses a dynamic parameter. FLR-0391 owns transferring the
  constant shader source to Sequoia via Devtool and checking it on Mini QMP.
  FLR-0390 itself remains environment-only and has no product changes.

## UNKNOWN

- Whether the existing Sequoia LIT material plus the historical SUN produces
  recognizable live Sequoia pixels; the separate runtime ticket owns that
  visual gate.
