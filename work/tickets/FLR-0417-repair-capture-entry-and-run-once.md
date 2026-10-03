# FLR-0417 — repair capture entry/finalization and run once

- Status: Done
- Priority: High
- Created: 2026-10-03
- Owner: Mac capture controller / Mini QEMU / UID-1001 Example Demo / QMP evidence
- Branch: `feature-flr-0417-capture-entry-once`
- Predecessor: [FLR-0416](FLR-0416-correlate-libllvm-hit-with-present-and-qmp.md)
- Candidate baseline: [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Consumed attempt: `$BUILD_EVIDENCE/flr0416-0001/qemu/`
- Working log: [FLR-0417 working log](../logs/2026-10-03-flr0417.md)
- Execution plan: [FLR-0417 plan](../../docs/superpowers/plans/2026-10-03-flr0417-capture-entry-once.md)

## Work unit

Repair the observation startup/finalization path, then perform exactly one
fresh diagnostic attempt on the unchanged FLR-0410 image using immutable run ID
`flr0417-0001`. The attempt is diagnostic only: it must first pass explicit
repository-cwd, exact-process identity, fresh-evidence, ownership, port, and
artifact gates; then perform the guest GDB API smoke before launching Flutter;
then correlate the first-hit observer with bounded present/kernel/QMP evidence
or preserve the earliest failure and fully finalize the run.

This ticket does not modify product source/layer state, use Devtool, run
`do_patch`, build an image, change caches, or declare the Fluorite 3D goal
complete. The preceding `flr0416-0001` evidence is immutable and consumed.

## Purpose and success measure

FLR-0416's one attempt booted the unchanged image and reached guest SSH
readiness, but the controller failed before guest setup because the canonical
guard inherited the SSH working directory. The guard failed from the remote
default directory and passed when explicitly run from the receiver root. The
later exception also occurred after the QEMU PID/start identity had been
validated but before `run()` copied it into the final record. Independent QMP
quit/PID disappearance/socket/postflight checks passed, while the structured
record correctly remains `teardown_verified=false` without that identity.

The success measure is a deterministic one-shot observer that cannot be
confused by the caller's working directory, cannot erase or reuse evidence,
cannot let a second controller tear down the first one's QEMU, and retains the
verified QEMU identity even if a later prelaunch step raises. Its one live run
must execute the guest GDB smoke before Flutter and capture correlated
first-hit/present/QMP evidence or preserve the earliest diagnostic failure with
truthful finalization. Neither outcome is a product-render pass.

## Facts, inference, hypotheses, and UNKNOWN

### Facts

- FLR-0416 commit `d97dec4` and its bundle reached the fixed Mini receiver;
  the exact FLR-0410 artifact preflight and one QEMU boot passed.
- `flr0416-0001` reached guest-ready, then stopped before guest setup/GDB/
  Flutter at `RuntimeError:canonical repository guard failed`.
- A cwd-only A/B failed from SSH's default directory and passed from the
  receiver root. Origin and required repository metadata checks passed.
- QMP quit, recorded PID disappearance, socket absence, and official postflight
  passed. The final JSON lacks `qemu_host_identity` and records
  `teardown_verified=false`.
- No GDB smoke, Flutter launch, QMP image, or product observation was produced.
- GPT-6.1 Sol's judgment-only recommendation is one coherent successor with a
  fresh immutable ID. A second review identified that a duplicate capture can
  otherwise fail on an existing artifact and still enter cleanup, potentially
  quitting the first controller's QEMU.

### Inferences

- The first failure is an orchestration/cwd contract defect, not evidence of
  Flutter, Filament, Mesa, QEMU rendering, or guest-kernel failure.
- Missing QEMU identity in the final record is an evidence-retention defect;
  independently successful cleanup checks do not authorize changing the
  structured `teardown_verified=false` result retroactively.
- A persistent atomic start claim and a separate controller claim are needed
  because the QEMU-start path and the controller-finally path have different
  ownership risks.

### Competing hypotheses

1. **Cwd-dependent guard invocation is the entry failure.** Support: the
   remote home/repository-root A/B changes only cwd and flips guard outcome.
   Falsifier: the controller still fails with the explicit resolved repo-root
   cwd while a direct guard in that same directory passes.
2. **Early exception only loses serialization, not the QEMU identity.**
   Support: `_verify_qemu_identity()` populated the exact PID/start pair before
   the guard raised. Falsifier: a controlled unit test cannot preserve that
   identity in the final record without weakening any teardown predicate.
3. **Duplicate owner races are independently unsafe.** Support: start accepts
   an already-staged directory, and a second controller may reach `finally`
   before `_record_result()` rejects reused output. Falsifier: an atomic claim
   test shows a competing invocation can never proceed to QEMU start or QMP
   cleanup.

## Acceptance gates

1. Canonical guard execution is independent of SSH's initial cwd: controller
   passes `cwd=self.repo_root`; invalid repository identity still fails closed.
2. If a post-identity layout/guard step raises, the exact PID/start identity is
   present in `controller-final`. Missing/changed identity, residual QEMU,
   failed postflight, remaining socket, or teardown error still keeps
   `teardown_verified=false`.
3. `flr0416-0001` is never reused. A pre-existing `flr0417-0001` evidence path
   is rejected before modification. Atomic persistent start and controller
   claims reject a second owner; a duplicate controller must not run QMP quit.
4. Exactly one fresh runtime attempt passes owner/port/artifact preflight,
   captures the guest GDB smoke before Flutter, and records either a live
   identity/present/QMP-correlated first-hit observation or the earliest
   failure together with complete finalization evidence.
5. No automatic retry, second QEMU, fallback profile, product override,
   bypass, or after-the-fact evidence promotion. A later attempt requires a new
   ticket/PDCA decision.

This ticket's outcome does not prove production Sequoia material/texture/light,
same-frame HUD composition, interaction/repaint stability, five-minute present
progress, or two independent boots. Those product gates remain open.

## Constraints and risk

- Preserve FLR-0416's raw Mini evidence and `teardown_verified=false` record.
- Use only exact unchanged FLR-0410 kernel/rootfs/qemuboot artifacts and the
  established fixed build/TMPDIR. Do not sync, switch the receiver, clean
  caches, or run BitBake.
- Before bundle handoff and immediately before QEMU, perform fresh read-only
  receiver, process-owner, build-owner, image-hash, evidence-path, memory/disk,
  port, and socket checks. Do not interrupt an existing owner.
- All claims are create-only persistent evidence. A partial/occupied claim
  consumes that run ID; never remove it to retry.
- Long QEMU work begins only after communicating the exact run and gates to the
  user. Keep all raw QMP frames and logs on Mini; Mac previews are post-teardown
  derived evidence only.
- No personal account, host/IP, credential, key, or private absolute path in
  committed files/logs.

## Plan / Do / Check / Act

### Plan

- Run the canonical guard and checkpoint; confirm FLR-0416 is Waiting and
  FLR-0417 is the sole In Progress ticket.
- Add failing tests for explicit cwd, identity retention under early exception,
  truthful teardown, immutable ID collision, persistent start/controller claims,
  and duplicate-controller non-cleanup.
- Implement the smallest controller and launcher changes. Keep the original
  FLR-0416 evidence and profile unchanged; use `flr0417-0001` consistently in
  host, guest, QMP, and post-teardown media-export contracts.

### Do

- Implemented the explicit resolved-repository cwd for the canonical guard,
  retained the validated QEMU PID/start identity through the terminal record,
  and added persistent atomic start/controller claims. Duplicate-controller
  rejection occurs before the cleanup-owning `try/finally`. Host, guest, QMP,
  and preview participants now use the fresh immutable `flr0417-0001` ID.
- TDD was red before implementation: focused controller tests exposed the
  inherited cwd, missing final identity, and absent claim contract; launcher
  tests exposed missing fresh-ID/claim behavior and collision rejection after
  earlier unrelated preflight. The corresponding final tests are green.
- Commit `e1a3949a7163dcf739975eefa916bfeb72540f06` was transferred with the
  established bundle helper and the fixed Mini receiver reached that exact
  HEAD. No Devtool, `do_patch`, BitBake, product-source, image, or cache change
  occurred.
- Exactly one `flr0417-0001` QEMU observation ran on unchanged FLR-0410-0001.
  Guest GDB API smoke and Example Demo launch both returned PASS. The load wait
  printed `FLR0416_WAIT=load-ready.json:READY`, then the guest serial login
  shell logged out; the serial runner reached its bounded
  `guest-command-output` deadline waiting for the completion marker.

### Check

- Focused FLR-0417 suites passed: 36 controller, 15 preflight/launcher, 16 GDB
  observer, 12 guest snapshot, and 11 media-export tests (90 total).
- Full repository Python tests passed 339/339 and MCP smoke passed 52/52.
  Canonical, privacy, shell syntax, Python AST syntax, whitespace, file size,
  QEMU harness, runtime-log-slice, Devtool finish/rebase, Mini patch/handoff,
  and runtime-checkpoint gates passed.
- `make verify` stops at 11 existing Markdown missing-target errors for
  FLR-0338/0339 and FLR-0391/0395 evidence/ticket paths; no FLR-0417 link is
  missing. The initial sandboxed run's 13 localhost-bind errors were execution
  policy, not test assertions; the same full command outside the sandbox passed
  all 339 Python and 52 MCP tests.
- Local tests and validation passed before commit; the exact commit/bundle was
  transferred and receiver identity/preflight passed before the one run.
- The controller recorded `DIAGNOSTIC_CAPTURE_FAIL` at
  `wait-load-ready.json`, exact QEMU PID/start identity, QMP quit PASS, process
  gone, QMP socket absent, official postflight PASS, and
  `teardown_verified=true`. Product acceptance is `NOT_CLAIMED`.
- Only the pre-launch system still exists. Raw Mini PPM SHA-256 is
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`; its
  derived PNG SHA-256 is
  `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.
  It is black and was captured before GDB/Example Demo launch, so it is not a
  product-render observation. No load/hit/post QMP frame or video exists.
- The transcript and controller source strongly support a serial-wrapper exit
  defect: `_wait_marker()` emits `exit 0` after READY, while `serial-exec`
  appends its `rc` and unique completion marker only after the guest command
  returns. The transcript contains logout/login prompt but no completion
  marker; the runner reports `deadline-expired stage=guest-command-output`.
  Whether a separate observer error occurs after fixing this is UNKNOWN.

### Act

- Close FLR-0417 as a bounded diagnostic/finalization unit. Preserve its only
  run ID and raw Mini evidence; do not replay it. FLR-0418 owns the separate
  serial-shell completion repair and a new immutable run ID. Overall product
  rendering remains open.

## PDCA checker

- Status: PASS
- Checked by: GPT-6.1 Sol, independent read-only audit on 2026-10-04
- Findings: The bounded diagnostic acceptance is evidenced. `FLR0416_*` are
  protocol labels from the retained helper family; the immutable runtime and
  staged guest paths are `flr0417-0001`, and the controller stores outputs in
  that run directory. The run preserved the first serial-completion failure
  and exact teardown. Product rendering, present, and composition remain open.
