# FLR-0401 — live FEngine stack at unmatched Present Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Each task ends with a testable deliverable and a local commit; do not push.

**Goal:** Capture one identity-bound GDB stack from the live `FEngine::loop` thread at the first unmatched Present on the exact patch-0334 image.

**Architecture:** Preserve the FLR-0399/0400 bounded host poll, serial framing, QMP capture, and exact cleanup. Add an opt-in direct-launch mode so a single bounded GDB attach can occur while the target is live; append its selected-thread output to the same app log consumed by the observer. At the first unmatched sample, take a separately named identity-bracketed QMP still immediately before the attach. Keep the default GDB-owned launch path unchanged for backward compatibility.

**Tech Stack:** Python 3, `unittest`, bounded guest shell commands, GDB batch attach, the existing Mini QEMU runtime harness, QMP framebuffer capture, Git bundle handoff.

**Spec:** `work/tickets/FLR-0401-capture-live-fengine-present-stack.md`

## Global Constraints

- Reuse the exact FLR-0396/0334 kernel, rootfs, qemuboot, app bundle, QEMU profile, build/TMPDIR, and evidence roles; verify them at fresh preflight.
- Freeze the Example Demo launch arguments and all four FLR-0400 diagnostic environment values; change only debugger supervision.
- Use one fresh run ID, one QEMU, one global 120-second deadline, and at most one 20-second GDB attach; no automatic retry.
- Capture QMP evidence before GDB pauses Flutter, and require matching PID/UID/start identity before and after capture/attach.
- Do not edit product source, Devtool patches, recipes, image inputs, camera, model, materials, textures, lighting, Flutter UI, build caches, or TMPDIR. Do not build or copy a VM image to Mac.
- Keep Mini paths/credentials out of Git; refer to Mini directories through role names such as `$BUILD_EVIDENCE`.
- Commit scoped work locally only; no push. Transfer only through the official bundle helper.

## File map

- Modify `scripts/flr0399_live_capture.py` for opt-in direct launch, CLI launch-mode plumbing, FLR-0401 run-ID acceptance, validated Present counters, trigger still + one unmatched-Present callback, and a bounded selected-thread GDB command.
- Modify `work/commands/FLR-0399-qemu-start.sh` to accept the fresh `flr0401-NNNN` run-ID namespace while preserving its existing profile guards.
- Modify `tests/test_flr0399_live_capture.py` for state-counter parsing, direct-launch command shape, selected-stack bounds, one-shot trigger behavior, identity checks, and compatibility of the default launch mode.
- Reuse `work/commands/FLR-0399-qemu-start.sh`, `scripts/qemu-runtime-harness.sh`, and `scripts/qemu-pixel-capture.py` unchanged for the exact 0334 image/run profile.
- Update `TASKS.md`, the FLR-0400 ticket/log, and `work/evidence/FLR-0400-0001.md` with the completed observer run and its QMP evidence.
- Add `work/tickets/FLR-0401-capture-live-fengine-present-stack.md`, `work/logs/2026-10-02-flr0401.md`, and the FLR-0401 runtime evidence manifest after the run.

## Interfaces

- Extend `Sample` with integer `ready_count`, `present_begin`, `present_return`, and `sun_count` fields defaulting to zero, so existing test constructors remain source-compatible.
- Extend `GuestCommands` with `capture_present_stack: str`.
- Keep `guest_commands(run_id)` behavior unchanged. Add keyword-only `launch_mode: str = "gdb-run"`; accept only `"gdb-run"` and `"direct"`. The `direct` mode launches the same app/env into the configured combined log and uses the generated `capture_present_stack` serial command.
- Extend `run_once(..., capture_present_stack: Callable[[Sample, float], None] | None = None)`. On the first live sample with `present_begin > present_return`, call it once for the run. The injected callback captures a uniquely named full QMP still, then issues the bounded guest GDB command; the controller then re-reads and verifies the same identity. Preserve callback/timeout errors in `Outcome.errors`; never weaken the existing deadline, log-source, echo, or teardown rules.

---

### Task 1: Add failing tests for the current Present boundary and debugger contract

**Files:**
- Modify: `tests/test_flr0399_live_capture.py`
- Test: `tests/test_flr0399_live_capture.py`

**Interfaces:**
- Consumes: current `parse_state_output`, `guest_commands`, and `run_once` APIs.
- Produces: regression tests for the new `Sample` counters, opt-in direct launch, selected-stack command, and one-shot callback.

- [ ] **Step 1: Test counter preservation on an unmatched state**

```python
def test_state_parser_preserves_unmatched_present_counters():
    sample = parse_state_output(
        "FLR0399_STATE=READY PID=694 UID=1001 START=23470 "
        "READY=1 PRESENT_BEGIN=3 PRESENT_RETURN=2 SUN=1 "
        "LOG_PATH=/run/user/1001/flr0401-0001-gdb.log\n",
        stage="ready",
    )
    assert sample.ready_count == 1
    assert sample.present_begin == 3
    assert sample.present_return == 2
    assert sample.sun_count == 1
```

- [ ] **Step 2: Test direct launch, strict counter rejection, and bounded selected-stack command**

```python
def test_direct_launch_keeps_profile_and_defers_one_selected_stack_attach():
    commands = guest_commands("flr0401-0001", launch_mode="direct")
    assert "/usr/bin/flutter-auto" in commands.launch
    assert "FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1" in commands.launch
    assert "FLR0305_PRODUCTION_SCENE_LIGHT=1" in commands.launch
    assert "/usr/bin/gdb -q --batch -p" not in commands.launch
    assert "PRESENT_BEGIN" in commands.capture_present_stack
    assert "PRESENT_RETURN" in commands.capture_present_stack
    assert "FEngine::loop" in commands.capture_present_stack
    assert "lvp_pipe_sync_wait" in commands.capture_present_stack
    assert "bt 8" in commands.capture_present_stack
    assert "bt 24" in commands.capture_present_stack
    assert "thread apply all" not in commands.capture_present_stack
    assert ">>\"$log\" 2>&1" in commands.capture_present_stack
```

Also assert that missing, duplicate, negative, and non-decimal counter fields
are rejected, and that the default `guest_commands("flr0400-0001")` remains
the existing GDB-owned launch.

- [ ] **Step 3: Test the callback runs once only for a stable live unmatched sample**

```python
def test_unmatched_present_requests_one_live_stack_capture():
    identity = Identity(pid=694, uid=1001, start_time=23470)
    log_path = "/run/user/1001/flr0401-0001-gdb.log"
    samples = iter(
        [
            Sample("READY", identity, log_path, present_begin=1, present_return=0),
            Sample("LIVE", identity, log_path),
            Sample("LIVE", identity, log_path),
            Sample("PRESENT", identity, log_path, present_begin=1, present_return=1),
            Sample("LIVE", identity, log_path),
        ]
    )
    events = []

    def read_state(stage, _remaining):
        events.append(("read", stage))
        return next(samples)

    result = run_once(
        read_state=read_state,
        capture_frame=lambda stage, seen, _remaining: events.append(
            ("frame", stage, seen)
        ),
        capture_present_stack=lambda seen, remaining: events.append(
            ("gdb", seen, remaining)
        ),
        preserve_evidence=lambda: events.append(("preserve",)),
        teardown=lambda: events.append(("teardown",)),
        expected_log_path="/run/user/1001/flr0401-0001-gdb.log",
        timeout_seconds=10,
        monotonic=lambda: 0.0,
    )
    assert sum(event[0] == "gdb" for event in events) == 1
    assert [event[1] for event in events if event[0] == "gdb"] == [identity]
    assert result.status == "OBSERVED"
    assert events[-2:] == [("preserve",), ("teardown",)]
```

- [ ] **Step 4: Run the focused suite and confirm the new tests fail for missing behavior**

Run: `python3 -m unittest tests.test_flr0399_live_capture -v`

Expected: failures are limited to the new counter fields, direct launch/GDB command, and unmatched-stack callback; existing 44 FLR-0400 tests continue passing.

- [ ] **Step 5: Commit the red tests locally**

```sh
git add tests/test_flr0399_live_capture.py
git commit -m "test(observer): cover live unmatched present stack capture"
```

### Task 2: Add the opt-in direct launch and identity-checked GDB command

**Files:**
- Modify: `scripts/flr0399_live_capture.py`
- Test: `tests/test_flr0399_live_capture.py`

**Interfaces:**
- Consumes: `guest_commands(run_id, launch_mode=...)` and the run-scoped `LOG_PATH`/identity file.
- Produces: unchanged default `gdb-run` commands; `direct` launch plus `GuestCommands.capture_present_stack`.

- [ ] **Step 1: Accept FLR-0401 run IDs and add strict state-counter parsing**

Extend the Python run-ID regex and `work/commands/FLR-0399-qemu-start.sh` case regex to accept `flr0401-NNNN`; retain the 0399 and 0400 cases and reject all others. Update the associated validation messages. Add an assertion that `expected_run_dir("flr0401-0001")` and `guest_commands("flr0401-0001", launch_mode="direct")` are accepted.

Parse one non-negative decimal value for each `READY`, `PRESENT_BEGIN`, `PRESENT_RETURN`, and `SUN` field. Reject missing, duplicate, negative, or non-decimal counter fields. Populate the four `Sample` fields without changing state classification or process identity parsing.

- [ ] **Step 2: Generate the direct app command with the exact pinned profile**

Keep `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, the same four environment assignments, Demo bundle, `/usr/bin/timeout` bound, stdout/stderr path, and PID/UID/start recording. Do not invoke GDB in the direct launch command. Add `--launch-mode {gdb-run,direct}` to the CLI; default to `gdb-run` so FLR-0399/0400 behavior is unchanged.

- [ ] **Step 3: Generate a single bounded selected-thread attach command**

Reuse the selected-thread logic from `work/commands/FLR-0341-capture-present-stack.cmd`: require `PRESENT_BEGIN > PRESENT_RETURN`, verify the saved app PID/UID/start token, run GDB with a 20-second timeout, print at most eight frames for each exact `FEngine::loop` thread, expand to 24 only when the eight-frame stack contains `lvp_pipe_sync_wait`, and detach. Append GDB stdout/stderr to the configured combined app log. Print a unique result marker for attach success, timeout, or no selected thread. Extend `make_state_reader` to route `present-stack` to `GuestCommands.capture_present_stack`. Recheck process identity after GDB in the controller and fail closed if it changed.

- [ ] **Step 4: Validate both launch modes and command framing**

Run: `python3 -m unittest tests.test_flr0399_live_capture.LiveCaptureControllerTests -v`

Expected: direct mode is explicit; the default `guest_commands("flr0400-0001")` still generates the old GDB-owned launch; every generated serial command remains single-line and at most 4096 bytes.

- [ ] **Step 5: Commit the command-generation change locally**

```sh
git add scripts/flr0399_live_capture.py tests/test_flr0399_live_capture.py
git commit -m "feat(observer): attach to live unmatched present"
```

### Task 3: Trigger the attach once within the existing absolute deadline

**Files:**
- Modify: `scripts/flr0399_live_capture.py`
- Test: `tests/test_flr0399_live_capture.py`

**Interfaces:**
- Consumes: parsed counter fields, `capture_present_stack` command, existing `read_state`, QMP capture, and exact teardown adapters.
- Produces: at most one selected GDB capture after a live unmatched sample and a post-attach identity verification.

- [ ] **Step 1: Call the injected stack-capture callback at the first live unmatched sample**

Check `sample.present_begin > sample.present_return` after each identity-stable live state sample and before sleeping for another poll. Do not call when the counters match, the identity is absent/wrong UID, or the callback has already been attempted. The callback writes a separately named QMP still before the GDB serial request. Use the remaining portion of the same 120-second monotonic deadline; cap the GDB sub-operation at 20 seconds.

- [ ] **Step 2: Verify process identity after the attach and preserve failures**

Request one identity snapshot after the attach. If PID/UID/start changed, classify the stack as non-live evidence and stop further polling. Record timeout/attach errors in `Outcome.errors`; if the process identity remains stable after a bounded GDB timeout, continue polling under the original absolute deadline. In all cases use the existing evidence-preservation-then-exactly-once-teardown path; do not retry GDB.

- [ ] **Step 3: Add deterministic tests for trigger/no-trigger/identity-change/deadline cases**

Assert one trigger still/attach on repeated unmatched polls, zero attach when `present_begin <= present_return`, no attach for missing/wrong identity, no read or attach after the absolute deadline, stable identity after attach, and evidence preservation before exactly-once teardown after attach timeout. Assert the trigger still occurs before the GDB serial call.

- [ ] **Step 4: Run focused observer and serial regressions**

Run: `python3 -m unittest tests.test_flr0399_live_capture -v`

Expected: all focused observer tests pass; the existing localhost serial tests remain unchanged and pass.

- [ ] **Step 5: Commit the one-shot controller change locally**

```sh
git add scripts/flr0399_live_capture.py tests/test_flr0399_live_capture.py
git commit -m "fix(observer): bound live stack capture and teardown"
```

### Task 4: Verify locally and transfer the committed observer to Mini

**Files:**
- Modify: `TASKS.md`, FLR-0400 ticket/log, FLR-0401 ticket/log, and evidence manifests.
- Test: repository verification targets and the official Mini bundle receiver.

**Interfaces:**
- Consumes: the clean committed FLR-0401 branch and the official bundle helpers.
- Produces: receiver at the exact FLR-0401 tip; no build or QEMU process yet.

- [ ] **Step 1: Run focused and repository checks**

Run the focused suite, `make verify`, canonical/privacy/runtime-checkpoint checks, shell syntax checks for generated commands, Markdown links, file-size limits, and the independent QEMU/runtime-log/Mini-bundle gates. Record the known unrelated FLR-0397 stale-run-ID failure separately; do not fix it here.

- [ ] **Step 2: Commit scoped ticket, plan, log, tests, and observer changes locally**

Run `git diff --check`, canonical/privacy/runtime-checkpoint checks, then commit the FLR-0401 files on `feature-flr-0401-live-present-stack`. Do not push.

- [ ] **Step 3: Use the official bundle handoff and receiver gate**

Run only `scripts/handoff-fluorite-bundle.sh` and the paired receiver validator. Require the exact commit tip, a clean receiver, fixed `TOPDIR`/`TMPDIR`, unchanged 0334 artifact hashes, no active build/runtime owner, free QEMU ports/socket, and unused run ID. Do not manually assemble a bundle or create another TMPDIR/container.

### Task 5: Capture one exact-image live stack and preserve the bounded outcome

**Files:**
- Runtime artifacts: `$BUILD_EVIDENCE/flr0401-0001/qemu/` on Mini.
- Local review derivatives: `work/evidence/FLR-0401-0001/`.
- Update: `work/tickets/FLR-0401-capture-live-fengine-present-stack.md`, `work/logs/2026-10-02-flr0401.md`, `TASKS.md`.

**Interfaces:**
- Consumes: committed observer, direct app launch profile, Mini roles, fixed image, serial/QMP helpers.
- Produces: one live selected stack or one explicit bounded no-trigger/exit/attach-timeout result, full QMP still/video, preserved kernel/coredump evidence, and clean postflight.

- [ ] **Step 1: Run the exact image preflight**

```sh
FLR0399_RUN_ID=flr0401-0001 bash work/commands/FLR-0399-qemu-start.sh preflight
```

Expected: exact kernel/rootfs/qemuboot hashes, fixed machine/build/TMPDIR, PIDFD, free QEMU/ports/socket, and fresh evidence path all pass; QEMU remains stopped.

- [ ] **Step 2: Start exactly one QEMU and run the direct-launch observer**

```sh
FLR0399_RUN_ID=flr0401-0001 bash work/commands/FLR-0399-qemu-start.sh start
python3 scripts/flr0399_live_capture.py observe \
  --run-id flr0401-0001 --launch-mode direct \
  --evidence-root "$BUILD_EVIDENCE" \
  --run-dir "$BUILD_EVIDENCE/flr0401-0001/qemu" \
  --qmp "$BUILD_EVIDENCE/flr0401-0001/qemu/qmp-0401.sock"
```

Expected: one direct Flutter identity, first live QMP capture, one triggered GDB attach only if Present is unmatched, exact evidence preservation and teardown. Never rerun the consumed ID.

- [ ] **Step 3: Review evidence and determine the next discriminator**

Verify QMP dimensions, still/video hashes, exact PID/UID/start before and after capture/attach, marker counts, selected stack outcome, bounded kernel/coredump query, and postflight. Compare the selected stack with FLR-0341 but do not claim WSI causality from a matching symbol alone. If WSI frames recur, open a separate producer-state discriminator; otherwise follow the captured caller. Keep material/texture/light and composition gates UNKNOWN.

- [ ] **Step 4: Commit only the task record/evidence review locally**

Commit the updated dashboard, FLR-0401 ticket/log, and small QMP PNG/MP4 evidence artifacts. Do not push; do not transfer images, caches, or build artifacts.

## Self-review

- Spec coverage: the one-factor debugger-supervision change, matched process identity, one selected attach, current-image provenance, QMP full frame/video, bounded kernel/coredump evidence, and cleanup all have explicit tasks.
- Competing hypotheses remain separate; no Oops opcode, submission marker, READY marker, or diagnostic material is promoted to a root cause or product pass.
- The default FLR-0399/0400 launch remains unchanged, so the new diagnostic mode can be reviewed independently and reverted without changing prior evidence semantics.
