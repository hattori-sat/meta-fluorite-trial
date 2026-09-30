# Rebind the fixed Podman Devtool container to the current repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to execute this plan task-by-task. Keep the existing repository work intact and stop on any failed preservation or identity check.

**Goal:** Make the one existing Podman Devtool container use the current canonical project checkout while preserving its fixed state and TMPDIR.

**Architecture:** The container bind mount cannot be changed in place, so preserve `/workspace/tmp` in one archive stored on the already-mounted state bind, remove only the verified fixed-name idle container, and recreate it through the existing Podman wrapper. Restore and compare the saved TMPDIR before deleting the archive. The persistent state and AGL mounts remain untouched.

**Tech Stack:** Podman machine, the existing `fluorite-yocto-devtool:22.04` image, `scripts/run-podman-devtool.sh`, GNU tar, and the project runtime checkpoint.

**Spec:** `work/tickets/FLR-0390-rebind-podman-project-to-current-repository.md`

## Global Constraints

- Run `bash scripts/assert-canonical-repository.sh` before mutation.
- Reuse the existing Podman machine, image, container name, AGL bind, state bind, and one `/workspace/tmp` tmpfs.
- Do not create a second container, machine, volume, TMPDIR, or Yocto build directory.
- Do not modify source, patches, recipes, image artifacts, or protected caches.
- Preserve the old project clone; do not delete or modify it.
- Keep the preservation archive until its SHA, entry count, and post-restore tar comparison pass.
- Never record personal absolute paths, hostnames, IPs, or credentials in tracked files.

---

### Task 1: Record and recheck the exact pre-rebind contract

**Files:**
- Modify: `work/logs/2026-10-01-flr0390.md`
- Verify: `work/tickets/FLR-0390-rebind-podman-project-to-current-repository.md`

**Interfaces:**
- Consumes: the current checkout and fixed Podman container `fluorite-mac-devtool`.
- Produces: a bounded preflight record proving the exact target is idle and its persistent binds are identified.

- [x] Re-run the canonical guard and verify the current checkout path equals the expected project root, without printing the path into the log.
- [x] Verify the fixed container is running and has the expected image/name; verify the current project bind mismatches, while AGL and state binds match.
- [x] Verify no Devtool/BitBake process remains, the state filesystem has at least 2 GiB free, the archive path is absent, and `/workspace/tmp` is the existing 3-GiB tmpfs.
- [x] Record only role paths, comparison verdicts, container ID prefix, disk headroom, and TMPDIR usage in the working log.

**Verification:** All checks pass; otherwise stop without stopping or removing the container.

### Task 2: Preserve the one existing TMPDIR

**Files:**
- Modify: `$DEVTOOL_STATE_ROOT/.flr0390-devtool-tmp-preserve.tar` (temporary archive only)
- Modify: `work/logs/2026-10-01-flr0390.md`

**Interfaces:**
- Consumes: the idle container's `/workspace/tmp` and fixed `/workspace/state` bind.
- Produces: one verified GNU tar archive in the existing state bind.

- [x] In the existing container, archive `/workspace/tmp` using GNU tar with numeric owners, ACLs, and xattrs preserved; do not create another host directory.
- [x] Record archive SHA-256 and `tar -tf` entry count; run `tar -tf` again to confirm the archive is readable.
- [x] Verify the archive resides on the already-mounted state bind and that state free space remains sufficient.

**Verification:** Archive exists exactly once, is readable, and has a recorded checksum. If tar reports an unsupported socket or metadata loss, stop and retain the archive/container.

### Task 3: Recreate the same fixed container against the current checkout

**Files:**
- No source or recipe files.
- Modify: `work/logs/2026-10-01-flr0390.md`

**Interfaces:**
- Consumes: verified TMPDIR archive and the exact idle container identity.
- Produces: the same fixed container name/image/state/AGL contract with a new current-repository project bind.

- [x] Stop only `fluorite-mac-devtool` after the immediate process/bind preflight passes.
- [x] Remove only that stopped fixed-name container; do not remove its image, machine, old checkout, state directory, or any other container.
- [x] Run `FLUORITE_MAC_PROJECT_ROOT="$PWD" scripts/run-podman-devtool.sh status` once; this is the documented path that creates the missing fixed container and reuses the existing state bind.
- [x] Compare the new container ID and mount/label identities. Require exactly one matching container and the current checkout at `/workspace/project`.

**Verification:** Current project bind passes the canonical guard; same image/state/AGL identities; no duplicate container or Podman machine.

### Task 4: Restore and verify TMPDIR, then close the environment gate

**Files:**
- Modify: `docs/environment.md`
- Modify: `TASKS.md`
- Modify: `work/tickets/FLR-0390-rebind-podman-project-to-current-repository.md`
- Modify: `work/logs/2026-10-01-flr0390.md`

**Interfaces:**
- Consumes: the new container and the preserved archive.
- Produces: restored TMPDIR and an accurate environment/ticket record.

- [x] Extract the archive into the new `/workspace/tmp` with owner, ACL, xattr, and mode preservation.
- [x] Run GNU tar compare against the archive; verify tmpfs capacity/type and the same archive SHA/entry count.
- [x] Run `FLUORITE_MAC_PROJECT_ROOT="$PWD" scripts/run-podman-devtool.sh status` a second time and require PASS.
- [x] Remove only the archive created in Task 2 after all restore checks pass; leave it in place on any failure.
- [x] Update `docs/environment.md` to name the current project bind and remove the stale-branch mount claim; update TASKS and complete Plan/Do/Check/Act.
- [x] Run `scripts/runtime-checkpoint.sh verify --ticket FLR-0390 --log work/logs/2026-10-01-flr0390.md`.

**Verification:** Two consecutive wrapper status checks pass, the sole fixed container uses the correct project bind, restored TMPDIR compares exactly, and the task has no product changes.

## Self-review

- Spec coverage: ticket objective, exact one-container scope, fixed state preservation, TMPDIR recovery, and docs/dashboard changes are covered by Tasks 1–4.
- No code patch is generated in this environment-only ticket.
- The original follow-up assumption that the Sequoia parameter expression was
  already the current-image known-positive was corrected against FLR-0369.
  FLR-0391 therefore transfers the proven constant-source LIT material rather
  than repeating an identical parameterized patch or doing a runtime-only
  replay.
