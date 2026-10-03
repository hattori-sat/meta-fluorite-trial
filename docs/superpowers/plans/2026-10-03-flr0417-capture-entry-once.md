# FLR-0417 — repair capture entry/finalization and run once

> **For agentic workers:** execute the steps in order. Preserve the one-shot
> gates; a failure consumes this run ID and does not authorize a retry.

**Goal:** Fix cwd-dependent capture startup, retain truthful QEMU identity on
early exceptions, prevent duplicate QEMU/controller ownership, and obtain one
fully bracketed diagnostic result on the unchanged FLR-0410 candidate.

**Design:** Keep an immutable ticket-specific run ID (`flr0417-0001`) shared by
host, guest, GDB, QMP, and media exporter. Use create-only atomic evidence
claims for start and controller ownership. Invoke the canonical guard with the
resolved repository as its cwd. In `finally`, serialize the exact QEMU identity
already verified by the controller before computing teardown status. Preserve
all existing fail-closed teardown predicates; missing evidence remains
unverified. A duplicate controller must be rejected before entering the
cleanup-owning `try/finally` path.

**Tech Stack:** Python 3 host controller and tests, Bash Mini runner, guest GDB
14.2, exact FLR-0410 Mini QEMU image, QMP raw PPM and bounded guest snapshots.
No product source, Devtool, BitBake, image, or cache changes.

**Spec:** [FLR-0417 ticket](../../../work/tickets/FLR-0417-repair-capture-entry-and-run-once.md)

## Evidence baseline

- Predecessor FLR-0416 commit: `d97dec4246208aba28fbb2f991dd7653815ce44b`.
- Preserve consumed run `flr0416-0001`; its final record reports
  `teardown_verified=false` and contains no visual observation.
- Candidate remains exact FLR-0410-0001 rootfs SHA-256
  `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`, kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot
  `3872b66339ac3601c704f1b54cab5630796ccf5f0f95ebc4e7077210e89d107f`.
- Remote cwd-only discriminator: guard from SSH default cwd FAIL; guard from
  receiver root PASS. No guest setup, GDB smoke, Flutter, QMP frame, or product
  pixels were produced in FLR-0416.
- This ticket allows exactly one new ID `flr0417-0001`. It must not overwrite
  any existing evidence or claim.

## Competing explanations

| Boundary | Explanation | Discriminator |
| --- | --- | --- |
| Guard | It reads the correct repo but inherits an unrelated SSH cwd | Run through the controller with an explicit resolved repo cwd; test invalid origin/metadata still fails |
| Final record | Identity exists but is copied only after the throwing layout path | Force post-identity layout failure and inspect final record and every teardown predicate |
| Duplicate ownership | Existing-output collision can reach `finally` and stop another controller's QEMU | Atomic start/controller claims; second start/capture rejected before QEMU or cleanup, with prior evidence byte-identical |
| Product runtime | Prior failure may have said nothing about rendering | One same-image guest GDB smoke + live first-hit/present/QMP evidence; classify product only from a valid bracket |

## Global constraints

- Keep FLR-0416 Waiting and the one-shot run ID consumed. FLR-0417 must be the
  sole `In Progress` ticket.
- Preserve all existing worktree changes. Commit only reviewed FLR-0417 files,
  locally and without push.
- Do not modify product layers/source, invoke Devtool/`do_patch`/BitBake, clean
  caches, alter the candidate image, or use a rendering override/bypass.
- Before handoff and before QEMU, verify the canonical source and fixed Mini
  receiver, exact image hashes, current owners/builds, evidence collision,
  memory/disk headroom, ports, and QMP socket. No competing work may be stopped.
- Send a brief user-facing notice before the long live QEMU attempt. Start only
  one QEMU and never retry automatically.
- Preserve all raw guest/QMP evidence on Mini. Generate a Mac PNG/video preview
  only after exact teardown is proven; preview is not a product pass.

## Implementation tasks

### Task 1 — establish the ticket and failing regressions

- [x] Verify canonical guard, branch, current ticket state, and all existing
  diffs. Keep `flr0416-0001` evidence untouched.
- [x] Add failing tests proving `_check_layout()` passes `cwd=self.repo_root`
  and still rejects an invalid canonical repo.
- [x] Add a run-path test where QEMU identity verifies and a later layout/guard
  exception occurs; the final JSON retains identity but remains a diagnostic
  failure. Missing identity or any missing teardown predicate remains false.
- [x] Add create-only start/controller claim tests. A duplicate controller must
  not call QMP quit or modify any existing record.
- [x] Freeze `flr0417-0001` consistently across runner, controller, guest GDB,
  snapshot helpers, QMP socket, tests, and Mac media exporter. Test occupied
  run directory and consumed `flr0416-0001` rejection without writes.

### Task 2 — implement the narrow capture-harness correction

- [x] Add explicit cwd to the canonical guard subprocess invocation.
- [x] Serialize the already validated identity in the terminal record even if
  `_check_layout()` raises after validation; do not relax `controller_final_record`.
- [x] Create persistent atomic start and controller claims before starting QEMU
  or entering cleanup ownership. Existing or partially written claims block
  reuse; do not auto-clear stale claims.
- [x] Keep staged source hashes and the guard log scoped to the new run ID.

### Task 3 — verify locally before any transfer

- [x] Run focused FLR-0417 controller, launcher, guest observer, and exporter
  tests; run relevant shell syntax checks and `git diff --check`.
- [x] Run canonical/privacy/runtime-checkpoint gates. Record any unchanged
  historical Markdown link failures without broadening scope.
- [x] Run the repository test suite. (The 339 repository tests and 52 MCP tests
  passed; `make verify` is stopped only by 11 pre-existing Markdown targets.)
- [x] Review the explicit staged diff; commit the ticket, plan, log, code, and
  tests locally using privacy-safe metadata. Do not push.
- [x] Create the normal Git bundle from the exact new commit and use the
  established helper only. Verify helper-reported bundle SHA and exact receiver
  HEAD; no manual source copy and no build.

### Task 4 — one fresh exact-image runtime attempt

- [x] Recheck no owners/builds, run-ID and claim paths absent, ports/QMP socket
  free, 6144-MiB policy/headroom, and exact unchanged FLR-0410 kernel/rootfs/
  qemuboot hashes before prepare/start.
- [x] Prepare one evidence directory, verify all staged hashes, acquire the
  atomic start claim, and start one QEMU. Require guest readiness.
- [x] Invoke capture once. Require controller claim before it can own teardown;
  run guest GDB/Python API smoke before launching Flutter.
- [x] Capture first-hit load/hit/post evidence with the existing identity,
  present, kernel, guest-clock, and QMP brackets. If any stage fails, stop at
  first failure and retain bounded evidence; do not launch an ordinary fallback.
- [x] Quit only the recorded QEMU. Check PID/start identity disappearance, QMP
  socket absence, postflight, and unchanged image hashes. Save final JSON before
  preview export.
- [x] If teardown is verified, export the allowlisted QMP still/video to Mac,
  inspect the entire frame, and record hashes. If evidence is incomplete, keep
  the result UNKNOWN and do not infer a render failure from a post-exit frame.

### Task 5 — close this bounded diagnostic unit

- [x] Compare the two orchestration hypotheses with support/falsifier evidence.
- [x] Update the ticket/log/TASKS with exact run ID, commit/bundle identity,
  preflight, guest GDB, QMP/present/kernel, teardown, and media verdicts.
- [x] Run canonical/privacy/checkpoint/diff verification and a read-only
  postflight for no residual QEMU/build owners.
- [x] Mark FLR-0417 Done only if its observation/finalization acceptance gates
  pass. Even then keep the product 3D goal open until its separate material,
  HUD, interaction, five-minute, and two-boot criteria are proven.
