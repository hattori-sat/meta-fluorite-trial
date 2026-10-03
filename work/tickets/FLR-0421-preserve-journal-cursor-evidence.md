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
- Runtime evidence: [FLR-0421-0001](../evidence/FLR-0421-0001.md), consumed; never retry
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
- No product-image change, BitBake task, or image build was run. The standard
  bundle handoff and one unchanged-image QEMU attempt are recorded in the
  outcome section and linked working log; raw runtime logs remain on the Mini.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Safe empty-cursor rule | Equal accepted; all changed/ambiguous values rejected | Equal-anchor accepted only with both exact probes; changed/duplicate/moved-anchor cases reject | 23 guest snapshot tests | PASS (local unit boundary) |
| Bounded collector | Dual-pipe, byte/line/time caps; child reaped | Byte cap, line cap, timeout, concurrent pipes, and reap tests pass | Guest snapshot collector tests | PASS (local unit boundary) |
| Privacy-safe evidence | Hash/classification only; no raw cursor/journal text | Guest output and host error decoder preserve allowlisted summaries and reject raw/unknown fields and reasons | Guest leak tests and 52 host capture tests | PASS (local unit boundary; runtime not yet observed) |
| Full local repository gates | Run focused/full Python, MCP, shell, privacy, size, QEMU, Markdown, Devtool/bundle checks | Python 366/366 PASS; privacy, file-size, runtime-log-slice, active-ticket checkpoint, and staged-whitespace checks PASS; Markdown reports 55 historical missing targets, with no errors in touched files | `make verify`, focused gates, and changed-file Markdown filter | PASS WITH HISTORICAL FAILURES; changed-file links PASS |
| Fresh Mini attempt | Exact image, one new ID, post-release QMP only after every release gate passes | One exact unchanged-image run; load release accepted; hit release refused because caller mapping was UNKNOWN; no post-release capture; QMP quit and postflight passed | [FLR-0421-0001 evidence](../evidence/FLR-0421-0001.md) | FAIL-CLOSED / PARTIAL; no retry |
| Product rendering | Real Sequoia and HUD acceptance | Not in this ticket; global goal remains open | Live QMP required | UNKNOWN |

### Act

- Standardize the collector only after tests and Mini evidence pass. If the
  journal boundary is resolved but product pixels remain absent or unstable,
  create a separate ticket based on the first observed renderer/present/
  composition boundary. Never turn a diagnostic bypass into a product fix.

## FLR-0421-0001 outcome

- The fixed bundle handoff updated the authoritative Mini receiver to
  `604e3fbbf6ba9b4aae85d3cb59cd77ac32ea5009`; effective build roles and the
  unchanged FLR-0410 kernel/rootfs/qemuboot hashes passed.
- Immediate ownership/resource preflight and 12-file staging passed. One QEMU
  run started. Guest load readiness and load-stage release acceptance passed,
  so the journal cursor gate did not block this run.
- At the next temporary hardware breakpoint, target PC/process identities and
  the QMP bracket matched. `caller_mapping` was `UNKNOWN` with
  `errors.caller_mapping=ValueError`; release was correctly blocked by
  `caller_mapping_unknown`. The capture exited 1 after recording the abort.
- The Mini-only hit still and eight-frame sequence are preserved. The still is
  1280×800 P6 PPM, SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  Its frozen hit-boundary pixels are not a post-release product verdict. The
  video preview remains pending; no media was copied to the Mac.
- Present counters stayed `2/1/1` across the stopped hit bracket; kernel fault
  delta was zero. Neither measurement establishes post-release progress.
- QMP quit, exact cleanup, and postflight passed. No target owner or QMP socket
  remained and all reserved ports were free. See the linked evidence manifest
  for the bounded record and limits.

### Evidence boundary and next discriminator

The immediate failure is in the GDB evidence gate, not proven product code.
The callback takes `gdb.selected_frame().older().pc()` and asks the resolver to
find exactly one executable `/proc/PID/maps` range; see
[`flr0416_gdb_callback.py`](../commands/flr0416_gdb_callback.py) and
[`flr0416_gdb_observer.py`](../commands/flr0416_gdb_observer.py). The run saved
the exception class but not its safe reason or same-stop map rows. Therefore:

1. the caller frame/unwind may have produced an unusable PC; or
2. the PC may be valid but no unique executable map range matched it, including
   a non-executable, out-of-range, or interval-boundary case.

Neither is confirmed. GPT-6.1 Sol advises replaying the exact caller PC against
the exact hit-time map snapshot with a preserved match count and finite reason
code. That snapshot was not saved, so it cannot be reconstructed from this
run. [FLR-0423](FLR-0423-capture-caller-mapping-provenance.md) owns that
separate provenance task. Keep this ticket In Progress: its post-release QMP
success measure was not met, and the overall product goal remains open.

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
- Guest systemd version/build identity tied to the unchanged FLR-0410 rootfs.
- The exact reason `caller_resume_pc` failed executable-map resolution and the
  caller-frame unwind provenance; the same-stop map snapshot is absent.
- Any post-release present progression, live Sequoia/HUD pixels, post-release
  kernel Oops state, five-minute stability, interaction/repaint behavior, and a
  second-boot reproduction.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings: Unit and local repository checks passed, and the one authorized
  fresh-ID runtime attempt plus teardown completed. The required post-release
  QMP capture did not occur because the caller-map gate failed closed. Keep this
  ticket In Progress; do not infer product rendering acceptance from snapshot,
  GDB hit, or harness success. FLR-0423 is the separate next issue.

## Repository/PR integration gate — 2026-10-04

### Facts

- The worktree is clean at `216e5f1`. Fresh local checks passed: privacy,
  runtime checkpoint (`active=1`), file size, and runtime-log slice.
- Remote refs are `origin/main` at `5770cec`, `origin/dev-foundation` at
  `aaa3671`, and `origin/dev-fluorite-demo` at `3616e71`. The local intended
  milestone `dev-flr-0421-runtime-evidence` is at `1fb42ee`; its reflog says
  `branch: Created from HEAD` at the FLR-0418 feature tip.
- `origin/main` is an ancestor of the local milestone, which is 155 commits
  ahead. The feature is 3 commits ahead of that local milestone (24 files,
  +2,652/−236), but diverges from `origin/dev-fluorite-demo` (158 local-only,
  14 remote-only; three-dot diff 2,080 files, +217,421/−316).
- An escalated `git push --dry-run` reported a new branch would be created; it
  made no remote change. No push, PR, merge, cherry-pick, or branch rewrite was
  performed. Fetching the observed remote heads only added local
  remote-tracking refs; the worktree stayed clean.

### Inference and decision — initial review; superseded below

- The local target isolates this ticket's commit range but does not prove that
  its 155-commit milestone snapshot was integrated under the required branch
  workflow. Existing remote `dev` branches would pull in extensive history.
- GPT-6.1 Sol's read-only review found no safe existing remote base for a
  ticket-scoped PR and recommended a reviewed baseline-recovery disposition.
- Keep FLR-0421 open and its single runtime ID consumed. Do not publish or merge
  this branch until [FLR-0424](FLR-0424-reconcile-feature-pr-baseline.md)
  resolves the baseline provenance. FLR-0423 remains Inbox behind that gate.

### UNKNOWN — initial review; superseded below

- Whether the local milestone's 155 commits form the approved FLR-0421 milestone
  dependency set, or include unrelated/unreviewed feature work.
- The policy-compliant way to publish the milestone without broadening a
  ticket-scoped PR or rewriting protected history.

## Final publication disposition — 2026-10-04

- Follow-up topology inspection confirmed `origin/main` (`5770cec`) is an
  ancestor of local `dev-flr-0421-runtime-evidence` (`1fb42ee`), which has 122
  first-parent commits and 4 merge commits after main. The initial no-safe-base
  review above is superseded by GPT-6.1 Sol's updated read-only review.
- Sol's final verdict is **GO for publication only**: push the existing local
  milestone at exactly `1fb42ee` as a new remote `dev` ref, then push the
  FLR-0421 feature and create a feature-to-dev PR. This does not authorize a
  merge, certify the 155 prior commits, or permit changing existing refs.
- At review tip `29c4294`, the feature range was 4 commits / 25 files
  (+2,823/−236). The only subsequent planned change is this docs-only decision
  record; recompute exact range and rerun privacy checks before publication.
- Full-range privacy checks passed at review tip for
  `origin/main..dev-flr-0421-runtime-evidence` and
  `dev-flr-0421-runtime-evidence..HEAD`. They must pass again after this update.
- FLR-0424 records the completed baseline disposition. FLR-0421 remains In
  Progress because the required post-release QMP capture and product behavior
  are still UNKNOWN.

### Remaining UNKNOWN

- Whether all 155 commits on the local milestone have been independently
  reviewed as a dependency set. Publication exposes that history for review but
  is not approval of its integration.
- Actual remote publication, PR review/integration, and any post-release
  Sequoia/HUD runtime evidence have not occurred yet.
