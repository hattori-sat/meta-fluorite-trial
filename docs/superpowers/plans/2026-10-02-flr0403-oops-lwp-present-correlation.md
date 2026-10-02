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

## Task 1 — Test and add only the missing GDB identity fields

**Files:** `scripts/flr0399_live_capture.py`,
`tests/test_flr0399_live_capture.py`.

- [ ] Add a regression that generated GDB Python emits every relevant
  `InferiorThread.ptid` (including LWPID), without removing thread name/number.
- [ ] Add a filtered marker for current objfile filename and `build_id` for
  `libLLVM`, `libvulkan_lvp`, and relevant Filament objects; tolerate missing
  Build-ID only as explicit `UNKNOWN`, never as a successful identity.
- [ ] Assert identity, present, and GDB diagnostics append to the same guest
  run log; retain exact PID/UID/start validation, bounded collection, and the
  existing serial command size limit.
- [ ] Run focused tests red before implementation, then green; run static
  shell/Python checks, whitespace, privacy, file-size, and runtime-checkpoint
  gates. Do not run QEMU from the local Mac.

## Task 2 — Commit and verify the Mini receiver without mutation

- [ ] Commit only FLR-0403 instrumentation/tests and its ticket/log records
  locally; do not push. Record the exact tip and create the official Git
  bundle.
- [ ] Use the established bundle receiver preflight. Verify receiver tip,
  exact rootfs/kernel/qemuboot hashes, BitBake idle, no QEMU/runqemu/Flutter/
  GDB process, free reserved ports, and a fresh run ID/evidence path.
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
  bounded GDB attach; retain per-thread name/number/ptid, filtered objfile
  filenames/Build-IDs, and the exact present/counter state. Include the
  timestamped kernel Oops TID and process/thread state after the observation.
- [ ] Stop only the recorded Flutter identity, quit QEMU through its recorded
  QMP socket, and verify zero newly owned residuals/listeners. Never kill an
  unrelated process.
- [ ] Record what is proven, falsified, and UNKNOWN. If no live frame, Oops,
  or unmatched present occurs, do not manufacture that condition; report the
  actual boundary and select one new discriminator.

## Task 4 — Review and close as bounded diagnostic evidence

- [ ] Review the whole QMP screenshot and four-frame video; keep only bounded
  evidence in the repository and raw logs on Mini.
- [ ] Verify all hashes, ticket/log/plan consistency, exact cleanup, and
  `runtime-checkpoint.sh` before marking Done.
- [ ] Commit closeout locally without push. Do not mark the overall Fluorite
  goal complete; original Sequoia appearance, HUD composition, interaction,
  five-minute stability, and two-boot reproduction remain separate gates.
