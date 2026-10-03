# FLR-0418 — preserve serial shell completion after guest wait markers

- Status: Done
- Priority: High
- Created: 2026-10-04
- Updated: 2026-10-04
- Owner: Mac capture controller / Mini QEMU / guest GDB observer / QMP evidence
- Branch: `feature-flr-0418-serial-wait-return`
- Parent milestone: `dev-flr-0417-capture-entry`
- Predecessor: [FLR-0417](FLR-0417-repair-capture-entry-and-run-once.md)
- Candidate baseline: unchanged [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Runtime evidence: [FLR-0418-0001 manifest](../evidence/FLR-0418-0001.md)
- Working log: [FLR-0418 working log](../logs/2026-10-04-flr0418.md)
- Execution plan: [FLR-0418 plan](../../docs/superpowers/plans/2026-10-04-flr0418-serial-wait-return.md)

## Work unit

Repair the guest wait-marker command so READY, observer error, GDB exit/change,
and timeout return a result without terminating the serial login shell or
skipping `serial-exec`'s completion marker. Then perform exactly one fresh
diagnostic capture on the unchanged FLR-0410-0001 image under immutable run ID
`flr0418-0001`.

This is host/guest observation-harness work only. Do not change product source,
Devtool patches, image configuration, build output, or caches. A successful
serial exchange, GDB readiness marker, QEMU launch, or pre-launch QMP still is
not a product-render result.

## Facts, inference, hypotheses, and UNKNOWN

### Facts

- FLR-0417's exact Mini run recorded GDB API smoke PASS and Example Demo launch
  PASS, each with command status 0 and a serial completion marker.
- Its `wait-load-ready.json` output printed `FLR0416_WAIT=...:READY`, followed
  by `logout` and an AGL login prompt. The runner reports
  `deadline-expired stage=guest-command-output`.
- The FLR-0417 baseline wait command executed `exit 0` in its observer-error,
  READY, and GDB-exited branches. `serial-exec` appends `rc` and a unique
  completion marker after that command returns.
- FLR-0417 finalization passed, and its sole QMP still was captured before
  Example Demo launch. Production pixels and present behavior are UNKNOWN.

### Inference

The predecessor's `exit 0` is confirmed as the cause of its missing wrapper
completion marker: the old runtime transcript showed READY then logout, and the
real-shell regression reproduced the missing marker. The corrected FLR-0418
runtime wait now returns READY, `rc=0`, and the wrapper marker.

FLR-0418 reached the deliberate `catch-load-libLLVM` breakpoint with all
Example Demo app threads stopped before the renderer continued. The following
guest snapshot failed while parsing the incremental kernel-journal response;
the controller therefore requested an abort before releasing the app. The
black load-stage screenshot is not evidence of a product render failure.

### Competing hypotheses

1. **Wait command exits the guest login shell.** Support: exact generated
   command, orderly logout/login output, absent `rc` and completion marker, and
   the runner's guest-command-output deadline. Falsifier: a raw transcript
   showing that the unique wrapper marker was emitted before logout.
2. **The guest shell or serial transport terminates independently.** This is
   less consistent with the orderly prompt, but the new shell-level regression
   and fresh runtime transcript will distinguish it.
3. **The wait command completes but the observer reports an error.** This may
   be a real next runtime result; it must arrive as an observer-error marker,
   not be conflated with a serial timeout.

## Success criteria

1. An integration-style local test runs the actual generated wait command
   inside the same shell completion wrapper used by `serial-exec`. Cover READY,
   observer error, GDB missing/changed, timeout, wait-command failure, and
   simultaneous observer-error+READY priority. Require exactly one completion
   marker, wrapper `rc=0`, the expected status marker, a successful next
   command in the same shell, and no logout.
2. The controller treats only READY as success and reports each other marker
   distinctly. Accept only configured marker windows 17–540 seconds, validating
   CLI values before the attempt claim. Bound the guest wait to
   `min(requested, floor(remaining)-15)`; reject a result below one second.
   Give serial-exec up to two seconds after its guest timeout to return its
   status, without exceeding the active ACK/abort deadline. The old `exit 0`
   behavior must fail the completion regression.
3. Run focused controller/launcher/observer/exporter/harness tests, canonical,
   privacy, shell, whitespace, file-size, checkpoint, and relevant repository
   verification gates. Record unrelated pre-existing gate failures unchanged.
4. Commit locally without push. Transfer the exact feature tip through the
   standard Git bundle helper; verify fixed receiver and unchanged
   FLR-0410 kernel/rootfs/qemuboot identities before QEMU.
5. Use exactly one new attempt, `flr0418-0001`; no automatic retry or second
   QEMU. Preserve GDB smoke, actual Example Demo launch, marker outcome,
   identity-bracketed QMP/present/kernel evidence where available, and exact
   teardown. Export only the fixed allowlist after teardown and inspect the
   full QMP frame. No product acceptance is inferred from harness success.

## Constraints and impact

- Preserve all FLR-0417 Mini raw evidence; never reuse `flr0417-0001`.
- No concurrent build/QEMU, image changes, Devtool, `do_patch`, BitBake, cache
  cleanup, or rootfs copy to Mac.
- Change only the wait-marker shell contract and the immutable run-ID-bound
  controller/observer/launcher/exporter fixtures needed for `flr0418-0001`.
- Build-time and packaging impact: none. Runtime image impact: none. Integration
  risk is bounded to the serial shell command/result protocol and is checked
  before any QEMU attempt.
- Keep personal account, host/IP, credentials, keys, and private absolute paths
  out of committed files and evidence.

## Plan / Do / Check / Act

### Plan

- Confirm generated guest command and outer `serial-exec` wrapper as the tested
  boundary; model each marker outcome, marker-priority collision, and the
  next-command sentinel.
- Add one behavioral regression at a time and observe the old exit behavior
  fail before changing the command.
- Encode marker state with a shell function/return path safe under `set -eu`;
  make the shell's final command successful so the wrapper can append its own
  completion marker.
- Update all active helpers, tests, QMP socket, and media-export allowlist to
  the new immutable `flr0418-0001` identity.
- Transfer the clean commit by bundle and make one same-image run only after
  immediate no-owner/artifact/resource preflight.

### Do

- Added a shell-boundary integration regression for the generated wait command,
  the production serial-exec wrapper tail, and a subsequent same-shell command.
- Confirmed red before the fix: READY printed, but the command's `exit 0`
  suppressed the wrapper completion marker.
- Replaced shell termination with a guest function returning typed statuses;
  status capture is guarded by `if/else` under `set -eu`, and the wrapper tail
  remains reachable for every outcome.
- Added READY, observer-error, GDB-missing, GDB-start-changed, timeout, and
  wait-command-failure coverage, plus simultaneous observer-error+READY
  priority. Added ACK/abort deadline coverage, a one-second clock-advance case,
  invalid short-window rejection before claim, and exhausted guest-budget
  rejection. After Sol's final review, added a second clock-advance regression
  that delays command-file preparation and proves the final dispatch guard
  rejects ACK/abort 11s and 14s cases before serial-exec. No product build ran;
  the one authorized QEMU diagnostic attempt is recorded below.

### Check

- Red-before-fix regression reproduced the missing wrapper marker. The fixed
  real-shell integration test covers six marker outcomes and one priority
  collision (seven scenarios); each observes exactly one completion marker,
  wrapper `rc=0`, the next command in the same shell, and no logout.
- Sol's review found that the active serial timeout equaled the host controller
  timeout, so controller termination could race the serial-exec timeout report.
  The controller now allows up to two seconds after the guest timeout while
  remaining within the ACK/abort deadline. It rejects an active budget that
  cannot preserve that grace or produce at least one guest timeout second.
  The wait loop is capped at `min(requested, floor(remaining)-15)`; the
  configured 17-second minimum and CLI validation keep impossible marker
  windows from reaching the attempt-claim stage.
- Tests cover 90, 30, 16.5, 16, 15.999, 15.5, 15, and 14 seconds under both
  ACK and abort deadlines, a one-second dispatch delay, insufficient guest
  budget, and four final-dispatch delays (11s/14s × ACK/abort). The prepared
  command file exists in each delayed case, and serial-exec is not invoked.
  The five-module scoped suite passes 99/99 tests.
- GPT-6.1 Sol's final review found no residual P1/P2 issue and independently
  verified the final dispatch guard. Its optional P3 request to commit tests
  for post-command-preparation delays is now covered by the four regression
  subcases above. Real Mini PTY behavior remains UNKNOWN.
- Fresh `make verify` passed canonical, shell syntax (61 files),
  Python 348/348, and MCP 52/52, then exited 2 at 55 historical Markdown
  targets. The new FLR-0417/0418/0419 links are not among them; FLR-0417's
  earlier count was 11 and exact revision/media projection equivalence is
  UNKNOWN. [FLR-0420](../tickets/FLR-0420-reconcile-markdown-verification-baseline.md)
  owns reconciliation. File-size, QEMU harness, runtime-log-slice, Devtool
  finish/rebase, Mini patch, and bundle-handoff gates passed. The initial
  post-commit privacy check correctly rejected the commit's Git metadata. The
  local commit was amended with reset-author to the repository role identity;
  the resulting tree is unchanged and the fresh privacy check passes. Final
  staged-whitespace and checkpoint results are recorded in Iteration 7 of the
  working log.
- First focused invocation after adding the final-dispatch test failed before
  test collection with `IndentationError` in that test block; indentation was
  corrected, after which the new case passed and the 99-test scoped suite passed.
- Local commit `8506d4b` was created without push and was transferred through
  the standard fixed-path bundle helper; at that point Mini receiver HEAD
  matched exactly and effective TOPDIR/TMPDIR checks passed. Its author metadata
  then failed privacy validation. The local history was explicitly authorized
  for rewrite and amended as `1fb42ee`; the Git tree is identical to the
  transferred commit. The Mini receiver still names the prior commit object,
  but its tree matches; FLR-0421 must hand off its exact new tip before runtime.
- Exactly one `flr0418-0001` run was started against unchanged FLR-0410-0001 with
  6144 MiB. GDB API smoke, ordinary Example Demo launch, and wait-marker serial
  completion all passed. The load-ready snapshot then returned
  `kernel_journal_empty_marker_conflicts_with_returned_cursor`; controller
  status is `LOAD_STAGE_ABORT_REQUESTED`, not a render result. The QMP load
  still was captured, but the required load bracket is unverified.
- The pre-launch and load PPMs are byte-identical black 1280×800 frames. GDB had
  stopped all app threads at `__GI__dl_debug_state` during `libLLVM` loading,
  before rendering. QMP quit, QEMU disappearance, socket absence, teardown, and
  postflight passed with no teardown errors. No present progression, 5-minute
  run, or second boot was tested; kernel-Oops status remains UNKNOWN because the
  snapshot failed.
- The fixed allowlist media export passed after teardown. Its two PNG previews
  were first local-only previews; the selected full-screen load still is now
  attached as [QMP evidence](../evidence/FLR-0418-0001-qmp-load.png). The PPMs
  and raw serial/controller evidence remain on Mini. No rootfs or image was
  copied to the Mac.

### Visual evidence

- QMP-only 1280×800 full-screen load still: [FLR-0418-0001-qmp-load.png](../evidence/FLR-0418-0001-qmp-load.png).
- The frame is black while all Flutter threads are deliberately stopped at the
  LLVM load boundary, before the renderer continues. It is not a product-render
  verdict. PPM SHA-256: `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`;
  PNG SHA-256: `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.

### Act

- Closed as a bounded, unsuccessful diagnostic attempt: the serial-shell
  completion contract passed, the one new-ID run reached the next snapshot
  boundary and failed closed there, and exact teardown passed. No second run is
  allowed under this ticket. FLR-0421 owns the distinct journal-cursor boundary;
  product rendering remains open and the black pre-render frame is not a
  rendering failure result.

## PDCA checker

- Status: PASS WITH CONDITIONS
- Checked by: GPT-6.1 Sol (judgment-only review) and local evidence review
- Findings: The ticket's bounded harness and one-attempt/finalization criteria
  are evidenced. The runtime attempt failed safely at incremental journal
  parsing before renderer release; no product-render criterion is claimed.
  FLR-0421 owns the follow-up and must use a fresh immutable run ID.
