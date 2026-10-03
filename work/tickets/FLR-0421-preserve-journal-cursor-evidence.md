# FLR-0421 — preserve bounded journal cursor evidence and continue live capture

- Status: In Progress
- Priority: High
- Created: 2026-10-04
- Owner: Mac runtime harness / Mini QEMU / guest journal snapshot / QMP evidence
- Branch: feature-flr-0421-journal-cursor-evidence
- Parent milestone: dev-flr-0421-runtime-evidence
- Predecessor: [FLR-0418](FLR-0418-preserve-serial-wait-completion.md)
- Candidate baseline: unchanged [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Prior attempt: [FLR-0418-0001](../evidence/FLR-0418-0001.md), consumed; never retry
- Working log: [FLR-0421 working log](../logs/2026-10-04-flr0421.md)
- Execution plan: [FLR-0421 plan](../../docs/superpowers/plans/2026-10-04-flr0421-journal-cursor-evidence.md)

## Work unit

Make the guest incremental kernel-journal snapshot distinguish a verified
no-new-entry response from cursor movement, while keeping memory, evidence, and
logs bounded. Then make exactly one new-ID attempt on the unchanged FLR-0410
image. Continue past the deliberate LLVM-load GDB stop only when the journal
anchor is proven unchanged; capture the first post-release full-screen QMP
frame and all available present/kernel/process evidence. This is an observation
harness ticket, not a product-render acceptance ticket.

## Problem

### Purpose

FLR-0418 fixed the serial-shell completion boundary, but its one authorized
run stopped at the next snapshot gate. The guest reported
`kernel_journal_empty_marker_conflicts_with_returned_cursor`; the controller
aborted before releasing Flutter from the deliberate `catch-load-libLLVM`
breakpoint. This prevents a live post-render observation. The exact returned
cursor and query output were not retained, so the previous failure cannot be
classified retrospectively.

### Success measure

The parser accepts only a fully verified no-new-entry response: either the
exact empty marker without a cursor, or that marker plus exactly one valid
cursor byte-for-byte equal to the saved anchor, with successful anchor checks
before and after. Changed/ambiguous/oversized/partial output remains fail-closed.
One fresh run records redacted query evidence and reaches a post-release QMP
capture if and only if the acceptance rule is met. No product success is
claimed unless the actual post-release pixels support it.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Incremental kernel-journal read returns the explicit empty marker and at least one cursor; current parser rejects the combination | FLR-0418-0001 manifest; guest helper at `work/commands/flr0416_guest_snapshot.py` |
| Where | Guest snapshot process, after GDB reports all Example Demo threads stopped at the LLVM load boundary and before renderer release | FLR-0418-0001 load-ready and failure records |
| When | First snapshot after `load-ready.json` in one run on unchanged FLR-0410-0001 | FLR-0418-0001 working log/evidence |
| Who | Guest journal snapshot helper; host capture controller consumes its marker and controls release/abort | `scripts/flr0416_live_capture.py`, guest helper and controller records |
| How | Successful query output contains `-- No entries --` and a returned cursor; no returned value was saved, so anchor equality and rotation state are unknown | Exact failure reason retained; no incremental journal-output record exists |

### Priority selection

- Compared strata: product renderer / GDB-stop boundary / guest snapshot cursor.
- Selected focus: snapshot cursor gate, the first failing process boundary after a valid READY and serial completion marker.
- Selection evidence: the capture stopped before renderer release; changing product materials, camera, or composition now would not address the observed stop.

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| Save baseline | Current boot kernel journal and cursor | Create-only baseline with cursor and fault count | Baseline record exists on Mini | FLR-0418-0001 run directory |
| Verify anchor before query | Saved opaque cursor | Exactly one resolved cursor equals saved value | Result was not retained | Snapshot helper implementation; no anchor-probe artifact |
| Read delta | `--after-cursor` plus `--show-cursor` | New records, or exact no-new marker with an unambiguous cursor | Error says empty marker conflicted with cursor | FLR-0418-0001 serial result |
| Verify anchor after query | Same saved cursor | Exact same cursor still resolves | Result was not retained | Snapshot helper implementation; no anchor-probe artifact |
| Decide release | Complete, valid snapshot | Continue observer and QMP flow | Controller requested abort before release | FLR-0418-0001 controller final |

### Problem point

The first non-normal boundary is the guest journal snapshot classification. The
current rule rejects every empty-marker-plus-cursor response without comparing
the returned cursor with the independently validated saved anchor. Separately,
the query uses `capture_output=True` and checks the byte limit only after the
entire output has been buffered.

### Ideal condition

The journal query has a strict output/time/line memory bound. It emits only a
redacted summary: return code, completion/truncation state, byte counts and
SHA-256 values, output classification, cursor count/hash/equality, and
before/after anchor-probe outcomes. No raw cursor or journal line is emitted or
persisted in host evidence. Truncation, timeout, extra output, and ambiguity
cannot be interpreted as an empty journal.

### Current condition — Facts

- FLR-0418-0001 reported the exact parser error after valid GDB readiness,
  ordinary Example Demo launch, and the corrected serial completion marker.
- All app threads were stopped at `catch-load-libLLVM` / `__GI__dl_debug_state`;
  the capture controller safely aborted before releasing them.
- The full-screen pre-launch and load QMP frames were identical black frames.
  This is before product rendering and cannot classify the Sequoia result.
- The Mini run directory has no incremental journal stdout/stderr or anchor
  probe record. The helper emitted only the failure reason. The exact returned
  cursor and guest systemd version are therefore not recoverable for that run.
- The current test rejects an empty marker paired with a cursor different from
  the supplied anchor, but it does not cover the equal-cursor case.

### Gap

The parser lacks a safe equality discriminator and useful bounded failure
evidence. Its current size check does not bound subprocess buffering.

### Impact

The product renderer cannot reach a live QMP frame through this capture flow;
the current all-black image is not a product verdict. Unbounded buffering could
also make a noisy journal query consume excessive guest memory.

### Point of occurrence

Guest snapshot command, in the incremental journal query and its two cursor
anchor probes. No product source, material, camera, lighting, or surface
composition stage has yet been reached in this attempt.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| Parser falsely rejects a valid empty delta whose returned cursor equals the validated anchor | Returned cursor equals the saved cursor; both anchor probes resolve exactly; query has only the empty marker and one cursor line | Preserve hashes, equality boolean, probe results, and output classification in the fresh attempt | Plausible, unproven | Existing code/test; FLR-0418 did not retain the pair |
| Anchor rotated or query resumed at a different entry | Returned cursor differs, or one anchor probe fails/resolves elsewhere | Compare in-memory cursor bytes and both exact probes; any mismatch must stop the flow | Plausible, unproven | Previous run lacks query/probe output |
| Output was truncated/oversized, stderr was nonempty, or another query error was conflated with an empty result | Nonzero status, stderr, timeout, line/total output cap, extra output, or incomplete process | Bounded collector reports partial/oversized/timeout and parser fails closed | Not tested on the guest yet | Existing code checks size only after capture |

### Confirmed root cause

UNKNOWN. FLR-0418 proves where the controller stopped, not whether the
returned cursor equaled the baseline or whether the journal rotated.

### Minimal countermeasure

Stream stdout and stderr concurrently in fixed-size chunks with strict total
byte and per-line ceilings. Hash/count bytes as received; retain only parser
state for the marker, cursor, and bounded fault categories. On limit, timeout,
or truncation, terminate and reap the child, mark the evidence incomplete, and
fail closed. Accept an empty delta only under the exact marker/anchor rule
above. Emit redacted diagnostics, never raw journal text or cursor values.

## Scope

### In scope

- Guest snapshot journal query and anchor-probe collector, parser, and
  redacted diagnostics.
- Deterministic tests for equal/different/missing/duplicate/malformed cursors,
  extra output, query errors, anchor movement, oversized output/lines, timeout,
  simultaneous stdout/stderr, process reaping, and no raw-value leakage.
- Change the active run-bound harness literals and fixtures from consumed
  `flr0418-0001` to fresh immutable `flr0421-0001`, preserving the old source
  revision in Git history.
- One same-image Mini runtime attempt, exact teardown, fixed allowlist export,
  and QMP inspection after renderer release if the gate passes.

### Out of scope

- Product source, Devtool, recipe, patch, image, BitBake, or cache changes.
- Any cursor bypass, raw-journal dump, GDB release that ignores failed
  verification, second attempt, second QEMU, or reuse of a consumed run ID.
- Declaring 3D, lighting, texture, camera, HUD composition, interaction,
  five-minute stability, or two-boot acceptance complete.

## Success criteria

1. Red-before-fix unit tests prove the parser currently rejects the safe
   equal-cursor case. The corrected parser accepts only exact empty output with
   zero cursor, or exact empty marker plus one valid cursor equal to the saved
   anchor, with both independent anchor checks passing.
2. Every different, duplicate, malformed, missing-required, extra-line,
   nonzero-exit, stderr, timeout, oversized, line-overflow, or incomplete
   observation fails closed. All subprocesses are terminated and reaped.
3. Tests prove stdout/stderr are drained concurrently, output is bounded before
   storage grows beyond the configured cap, and emitted evidence contains no
   raw cursor or raw journal line.
4. Focused tests, full Python/MCP checks, privacy, shell syntax, file-size,
   QEMU-harness, staged-whitespace, Markdown, and runtime-checkpoint results are
   recorded honestly. Preserve any unchanged historical Markdown failures.
5. Commit locally without push and use the standard fixed-path bundle helper.
   Before QEMU, confirm exact Mini tip, exact unchanged FLR-0410 image identity,
   idle build, one-QEMU ownership, free run ID/ports, and available resources.
6. Run exactly one `flr0421-0001` attempt. Release from the LLVM-load stop only
   when the evidence proves the acceptance rule. Capture a full-screen QMP
   still and available frame sequence after release, preserve present/kernel/
   process evidence, then verify exact teardown and postflight. If any gate
   fails, stop and preserve the failure; do not retry.
7. Report Sequoia/HUD pixels as UNKNOWN unless the captured live frame actually
   proves them. This bounded ticket is not the overall 3D goal.

## Hypotheses

1. The new cursor is identical to the twice-validated baseline: the prior error
   was a parser over-rejection. Accept exactly this case and proceed to live
   renderer observation.
2. The new cursor differs or an anchor probe fails: retain fail-closed behavior;
   investigate journal rotation/query semantics under a separate ticket.
3. A size/line/time limit is reached: classify the observation as incomplete,
   terminate/reap, and do not release the app based on truncated data.

## PDCA

### Plan

- Add the equal-cursor acceptance test first and demonstrate it failing against
  the current parser. Keep the changed-cursor rejection as a negative control.
- Add a streaming, dual-pipe, byte/line/time-bounded journal collector. Retain
  only counts, hashes, category summaries, cursor equality, and probe outcomes.
- Replace only active run-ID literals/fixtures with `flr0421-0001`; keep all
  older source and evidence intact in parent commits.
- Validate locally before the standard bundle handoff. No BitBake build is
  required because no image, source, recipe, or package changes are in scope.
- Make one new-ID runtime attempt only after a fresh no-owner/resource/image
  preflight. On the first failure, preserve evidence and stop.

### Do

- TDD red was observed for the exact-empty-marker/equal-anchor case against the
  original parser. The streaming collector and equality classifier are now in
  place; focused tests cover equality, changed/duplicate cursors, rotated
  anchors, overflow, timeout, dual-pipe drain, and child reaping.
- The host decoder now accepts only the bounded journal diagnostic schema and
  rejects unknown/raw-value fields before they can enter controller errors.
  Its reason field is also a finite safe-code allowlist; arbitrary error text is
  never emitted into controller errors. GPT-6.1 Sol identified this as a P2
  privacy risk, and a red test reproduced the leak before the allowlist fix.
  Valid, malformed, oversized, unknown-field, unhashable-value, and unsafe
  reason cases now have coverage.
- Focused local command: `python3 -B tests/test_flr0416_guest_snapshot.py`
  (23/23 PASS), `python3 -B tests/test_flr0416_live_capture.py` (52/52 PASS),
  `python3 -B tests/test_flr0416_gdb_observer.py` (16/16 PASS),
  `python3 -B tests/test_flr0416_media_preview.py` (11/11 PASS), and
  `python3 -B tests/test_flr0416_qemu_preflight.py` (15/15 PASS). Total: 115
  tests PASS after the safe-reason tests. The controller-claim failure line is an expected negative-case
  test. `bash -n work/commands/FLR-0416-qemu-start.sh` and `git diff --check`
  also PASS; active helper/test scan found no consumed 0418 run literal.
- A filtered, read-only Mini process inventory found no QEMU, runqemu, BitBake,
  Podman, or `flutter-auto` command line. This is only an initial snapshot, not
  the mandatory immediate pre-run ownership/resource/image gate.
- A read-only Mac executable-name check found the existing Podman `gvproxy` and
  `vfkit` processes. They were left untouched; no QEMU or BitBake process was
  found by the executable-name filter.
- Full `make verify` reached the Markdown gate after canonical/privacy/shell,
  Python, and MCP checks. The final Python-only rerun passed 366/366. File-size,
  QEMU-harness, runtime-log-slice, Devtool finish/component, Mini recipe-patch,
  and Mini bundle-handoff contract targets all passed. The Markdown gate
  reports 55 missing evidence targets in historical tickets; a filtered check
  found no broken links in TASKS, FLR-0418/0421/0422, or the 0421 plan/log.
- No bundle, BitBake, build, or QEMU attempt has been made. Record subsequent
  commands and results here through the linked working log; do not duplicate
  raw runtime logs here.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Safe empty-cursor rule | Equal accepted; all changed/ambiguous values rejected | Equal-anchor accepted only with both exact probes; changed/duplicate/moved-anchor cases reject | 23 guest snapshot tests | PASS (local unit boundary) |
| Bounded collector | Dual-pipe, byte/line/time caps; child reaped | Byte cap, line cap, timeout, concurrent pipes, and reap tests pass | Guest snapshot collector tests | PASS (local unit boundary) |
| Privacy-safe evidence | Hash/classification only; no raw cursor/journal text | Guest output and host error decoder preserve allowlisted summaries and reject raw/unknown fields and reasons | Guest leak tests and 52 host capture tests | PASS (local unit boundary; runtime not yet observed) |
| Full local repository gates | Run focused/full Python, MCP, shell, privacy, size, QEMU, Markdown, Devtool/bundle checks | Python 366/366 PASS; other code/contract checks PASS; Markdown reports 55 historical missing targets, none in current files | `make verify`, focused gate commands, filtered Markdown-link check | PASS WITH HISTORICAL FAILURES; staged checks pending |
| Fresh Mini attempt | Exact image, new ID, post-release QMP if journal gate permits | Pending | FLR-0421-0001 evidence manifest | UNKNOWN |
| Product rendering | Real Sequoia and HUD acceptance | Not in this ticket; global goal remains open | Live QMP required | UNKNOWN |

### Act

- Standardize the collector only after tests and Mini evidence pass. If the
  journal boundary is resolved but product pixels remain absent or unstable,
  create a separate ticket based on the first observed renderer/present/
  composition boundary. Never turn a diagnostic bypass into a product fix.

## Decision log

- GPT-6.1 Sol reviewed scope and recommends closing FLR-0418 as a bounded
  unsuccessful attempt, using a new immutable ID, accepting the empty marker
  only when its optional returned cursor exactly equals the verified anchor,
  and retaining the no-cursor empty case only with both anchor checks.
- Sol also identified that post-capture size checks do not bound memory. This
  ticket therefore includes a narrowly scoped streaming collector. It does not
  silently cap journal lines or accept truncated output.
- The host-side FAIL-marker parser was reviewed and tightened after noticing
  that decoded diagnostic JSON could otherwise be copied wholesale into a
  controller error. GPT-6.1 Sol identified a separate P2 risk: the normalized
  free-form `reason` could still contain a cursor-like string. The guest now
  emits a finite reason code and the host validates the same finite set. A red
  regression test reproduced the leak before this fix; host/guest suites now
  pass. The guest runtime remains the final integration check.
- Redacted diagnostics are retained rather than raw cursor/journal values:
  command status, complete/partial marker, byte count/hash, exact parsed shape,
  cursor count/hash/equality, and each anchor-probe result. Temporary use of the
  cursor as the journalctl argument remains visible to the guest process while
  that command runs; durable artifacts and host logs must not expose it.

## Unknowns

- Whether FLR-0418's returned cursor equaled the saved cursor; its output and
  anchor-probe results were not recorded and cannot be reconstructed.
- Guest systemd version/build identity for FLR-0418; FLR-0421 must record the
  version tied to the exact unchanged rootfs identity.
- Whether FLR-0421's query passes, whether the load breakpoint can be released,
  first present progression, live Sequoia/HUD pixels, kernel Oops, five-minute
  stability, interaction/repaint behavior, and a second-boot reproduction.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings: Do not mark Done until the bounded parser/collector tests, the one
  fresh-ID runtime/teardown boundary, and required repository gates are checked.
  No product rendering acceptance is inferred from snapshot or harness success.
