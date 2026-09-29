# FLR-0360 — diagnose the GDB attach precondition at the same decision point

- Status: Done
- Priority: High
- Owner: QEMU guest attach gate / runtime evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0359](FLR-0359-use-committed-qemu-runtime-helper.md)
- Plan: [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0360-diagnose-gdb-attach-precondition.md)
- Working log: [FLR-0360 log](../logs/2026-09-29-flr0360.md)

## Objective

Identify which exact predicate makes `FLR0350_GDB_ATTACH=FAIL precondition` in the current Mini guest, without changing the gate's acceptance semantics. Preserve same-point evidence for syscall number/fd, fd 0/fd 3 FIFO identity, process identity, GDB script readability, and collision markers. If any predicate fails, stop before GDB attach and GO.

## Why this is the next unit

FLR-0359 used the exact committed helper and passed the official FIFO read gate, then stopped at the GDB attach precondition. Its observer saw `read(0)` on the gate. This ticket added same-point predicate output without changing acceptance and used one fresh Mini run. The exact result confirms `syscall_fd3` is the only failed original predicate: syscall `read(0)` was blocked on the run FIFO, and both fd 0 and fd 3 resolved to that same FIFO. The launch source uses shell builtin `read` with `<&3`, consistent with the observed standard-input read. This is a gate mismatch, not a renderer result.

Historical evidence is fallible and scoped:

- FLR-0350's original log explicitly left target `/proc` and ptrace unproven.
- FLR-0356 observed matching process/FIFO identity but failed host framing before GDB/GO.
- FLR-0358 did not exercise its serial fix because the Mini selected an older helper.
- FLR-0359 now proves the current committed helper path passes serial framing and the FIFO gate, then fails at the separate attach precondition.
- FLR-0251 and FLR-0286 prove HUD plus self-made 3D fixture composition; FLR-0287 is a distinct production Sequoia draw/present run with a zero-chroma native ROI. None proves this run's renderer because GO was not sent.

## Success criteria

1. A static regression test fails before the change because the current attach command does not expose named precondition results.
2. The guest emits one bounded `FLR0350_GDB_ATTACH_PREFLIGHT` record from the exact attach decision point, with an individual PASS/FAIL for each existing predicate and observed `syscall_nr`, `syscall_fd`, `fd0_same_gate`, and `fd3_same_gate` values.
3. Existing predicate semantics remain unchanged: syscall fd 3 remains required; no descriptor equivalence or alternate path is allowed without separate evidence and approval. Any failure keeps GDB and GO unexecuted.
4. The command remains POSIX-shell-valid, a single serial command no larger than 4096 bytes, and the existing launch-gate `--check` passes.
5. One fresh Mini run uses the exact committed bundle tip and existing pinned QEMU artifacts. Its first failed predicate is named, or all predicates pass and the runner's next measured stage is recorded. Do not retry the run ID. **PASS:** `flr0360-0001` named the sole failed predicate `syscall_fd3`; GDB/GO remained unexecuted.
6. Preserve QMP-only full-frame screenshot and eight-frame video; label each pre-GO/post-GO. Prove run-owned FIFO removal, QMP quit, and zero run-owned process residuals. **PASS:** evidence is pre-GO; cleanup and residual checks pass.
7. Record exact role-redacted command invocations, output markers, source/bundle/image identity, pixel hashes/counts, and failed/corrected probes in this ticket's working log. Never dump unrelated full logs. **PASS:** see the linked log and evidence index.

## 4W1H stratification (Why excluded)

| Dimension | Current evidence | Next discriminator |
| --- | --- | --- |
| What | FIFO observer PASS, then only `syscall_fd3` fails; actual syscall is `read(0)` | Align the downstream pre-GO gate checks with the observed shell read while retaining exact FIFO/process identity |
| Where | `work/commands/FLR-0350-attach-pre-submit.cmd`, before `/usr/bin/gdb` | Output immediately before the existing GDB branch |
| When | `flr0360-0001`, after `FLR0350_FIFO_READ_GATE=PASS`, before GDB/GO | Next ticket uses one fresh ID after exact bundle/image/preflight checks |
| Who | Guest command owns predicate evaluation; runner owns stopping on FAIL; evidence role owns QMP/cleanup | Keep the ownership boundaries unchanged |
| How | Attach-time marker: `syscall_fd3=FAIL`; all other original checks PASS, `syscall_fd=0x0`, `fd0_same_gate=PASS`, `fd3_same_gate=PASS` | Next ticket revalidates both FIFO descriptors, type/device/inode, PID/start/UID, and blocked syscall after GDB attach and before GO |

## Hypotheses

1. **Confirmed:** `syscall_fd3` alone rejects the observed pre-GO wrapper. Actual syscall is `read(0)` while fd 0 and fd 3 both identify the gate; the other 12 original predicates pass.
2. **Not observed in this run:** fd 3 path, process identity, GDB script readability, and marker collision predicates do not explain the stop; all reported PASS.
3. **Still a risk for the next ticket:** state can drift between observer, GDB attach, and GO. Revalidate at each transition against the same run-owned FIFO identity and process start time.

Do not weaken the gate based on the observer-only `read(0)` record. The current failure has not demonstrated that fd 0 is an intended equivalent to fd 3.

## Scope

### In scope

- One test-first diagnostic improvement to the guest attach command and its existing static contract.
- Exact bundle transfer to the fixed Mini receiver and one fresh run on the existing pinned image, only after local gates and read-only preflight pass.
- Bounded QMP screenshot/video, first-divergence record, and run-owned cleanup verification.

### Out of scope

- Changing the required syscall descriptor or other attach predicate semantics.
- Flutter, Filament, camera, lighting, material, texture, Wayland composition, or product image changes.
- BitBake, Devtool, image build, new receiver/TMPDIR, cache cleanup, QEMU image transfer to Mac, or retrying `flr0359-0001`.
- Claiming 2D/3D renderer behavior from a pre-GO frame.

## Visual evidence

- Run: `flr0360-0001`; QEMU profile qemux86-64, 6144 MiB. QMP was classified **pre-GO** because attach failed and `release-go.serial.log` was never created.
- Screenshot: ![QMP-only pre-GO frame; uniform black, not a renderer verdict](../evidence/FLR-0360-qmp-pre-go-2026-09-29.png)
- Eight-frame, one-frame-per-second MP4: [view the pre-GO capture](../evidence/FLR-0360-qmp-pre-go-2026-09-29.mp4). The eight raw PPM frames are identical.
- Evidence index: [FLR-0360 QMP evidence](../evidence/FLR-0360-qmp-pre-go-2026-09-29.md). Original still and frames plus focused logs are retained at Mini role path `/mnt/yocto/evidence/flr0360-0001/qemu/`; the Mac review copy is under `/private/tmp/flr0360-0001/qemu/`. No QEMU image was copied to Mac.

## PDCA

### Plan

- See [FLR-0360 implementation plan](../../docs/superpowers/plans/2026-09-29-flr0360-diagnose-gdb-attach-precondition.md).

### Do

- Promoted as the sole active unit on `feature-flr-0360-diagnose-gdb-attach-precondition`, based on FLR-0359 closeout commit `7f6c4ba`.
- Added the same-point preflight marker and named fail list to the guest attach command. fd 0/3 inode comparisons are diagnostic only; original attach acceptance predicates remain required.
- Test-first result: `test_attach_preflight_reports_each_existing_predicate` failed against the old generic marker, then passed after the change. `test_attach_failure_stays_before_gdb_and_release_go` verifies failure remains before GDB and the runner checks attach PASS before GO. A temporary-proc behavior test executes the actual pre-GDB prefix and passes all predicates, rejects only a wrong syscall fd, and proves an fd0-only mismatch does not reject the attach gate.
- `python3 tests/test_flr0350_launch_gate.py` → 34 tests PASS; `bash work/commands/FLR-0350-run-sync-producer.sh --check` → all static/helper markers and 34 tests PASS; POSIX shell syntax PASS; one-line command is 4041 bytes of 4096.
- Local commit `8c840b8d3c7f7dbcb5f0ccba3849043127067eb0` was transferred using the standard exact-bundle helper; bundle SHA-256 is `099cc98fa37f29d9d71fac5efdb1c0040e43971877f7edc9c09c52c20bb81669`. Mini receiver and effective TOPDIR/TMPDIR gates match; no BitBake, Devtool, image build, or image transfer to Mac occurred.
- One fresh Mini run used `flr0360-0001`; all 11 commands and helper provenance passed. Pinned kernel/rootfs/qemuboot hashes matched: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`, `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`.
- Runtime invocation recorded before result inspection: `bash work/commands/FLR-0350-run-sync-producer.sh flr0360-0001` on `$BUILD_RECEIVER` via `$BUILD_HOST`.
- Same-point marker named `syscall_fd3` as the only failure. Observed `syscall_nr=0`, `syscall_fd=0x0`, `fd0_same_gate=PASS`, `fd3_same_gate=PASS`; all other original predicate fields passed. The guest command's `IFS= read -r token <&3` is consistent with the shell builtin performing the blocking read via fd 0.
- `release-go.serial.log` is absent, proving the fail-closed runner did not issue GO. The black QMP screenshot and eight identical frames are pre-GO only: post-run PPM SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`; full frame and 3D ROI have zero changed/chromatic/edge pixels. The pre-launch PPM SHA-256 is `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- Cleanup: `FLR0350_GDB_INTERRUPT=not-running`, `FLR0350_APP_STOP=PASS`, `flutter_processes=0`, `FLR0350_FIFO_CLEANUP=PASS removed=run-owned-fifo`, QMP quit accepted, `residual_targets=0 residual_qmp=0`.
- One early log extraction used an anchored grep and missed a marker prefixed by serial control/prompt bytes; the follow-up bounded extraction used `grep -aoE` on only the expected markers and exposed the exact line. No runtime state changed. The first plan lookup also returned a zsh unmatched-glob error after printing the runner; it was replaced by `rg --files | rg`, with no state change.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Test-first/static + fixture contract | Fails on current generic attach marker, then passes on named per-predicate output; executes all-pass/fail-closed/fd0-diagnostic cases | PASS; 34 focused tests pass |
| Guest command limit/syntax | One line, <=4096 bytes, `sh -n` passes | PASS; 4041 bytes |
| Mini source/image identity | Exact bundle tip, fixed receiver, pinned artifacts, one fresh ID | PASS; exact receiver tip and all three pinned image hashes verified |
| Attach predicate result | First failing predicate named; no GDB/GO on failure | PASS; sole failure `syscall_fd3`, no release-GO artifact |
| QMP evidence/cleanup | Still + eight-frame video, GO classification, FIFO removed, residuals zero | PASS as pre-GO evidence; cleanup and residual checks PASS; renderer NOT REACHED |

### Act

- Add the red static contract first; do not weaken or bypass any existing attach predicate. The next separate ticket may align checks with the observed shell `read(0)` only while proving both descriptors remain on the exact run-owned FIFO and rechecking identity at attach/GO boundaries.

## PDCA checker

- Status: PASS
- Checked by: fresh runner, privacy, file-size, Markdown-link, and runtime-checkpoint gates
- Findings: FLR-0360's bounded same-point diagnosis and QMP evidence are complete. Markdown check retains nine older missing links in FLR-0338/0339/0340; no FLR-0360 links are failing. Production 2D+3D acceptance remains open.
