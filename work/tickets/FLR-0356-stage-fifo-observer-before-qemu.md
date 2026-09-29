# FLR-0356 — stage the FIFO observer before QEMU launch

- Status: Waiting
- Wait reason: the observer ran, but the official FIFO gate failed closed at `marker-not-first`; FLR-0358 must repair serial framing and use a fresh run ID before this ticket can close.
- Priority: High; blocks the actual-FD FIFO gate and next production runtime observation
- Owner: Mac runtime-harness / Mini QEMU / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0355](FLR-0355-relay-run-id-and-retest-fifo-gate.md)
- Plan: [FLR-0356 plan](../../docs/superpowers/plans/2026-09-29-flr0356-stage-fifo-observer.md)
- Working log: [FLR-0356 log](../logs/2026-09-29-flr0356.md)
- Fresh run ID: `flr0356-0001` (one attempt only)

## Purpose

Prevent the FLR-0355 failure mode by making the runner's static serial-command
staging list a tested contract, staging every command into the run evidence
parent before QEMU starts, and retaining a copy under the QEMU run directory.
Then use one new, unchanged-image Mini QEMU attempt to actually evaluate the
FIFO observation gate and continue to QMP capture/cleanup. This is still a
diagnostic harness task; it does not modify the image or claim 3D success.

## Facts

- FLR-0355's sole run ID, `flr0355-0001`, is consumed and must not be retried.
- In that run, Mini receiver/bundle identity, pinned artifact hashes, guest
  readiness, guest preflight, GDB-script transfer, and paused-wrapper launch
  passed. The runner then failed with `command-file-not-readable` while trying
  to execute `FLR-0350-observe-fifo-read-gate.cmd`.
- The observer command is present in the repository and passes shell syntax
  validation. It appears in the runner's static command-name checks and in a
  `guest_run` callsite, but the later runtime copy list omits it. `guest_run`
  searches both the QEMU run directory and its evidence parent; neither had
  that file.
- Consequently, the actual-FD FIFO predicate, GDB attach, and GO were not
  reached. QMP captured a uniformly black frame and eight identical frames;
  this is not evidence about Flutter drawing. Targeted app/FIFO/QMP teardown
  passed with zero residual runtime processes.
- No product source, layer, recipe, image, or pinned QEMU artifact was changed.
- FLR-0355's detailed command result, QMP image hash, pixel analysis, and
  cleanup markers are recorded in its linked working log and Mini evidence
  root. The new run must use a new ID and retain its own evidence separately.

## Runtime result — `flr0356-0001`

- Bundle handoff reached receiver tip `969d93c331befba7579f5f376bcf03c80c771aa0`;
  bundle SHA-256 `73d703ce6136bae2c097eb00c0ed5ae582e208de79b0f9991237bccc9102c831`.
- Mini static check passed all 28 tests. The fixed QEMU artifact/hash, process,
  port, and unused-ID preflight passed. Before QEMU start, all 11 serial command
  files were staged into the run evidence parent.
- Guest readiness passed on SSH attempt 12. Guest preflight, all four GDB
  transfer chunks, script installation, and the paused launch wrapper passed.
- The FIFO observer executed and emitted a complete record: the target process
  was `read`-blocked on a FIFO; target and gate were both device 40 / inode 23;
  PID/start-time/UID/command fields matched the launch record. However, the
  host validator rejected the serial file as `marker-not-first`, so its
  official gate verdict was FAIL and GDB attach/GO were correctly not run.
- The captured serial file begins with the previous `stty -echo` response and
  shell prompt immediately before `FLR0350_GATE_OBSERVATION`. The host parser
  requires the marker to be the first token. Source review found that
  `serial-exec` clears its receive buffer before the echo-off command, but does
  not clear the accumulated echo-off response before sending the requested
  command. This is the first proven host-side divergence; a fix belongs to a
  separate ticket and is not included here.
- QMP captured a 1280×800 still and eight 1-fps frames. Still and all frames
  share SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  Full frame: 1,024,000 black pixels, zero changed/edge/chromatic pixels,
  luma `[0,0]`. Fixed 3D ROI `[0,200,1280,600]`: 768,000 black pixels and
  zero changed/edge/chromatic pixels. Since the wrapper never received GO,
  this is not a Flutter/Filament render verdict.
- QMP teardown and targeted cleanup passed: zero residual target processes and
  zero QMP socket. No image/build/product-source change occurred.

## Capability contract

| Field | Contract |
| --- | --- |
| Requested capability | Reliably run the actual-FD FIFO observation and continue the bounded production diagnostic sequence. |
| Target/environment | Existing fixed Mini receiver and pinned FLR-0335 `runqemu` artifacts; no image build. |
| Stimulus | One runner invocation using `flr0356-0001`; same diagnostic profile and QEMU arguments. |
| Expected observation | Every statically referenced `guest_run` command is validated and staged before QEMU launch; observer reaches the guest and returns a gate result before attach/GO. |
| Repeatability | One attempt; the run ID is consumed once its evidence directory exists. |
| Identity | Exact feature commit/bundle hash, receiver revision, pinned artifact hashes, run ID, QMP socket/process, guest wrapper identity, and actual FIFO object identity. |
| Evidence | Red/green staging regression, local and Mini static checks, bounded serial/GDB outputs, QMP still and eight frames, MP4, pixel analysis, artifact hashes, and exact teardown. |
| Scope/stops | Harness/tests/docs only; no BitBake/Devtool/image changes. Stop before launch if any static command is unstaged/unreadable, receiver differs, run ID is used, a target process/port/socket is occupied, or artifact hashes differ. Do not retry the run ID or use global kills. |

## 4W1H and focus

| Dimension | Observation |
| --- | --- |
| What | The host runner called a static guest command absent from its staging list, so the diagnostic stopped before the actual-FD FIFO check. |
| Where | Mac runner command inventory/copy loop → Mini evidence parent/QEMU run directory → guest serial harness. |
| When | After the paused production wrapper launched and before GDB attach or GO. |
| Who | Mac harness role owns command inventory and local regression; Mini QEMU role owns exact receiver/image preflight and one launch; QMP role owns pixels/video and cleanup evidence. |
| How | Parse static `guest_run` command references against one declared staging array; verify sources and stage them before QEMU start; run once under a fresh ID. |

### Ranked hypotheses

1. **Confirmed:** an omitted static staging entry caused FLR-0355's host-side
   `command-file-not-readable` failure. The runner source list and bounded
   harness output agree.
2. **Unknown:** after staging is repaired, the guest supports the observer's
   `stat` invocation and reports stable process/FIFO identity.
3. **Unknown:** the actual blocked `read` FD names the run-owned FIFO; the gate
   must compare type/device/inode, not pathname alone.
4. **Unknown:** after a valid gate, GDB attaches and the producer/wait path
   reaches the bounded watch window.
5. **Independent visual question:** whether the resulting QMP image contains
   HUD or 3D pixels. Logs and gate markers cannot substitute for pixels.

## Root-cause and countermeasure

The first proven process defect is in host-side preparation: command existence
and call ordering were tested separately, but the actual static command
callsite set was not compared with the list copied into the run directory. The
minimal countermeasure is one declared static-command array, a regression
asserting that every fixed `guest_run` command is in that array, a pre-launch
readability check, and staging into the evidence parent before the QEMU start
call. After start, the same staged inputs are copied into the QEMU run folder
for attribution. There is no product, build-time, packaging, or image-runtime
impact. Integration risk is isolated to the shell runner and its tests.

## Scope

### In scope

- A red/green test covering all fixed `guest_run` command files and pre-launch
  staging order.
- The minimal staging-list/copy-loop correction, including the FIFO observer.
- Refresh the static fresh-ID sample to `flr0356-0001` without changing the
  shared run-ID validator or the consumed-ID policy.
- Local focused tests/static checks, privacy/checkpoint gates, one exact bundle
  handoff, one unchanged-image QEMU/QMP run, and teardown.

### Out of scope

- Flutter, Filament, product source, recipes, image contents, Devtool, BitBake,
  pinned artifacts, camera/light/material changes, or QEMU profile changes.
- Reuse of `flr0355-0001`, a second attempt under this ticket, a build, or any
  global process kill.
- Claiming that FLR-0355's black screenshot is a rendering failure or that a
  gate/present/log marker alone proves visible 3D.

## Success criteria

- [x] A new test fails before the staging correction because the observer
  callsite is missing from the staged command set.
- [x] The test passes after correction and proves all static guest commands
  are source-readable and staged before the QEMU `start` invocation.
- [x] Local focused tests, shell/static `--check`, privacy, and checkpoint
  validation pass; no product/image/build inputs change.
- [x] The exact committed bundle reaches the fixed Mini receiver; the new
  one-shot run ID, processes, ports, evidence path, and artifact hashes pass
  preflight.
- [x] One `flr0356-0001` run reaches the actual-FD observation before GDB
  attach/GO. The observation was captured but the host parser failed closed on
  `marker-not-first`; no retry was made.
- [x] QMP still/eight-frame capture, full-frame and fixed 3D ROI analysis,
  H.264 video, hashes, and pixel evidence are recorded and shown. The frames
  are black because GO was not sent; they do not establish a rendering result.
- [x] Targeted app/FIFO/QMP/QEMU cleanup passes with no residual target process
  or socket. The 3D verdict remains pixel-based and separate from the gate.

## Plan / Do / Check / Act

### Plan

1. Add a failing test that extracts static command references and compares
   them to the runner's declared staging array; assert the staging loop occurs
   before QEMU start.
2. Add the omitted observer and any other missing fixed command, validate
   source readability before side effects, and stage to the evidence parent
   before QEMU launch.
3. Run focused/static/privacy/checkpoint gates and commit only FLR-0356 files.
4. Transfer the exact bundle through the existing fixed receiver helper.
5. Verify target and pinned-image preconditions, then run once with the new ID.
6. Analyze and show QMP evidence, preserve bounded logs, and prove teardown.

### Do

- Root cause and FLR-0355 evidence are linked in Iteration 1 of the working
  log. The implementation has not started at ticket creation.

### Check

| Gate | Expected evidence | Result |
| --- | --- | --- |
| Staging regression | Red before fix; green after; every fixed callsite covered | PASS: red was missing inventory; then all 28 focused tests passed, including the callsite-to-inventory check and pre-start order |
| Local runner/static | Focused tests and `--check` | PASS: shell syntax, 28 tests, exact profile, 11 command files, and `QEMU_NOT_STARTED` |
| Privacy/checkpoint/whitespace | privacy scan, ticket/log contract, and staged whitespace | PASS |
| Bundle handoff | exact hash/tip and clean fixed receiver | PASS: exact tip and bundle SHA recorded above |
| Runtime | fresh ID, pinned artifact identity, actual-FD observation | Observation emitted; host validation failed closed at `marker-not-first`; no attach/GO |
| Visual | QMP still/eight frames/video and ROI pixel summary | CAPTURE PASS; uniform black before GO, not a rendering verdict |
| Teardown | app/FIFO/QMP/QEMU zero residue | PASS: zero residual targets and QMP socket |

### Act

- The staging defect is fixed and directly exercised. Preserve
  `flr0356-0001` as consumed. Track the independent serial receive-buffer
  framing defect in a new ticket; do not broaden this staging change to include
  it.

## Visual evidence

- QMP still preview: local review PNG SHA-256
  `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.
  The screenshot was shown during this task. It is uniformly black because the
  observer parser stopped the paused wrapper before GDB attach/GO.
- ![FLR-0356 QMP-only full frame captured before GO](../evidence/FLR-0356-qmp-pre-go-black.png)
- H.264 review video: 1280×800, 1 fps, 8 frames / 8 seconds, SHA-256
  `82e5f5a0490e7354ff44f6105d4eb6c17c31e16c51e064e33648f0a7d42df2e4`.
- The still, eight QMP PPMs, pixel reports, and bounded gate logs are retained
  outside Git under the one per-run Mac review directory and the fixed Mini
  evidence root. No kernel/rootfs/QEMU disk image was copied to the Mac.

## UNKNOWN

- Whether the official host validator accepts the gate after serial receive-
  buffer framing is corrected.
- Whether GDB attach/GO reaches producer correlation and its watch window.
- Whether Flutter draws HUD or 3D once the paused wrapper is released.
- Whether any 3D geometry/color is visible in the QMP ROI.
