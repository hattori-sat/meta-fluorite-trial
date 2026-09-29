# FLR-0362 — align the FIFO gate with the shell read descriptor

> **For agentic workers:** execute the checked tasks in order. Do not bypass a failed precondition or reuse a runtime ID.

**Goal:** Let the existing fail-closed QEMU diagnostic attach to the measured shell `read(0)` and reach GO only while the original process and the exact run-owned FIFO remain proven.

**Architecture:** Keep product code and image unchanged. The runner creates a root-owned, mode-0700 run directory in `/run`; the observer binds the fresh run ID, wrapper PID/start time, and FIFO device/inode into an exclusive identity record. GDB validates that record while the inferior is ptrace-stopped, creates attach authorization, and waits (bounded) without resuming the target. Release revalidates the stopped process before and after opening the FIFO writer, validates that one opened descriptor's device/inode, writes GO through that same descriptor, then exclusively publishes a root-owned GO record. If post-write record publication fails, GDB must terminate the exact attached inferior before returning an error; the runner also terminates the exact run-owned target before interrupting GDB whenever exec is not recorded or GO authorization is invalid. Longer guest decision logic lives in committed shell helper files; serial `.cmd` adapters stay one line/<=4096 bytes, and helper bytes are verified against HEAD and the exact bundle before transfer.

**Failure-path basis:** GNU GDB documents `kill` as terminating the process being debugged, while `detach` allows it to continue independently ([GDB inferior commands](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Inferiors-Connections-and-Programs.html)). Therefore “GDB does not issue `continue`” alone is not a sufficient post-write guarantee: error/exit may detach. FLR-0362 adds a PID/start/UID-bound kill and a runner-side kill-before-interrupt fallback, and requires visible abort evidence before claiming that a queued token could not be consumed.

**Historical basis:** FLR-0359/0360 prove that the observer sees `read(0)` while fd 0 and fd 3 both match the run FIFO; FLR-0360 stopped before GDB/GO, so its black QMP frames are not renderer results. FLR-0356/0358 document stale-helper/framing failure modes. FLR-0286's fixture+HUD and FLR-0287's production Sequoia result remain separate visual controls; do not collapse them into one claim.

**Spec:** [FLR-0362 ticket](../../../work/tickets/FLR-0362-align-fifo-gate-with-shell-read-fd.md).

## Invariants

- FLR-0362 is the sole `In Progress` ticket; FLR-0360 is closed only as a bounded pre-GO diagnosis.
- Do not change Fluorite/Flutter/Filament, camera, lighting, material, texture, Wayland, recipes, or image contents.
- Use the canonical Mini receiver, effective TOPDIR/TMPDIR, pinned QEMU artifacts, committed bundle handoff, and one fresh ID `flr0362-0001`. No BitBake/Devtool/image build and no VM image copy to Mac.
- All serial commands are one line and <=4096 bytes; runner `--check` owns this invariant.
- Named path, fd 0, and fd 3 must resolve to the same recorded FIFO object (device/inode); pathname text alone never authorizes attach/GO.
- Any missing, malformed, stale, substituted, or transitioning identity stops before GDB or GO. A failed attempt consumes its run ID.
- Capture a QMP still and eight-frame video, label them by GO state, and retain successful as well as failed evidence. No renderer inference before GO.

## Task 1 — red tests for persisted identity and transition failures

**Files:** `tests/test_flr0350_launch_gate.py` (test first); read the observer, attach, release, cleanup commands and GDB script.

- [ ] Change the test observation fixture to version 2 and bind it to an expected fresh run ID. Require `identity_record=PASS`, run ID, PID/start, device/inode; reject a wrong expected ID, missing/duplicate/malformed record, symlink or partial record, and any disagreement with launch PID/start or measured gate FIFO.
- [ ] Extend the temporary-proc attach fixture: exact `read(0)`, stable PID/start/UID, fd0/fd3 and named gate matching recorded dev/inode reaches the GDB seam; wrong syscall fd, either decoy descriptor, changed start, missing marker, or substituted identity fails before GDB.
- [ ] Add release-command behavioral fixtures. Exact identity writes one GO token through the descriptor whose identity was checked; changed process/start during writer open, missing/substituted marker, decoy fd, wrong state, and named-FIFO swap between precheck and open produce zero GO bytes. Separately simulate post-write GO-record publication failure and assert the exact inferior is terminated before GDB exits or cleanup interrupts GDB; preserve the “token written, execution prevented” evidence separately from zero-byte failures.
- [ ] Test cleanup states explicitly: complete matching run, no identity record, partial record, substituted marker/FIFO, and absent FIFO. Only proven run-owned objects may be removed; ambiguous state emits a named FAIL and retains evidence. Cleanup must not say PASS while a run marker remains.
- [ ] Add a GDB-script contract test for validation at the initial ptrace stop before the first `continue`; require stopped target state, PID/start/UID, root run ID/identity, fd0/fd3 object identity, exclusive attach authorization, a bounded wait for GO record, and no `continue` before that record validates. Every invalid/expired GO record path must terminate the exact inferior before GDB can exit/detach. Post-resume exec validation remains a separate state check.
- [ ] Run focused tests and observe the expected red failures before changing runtime commands.

## Task 2 — root-owned run identity from runner through observer

**Files:** `work/commands/FLR-0350-run-sync-producer.sh`, generated init command, observer `.cmd`, `scripts/flr0350_launch_gate.py`, tests.

- [ ] Add one static guest command that receives only the validated current ID, rejects `/run/flr0350` if it exists **or is a dangling symlink**, creates it atomically as `root:root` mode 0700, and writes the run ID with exclusive creation. Run it after guest preflight and before app launch; assert runner order and <=4096 bytes.
- [ ] Observer reads the root-protected run ID, repeats current process/FIFO checks, and exclusively records version, run ID, PID/start/UID, gate dev/inode. Emit identity PASS only after successful record creation; any collision/write/validation error fails closed. Marker content must be strictly parsed; no user-writable `/run/user/1001` file is trusted as identity authority.
- [ ] Host validator requires the expected run ID (`--validate <run-id> ...`) and exact version-2 fields; compare launch record, observer measurement, and persisted identity. Preserve the official observer's descriptor-agnostic measurement: it reports the actual `read(0)` and object, rather than hard-coding an FD.
- [ ] Test dangling-symlink collision, stale run ID, partial/existing identity marker, wrong owner/mode/type, run/PID/start mismatch, and dev/inode mismatch. Keep failure output bounded and specific.

## Task 3 — stopped attach, resumed revalidation, single-descriptor GO, safe cleanup

**Files:** attach/release/stop `.cmd` adapters and committed guest `.sh` helpers, `work/commands/FLR-0350-sync-producer.gdb`, runner, tests.

- [ ] If a command's identity checks do not fit its current serial line, move the decision logic into a readable committed guest `.sh` helper and keep its `.cmd` adapter minimal. Stage only one existing run-scoped guest payload area; verify each helper's working-tree bytes equal `HEAD`, record SHA-256, transfer with bounded base64 chunks, and verify the installed guest SHA before execution. Do not create another temp directory or persistent volume.

- [ ] Pre-GDB gate accepts only syscall number 0 with arg1 `0x0`, unchanged PID/start/comm/UID, and fd0/fd3/named gate all matching the root identity record. Keep every failed predicate named and GDB unreachable on any failure.
- [ ] In GDB's Python pre-continue path, verify the selected inferior matches recorded PID/start/UID, the target is ptrace-stopped, both descriptors match the recorded FIFO dev/inode, and root run ID/identity are valid. Create an exclusive root-owned attach-authorization record bound to run ID, target PID/start, GDB PID/start, and FIFO dev/inode; otherwise raise a GDB error.
- [ ] Keep the target stopped while GDB waits for the release command's GO record, with a short fixed deadline and repeated PID/start/UID/stopped-state/fd-identity checks. Timeout or changed state fails closed; never continue merely because a wait expired. Because batch-GDB exit can detach/resume, terminate the exact inferior before raising on invalid or expired post-write state.
- [ ] Release-GO requires the GDB tracer and target to remain stopped; validates root identity and attach authorization; opens the FIFO writer once under a bounded timeout; compares the opened descriptor's dev/inode with the record; then rechecks target PID/start/UID/stopped state and fd0/fd3 identities while the target is still stopped. Only then write GO through that same open descriptor and exclusively publish a root-owned GO record binding run ID, target/GDB identity, FIFO dev/inode, and write result. No pathname reopen is allowed. Any failed check before the write produces zero GO bytes. If record publication fails after a successful write, GDB kills the exact inferior while still attached; if that kill cannot be confirmed, hold GDB and require the runner's exact-PID kill before interrupting it.
- [ ] GDB validates the exact GO record while the target remains stopped, then continues. The runner checks attach PASS before invoking release-GO; release-GO PASS requires the subsequent same-PID exec marker, making GO authorization and actual exec distinct recorded states.
- [ ] After continuation, validate same PID/start/UID, expected tracer, `flutter-auto` exec path, and GDB exec marker. Keep stopped-state checks separate from running/exec checks; do not require syscall `read(0)` after GO.
- [ ] Cleanup validates run ID, identity record, attach authorization, and GO record before removing run-owned FIFO/records. Before sending GDB SIGINT/TERM, if same-PID exec is not recorded or GO record is invalid, terminate only the target whose PID/start/UID match the protected identity; if that cannot be confirmed, do not interrupt GDB and report cleanup FAIL. Remove only objects whose type, owner, mode, and dev/inode are proven.
- [ ] Add regression tests for the actual pre-GDB/release shell decision seams, including process-state mutation and path swap after prechecks but before/while writer open; assert zero GO bytes on every pre-write failure. Separately test post-write GO-record publication failure: target termination precedes GDB error/interrupt and the log explicitly says token written but execution prevented. Assert GDB stop authorization precedes its first continue, GDB waits for a valid GO record, and the runner cannot issue release before attach PASS.
- [ ] Run focused tests, `sh -n` for helpers and adapters, runner `--check`, one-line byte checks, exact source/HEAD/staged payload checks, and failure-output review. Do not start Mini runtime if any local gate is FAIL/UNKNOWN.

## Task 4 — commit, exact bundle, one Mini run, and evidence closeout

- [ ] Run canonical-repository, privacy, file-size, Markdown, checkpoint, focused-test, runner-`--check`, and diff checks. Record the nine pre-existing Markdown link failures in FLR-0338/0339/0340 without widening scope.
- [ ] Finish FLR-0360's ticket/log/dashboard closeout in its existing feature branch and commit that bounded closeout locally. Do not stage FLR-0362 plan/ticket/log on the FLR-0360 branch.
- [ ] Create `dev-flr-0360-attach-gate` from `main`, merge the completed FLR-0360 feature locally, then create `feature-flr-0362-align-shell-read-fd` from that dev branch. Record every ref/merge in the working log; do not push or open a PR.
- [ ] Commit FLR-0362 docs/tests/implementation locally on its feature branch; record full SHA. Do not push.
- [ ] Transfer exact commit via `scripts/handoff-fluorite-bundle.sh <receiver-base> <local-tip>` to the established Mini receiver; verify receiver tip and effective TOPDIR/TMPDIR. Do not transfer QEMU images.
- [ ] Before consuming `flr0362-0001`, the runner's read-only preflight must verify exact artifacts, receiver, helper provenance, free ports, no target processes, and unused evidence path. Record invocation before inspecting results.
- [ ] Require observer v2 identity PASS, stopped-attach authorization PASS, resumed attach PASS, and release-GO/EXEC evidence. On first failed predicate, stop, preserve bounded logs/QMP, and do not bypass or retry.
- [ ] Preserve QMP full-frame still/eight-frame video and hashes. Record GO state, full-frame and 3D-ROI pixel metrics, HUD/Sequoia visibility, and first divergence. If GO occurs but pixels fail, open a separate renderer ticket informed by FLR-0286/0287; do not call this gate ticket a renderer success.
- [ ] Verify app stop, exact run-owned FIFO/record cleanup, accepted QMP quit, and zero run-owned QEMU/QMP/app residuals. Update ticket/log PDCA and close only with evidence.

**Acceptance:** only the exact, run-bound `read(0)` FIFO reaches GDB/GO; GDB validates identity while stopped; GO is written through the one descriptor whose dev/inode was checked; all pre-write substituted/partial states fail with zero GO bytes; any post-write GO-record failure terminates the exact target before it can consume the queued token; every serial adapter is one line <=4096 bytes and every installed helper matches committed source SHA; one exact-bundle Mini run reaches a named next boundary or records the first stop; QMP evidence and cleanup status are retained. Product 2D+3D success remains a separate acceptance criterion.
