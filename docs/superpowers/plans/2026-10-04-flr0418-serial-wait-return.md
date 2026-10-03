# FLR-0418 — preserve serial shell completion after wait markers

> **For agentic workers:** one TDD slice at a time. A failed runtime attempt
> consumes `flr0418-0001`; no retry or second QEMU within this ticket.

**Goal:** Return READY/error/GDB-exit/timeout markers through the guest serial
shell without suppressing `serial-exec`'s unique completion marker, then make
one diagnostic capture on the unchanged FLR-0410-0001 image.

**Design:** Exercise the actual generated guest command under `/bin/sh` with
the production `serial-exec` wrapper tail. Observe both the marker and a
subsequent shell command. Use a function and conditional status capture so
`set -eu` cannot terminate the login shell. Accept only 17–540 second marker
windows; validate CLI values before claim. Bound wait/serial/controller timeouts
by the active deadline, leave two seconds for the host to collect the serial
timeout result, and fail closed if less than one guest timeout second remains.
Do not use a subshell that could hide environment/cwd changes. Freeze one run
ID, `flr0418-0001`, across controller, guest, QMP, tests, and media exporter.

**Tech Stack:** Python 3 controller/tests, POSIX shell contract, existing Mini
QEMU, guest GDB and Example Demo, QMP raw PPM and fixed media exporter.
No product build, Devtool, `do_patch`, BitBake, image, or cache change.

**Spec:** [FLR-0418 ticket](../../../work/tickets/FLR-0418-preserve-serial-wait-completion.md)

## Evidence baseline

- Predecessor FLR-0417 commit/bundle:
  `e1a3949a7163dcf739975eefa916bfeb72540f06`.
- FLR-0417 run `flr0417-0001` is consumed. GDB API smoke and Example Demo
  launch passed; READY was followed by logout and a serial completion timeout.
- Its final controller record and exact teardown passed; only a black QMP
  pre-launch system still exists. That is not a product-render result.
- Candidate remains unchanged FLR-0410-0001. This ticket uses the new ID
  `flr0418-0001` and must not alter the image.

## Implementation tasks

### Task 1 — add the failing serial protocol regression

- [x] Drive the original wait command through `/bin/sh` with the exact wrapper
  tail; the test failed as expected with READY output and no completion marker.
- [x] Add six marker outcomes for READY, observer error, GDB missing or
  start-token change, guest timeout, and wait-command failure; add a separate
  observer-error+READY priority case. All seven shell scenarios pass locally.

### Task 2 — fix one shell boundary

- [x] Replace shell `exit` paths with function return/status handling under
  `set -eu`; preserve marker priority and distinct outcome names.
- [x] Confirm the command returns normally and leaves the serial shell usable.
- [x] Update active helpers, tests, QMP socket, and exporter to
  `flr0418-0001`; reject any run-ID collision.

### Task 2a — protect the active serial deadline

- [x] Add a red-capable test for fresh, spent, and exhausted ACK windows using
  the actual `_wait_marker`/`_serial` timeout calculation (subprocess mocked).
- [x] Cover both ACK and abort deadlines, 15/15.5/15.999/16/16.5-second
  fractional boundaries, one-second dispatch delay, and insufficient guest
  budget without invoking serial-exec.
- [x] Delay the clock by 11/14 seconds after the command file is prepared;
  prove the final dispatch guard rejects both cases under ACK and abort windows
  without invoking serial-exec.
- [x] Validate the configured marker window as 17–540 seconds in both the
  constructor and CLI parser, before the claim-only branch can consume the run.
- [x] Cap the guest shell loop at `min(requested, floor(remaining)-15)` and
  reject budgets below one second. Bound the serial-exec guest timeout by
  `floor(remaining)-2`; allow its host controller at most two extra seconds,
  capped by the same ACK/abort deadline. Reject an active budget below those
  limits rather than clamping it to one second.
- [x] Run focused shell/deadline regressions and all 99 tests across the
  controller, preflight, GDB observer, snapshot, and media-exporter suites.

### Task 3 — validate and commit locally

- [x] Run focused shell/controller/observer/launcher/exporter tests and the
  full repository suite: Python 348/348, MCP 52/52, canonical/privacy/shell
  pass. `make verify` stops at the known 55 historical Markdown targets;
  FLR-0420 owns that reconciliation.
- [ ] Run runtime-checkpoint and privacy gates after the final log update;
  rerun staged whitespace after explicit staging.
- [ ] Review the explicit diff, commit locally with privacy-safe metadata, and
  do not push.

### Task 4 — transfer and one unchanged-image runtime attempt

- [ ] Use the standard bundle helper with the previous Mini tip as an ancestor;
  verify bundle SHA, exact receiver tip, no competing process/build, artifact
  identity, fresh run/claim/socket, memory/disk, and ports.
- [ ] Start one `flr0418-0001` QEMU under the existing `runqemu` flow. Require
  guest readiness, GDB API smoke, Example Demo launch, and each wait marker to
  complete the serial wrapper before proceeding.
- [ ] Save bounded load/hit/post QMP and present/kernel/process evidence if the
  stages reach them. On the first failure, retain it and stop; do not retry.
- [ ] Quit only the owned QEMU, verify process identity disappearance, socket
  absence and official postflight, then use the fixed allowlist exporter and
  inspect the entire frame. Raw media remains on Mini.

### Task 5 — close only this diagnostic unit

- [ ] Update ticket/log/TASKS, include QMP-only image/video evidence that
  actually exists, hashes, commands, test results, and UNKNOWNs.
- [ ] Run runtime-checkpoint, privacy, link, and branch-state checks.
- [ ] Mark Done only if the serial wrapper contract and runtime finalization
  gates pass. Product 3D/HUD acceptance remains open unless the same image
  independently proves it.
