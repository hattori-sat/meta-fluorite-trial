# FLR-0399 — capture live Sequoia state on the exact 0334 image

- Status: In Progress
- Priority: High
- Created: 2026-10-01
- Owner: Mini QEMU / guest Flutter+GDB / QMP capture / runtime-evidence roles
- Branch: `feature-flr-0399-live-qmp-capture` (local only; no push)
- Plan: [FLR-0399 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0399-live-qmp-capture.md)
- Working log: [FLR-0399 working log](../logs/2026-10-01-flr0399.md)
- Prior attempt: [FLR-0396 runtime manifest](../evidence/FLR-0396-0001.md)
- Reused candidate: patch 0334; rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`

## Objective

On the exact already-built 0334 candidate, make one bounded Mini QEMU run that
captures a complete QMP frame while the recorded Example Demo process is live,
and preserves the bounded GDB/inferior and kernel-fault evidence on Mini before
teardown. Classify the colored-Sequoia result without conflating it with the
separate HUD-composition question.

No source/material, camera, texture, light, widget-tree, recipe, or image-build
change is in scope. Do not rebuild or copy a VM image to Mac.

## Independent visual gates

1. **Gate A — colored production Sequoia:** recognizable colored Sequoia pixels
   in a full-frame, identity-bracketed live QMP capture under the existing
   native-above-parent visual-isolation presentation. The HUD ROI must be
   measured and reported. Native-above-parent can mask the Flutter parent; it
   does **not** mean Flutter 2D was disabled.
2. **Gate B — HUD + real Sequoia composition:** recognizable Sequoia and the
   actual Flutter HUD in the same live full-frame QMP image. This is a distinct
   task owned by FLR-0398 after Gate A is established; FLR-0399 must not claim
   Gate B based on the fixture+HUD control or a historical photo.

The supplied historical image proves only that HUD pixels and red
vehicle-like pixels once co-occurred in a frame with no attributable run/image
identity. Its white lines are likely Shape visualization, exact source
UNKNOWN. It is not a current-image pass for either gate.

## Facts, hypotheses, and unknowns

### Facts

- FLR-0396 applied Devtool patch 0334 and passed Mini `do_patch`, compile, and
  the full `agl-ivi-image-flutter` build. The exact rootfs hash is recorded
  above; kernel/qemuboot hashes are in the linked manifest.
- One run reached Sequoia `READY parameter=linear-float3`, 24 binding log
  records, and SUN setup; it then recorded 2 present begins, 1 return, and an
  `FEngine::loop` kernel Oops.
- The FLR-0396 readiness observer read the `app.log` path while GDB wrote
  combined inferior/debugger output to a different `gdb.log` path. The missing
  file produced repeated numeric-parse errors and the live capture window was
  missed.
- The only FLR-0396 QMP still/video were captured after Flutter exited. The
  black frame is not evidence that the live Sequoia ROI was black. The raw GDB
  output was not persisted before QEMU shutdown, so the userspace backtrace is
  UNKNOWN.
- FLR-0396 QEMU teardown passed; no Mini QEMU/Flutter/QMP residue remained at
  the last read-only check.
- FLR-0394 is a positive same-image LIT fixture+HUD control; it is not a
  production Sequoia result.
- Read-only Mini preflight on 2026-10-02 found no saved FLR-0396 runqemu
  command/evidence directory under the fixed evidence role. The immutable 0334
  image is still present: rootfs, kernel, and qemuboot were independently
  rehashed from the fixed qemux86-64 deploy role and all three match the
  ticket's hashes. The matching build template resolves to exactly one
  existing `oe-init-build-env`/`runqemu` pair. No image was copied or rebuilt.
- The Mini evidence role is `$BUILD_EVIDENCE/$run_id/qemu` (lowercase run id),
  not a repository-local `evidence/FLR-...` directory. The observer now
  requires `--evidence-root`; its exact path contract is unit-tested.

### Inferences

- The immediate process defect was an observer/source-of-truth mismatch. It
  explains why the capture was missed, not why Sequoia may or may not render.
- Reusing the exact 0334 image isolates runtime evidence collection from
  material source and build changes.
- A valid live frame can settle whether the forced known-visible material
  renders production Sequoia geometry; it cannot establish original GLB
  material/texture/light correctness.

### Hypotheses

1. Sequoia produces colored pixels before the present/Oops fault; FLR-0396
   missed them solely because capture was not tied to the log actually written.
2. The same present/Oops sequence occurs before visible Sequoia output; a
   live READY-time capture will show no colored vehicle pixels.
3. The guest faults or exits before any valid live QMP frame; Gate A remains
   UNKNOWN, but the preserved first-fault evidence narrows the next ticket.

### UNKNOWN

- Whether colored Sequoia pixels exist while Flutter is live on the 0334 image.
- Whether the full current frame masks HUD pixels in the native-above-parent
  presentation; no such FLR-0396 live frame exists.
- The exact userspace stack/registers at the kernel Oops and whether the
  unmatched present causes, or merely precedes, it.
- Whether a forced-color Sequoia render says anything about original
  production texture or lighting behavior beyond geometry/material override.

## Scope and guardrails

- Reuse the existing Mini runqemu/QMP/serial-exec workflow and exact FLR-0396
  artifacts. One QEMU run, one evidence directory, one run ID.
- Add only a narrow FLR-0399 one-run observer/controller and its deterministic
  tests, plus ticket evidence. Do not change the general-purpose QEMU harness
  unless the test demonstrates a contract defect that blocks this scoped path.
- Use one configured guest log path for GDB output and readiness/present
  observation. Missing/unreadable log must fail once with a clear reason before
  numeric parsing or polling.
- Capture at the first useful READY point and again at the first present
  return if the same process is still live; record the actual return value.
  Bracket each QMP capture with matching PID/UID/start identity. A post-exit
  screenshot is labelled `POST_EXIT` and can never pass Gate A.
- Copy a bounded GDB/inferior excerpt and focused kernel Oops/coredump query to
  Mini evidence before QMP teardown. Do not dump unbounded logs.
- Do not retry after a first fatal Oops, process exit, observer failure, or
  deadline. Preserve evidence, teardown the exact QEMU, and decide the next
  discriminator from the result.
- No Docker, new Podman machine/container, new cache/TMPDIR, cache cleanup,
  `cleanall`, `cleansstate`, broad process kill, image transfer, push, or
  unrelated FLR-0397 repair.

## Mini run procedure

The ticket-specific starter pins the existing build, 0334 image hashes,
6144-MiB headless runqemu profile, standard serial/SSH/telnet ports, and one
fresh evidence directory. It does not run BitBake or modify the image:

```sh
FLR0399_RUN_ID=flr0399-0001 bash work/commands/FLR-0399-qemu-start.sh preflight
FLR0399_RUN_ID=flr0399-0001 bash work/commands/FLR-0399-qemu-start.sh start
python3 scripts/flr0399_live_capture.py observe \
  --run-id flr0399-0001 --evidence-root "$BUILD_EVIDENCE" \
  --run-dir "$BUILD_EVIDENCE/flr0399-0001/qemu" \
  --qmp "$BUILD_EVIDENCE/flr0399-0001/qemu/qmp-0399.sock"
```

Run these in the existing Mini receiver. Do not retry or reuse the run ID if
the start/observer reports a failure; preserve the single evidence directory
and classify the stop point first.

## Success criteria

1. The canonical guard passes and FLR-0399 is the only In Progress ticket.
2. Focused tests prove missing log fails closed without numeric errors or
  polling storm; READY/present capture is allowed only with a live matching
  identity; post-exit capture is classified and cannot pass; teardown runs at
  most once; the configured GDB/observer log source is singular. Cleanup tests
  must prove exact QMP-endpoint matching, PIDFD-bound signalling with an
  identity recheck, and fail-closed behavior without PIDFD support. Serial and
  QMP timeouts must preserve bounded partial evidence, and initial teardown
  failures must remain recorded even if a later check passes. An empty matching
  coredump query is a valid EMPTY result; actual journal/query failures fail.
3. Before one Mini run, the exact kernel/rootfs/qemuboot hashes, free QEMU
   process/ports/socket state, and fresh unique evidence directory are checked.
4. One QEMU run on the exact 0334 image produces a complete 1280×800 QMP frame
   and bounded video while Flutter identity is bracketed, or a precisely
   recorded fail-closed outcome if the process faults before capture.
5. Bounded GDB/inferior output and focused kernel evidence are present in Mini
   evidence before teardown; postflight finds no QEMU/runqemu/flutter-auto,
   QMP socket, or forwarded-port residue.
6. The full frame is visually inspected; fixed Sequoia and HUD ROIs, hashes,
   present counters, and process/fault state are recorded. Gate A is PASS only
   when production Sequoia is visibly colored in an attributable live frame.
   Gate B remains a separate FLR-0398 task.

## Impact

- **Build-time:** none; reuse the exact Mini-built image and existing caches.
- **Packaging:** none; no layer, recipe, package, or dependency edit.
- **Runtime:** diagnostic-only capture timing around the existing Example Demo;
  no product behavior is changed.
- **Integration risk:** a second observer or capture command could perturb a
  short fault window. Keep one controller, fixed deadlines, minimal reads, and
  fail closed on stale identity or missing log.

## 2026-10-02 observer reliability follow-up

- The QEMU harness was changed only after a concrete serial-worker contract
  defect was reproduced: parent timeout could terminate the Bash wrapper while
  its Python serial reader remained alive. The worker now owns the harness PID,
  uses one deadline, flushes command output incrementally, and the controller
  terminates its owned process group on timeout.
- Failed-start cleanup accepts only the launched QEMU or official `runqemu`
  executable with the exact run QMP endpoint. It opens and revalidates a Linux
  PIDFD before signalling, then signals through that PIDFD. Mini preflight must
  prove the PIDFD API/kernel capability before QEMU is allowed to start.
- QMP timeout output, pre-cleanup and final postflight reports, and empty vs
  failed coredump queries are separately retained/classified.
- A second red/green loop exposed and fixed a deadline hole: late serial
  responses can no longer authorize the next command after the global deadline.
  Login/echo-off bytes are stored in a separate bounded setup transcript, and
  command output remains isolated for strict gate parsing. Failed kernel and
  Flutter-coredump queries retain only the final eight diagnostic lines, each
  clipped to 400 characters.
- Check: 35/35 FLR-0399 tests and four localhost serial regressions pass. The
  full runtime-harness suite is 7/8; the sole failure is the pre-existing,
  separately-ticketed FLR-0397 stale test invocation. Full verification ran
  186 tests with only that failure; all independent later gates passed except
  the Markdown checker, which reports 11 historical missing targets outside
  the new FLR-0399 files. Astra's read-only re-review found no actionable issue
  in the repaired paths. No QEMU or image action has occurred.
- This is observer/evidence/teardown hardening only. No QEMU, BitBake, image,
  Flutter, material, camera, texture, light, or app-layout change has occurred.

## 2026-10-02 read-only Mini ownership preflight

- No target QEMU/runqemu/Flutter/BitBake/Devtool/GDB-server process or listener
  on the three pinned runtime ports was present at the observation time. One
  container-hosted `gateway.ivi_bridge` Python process remained running; its
  ownership is UNKNOWN and it was left untouched.
- The pinned 6-GiB QEMU profile fit the observed available host memory. The
  fresh `$BUILD_EVIDENCE/flr0399-0001` directory does not exist.
- The canonical Mac shell has no documented fixed Mini role values loaded. A
  receiver candidate from an older plan is clean but detached at `969d93c331`
  and lacks patch 0334, so it is not accepted as FLR-0399's receiver. The exact
  active receiver/build/inbox ownership is UNKNOWN; no bundle transfer or
  checkout was attempted.
- **Decision:** keep FLR-0399 In Progress but do not start QEMU until the fixed
  roles and the receiver/image provenance are reconciled. This is a workflow
  identity gap, not a rendering verdict. No current-image live visual result
  exists yet.

## 2026-10-02 provenance follow-up

- Read-only Mini verification found the exact FLR-0396 rootfs/kernel/qemuboot
  hashes in `/mnt/yocto/flourite-qemux86-64`; the active build is
  `qemux86-64` and uses build-local `TMPDIR`.
- The active clean trial-layer receiver is at `58ff985594…`; its patch 0334
  hash matches both the canonical source patch and FLR-0396. The fixed inbox
  already contains a bundle at that same receiver tip; its SHA-256 is recorded
  in the working log. No transfer or overwrite was made.
- The active receiver lacks all three files needed for this ticket's new
  observer/start/cleanup path (`flr0399_live_capture.py`,
  `flr0399_process_cleanup.py`, and `FLR-0399-qemu-start.sh`). Thus its existing
  bundle is stale relative to local FLR-0399 HEAD `a9cbf442…`.
- **Status:** image and source provenance are now verified; observer availability
  on Mini, evidence-role configuration, and live Sequoia pixels remain UNKNOWN.
  No QEMU/build was run. The older scripts were not used because they would not
  verify the repaired same-log and identity-safe observer contract.
- **Approval / next gate:** the user explicitly authorized a local commit of
  these three Markdown records with no push. Commit only these records; then use
  the official helper (no manual bundle/transfer) to send the committed FLR-0399
  observer code, verify the exact Mini tip and fixed roles, and run a fresh
  conflict-free preflight before one QEMU observation.

## 2026-10-02 precommit verification

- `make verify` under the default sandbox stopped at five loopback-only test
  fixtures with `PermissionError` on `localhost` bind. Re-running with the
  approved loopback permission allowed those four serial regressions to pass;
  the full suite ran 186 tests and retained one unrelated FLR-0397 failure:
  `test_serial_exec_capture_passes_strict_gate_without_setup_preamble` invokes
  `flr0350_launch_gate.py --validate` without its now-required run ID.
- Independent later gates passed: MCP 52/52, file-size (2,045 files), QEMU
  runtime harness, runtime-log slice, Devtool finish, Devtool component rebase,
  Mini recipe-patch, and Mini bundle-handoff contracts.
- The global Markdown link check still reports 11 historical missing targets
  in FLR-0338/0339 evidence and FLR-0391/0395 plans; none is in the three
  approved files. The commit remains documentation-only; no source/image/QEMU
  changes are included.
