# FLR-0359 — Bind QEMU runs to the committed runtime helper

> **For agentic workers:** execute task-by-task. Keep the current ticket as the only `In Progress` unit and update the working log at each gate.

**Goal:** Ensure the runner and QEMU starter both execute one run-scoped helper byte-identical to `scripts/qemu-runtime-harness.sh` in the exact committed bundle tip, then validate that helper once on the existing Mini QEMU image.

**Architecture:** The runner verifies the repository helper is executable and its SHA-256 matches the blob at `HEAD`, copies it into the fresh run parent before QEMU start, then verifies/logs committed, source, and staged hashes. It uses that staged copy for all host serial/QMP operations. The starter repeats the `HEAD`/source check in preflight and, in `start` mode, compares the executable run-scoped file byte-for-byte and by SHA to both. The historical QMP pixel-capture helper and saved runqemu arguments remain pinned under the prior evidence directory; only helper provenance is changed.

**Tech stack:** Bash, Python `unittest`, existing FLR-0350 serial/FIFO/GDB/QMP harnesses, established Git bundle handoff, Mini QEMU `runqemu`.

**Spec:** [FLR-0359 ticket](../../../work/tickets/FLR-0359-use-committed-qemu-runtime-helper.md).

## Constraints

- Work in the canonical repository on `feature-flr-0359-committed-qemu-helper`; preserve prior ticket commits and unrelated changes.
- During execution, keep FLR-0358 in Waiting and FLR-0359 as the sole In Progress ticket; close FLR-0359 after its bounded Mini gate result is recorded.
- Do not edit Flutter/Filament, Yocto recipe/layer, image, camera/light/material/texture, or composition code.
- Do not loosen the official FIFO parser or process/FIFO identity predicates.
- Stage the helper from the exact repo commit into the unique run parent and prove both runner/starter use that same file; do not select an executable from a prior run.
- Preserve the fixed QMP pixel helper identity and pinned kernel/rootfs/qemuboot artifacts.
- Use standard Mac-to-Mini Git bundle handoff; no BitBake, Devtool, image build, or rootfs/kernel copy is required for this host-runner change.
- Run one fresh Mini ID only after local checks and exact receiver/artifact/process preflight. Never retry it.
- Capture QMP-only still and eight frames/video. Classify every capture as pre-GO or post-GO; only post-GO pixels inform the renderer.

## Historical evidence to reuse

- FLR-0356: all 11 commands were staged and FIFO identity fields matched; the official host gate still failed `marker-not-first` before GDB/GO.
- FLR-0358: serial capture boundary is locally tested, but Mini executed the FLR-0335 helper SHA `339472…`, not the committed helper SHA `088e8e…`; therefore Mini did not test the serial fix.
- FLR-0109 / FLR-0351: reject wrong OE source/template assumptions; read-only preflight must derive the unique source matching the fixed build's persisted `TEMPLATECONF` before receiver mutation.
- FLR-0286: lit self-made Filament fixture and HUD are proven in the same QMP frame; use as the generic composition positive control.
- FLR-0287: production Sequoia reached scene-add/draw/present while native ROI remained `0/144000` changed/chromatic and HUD had 2,845 chromatic pixels. This is a distinct production boundary, not a contradiction of FLR-0286.
- FLR-0357: pre-GO black frames are harness-stop evidence, not render failures; do not repeat unsupported camera/light/compositor theories before the gate reaches GO.

---

### Task 1 — Add a failing provenance contract before changing orchestration

**Files:**
- Modify: `tests/test_flr0350_launch_gate.py`
- Modify: static contract in `work/commands/FLR-0350-run-sync-producer.sh::static_check`

- [x] Add tests asserting the runner's helper source is `scripts/qemu-runtime-harness.sh`, the run-scoped copy is staged before the starter `start` call, and the runner uses that copied file.
- [x] Add tests asserting the starter's `start` mode uses the same run-parent file and compares it to repo source; reject any executable reference to `flr0335-0001/qemu/qemu-runtime-harness.sh` or a fixed old helper SHA.
- [x] Preserve a test that the QMP pixel-capture helper still uses its explicit immutable SHA.
- [x] Run the focused tests first and observe the expected red result on old source selection (2 failed, 1 passed); shorten failure output and correct self-matching assertions so the gate checks executable runtime sections rather than its own embedded contract strings.

### Task 2 — Implement one source and one run-scoped helper copy

**Files:**
- Modify: `work/commands/FLR-0350-run-sync-producer.sh`
- Modify: `work/commands/FLR-0350-qemu-start.sh`
- Tests: Task 1 contract

- [x] In the runner, require an executable helper whose bytes match `HEAD:scripts/qemu-runtime-harness.sh`; after creating the unique run parent, copy once to `$parent/qemu-runtime-harness.sh`, verify it, record committed/source/staged hashes and commit identity, then select that copy before QEMU start.
- [x] In starter preflight, require the executable current source and verify its hash against the committed HEAD blob without requiring a run copy that does not yet exist.
- [x] In starter start, require an executable run-scoped helper, verify it against both repo source and committed HEAD, report named fail-closed reasons on mismatch, and invoke the staged file for QEMU preflight/start.
- [x] Keep capture-helper selection and SHA validation intact; remove only the runtime-helper historical path/hash pin.
- [x] Make `--check` fail closed if source/staging/use order or either caller diverges. Focused tests and runtime contract pass; full local gates remain in Task 3.

### Task 3 — Run local gates and make a local-only ticket commit

**Files:** runner, starter, tests, ticket, working log, plan, `TASKS.md`.

- [x] Run focused provenance tests, `bash work/commands/FLR-0350-run-sync-producer.sh --check`, QEMU/runtime harness contract, shell syntax, full Python suite, privacy, ticket checkpoint, file-size, and Markdown-link checks. The only suite environment rejection was sandbox loopback bind; the same 132-test run passed with loopback permission.
- [x] Record the nine pre-existing repository-wide Markdown failures in FLR-0338/0339/0340; no new FLR-0359 link error appeared. Do not repair unrelated historical evidence links.
- [x] Inspect staged paths and privacy identity, then commit locally on this feature branch. Do not push. Code commit `f63956e`; exact-tip preflight record `8de11b0e`.

### Task 4 — Bundle exact tip and preflight existing Mini runtime

**Files:**
- Use: `scripts/handoff-fluorite-bundle.sh`, `scripts/reuse-mini-build-receiver.sh`, `work/commands/FLR-0350-run-sync-producer.sh`.

- [x] Transfer the exact local tip using the established bundle script. Bundle SHA `201a298a90beeeeecc49a2f89a8323a4e6862d86c2d296f182d580e85cee228e`; receiver tip `8de11b0e47304724f436d5567b55e62640a237d3`.
- [x] Use the existing fixed receiver/build/TMPDIR; exact bundle-handoff PASS and pinned artifact hashes are recorded. The runner/starter's freshness, process, and port guards executed and did not abort, but the exact preflight marker was not retained. The supplemental SSH process/port/run-directory inventory is UNKNOWN, not an observed PASS.
- [x] No BitBake task, Devtool, image build, VM/cache cleanup, or QEMU artifact copy.
- [x] Receiver HEAD helper SHA matched `088e8e39…` before the fresh runtime attempt.

### Task 5 — Make exactly one Mini runtime attempt and preserve QMP evidence

**Files:**
- Use: `work/commands/FLR-0350-run-sync-producer.sh`, existing serial validator, GDB and QMP capture helpers.

- [x] Use one fresh ID `flr0359-0001`; stage all 11 serial commands and the helper before QEMU start.
- [x] Confirm the run log identifies commit `8de11b0e…` and matching committed/source/staged helper SHA `088e8e39…`.
- [x] The unchanged official FIFO validator passed. The next GDB attach stage failed its generic precondition and stopped before attach/GO; `FLR0350_EXEC` was absent.
- [x] Capture QMP full-frame still and eight frames/video; classify as pre-GO. Post-run still and all eight frames were black/identical; this is not a renderer verdict.
- [x] QMP quit was accepted and cleanup proved zero run-owned QEMU/app/QMP residuals.
- [x] Hand off only the new GDB-attach predicate ambiguity; no renderer patch or second hypothesis was mixed into FLR-0359.

**Acceptance result:** the exercised exact source → staged file → runner/starter → bundle receiver path is proven and was observed on Mini. Static contracts assert the required source/staging/call-site relationship; missing/mismatch runtime branches were deferred and are not claimed executed. Mini passed the unchanged FIFO gate, then stopped at the GDB-attach precondition before GO. QMP evidence is preserved and classified as pre-GO; cleanup passed. The 3D objective remains open.
