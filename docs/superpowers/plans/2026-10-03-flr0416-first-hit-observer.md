# FLR-0416 — correlate the first libLLVM hit with present and QMP

> **For agentic workers:** execute this plan task-by-task and preserve the
> checkpoint gates below. The task is one bounded diagnostic run, not product
> acceptance.

**Goal:** Repair the deterministic GDB hit-observer failure and, on one fresh
run of the unchanged FLR-0410 candidate, correlate the first verified hardware
breakpoint with caller mapping, present state, process identity, guest clocks,
kernel state, and QMP pixels.

**Design:** Do not build GDB command text with nested `%` interpolation. Use a
small, host-testable helper for exact `/proc/<pid>/maps` address selection and
JSON marker formatting, plus a `gdb.Breakpoint` subclass that is explicitly
hardware-assisted and temporary. Its `stop()` first writes and flushes a
constant `HIT_BEGIN` marker, then independently records optional read-only
identity/register/frame/map fields, catches observer errors (including
`KeyboardInterrupt`) at that boundary, and always returns `True` to hold the
process. It does not run GDB commands or change frame/thread/inferior state.
Host-controlled gates observe the library-load stop and first hit; only an
explicit, evidence-validated release allows continuation. GDB deletes the
temporary target breakpoint when hit, preventing that breakpoint from
retriggering after release.

**Tech Stack:** guest GDB 14.2/Python, one Mini PC QEMU via the existing runtime
harness, UID-1001 Example Demo, QMP capture, bounded app/kernel snapshots, Mac
offline unit and command tests. The GDB Python breakpoint API is documented by
the [GNU GDB manual](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Breakpoints-In-Python.html).

**Spec:** [FLR-0416 ticket](../../../work/tickets/FLR-0416-correlate-libllvm-hit-with-present-and-qmp.md)

## Evidence baseline

- Reuse only the unchanged FLR-0410 image: rootfs
  `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`, kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot
  `3872b66339ac3601c704f1b54cab5630796ccf5f0f95ebc4e7077210e89d107f`.
- FLR-0415 reached `libLLVM.so.18.1` VMA `0xb1d541` at runtime address
  `0x7fffefb4d541`, in `FEngine::loop` / `llvm::CmpInst::isOrdered()+1`.
- FLR-0415's nested formatting failed after bounded registers/instructions/
  stack output. The inferior's exact exit path and QMP-to-present correlation
  remain UNKNOWN. Its QEMU was exactly stopped and its image hashes matched
  postflight.
- FLR-0415 and FLR-0416 are separate work units. Never relaunch run
  `flr0415-0001`.
- GDB constructor success alone does not prove that a hardware breakpoint was
  inserted by the target. Record the requested type/address and require a real
  stop at the exact target before treating insertion as runtime-verified.
- The `stop()` callback may read state and write its observer record only. Do
  not use `gdb.execute`, alter the selected frame/thread, change a breakpoint,
  or call into the inferior from the callback.

## Competing explanations

| Explanation | Prediction | Discriminator |
| --- | --- | --- |
| Nested observer formatting alone prevented the hit marker/hold | A typed breakpoint callback writes the first-hit marker and remains stopped | Offline helper test, guest GDB API smoke, same-run live identity while held |
| GDB/app exited independently of the marker writer | No valid hit marker or live inferior identity despite the verified address | Capture GDB/app identities, exact stop reason, guest process start token, and kernel delta before release |
| The hit is a normal helper call, not the failure boundary | Caller mapping resolves outside an actionable failing boundary, or presents progress after release without new fault | Caller PC/map/build identity plus present counts and QMP before/at/after; do not infer from function name alone |

The first explanation is confirmed only for the observer exception: the old GDB
script placed `%d`/`%s` formatting inside an outer `%` operation, then the
generated callback formatted the same values again. This does not explain any
product rendering or crash behavior.

## Global constraints

- Run `bash scripts/assert-canonical-repository.sh` before mutation; keep the
  current canonical checkout and branch. FLR-0416 is stacked on FLR-0415's
  evidence commit because it consumes that run's exact-image state; do not
  rewrite either branch.
- Keep FLR-0415 Waiting. FLR-0416 must be the sole `In Progress` ticket.
- No product source/layer patch, Devtool operation, BitBake task, `do_patch`,
  image build, cache change, baseline sync, or environment change in this
  diagnostic unit. After the helper/ticket files are locally committed and a
  read-only Mini owner/build/QEMU check passes, the standard bundle handoff
  helper may transfer only that committed diagnostic change set to the fixed
  receiver; do not manually copy files or mutate the product image.
- Do not interfere with another Mini owner, QEMU, BitBake, source checkout,
  build directory, or evidence directory. No second QEMU or concurrent build.
- The one fresh run uses ID `flr0416-0001`, the exact FLR-0410 hashes above,
  existing fixed build/TMPDIR, 6144 MiB, and the existing Mini QEMU harness.
  Reuse only ports proven free by the immediate preflight; use a fresh QMP
  socket inside the one evidence directory.
- Before receiver handoff, inspect the fixed receiver/build/QEMU owners
  read-only. Repeat the owner/port/artifact gate immediately before QEMU start;
  any active or ambiguous owner stops transfer/run rather than being displaced.
- Run the guest GDB/Python/hardware-breakpoint API smoke before launching the
  app. Any failed gate stops this same QEMU without ordinary-launch fallback.
- Attempt a controlled loaded-library stop before the target hit; if it cannot
  be safely held, record that pre-hit phase UNKNOWN. The required stages are the
  first target hit while the exact app identity is stopped and the bounded
  post-release interval. Bracket each QMP request with host wall/monotonic
  request bounds and guest PID/UID/start, GDB PID/start, guest wall/monotonic,
  app-log present begin/return/success counts, and bounded kernel state. Host
  and guest monotonic values have different origins; report intervals, not
  simultaneous timestamps. Keep raw artifacts on Mini.
- Stop only the exact recorded wrapper/GDB/app/QEMU identities. Preserve
  evidence and check image hashes before QMP quit and after teardown.
- Guest `LOAD_READY`, `HIT_READY`, release-accepted, abort-accepted, and
  observer JSON records are atomically published with no-replace semantics.
  Host collection has one monotonic 540-second deadline per ACK stage; guest
  waits use the same 540-second budget plus 60 seconds to accept an identity-
  bound abort. Host abort publication has an independent monotonic 50-second
  cap. Every blocking serial/QMP/video operation is capped by its active
  deadline. The GDB supervisor timeout must cover both stages and cleanup.
- Before and after each incremental kernel-journal query, verify the saved
  cursor with `journalctl --cursor=<saved> --lines=+1 --show-cursor` and
  require the returned cursor to match exactly. systemd may seek to the nearest
  remaining entry if the saved entry has rotated out. Only then can exact
  `-- No entries --` mean zero new records. Any missing, ambiguous, or
  different cursor output remains UNKNOWN/fail-closed. Separate invocations
  bracket rotation but are not an atomic journal lock.
- Start the load deadline before GDB/Example Demo launch and the hit deadline
  before publishing the load release. Carry those original deadlines into the
  stage handlers. If a release is published but ACK validation fails, record
  release acceptance and inferior-held state as UNKNOWN and perform exact
  QEMU teardown.
- Commit ticket-scoped source/tests/commands/plan/log/TASKS locally only; no
  push. Do not commit QMP media, deploy images, connection data, or personal
  identifiers.

## Task 1 — implement a testable observer and fail-closed guest commands

**Files:**

- Create `work/commands/flr0416_gdb_observer.py` and
  `work/commands/flr0416_qemu_preflight.py`.
- Create `work/commands/FLR-0416-prearm-libllvm.gdb`.
- Create the ticket-scoped guest install, smoke, launch, snapshot, release,
  export, and exact-stop commands under `work/commands/`.
- Create `tests/test_flr0416_gdb_observer.py` and
  `tests/test_flr0416_qemu_preflight.py`.
- Create `scripts/export_flr0416_media_preview.py` and
  `tests/test_flr0416_media_preview.py` for hash-checked Mac-only previews.
- Create `work/tickets/FLR-0416-correlate-libllvm-hit-with-present-and-qmp.md`
  and `work/logs/2026-10-03-flr0416.md`; update `TASKS.md`.

**Test seams (selected after GPT-6.1 Sol's judgment):** test the pure observer
helpers `mapping_for_address(maps_text, address)`,
`encode_hit_record(fields)`, `create_once(path, text)`, and
`validate_controller_release(root, stage, expected_process)`, plus process
visibility and port queries, through public results and real temporary files
or injected command results. Test the actual guest GDB command through its API
smoke and the one runtime gate; introduce no mock of GDB internals or product
engine.

- [x] **Step 1: Add focused unit tests first.** Cover executable map lookup
  (one exact mapping, no mapping, ambiguous overlap), deterministic JSON
  records, create-only durable files, controller ACK digest/identity/artifact
  checks including all bracket/still/eight-frame names, and controller abort
  identity. For host preflight, cover hidden/restricted proc mounts, unreadable
  and unresolved live PID entries, confirmed PID disappearance, zombie owners,
  and missing/failed/occupied/free port queries. The callback first attempts a
  constant create-only `HIT_BEGIN` before GDB reads, then independently records
  guest boot ID, PID/UID/start token/LWP/PC/caller resume PC/map line, and
  wall/monotonic clocks. No overwrite or silent fallback.
- [x] **Step 2: Implement the helper and typed temporary hardware breakpoint.**
  Preserve FLR-0415's exact Build-ID/PT_LOAD/load-bias check. Use the documented
  `gdb.BP_HARDWARE_BREAKPOINT` type and `temporary=True`; validate breakpoint
  type/address at load stop, but treat constructor success as intent only. In
  `stop()`, create+fsync a constant `HIT_BEGIN` record before querying GDB;
  collect bounded read-only frame/register/map data with each field independently
  fallible, use UNKNOWN on missing values, catch its own exceptions (including
  `KeyboardInterrupt`), and always return literal `True`. Do not call
  `gdb.execute`, change frames/threads, alter breakpoints, or alter inferior
  state from the callback. Capture the unwind return PC as a caller resume
  address, not as a proven call instruction.
- [x] **Step 3: Add controlled load and first-hit gates.** The load-catchpoint
  command list only arms the typed breakpoint and disables the catchpoint; it
  contains no wait or `continue`. Let top-level `run` return at that load stop,
  verify identity/all-thread stop and emit `LOAD_READY`, then wait for the
  controller ACK before one top-level `continue`. If that boundary cannot be
  safely controlled, record the pre-hit phase UNKNOWN and abort this exact
  run; do not continue without an armed first-hit breakpoint. At first hit,
  `HIT_BEGIN` is early notification, not proof of a completed write or stopped
  inferior. After the callback returns, top-level GDB verifies exact record/
  PC/identity and each app thread's `is_stopped()` state before creating
  `HIT_READY`. Capture even if caller unwind is UNKNOWN, but mark that blocker
  and accept only an identity-matched controller abort; never release on
  incomplete caller evidence. Missing record, timeout, or identity mismatch
  blocks release; timeout leads only to recorded exact abort/teardown.
- [x] **Step 4: Build small capture helpers.** Each snapshot emits one bounded
  structured record with run ID, guest boot ID, exact process identities/start tokens, GDB
  stop/running state, guest wall+monotonic clocks, cumulative **app-log** Vulkan
  present begin/return/success counts, and kernel-fault baseline/current. Keep
  app present counts distinct from compositor presentation (not established by
  this observer). Record host wall+monotonic bounds around each QMP request and
  guest clocks from bracketing snapshots; their monotonic origins differ, so
  report intervals/uncertainty rather than claiming simultaneous timestamps.
  Live PC/caller PC is available only at a controlled stop; leave it UNKNOWN
  while running. Capture QMP stills and one eight-frame sequence at the required
  stages; store output/raw PPMs only under the one Mini run directory. Preserve
  each frame's capture interval and SHA-256 in the record. Encode no video on
  Mini: set `video_status=PENDING_MAC_PREVIEW`, separate from capture/ACK status.
- [x] **Step 5: Run Mac offline tests and payload gates.** Python unit tests,
  `py_compile`, GDB command/Python block syntax checks, guest POSIX `sh -n`,
  one-line/4096-byte serial contract, base64 decode/hash round-trip, canonical,
  privacy, diff, Markdown links, checkpoint, screen-only archive allowlist/hash
  tests, and a real-Mac-FFmpeg synthetic PPM→PNG/fragmented-MP4 smoke. Record
  historical link-check failures without editing unrelated links.

## Task 2 — one controlled same-image QEMU experiment

**Files:** run ticket commands; output only under
`$BUILD_EVIDENCE/flr0416-0001/qemu/`.

- [ ] **Step 1: Immediate Mini preflight.** Confirm `/proc` has no active
  `hidepid`, inspect each visible numeric PID's comm/cmdline, count entries
  that verifiably disappear during scan, and reject unreadable or unresolved
  live records. Report target QEMU/runqemu/flutter-auto/GDB/BitBake PID/UID/state
  without dumping unrelated arguments. Query each requested TCP listener with
  `ss`; missing tool, warning, nonzero status, malformed/occupied result is not
  free. Check run-ID absence, evidence path, exact artifact hashes, fixed build
  configuration, and memory/disk headroom. Repeat process/port gates at the
  final start boundary. If any owner or ambiguity exists, stop without touching it.
- [ ] **Step 2: Start exactly one QEMU.** Use the committed runtime harness and
  QMP-first sequence. Record host PID/start identity and guest readiness. Run
  the GDB API smoke before the app; on failure, capture bounded QMP/serial
  evidence and stop this exact QEMU without another launch.
- [ ] **Step 3: Capture the library-load boundary.** Launch
  the ordinary
  Example Demo as the GDB inferior, verify exact image and DSO Build-ID/PT_LOAD,
  request the typed temporary hardware breakpoint at `load_bias+0xb1d541`, and
  hold at library-load stop if GDB exposes that controlled boundary. The
  catchpoint command list only arms and disables; the top-level script records
  `LOAD_READY` and waits for the identity/hash-validated controller decision.
  Save identity/present/kernel state and bracket a QMP full-screen still with
  host wall/monotonic request bounds and guest wall/monotonic samples. If it
  cannot be safely held, record the pre-hit phase UNKNOWN and abort this exact
  run; do not proceed without an armed breakpoint, use a substitute image, or
  start a second VM.
- [ ] **Step 4: Capture the first target hit.** Require the `HIT_BEGIN` and
  create-only structured record, exact same PID/UID/start token and live GDB
  identity, exact stop PC, caller resume PC and matching executable-map line.
  After the callback returns, verify the recorded target/stop boundary and that
  all **app** threads report stopped; QEMU and the compositor continue
  independently. Only then write `HIT_READY`. While held, take a QMP still
  plus exactly eight frames and bounded present/kernel snapshots. Hash/export
  the hit record, GDB transcript, snapshots, and QMP artifacts; verify the
  manifest's own hash, exact identities, and guest artifact hashes before an
  explicit controller ACK permits release. If optional caller evidence is
  UNKNOWN, capture what is safely available but accept an identity-matched
  controller abort only; if core evidence is missing/ambiguous, abort without
  claiming a valid at-hit frame.
- [ ] **Step 5: Explicitly release once and capture after.** Use only the
  arm-time number/type/address for the temporary breakpoint; it is auto-deleted
  at the stop and must not be inspected afterward. Verify the exact controller
  ACK/manifest hashes, then continue once. GDB's synchronous `continue` blocks
  until the next stop/exit; the external Mini controller captures QMP and live
  process/present/kernel snapshots during that interval. Independently verify
  that the inferior resumed (a release request is not proof of resumption).
  Take a post-release bracketed still and
  eight-frame sequence, then snapshot identity/presents/kernel over one
  predefined bounded interval. If process exit/Oops occurs, preserve its exact
  GDB/app/kernel boundary and do not relaunch. Do not attribute the running
  frame to a caller PC unless a later controlled stop captured it.
- [ ] **Step 6: Exact teardown and immutable-image check.** Stop only the saved
  wrapper/GDB/app identities, negotiate QMP quit through the existing harness,
  verify zero residual owners/socket/ports, and rehash the same rootfs/kernel/
  qemuboot. Keep all raw evidence on Mini.
- [ ] **Step 7: Make the local visual preview only after QEMU teardown.** Run
  `scripts/export_flr0416_media_preview.py` with the fixed host/evidence roles
  and one unused local preview directory. It transfers only allowlisted QMP
  stills, frame sequences, and capture metadata—not rootfs, kernel, or logs—
  verifies the source SHA-256 manifest, and creates PNG/MP4 using Mac FFmpeg.
  Sidecars retain measured capture intervals and label 4-fps playback as
  nominal/non-real-time. Preserve raw PPMs on Mini; a preview or encoding pass
  is not a product-render pass.

## Task 3 — classify and commit the diagnostic result

- [ ] Compare at least two observer/runtime explanations against the captured
  first boundary. Clearly separate Facts, Inferences, Hypotheses, and UNKNOWN.
- [ ] Classify the visual evidence only if its identity/present/time brackets
  pass. A black frame after inferior exit or a GDB hold is not a product black
  verdict. This ticket cannot satisfy Sequoia, composition, interaction,
  five-minute, or two-boot acceptance.
- [ ] Update ticket/log/TASKS with exact command results, QMP media references,
  hashes, cleanup, and the most informative next product experiment.
- [ ] Run canonical/privacy/checkpoint/diff checks; record only the known
  historical Markdown-link failures. Inspect the exact staged diff and make a
  local commit without push.

### Recorded one-shot execution result (2026-10-03)

- The transferred commit `d97dec4` passed the full read-only FLR-0416 start
  preflight on the unchanged FLR-0410 artifacts. `prepare` staged 12
  hash-verified files. One 6144-MiB QEMU started and guest SSH readiness passed.
- The capture controller stopped before `_guest_setup`, GDB smoke, Flutter, or
  QMP capture with `RuntimeError:canonical repository guard failed`. A remote
  cwd-only A/B proves the guard fails from SSH's default directory and passes
  from the receiver root. The receiver origin and required metadata files pass
  their checks; this is a caller working-directory contract, not a repository
  identity failure.
- QMP quit succeeded, the recorded runqemu PID and exact QMP socket are absent,
  and official postflight passed. The controller-final record omitted the
  already-verified host identity because the guard exception happened before
  `run()` copied it into the result; therefore `teardown_verified=false` must
  remain unchanged despite independent cleanup evidence.
- No screenshot/video, guest GDB smoke, Flutter process, present correlation,
  or product visual result exists. Run ID `flr0416-0001` is consumed under this
  one-shot ticket; do not relaunch it. The evidence inventory and bounded
  records are under `$BUILD_EVIDENCE/flr0416-0001/qemu/`.
- The next action requires the pending Sol judgment about a separate ticket
  and fresh run-ID contract. A follow-up should test cwd-independent guard
  execution and early-failure identity retention before any new QEMU start.
