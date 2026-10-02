# FLR-0406 — make the serial-exec echo-off gate deterministic

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: QEMU runtime harness / bounded mock serial server / regression-test roles
- Trigger: FLR-0405 same-boot wall-clock query was blocked before guest dispatch
- Work unit: diagnose and make the existing serial-exec setup gate deterministic; no product/image change
- Branch: `feature-flr-0406-serial-exec-gate` from `dev-flr-0405-first-fault` at `c37ee7c`
- Plan: [saved implementation plan](../../docs/superpowers/plans/2026-10-02-flr-0406-serial-exec-gate.md)

## Problem

FLR-0405 could not dispatch its bounded guest journal query. Two calls to the
unchanged local/Mini `scripts/qemu-runtime-harness.sh serial-exec` returned
`FAIL reason=echo-off-response-unexpected`. The first setup transcript was 52
bytes and byte-identical to a prior successful guest-launch setup. The second
was 38 bytes containing two adjacent shell prompts after the first call had
already disabled tty echo. In both attempts the guest command output remained
empty, so no journal query ran. This is an observation-path failure, not
evidence about Fluorite rendering.

## Facts, hypotheses, and UNKNOWN

### Facts

- Local and Mini harness SHA-256 matched:
  `436d010ea6de3a0acd74eac7777b033bbd6add29bdf9fa6f12fc7d4e67f83605`.
- Attempt 1 and 2 both failed before command dispatch with the same result.
- Attempt 1 captured the same complete setup bytes as a previous successful
  launch, while attempt 2 captured two adjacent prompts and no echoed
  `stty -echo` command.
- The bounded query command passed hash, one-line, size, and `sh -n` checks.
- FLR-0405's QEMU was shut down after preserving its QMP/log/PPM evidence; no
  runtime is active for this ticket.
- A bounded local RED mock showed that the current implementation can accept
  the first prompt before the rest of a chunked setup transcript arrives,
  dispatch the requested command once, and print `serial-exec=PASS` without
  observing a per-session setup marker.
- The first post-fix mock modeled a marker in command output but not the same
  nonce echoed as terminal input. Its 11/11 focused and 227/227 Python results
  are retained as observed results but superseded as proof of echo safety.

### Inferences

- The prompt-only recognizer has a premature-readiness failure mode on a
  controlled duplicate-prompt stream. This is a demonstrated harness defect
  class; it does not prove that this exact interleaving caused either FLR-0405
  Mini attempt.

### Hypotheses

1. Residual serial bytes from the previous connection are being consumed as a
   fresh echo-off response. Support: repeated adjacent prompts on attempt 2;
   refute: mocked/replayed stream boundaries show no stale bytes at the next
   command boundary.
2. The current recognizer assumes echo-on command text or one prompt frame and
   rejects a valid already-no-echo response. Support: the second response has
   no command echo and fails; refute: a byte- and chunk-faithful mock reaches a
   different gate with the same observed stream.
3. The first attempt failed for a different framing condition not preserved in
   the transcript. This remains UNKNOWN until the gate reports its exact
   predicate or a faithful test reproduces it.

## Scope and acceptance

- Start with the current `serial-exec` implementation and focused tests; inspect
  the exact gate predicates before editing.
- Build a bounded mock serial server/replay for prompt split across reads,
  already-disabled tty echo, residual/duplicate prompts, and the normal
  echo-enabled path. Do not start QEMU for these tests.
- Ensure a setup-gate failure never dispatches the requested guest command.
- Ensure valid normal and already-no-echo sessions dispatch once and retain the
  exact command exit status/output without mistaking stale prompts for the
  completion marker.
- Run focused tests and the relevant repository verification; report unrelated
  baseline failures separately.
- Do not edit product source, Yocto recipes, image settings, or the FLR-0405
  runtime evidence. After a committed fix, transfer/verify the exact harness
  through the documented handoff before resuming FLR-0405 with a fresh run ID.

## Plan / Do / Check / Act

### Plan

- Compare tolerant prompt parsing with a two-phase echo-off gate. The RED mock
  demonstrated premature dispatch on a prompt-only boundary. A later review
  found that a nonce in the same `stty` command could itself be echoed before
  execution, so the corrected protocol sends nonce-free `stty` first, then a
  nonce-bearing status probe. The first prompt remains only a sequencing
  barrier.
- Record the initial results as superseded; test both echo-on and already-off
  startup states, false-ready echo, nonzero `stty`, chunked duplicate prompts,
  and stale completion output.

### Do

- Replaced the one-phase nonce command with two phases: `stty -echo` stores its
  status without a nonce; after its prompt barrier, a second command prints a
  per-session nonce/status line. Dispatch requires exact status 0, one nonce
  occurrence across the probe transcript, and exactly one final prompt after
  the line. A 50 ms bounded quiet check rejects prompt residue arriving in
  separate TCP reads.
- Made the guest-command completion marker unique per invocation so stale
  output from the former fixed marker cannot complete a new command.
- Reworked the loopback mock to model initial echo-on and echo-already-off,
  second-command echo, nonzero `stty`, prompt residue and duplication split
  across reads, missing marker, exact-once dispatch, command output/status,
  stale fixed completion marker, and global deadlines.
- Removed an obsolete FLR-0350 FIFO-validator call from this serial-exec test
  fixture. It supplied two paths to a CLI that requires a run ID and three
  arguments, and its version-1 sample was not a valid version-2 FIFO gate.
  Serial-exec tests now assert their own output/status contract directly.
- Updated the shell-level QEMU harness contract test to assert the new two-phase
  gate and per-invocation marker instead of pinning the former fixed marker.

### Check

- Focused RED before the harness fix: the mock observed no setup marker,
  recorded one requested guest command, and the old helper returned
  `serial-exec=PASS`; the regression failed as intended.
- The initial one-phase correction reported 11/11 focused and 227/227 Python
  tests passing, but the mock omitted terminal echo of the nonce-bearing input.
  Those results are superseded and are not accepted as echo-safety evidence.
- Corrected `python3 tests/test_qemu_runtime_harness.py`: 16/16 PASS.
  Corrected `make check-python`: 231/231 PASS. These are host-tool tests, not a
  Mini runtime or rendering result.
- The first `make check-qemu-harness` after changing the completion marker
  failed because its static test still required `__FLR_SERIAL_COMMAND_DONE_7B31__`.
  Updating that contract to require per-invocation nonces made
  `make check-qemu-harness` PASS.
- `make check-canonical check-privacy check-shell check-file-sizes
  check-qemu-harness check-runtime-log-slice` — all PASS; shell syntax covered
  59 files and file-size gate covered 2,082 files.
- `bash scripts/runtime-checkpoint.sh verify --ticket FLR-0406 --log
  work/logs/2026-10-02-flr0406.md` — PASS, exactly one active ticket.
- `make check-markdown` — FAIL with the same 11 historical missing links in
  FLR-0338/0339/0340 evidence and old FLR-0391/0395 plans. None points to
  FLR-0406. These unrelated artifacts were not rewritten.
- `git diff --check` passed before the last ticket/task-state update and must be
  rerun after the final documentation edit. Staged checks and Mini handoff
  remain pending.
- The quiet interval is explicitly bounded: it detects bytes delivered during
  50 ms after the final prompt; it cannot guarantee that no later serial byte
  will ever arrive. Per-command completion nonces prevent old fixed markers
  from satisfying the guest-command completion test.

### Act

- Keep FLR-0405 Waiting until the mock-backed gate is verified and the exact
  harness is transferred through the documented Mini handoff. This ticket is
  not a rendering test and cannot establish any 3D acceptance criterion.
- After the exact helper is verified on Mini, resume FLR-0405 using a fresh run
  ID and preserve the original display goal; do not infer that historical
  failure was caused by this gate without matching runtime evidence.

## Impact

- **Build-time:** none; no BitBake or image build.
- **Runtime:** affects only host-driven serial observation. It requires the
  guest shell to execute `stty` and `printf`; failure to prove echo disabled,
  return status 0, or produce the unique marker prevents subsequent command
  dispatch. It adds 50 ms bounded quiet time per successful serial command.
- **Packaging:** none; the QEMU harness is not installed into the image.
- **Integration risk:** a Mini-side run is still required to verify the exact
  transferred harness against the real serial endpoint before FLR-0405 resumes.
