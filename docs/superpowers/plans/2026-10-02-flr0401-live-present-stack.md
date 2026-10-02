# FLR-0401 — live FEngine stack at unmatched Present Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Each task ends with a testable deliverable and a local commit; do not push.

**Goal:** Capture one identity-bound GDB stack from the live `FEngine::loop` thread at the first unmatched Present on the exact patch-0334 image.

**Architecture:** Preserve the FLR-0399/0400 bounded host poll, serial framing, QMP capture, and exact cleanup. Add an opt-in direct-launch mode so a single bounded GDB attach can occur while the target is live; append its selected-thread output to the same app log consumed by the observer. At the first unmatched sample, take a separately named identity-bracketed QMP still immediately before the attach. Keep the default GDB-owned launch command byte-for-byte unchanged for backward compatibility.

**Tech Stack:** Python 3, `unittest`, bounded guest shell commands, GDB batch attach, the existing Mini QEMU runtime harness, QMP framebuffer capture, Git bundle handoff.

**Spec:** `work/tickets/FLR-0401-capture-live-fengine-present-stack.md`

## Global Constraints

- Reuse the exact FLR-0396/0334 kernel, rootfs, qemuboot, app bundle, QEMU profile, build/TMPDIR, and evidence roles; verify them at fresh preflight.
- Freeze the Example Demo launch arguments and all four FLR-0400 diagnostic environment values; change only debugger supervision.
- Use one fresh run ID, one QEMU, one global 120-second deadline, and at most one GDB attach with an 18-second SIGTERM deadline plus a 2-second kill grace (20-second wall-clock cap); no automatic retry.
- Bound GDB symbol loading with `--nx`, `sysroot=/`, `solib-absolute-prefix=/`, `solib-search-path=/usr/lib:/lib`, and `auto-solib-add off`; explicitly load only the needed Lavapipe shared-library symbols.
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

### Task 1: Add failing tests for state counters and the FLR-0401 run identity

**Files:**
- Modify: `tests/test_flr0399_live_capture.py`
- Modify: `scripts/flr0399_live_capture.py`
- Modify: `work/commands/FLR-0399-qemu-start.sh`

**Interfaces:**
- Consumes: current `parse_state_output`, `guest_commands`, and `run_once` APIs.
- Produces: regression tests only for the new `Sample` counters and accepted FLR-0401 run identity.

- [x] **Step 1: Test counter preservation on an unmatched state**

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

Also require `expected_run_dir(..., "flr0401-0001")` to resolve within its
evidence role, and exercise the start helper with that ID until it reaches the
expected missing-build-role gate (before any runtime action).

- [x] **Step 2: Test rejection of malformed state counters**

Add table-driven parser cases for a missing `PRESENT_BEGIN`, duplicate
`READY`, negative `SUN`, and non-decimal `PRESENT_RETURN`; each must raise
`ValueError`.

- [x] **Step 3: Run the focused suite and confirm the new tests fail for missing behavior**

Run: `python3 -m unittest tests.test_flr0399_live_capture -v`

Result: 46 tests ran; 4 failures and 3 errors reproduce the missing counter/run-ID behavior. Existing unrelated observer cases pass. The exact failure list is in the FLR-0401 working log.

- [x] **Step 4: Implement only the counter and run-ID slice**

Add four zero-default `Sample` counter fields. Require exactly one unsigned
decimal value for each READY/PRESENT_BEGIN/PRESENT_RETURN/SUN field and reject
missing or malformed values. Accept `flr0401-NNNN` in the Python and shell
validators and update their validation messages. Keep launch behavior and
state classification unchanged.

- [x] **Step 5: Re-run the focused suite and commit this green slice locally**

Run the focused suite and `bash -n work/commands/FLR-0399-qemu-start.sh`, then
commit only this parser/run-ID slice. Do not push.

### Task 2: Add the opt-in direct launch and identity-checked GDB command

**Files:**
- Modify: `scripts/flr0399_live_capture.py`
- Test: `tests/test_flr0399_live_capture.py`

**Interfaces:**
- Consumes: `guest_commands(run_id, launch_mode=...)` and the run-scoped `LOG_PATH`/identity file.
- Produces: unchanged default `gdb-run` commands; `direct` launch plus `GuestCommands.capture_present_stack`.

- [x] **Step 1: Add failing direct-launch and selected-stack command tests**

Assert that direct mode preserves the pinned Demo bundle, UID, XDG/Wayland
variables, four diagnostic environment values, timeout, shared log, and
PID/UID/start recording, but does not invoke GDB during app launch. Pin the
default `guest_commands("flr0400-0001")` launch-command digest so it remains
byte-for-byte unchanged. Assert the attach command checks saved identity and
unmatched counters, attaches only to that PID, appends to the same log,
disables automatic symbol loading and loads only `libvulkan_lvp`, selects exact
`FEngine::loop` threads, records at most eight frames and expands to 24 only
after `lvp_pipe_sync_wait`, detaches, and prints a bounded result marker.
Assert one-line/4096-byte framing and that the `observe` CLI accepts
`--launch-mode direct`.

- [x] **Step 2: Run the focused tests and record the expected red result**

Run: `python3 -B -m unittest tests.test_flr0399_live_capture.GuestCommandContractTests.test_default_gdb_run_launch_command_is_byte_for_byte_unchanged tests.test_flr0399_live_capture.GuestCommandContractTests.test_direct_launch_keeps_the_exact_demo_profile_without_gdb_parent tests.test_flr0399_live_capture.GuestCommandContractTests.test_present_stack_command_is_identity_and_unmatched_gated_and_bounded tests.test_flr0399_live_capture.GuestCommandContractTests.test_observe_cli_accepts_and_passes_the_direct_launch_mode -v`.
Result: the legacy launch digest passed; the direct-launch and capture-command
tests errored on missing `launch_mode`/`capture_present_stack` APIs; the CLI
rejected `--launch-mode`. Expected red state: 4 selected tests, 3 errors.

- [x] **Step 3: Implement launch selection and command generation**

Keep `gdb-run` as the default. Direct mode retains the exact profile and
`/usr/bin/timeout --signal=TERM --kill-after=2s 150` and shared log, but runs
`/usr/bin/flutter-auto` without a GDB parent. Generate one selected-thread
attach command with `/usr/bin/timeout --signal=TERM --kill-after=2s 18` (20-
second wall-clock cap), `gdb --nx`, and `-iex` settings applied before `-p`
loads the process. Reuse the FLR-0110 low-memory sysroot/library settings and
selective `libvulkan_lvp` symbols. Add the explicit CLI mode and pass it to
`guest_commands`. GNU GDB documents that `auto-solib-add off`
requires explicit `sharedlibrary REGEXP` loading and can reduce memory use
when library debug information is large; see
[GDB shared-library symbol loading](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Files.html).

- [x] **Step 4: Run focused tests and shell-parse generated commands**

Run: `python3 -B -m unittest tests.test_flr0399_live_capture -v` — 52/52
PASS. Generated commands for all supported IDs and both launch modes parse with
`sh -n` and `bash -n`; the legacy FLR-0400 launch digest is unchanged. The CLI
argument reaches `guest_commands(..., launch_mode="direct")`.

- [ ] **Step 5: Commit the direct-launch slice locally**

Commit the direct-launch/command-generation slice locally; do not push.

### Task 3: Trigger the attach once within the existing absolute deadline

**Files:**
- Modify: `scripts/flr0399_live_capture.py`
- Test: `tests/test_flr0399_live_capture.py`

**Interfaces:**
- Consumes: parsed counter fields, `capture_present_stack` command, existing `read_state`, QMP capture, and exact teardown adapters.
- Produces: at most one selected GDB capture after a live unmatched sample and a post-attach identity verification.

- [ ] **Step 1: Add failing callback tests for matched/unmatched and identity boundaries**

Test one trigger on the first live unmatched sample, no trigger when counters
match or identity is missing/wrong-UID, no second trigger on repeated unmatched
polls, no work after the absolute deadline, and preservation before exactly-once
teardown on callback timeout. Test stable-identity verification before and
after the trigger still and after GDB; assert still capture precedes the GDB
callback.

- [ ] **Step 2: Run focused tests and record expected red results**

Run: `python3 -m unittest tests.test_flr0399_live_capture -v`.
Expected: the new callback and ordering cases fail while existing observer
behavior remains unchanged.

- [ ] **Step 3: Implement the one-shot trigger inside the fixed deadline**

Check `present_begin > present_return` after each live sample and before the
next poll sleep. At most once, verify identity, capture the distinct full QMP
still, verify identity again before GDB, execute the 20-second-bounded attach,
and verify identity after GDB. Stop if identity changes; otherwise retain
callback/timeouts in `Outcome.errors` and continue polling within the original
deadline. Always preserve evidence before exactly-once teardown.

- [ ] **Step 4: Run focused observer and serial regressions**

Run: `python3 -m unittest tests.test_flr0399_live_capture -v`

Expected: all focused observer tests pass; the existing localhost serial tests remain unchanged and pass.

- [ ] **Step 5: Commit the one-shot controller change locally**

Commit the controller slice locally only; do not push.

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
