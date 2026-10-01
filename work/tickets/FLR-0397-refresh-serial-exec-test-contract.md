# FLR-0397 — refresh the serial-exec gate test contract

- Status: Inbox
- Priority: Medium
- Created: 2026-10-01
- Owner: QEMU runtime-harness test role
- Predecessor: repository `make verify` validation during FLR-0395 setup
- Work unit: Repair one stale test fixture and invocation; no harness behavior change unless the focused test proves it necessary

## Problem

The repository verifier produced 147/148 passing tests. The remaining test,
`test_serial_exec_capture_passes_strict_gate_without_setup_preamble`, invokes
`scripts/flr0350_launch_gate.py --validate` with the old two-path argument
shape and a v1 observation fixture. The current validator requires an
explicit run ID and v2 run-scoped observation fields, so the test receives
usage output instead of exercising the intended strict gate.

## Scope and acceptance

- Update only the stale test fixture and command arguments to the current
  validator contract.
- Keep runtime harness production behavior unchanged unless a focused test
  demonstrates a real regression.
- Run the focused test and the full `make verify`; both must pass.
- Record the exact command and result. Do not alter the active rendering
  ticket or mix this repair into its branch.

## Current evidence

- `make verify`: 147/148 passed; one stale test-contract failure.
- No `scripts/` or `tests/` files were changed during FLR-0395 setup.
- Root cause is classified as a stale test fixture/invocation; the runtime
  helper itself is not yet implicated.

## Next action

Schedule as a separate ticket after the current Sequoia material experiment.
