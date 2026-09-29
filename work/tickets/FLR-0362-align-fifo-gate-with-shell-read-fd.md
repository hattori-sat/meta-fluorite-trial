# FLR-0362 — align the FIFO gate with the shell read descriptor

- Status: In Progress
- Priority: High
- Owner: QEMU guest FIFO/attach gate and runtime evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0360 same-point diagnosis](FLR-0360-diagnose-gdb-attach-precondition.md)
- Plan: [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0362-align-fifo-shell-read-fd.md)
- Working log: [FLR-0362 log](../logs/2026-09-29-flr0362.md)
- Historical controls: [FLR-0286 fixture + HUD](FLR-0286-reproduce-known-good-combined-sequoia-hud.md), [FLR-0287 production Sequoia](FLR-0287-compare-production-sequoia-light-material.md), [FLR-0357 retrospective](FLR-0357-refresh-3d-visibility-retrospective.md)

## Objective

Make the existing pre-GO runtime gate agree with the shell's measured blocked `read(0)` without weakening run ownership: the exact recorded FIFO must be the object named by the gate and both fd 0 and fd 3, and process identity must remain stable before GDB, after attach, and immediately before GO.

## Why this is the next unit

FLR-0360's one exact-bundle Mini run used the existing `exec 3<>...; IFS= read -r token <&3` wrapper. At the same-point attach marker, `syscall_fd3=FAIL` was the only failed original predicate; `syscall_nr=0`, `syscall_fd=0x0`, `fd0_same_gate=PASS`, and `fd3_same_gate=PASS`. The host's official FIFO observer already accepted `read_fd=0` after verifying the target FIFO's type and device/inode. This is a real disagreement between the shell's wait descriptor and later attach/release checks, not evidence of a missing fd 3 or renderer failure.

Historical records are evidence with scope, not authority:

- FLR-0356's host framing stopped before GDB/GO; it does not diagnose this descriptor gate.
- FLR-0358 used a stale helper and did not exercise its intended serial correction.
- FLR-0359 passed exact helper provenance and FIFO observation, then stopped at a generic attach check.
- FLR-0360 named `syscall_fd3` as the only current failure; its QMP black still/video are pre-GO and cannot classify rendering.
- FLR-0286 proves same-frame HUD plus a self-made lit Filament fixture; FLR-0287 separately reached production Sequoia draw/present with a zero-chroma native ROI. They remain distinct controls.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Current evidence | Next discriminator |
| --- | --- | --- |
| What | Actual blocked syscall is `read(0)`; attach and release expect `read(3)` | All gates accept only read-0 on the recorded exact FIFO, or fail closed |
| Where | `FLR-0350-attach-pre-submit.cmd` precondition and post-GDB poll; `FLR-0350-release-go.cmd` | Same recorded device/inode checks at each decision boundary |
| When | Mini run `flr0360-0001`, after FIFO observer PASS and before GDB/GO | One fresh `flr0362-0001` after exact bundle/image/preflight passes |
| Who | Shell wrapper owns the wait; attach command owns GDB admission; release command owns GO; runner owns ordering and teardown | Preserve each owner; no host-side bypass |
| How | `<&3` redirection leaves both descriptors on one FIFO while the shell builtin blocks in `read(0)` | Record FIFO identity; revalidate fd0/fd3, PID/start/UID, tracer and wait state at attach/GO |

## Evidence and interpretation

- Exact FLR-0360 attach marker and QMP picture/video are recorded in [FLR-0360](FLR-0360-diagnose-gdb-attach-precondition.md) and its [evidence index](../evidence/FLR-0360-qmp-pre-go-2026-09-29.md).
- The prior black QMP frame occurred before GO. FLR-0362 must capture its own QMP-only still/eight-frame video and label it by GO state.
- Overall 2D+3D success remains open. Passing this gate only proves the diagnostic can advance to the next runtime boundary.

## Options considered

1. **Chosen — align the gate with observed `read(0)`:** record the observer-validated FIFO device/inode and require that identity for the named FIFO, fd 0, and fd 3 at pre-GDB, post-attach, and pre-GO boundaries. This retains shell behavior and adds no runtime dependency.
2. **Deferred — change the wait primitive to force `read(3)`:** the shell builtin's redirection is already observed to use fd 0; guaranteeing fd 3 would need a different primitive and more runtime integration. Reconsider only if a documented product/harness contract requires a literal fd-3 syscall.

## Hypotheses

1. **Confirmed:** shell builtin `read` with `<&3` blocks through fd 0; same-point evidence showed the two descriptors still refer to the same gate.
2. **Expected next result:** with recorded type/device/inode and stable process identity, GDB attach and GO will pass. Falsifier: a named process/FIFO transition check fails after the policy change.
3. **Open:** after GO, production Sequoia and HUD may be visible, partially visible, or black. Only post-GO QMP/runtime evidence can distinguish that renderer boundary.

## Scope

### In scope

- Record the exact FIFO identity in the existing observer/host-validation boundary.
- Update attach, post-attach polling, GO, preflight, and cleanup checks with test-first coverage.
- Exact bundle delivery to the existing Mini receiver and one fresh pinned-image QEMU run.
- QMP screenshot/video, compact evidence derivatives, first-divergence logging, and safe teardown.

### Out of scope

- Product Flutter/Filament/Yocto recipe or image changes; lighting, camera, material, texture, and Wayland composition fixes.
- Relaxing process/FIFO identity, tracer, or marker requirements; accepting `read(0)` by descriptor number alone.
- Building/rebuilding the image, Devtool, new receiver/TMPDIR/cache, global process kill, or copying VM images to Mac.
- Reusing `flr0360-0001` or any other consumed run ID.

## Success criteria

1. Regression tests demonstrate that current fd-3-only assumptions reject the measured exact-FIFO `read(0)` and that mismatched identity fails closed.
2. A root-owned, mode-0700 `/run` directory binds the fresh run ID; the observer creates an exclusive record with run ID, PID/start/UID, and exact FIFO device/inode. The host validator rejects stale, partial, substituted, or mismatched records.
3. GDB validates PID/start/UID, ptrace-stopped state, and fd0/fd3 identity before attach authorization; it stays stopped and waits for a valid GO record instead of resuming on timeout. Invalid/expired post-write state terminates the exact inferior before GDB exits.
4. Release-GO checks the stopped target, opens the writer once, validates the opened descriptor, rechecks target identity while still stopped, then writes through that same descriptor and publishes an exclusive GO record. GDB continues only after validating that record. Pre-write failure yields zero GO bytes; a post-write record failure terminates the exact target before token consumption, with runner-side kill-before-GDB-interrupt fallback.
5. Cleanup removes only proven run-owned objects. Partial or substituted state is named FAIL and retained; cleanup cannot say PASS while run records remain.
6. Guest commands remain POSIX-shell-valid one-liners at most 4096 bytes; behavioral regression tests, focused tests, and runner `--check` pass.
7. Exactly one fresh Mini run uses the exact committed bundle and pinned image. It reaches a named post-GO boundary or stops at a named fail-closed predicate; no retry or bypass.
8. QMP-only still/eight-frame video, GO classification, relevant runtime markers, hashes, and cleanup evidence are retained. If post-GO pixels remain black, create a separate renderer ticket; do not extend this gate ticket.

## Plan / Do / Check / Act

### Plan

- See the linked implementation plan; execute inline in this session because the user explicitly asked to continue without pausing for a plan-choice prompt.
- Test first, preserve the gate boundaries, then commit locally and use the established bundle/one-shot Mini workflow.

### Do

- Ticket opened from FLR-0360's exact finding; that sentence describes the initial state only.
- Updated the observer validator to bind fresh run ID and persisted FIFO/process identity; added committed-source guest helpers behind bounded serial adapters, run identity initialization, stale-helper collision preflight, and target-safe cleanup/abort checks.
- Current host verification: 46/46 tests and the runner's `--check` pass. No source commit or bundle transfer yet; Mini/QEMU/GO have not run, and `flr0362-0001` remains unused.
- Final local gates: privacy PASS, file-size PASS (1864 tracked/untracked files checked), checkpoint PASS (`active=1`), and `git diff --check` PASS. `make check-markdown` remains FAIL on nine pre-existing missing evidence targets in FLR-0338/0339/0340; FLR-0362 links pass and those unrelated historical references stay out of scope.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Persisted identity / transition regressions | Wrong ID, partial/substituted record, process change, or FIFO swap fails with zero GO bytes | Host suite 46/46 PASS; full runtime behavior remains UNKNOWN |
| GDB stopped-attach authorization | Exact process/FIFO identity checked before authorization; target remains stopped until GO record validates | Static contract PASS; Mini attach/GO remains NOT RUN |
| Guest command syntax/size and runner contract | POSIX syntax, <=4096 bytes, GO ordered after all checks | `--check` PASS (12 serial commands); helper install still awaits exact committed bundle |
| Local repository gates | No privacy leak, size limit, invalid checkpoint, or whitespace errors | Privacy PASS; size PASS; checkpoint PASS; diff check PASS. Markdown gate reports 9 pre-existing missing FLR-0338/0339/0340 evidence links, not FLR-0362 |
| Exact bundle / pinned Mini runtime | Receiver, effective TOPDIR/TMPDIR, image hashes, unique run ID all pass | NOT RUN |
| Attach/GO and QMP | Stable read-0 identity reaches GO or first new predicate stops; still/video labeled | NOT RUN |
| Cleanup | Identity marker and run FIFO removed; app/QEMU/QMP residuals zero | NOT RUN |

### Act

- After final local gates and a clean ticket-scoped commit, use the established exact-bundle handoff and one fresh Mini `runqemu` ID `flr0362-0001`. No recipe/image build is in scope. Capture QMP still/eight-frame evidence and classify it by GO state; stop at the first named failed predicate and do not retry the ID.
