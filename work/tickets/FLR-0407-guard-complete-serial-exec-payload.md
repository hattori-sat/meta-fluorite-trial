# FLR-0407 — establish the serial-exec payload-size boundary before adding a guard

- Status: Inbox
- Priority: Medium
- Created: 2026-10-03
- Owner: QEMU runtime harness / serial transport and focused regression tests
- Depends on: FLR-0405 post-capture serial command sizing
- Scope: observe and define the transport boundary first; no image, Yocto source, build, or QEMU changes

## Objective

Determine and document the safe maximum command size for the actual QEMU serial-exec path. Add a complete-payload guard only if a reproducible limit requires it; do not assume a 4096-byte limit for the final wire line without evidence.

## Facts

- The current harness rejects raw command text above 4096 bytes, then appends a fixed 99-byte completion/status wrapper and sends the result directly with socket.sendall.
- The recorded FLR-0405-0002 first-boundary command file was 4001 bytes. It executed on the guest, returned PERSISTENT_PRESENT_UNMATCHED, and produced the serial completion marker with rc=0; the wrapped line therefore exceeded 4096 bytes and was accepted on that path.
- The current serial-exec source has no /bin/sh -c between command_text and socket.sendall. A nested shell-quoting length reported by an external review is not part of the verified call path.
- The actual maximum accepted line size, terminal mode/buffering behavior at larger sizes, and whether an upper-bound transport failure exists remain UNKNOWN.

## Hypothesis

The helper has a documented raw-command guard but no separate full-payload guard. This may be sufficient for the actual serial endpoint; a defect is not yet established.

## Success criteria

1. Trace command-file parsing through the exact serial send and guest shell receive path.
2. Measure the fixed completion-wrapper length from the implementation and reproduce the 4100-byte FLR-0405-0002 case with evidence.
3. Establish the transport behavior around its real upper boundary with a bounded test; fail closed before guest dispatch if truncation or ambiguity is reproduced.
4. Add a guard only if supported by that evidence, and test both accepted and rejected boundaries without running an unintended guest command.
5. If no defect is reproduced, close this ticket with the verified supported limit and keep the existing raw-input guard unchanged.
6. Keep FLR-0405 as the sole In Progress ticket until its runtime unit closes.

## Plan / Do / Check / Act

### Plan

Review the exact harness and serial endpoint, then design a reversible boundary probe that cannot launch an arbitrary command when bytes are truncated.

### Do

Not started. FLR-0405 remains the sole In Progress unit.

### Check

Not started.

### Act

After FLR-0405 closes, promote this ticket only if its one bounded probe is ready and useful; otherwise retain it in Inbox.
