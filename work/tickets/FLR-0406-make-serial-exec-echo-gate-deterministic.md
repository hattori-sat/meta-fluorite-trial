# FLR-0406 — make the serial-exec echo-off gate deterministic

- Status: Inbox
- Priority: High
- Created: 2026-10-02
- Owner: QEMU runtime harness / bounded mock serial server / regression-test roles
- Trigger: FLR-0405 same-boot wall-clock query was blocked before guest dispatch
- Work unit: diagnose and make the existing serial-exec setup gate deterministic; no product/image change

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

- Reproduce the two observed transcript shapes locally with a deterministic
  mock, identify the exact rejecting condition, then make the smallest
  fail-closed change and add regression coverage.

### Do

- Not started. No source or test files have been changed.

### Check

- Not run. FLR-0405's query command was not dispatched; no product/runtime
  conclusion follows from this harness failure.

### Act

- Keep in Inbox until it becomes the single active work unit. FLR-0405 remains
  In Progress and resumes only after this gate is understood.
