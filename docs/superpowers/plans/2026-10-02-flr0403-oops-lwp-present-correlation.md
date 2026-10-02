# FLR-0403: correlate the FEngine Oops with its LWP and outstanding present

## Goal

On the unchanged patch-0334 rootfs, determine whether the run's kernel Oops
TID belongs to one of the GDB-observed FEngine threads, identify the loaded
ELF Build-IDs, and align those facts with the live QMP frame and unmatched
present. This is one diagnostic observation, not product acceptance.

## Constraints

- Work from the exact FLR-0402/0401 observer tip in the canonical repository.
- Preserve the last proven manual guest Flutter command and exact QEMU/image
  profile. No Devtool, BitBake, image build, product patch, camera/material/
  lighting change, second QEMU, or cache operation.
- Do not start if Mini ownership/process/port/hash/fresh-ID preflight is not a
  complete PASS. Never stop an unowned or mismatched process.
- Full-frame QMP still and four-frame evidence precede GDB attach. GDB output,
  process identity/readiness, and present markers share the same run-scoped
  guest log; retain timestamps and copy it before app teardown.
- Keep each runtime attempt one-shot and preserve QMP raw PPMs on Mini.

## Task 1 — Recover the exact known-good manual launch/observation commands

- [x] Read the FLR-0401/0399 records and existing helper source to recover the
  exact manual guest Flutter command, PID/UID/start identity check, GDB attach
  command, log sink, QMP endpoints, and cleanup sequence.
- [x] Compare at least two recorded launch paths only as needed: prefer the
  exact FLR-0401 direct Example Demo path on rootfs `80935c3f…`; do not mix in
  the FLR-0394 fixture or a different image/profile.
- [x] Do not edit the observer, run a new local QEMU, or construct new shell
  automation in this task before the manual sequence is inspected.

## Task 2 — Read-only Mini receiver/build preflight

- [x] Verify current Mini receiver tip/worktree without checkout, fetch, bundle
  update, or branch mutation. No source change is required on the build
  receiver; do not transfer documentation-only commits.
- [x] Resolve fixed build/evidence role paths from the prior exact run command
  and verify exact rootfs/kernel/qemuboot hashes, BitBake idle, no
  QEMU/runqemu/Flutter/GDB process, free reserved ports, and a fresh run ID.
- [ ] Recheck all owners, ports, artifact hashes, receiver cleanliness, and
  run-ID absence read-only immediately before any mutation. If they pass,
  create exactly one evidence run directory, then invoke the generic harness's
  read-only preflight (which requires that directory). Start remains a
  separate action and repeats its own ownership/hash/port gates.
- [ ] If any status is missing or ambiguous, stop before QEMU and record it as
  UNKNOWN; do not assume the machine is idle from Mac process visibility.

## Task 3 — One manual exact-image runtime observation

- [ ] Start exactly one QEMU only after Task 2 passes, using the pinned
  FLR-0401 profile and no changed image or diagnostic override.
- [ ] Confirm guest readiness and identity; manually start the existing
  production Example Demo / Flutter process with the documented command.
  Record its PID/UID/start identity and readiness in the run-scoped log.
- [ ] Capture the full QMP still and four consecutive frames while the
  inferior is alive. Save the actual PPM dimensions/hashes and analyze the HUD
  and fixed Sequoia ROI. Do this before GDB attach.
- [ ] At the first persistent unmatched present, perform one identity-checked
  bounded GDB attach and manually run `info threads` plus a bounded selected
  stack. Retain GDB target IDs/LWPs, mapped ELF paths, Build-IDs, and exact
  present/counter state in the same guest log as readiness markers. Include
  timestamped kernel Oops TID and process/thread state after observation.
- [ ] Use the exact mapped path from `/proc/<pid>/maps` with `readelf -n` to
  identify the current image's ELF Build-ID; do not substitute a matching
  historical symbol/offset or load all debug symbols as a shortcut.
- [ ] Stop only the recorded Flutter identity, quit QEMU through its recorded
  QMP socket, and verify zero newly owned residuals/listeners. Never kill an
  unrelated process.
- [ ] Record what is proven, falsified, and UNKNOWN. If no live frame, Oops,
  or unmatched present occurs, do not manufacture that condition; report the
  actual boundary and select one new discriminator.

## Task 4 — Only then decide whether observer automation needs a new ticket

- [ ] If all manual commands work and the missing step is genuinely repetitive,
  record the smallest reusable command contract; do not add it to this runtime
  ticket. Open a separate ticket before changing the observer.
- [ ] If a manual command fails, preserve the exact command/error and classify
  tool availability, permissions, process identity, or target state before any
  automation.

## Task 5 — Review and close as bounded diagnostic evidence

- [ ] Review the whole QMP screenshot and four-frame video; keep only bounded
  evidence in the repository and raw logs on Mini.
- [ ] Verify all hashes, ticket/log/plan consistency, exact cleanup, and
  `runtime-checkpoint.sh` before marking Done.
- [ ] Commit closeout locally without push. Do not mark the overall Fluorite
  goal complete; original Sequoia appearance, HUD composition, interaction,
  five-minute stability, and two-boot reproduction remain separate gates.
