# FLR-0356 Stage the FIFO Observer Before QEMU Launch — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the bounded Mini QEMU diagnostic runner prove that every fixed serial command it calls is readable and staged before QEMU launch, then use one fresh run to reach the actual-FD FIFO gate.

**Architecture:** Keep the existing run-ID validation, pinned image identity, QEMU profile, and guest commands unchanged. Define one static command inventory; make the runner's local regression compare that inventory with fixed `guest_run` callsites; preflight each source and copy the inventory into the evidence parent before QEMU start, then preserve those inputs under the QEMU run directory.

**Tech Stack:** Bash, Python 3/unittest, Yocto `runqemu` on the Mini PC, QEMU QMP, SSH/SCP, FFmpeg.

**Spec:** `work/tickets/FLR-0356-stage-fifo-observer-before-qemu.md`

## Global Constraints

- Run `bash scripts/assert-canonical-repository.sh` before editing; only edit in a passing canonical feature worktree.
- Keep exactly one ticket `In Progress`; FLR-0355 is `Waiting` and `flr0355-0001` must never be retried.
- Root this branch at `dev-mini-recovery` and retain FLR-0354/0355 as explicit prerequisite commits; do not modify the shared dev ref.
- Preserve all current kernel/rootfs/qemuboot SHA pins, command contents, diagnostic environment, QEMU arguments, ports, and 6144-MiB memory.
- Do not edit product source, recipes, image contents, build caches, deploy artifacts, or Mini TMPDIR. No Devtool or BitBake build is needed.
- Transfer only through `scripts/handoff-fluorite-bundle.sh`; do not push.
- Use exactly one fresh runtime ID, `flr0356-0001`; do not reuse it once its evidence directory exists.
- Capture display pixels only with the QMP helper; do not capture the host desktop or copy QEMU disk images to the Mac.
- Keep raw frames/video outside Git; transfer only QMP review evidence and bounded logs.
- Stop only the recorded app and QEMU instance through the existing cleanup and QMP `quit`; never use global kill.

---

### Task 1: Add a red staging-coverage regression

**Files:**
- Modify: `tests/test_flr0350_launch_gate.py`
- Test: `tests/test_flr0350_launch_gate.py::LaunchGatePredicateTests.test_all_fixed_guest_commands_are_staged_before_qemu_start`

**Interfaces:**
- Consumes: `work/commands/FLR-0350-run-sync-producer.sh`, fixed `guest_run` source callsites, and the runner's declared `runtime_command_files` array.
- Produces: a deterministic assertion that no fixed command reference is missing from the staged set and the parent staging copy precedes the starter's `start` invocation.

- [x] **Step 1: Write the failing test**

Add `import re`, then add this method to `LaunchGatePredicateTests`:

```python
    def test_all_fixed_guest_commands_are_staged_before_qemu_start(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        fixed_calls = set(re.findall(
            r"(?m)^\s*guest_run\s+\S+\s+(FLR-0350-[\w.-]+\.cmd)\s*$",
            runner,
        ))
        inventory = re.search(
            r"(?ms)^runtime_command_files=\(\n(.*?)^\)", runner
        )
        self.assertIsNotNone(inventory, "runner has no static command inventory")
        staged = set(re.findall(
            r"(?m)^\s*(FLR-0350-[\w.-]+\.cmd)\s*$", inventory.group(1)
        ))
        self.assertTrue(fixed_calls, "no fixed guest_run commands were found")
        self.assertEqual(fixed_calls - staged, set())
        self.assertIn("FLR-0350-observe-fifo-read-gate.cmd", staged)
        copy_parent = runner.index(
            'cp -- "$repo_root/work/commands/$file" "$parent/$file"'
        )
        start = runner.rindex(
            'FLR0350_RUN_ID="$run_id" bash "$start_script" start'
        )
        self.assertLess(copy_parent, start)
```

- [x] **Step 2: Run it and confirm the current runner fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_flr0350_launch_gate.py`

Expected: FAIL because the runner has no `runtime_command_files` inventory and the FIFO-observer command is not in the copy loop. Observed: one new failure at `runner has no static command inventory`; 27 prior tests passed.

### Task 2: Define and stage the complete command inventory

**Files:**
- Modify: `work/commands/FLR-0350-run-sync-producer.sh`
- Modify: `tests/test_flr0350_launch_gate.py`
- Test: `tests/test_flr0350_launch_gate.py`

**Interfaces:**
- Consumes: the fixed command callsites checked in Task 1.
- Produces: a single Bash array named `runtime_command_files` containing `FLR-0350-preflight.cmd`, `FLR-0350-launch-paused-production.cmd`, `FLR-0350-observe-fifo-read-gate.cmd`, `FLR-0350-attach-pre-submit.cmd`, `FLR-0350-release-go.cmd`, `FLR-0350-wait-symbol-gate.cmd`, `FLR-0350-wait-matched-wait.cmd`, `FLR-0350-watch-window.cmd`, `FLR-0350-interrupt-gdb.cmd`, `FLR-0350-capture-runtime-state.cmd`, and `FLR-0350-stop-recorded-app.cmd`.

- [x] **Step 1: Replace duplicate Python command names with the inventory parser**

Inside `static_check()`'s embedded Python, extract the array body from `runner_text` with `re.search(r"(?ms)^runtime_command_files=\(\n(.*?)^\)", runner_text)`, derive `command_names` from full-line `FLR-0350-*.cmd` entries, reject a missing/empty inventory, and retain the existing one-line, byte-size, and `sh -n` checks for each name.

- [x] **Step 2: Add the one inventory to the Bash runner**

Declare `runtime_command_files=(...)` once before `static_check()`, using the exact eleven filenames in the interface block. Replace the later hand-maintained `for file in ...` copy list with iteration over this array.

- [x] **Step 3: Validate and stage before QEMU start**

Before the target preflight can consume an ID, check every `"$repo_root/work/commands/$file"` is readable and fail with a bounded `FLR0350_COMMAND_STAGE=FAIL` marker if not. After creating `$parent` and installing the runner log, copy each inventory file to `"$parent/$file"` before invoking the starter in `start` mode. After QEMU starts, copy the same files from `$parent` to `$run_dir` for evidence. Keep `guest_run`'s existing run-directory-then-parent lookup.

- [x] **Step 4: Refresh the static fresh-ID sample**

Change the `--check` sample from `flr0355-0001` to `flr0356-0001`; preserve rejection of consumed `flr0350-0001`. Do not change `CONSUMED_RUN_IDS` or the shared validator.

- [x] **Step 5: Run the red/green and source checks**

Run `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_flr0350_launch_gate.py`; expected PASS. Then run `bash -n work/commands/FLR-0350-run-sync-producer.sh` and `bash work/commands/FLR-0350-run-sync-producer.sh --check`; expected PASS, exact diagnostic profile preserved, and `QEMU_NOT_STARTED` reported.

### Task 3: Record, verify, and commit FLR-0356 locally

**Files:**
- Modify: `TASKS.md`
- Modify: `work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md`
- Modify: `work/logs/2026-09-29-flr0355.md`
- Modify: `work/tickets/FLR-0356-stage-fifo-observer-before-qemu.md`
- Modify: `work/logs/2026-09-29-flr0356.md`
- Modify: this plan

**Interfaces:**
- Consumes: completed FLR-0355 evidence and the passing command-staging regression.
- Produces: one clean FLR-0356 commit on `feature-flr-0356-stage-fifo-command`, with FLR-0355 moved to `Waiting` and FLR-0356 the sole `In Progress` ticket.

- [x] **Step 1: Update the checkpoint log and ticket**

Record facts, inferences, hypotheses, UNKNOWN, exact test commands/results, and the source/packaging/runtime/visual/cleanup boundaries. Keep each file to its one ticket; link FLR-0355 only as predecessor evidence.

- [x] **Step 2: Run required documentation gates**

Run `bash scripts/assert-canonical-repository.sh`, `git diff --check`, `scripts/runtime-checkpoint.sh verify --ticket FLR-0356 --log work/logs/2026-09-29-flr0356.md`, and `make check-privacy`. Expected: canonical/privacy/checkpoint/whitespace PASS with exactly one ticket In Progress.

- [ ] **Step 3: Commit only reviewed FLR-0356 paths locally**

Stage named ticket, log, plan, task dashboard, runner, and test paths; run `git diff --cached --check`; commit as `fix: stage all FLR-0350 guest commands before QEMU`. Do not push.

### Task 4: Handoff and run one fresh Mini QEMU attempt

**Files:**
- Execute: `scripts/handoff-fluorite-bundle.sh <dev-mini-recovery-commit> <feature-tip>`
- Execute on Mini: `work/commands/FLR-0350-run-sync-producer.sh flr0356-0001`
- Evidence: Mini `$EVIDENCE_ROOT/flr0356-0001/` and one Mac review directory outside Git.

**Interfaces:**
- Consumes: exact committed FLR-0356 bundle, fixed receiver, the pinned FLR-0335 image and command set.
- Produces: gate verdict before attach/GO, bounded diagnostic logs, QMP still/eight frames/video, pixel summary, hashes, and zero-residue teardown evidence.

- [ ] **Step 1: Transfer exact bundle through the fixed helper**

Resolve `dev-mini-recovery^{commit}` and `HEAD^{commit}` to full commit IDs, call the existing bundle helper with the fixed role configuration, and record exact bundle SHA and receiver tip. Do not push or create another receiver.

- [ ] **Step 2: Run read-only target preflight**

Confirm the exact receiver tip is clean, `flr0356-0001` evidence directory is absent, QMP path and ports are free, target process count is zero, and the three pinned artifact hashes match. Run the receiver copy of `--check` and starter `preflight`; if any check fails, stop before the evidence directory is created.

- [ ] **Step 3: Execute the runner once**

Run `bash work/commands/FLR-0350-run-sync-producer.sh flr0356-0001` on `$BUILD_HOST`. Require `FLR0350_GATE_OBSERVATION` and `FLR0350_FIFO_READ_GATE=PASS` before GDB attach/GO. If the target gate fails, preserve its bounded reason and do not retry the ID.

- [ ] **Step 4: Capture and inspect QMP evidence**

Use the runner's QMP still and eight one-second QMP frames. Transfer only those display artifacts and bounded logs. Convert to PNG/H.264 on Mac, inspect full frame and ROI `0,200,1280,600`, compute hashes, resolution, frame count/FPS, and separate HUD versus 3D pixel verdicts; show the image/video.

- [ ] **Step 5: Verify exact teardown**

Require recorded wrapper/app stop, run-owned FIFO cleanup, QMP quit, QEMU exit, removed QMP socket, and zero target processes. Do not use a global kill.

### Task 5: Close the bounded ticket

- [ ] Put the gate, rendering, screenshot, and teardown verdicts in the FLR-0356 ticket/log; preserve UNKNOWN where evidence did not reach a boundary.
- [ ] Mark Done only if the target attempt, QMP evidence, and cleanup criteria pass. If a new target-side defect appears, create a new ticket and run ID before changing scope.

## Self-review

- The regression compares the static callsites to the source copied by the runner, rather than merely checking that the observer file exists.
- Static source checks and parent staging run before QEMU start; the actual QMP/video capture remains on the Mini QEMU instance.
- No image/build/profile change is part of the countermeasure.
- A black image before GDB attach/GO is not a Flutter rendering verdict; a 3D PASS requires visible ROI pixels.
- The one-run limit, fresh ID, bounded artifacts, and exact cleanup are explicit.
