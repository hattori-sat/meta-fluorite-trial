# FLR-0361 — Fail-closed checkpoint status matcher plan

## Outcome

The runtime checkpoint must never report one active task when multiple ticket files have canonical or legacy In Progress status spellings.

## Execution sequence

1. Build an isolated temporary fixture repository with one current ticket/log and a second ticket using a legacy active status; run `runtime-checkpoint.sh verify` and capture the false-pass red case.
2. Update the active-status parser to count documented legacy spellings and reject unknown In Progress-prefixed variants rather than ignoring them.
3. Extend `tests/test-runtime-checkpoint.sh` with canonical, suffixed, unbulleted, and Waiting cases. Assert multiple active tickets fail and Waiting does not count.
4. Run the focused test, current-repository checkpoint, privacy, Markdown, and size checks. Do not run QEMU, BitBake, or Devtool.
5. Record exact output and make a local commit after verification; no push.

## Constraints

- Do not modify or mark old tickets Done as a way to satisfy the test fixture.
- Keep FLR-0361 separate from FLR-0360's GDB attach diagnostics.
- The fixture must use a temporary root and leave the working tree unchanged.
- Keep canonical ticket states simple: `Inbox`, `Next`, `In Progress`, `Waiting`, `Done`, or `Cancelled`.

## Acceptance

- The fixture demonstrates red before the matcher change and green after.
- Existing checkpoint checks pass and no status variant is silently omitted.
- No product/runtime claim is made.
