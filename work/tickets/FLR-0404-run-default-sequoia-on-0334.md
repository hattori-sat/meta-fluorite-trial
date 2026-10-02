# FLR-0404 — verify ordinary Sequoia materials/lighting with the HUD

- Status: Done
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Example Demo / QMP screenshot-video / runtime evidence roles
- Branch: `feature-flr-0404-default-sequoia-runtime` (from `dev-flr-0404-ordinary-profile`, advanced to checkpoint `65f8094`)
- Depends on: [FLR-0403](FLR-0403-correlate-fengine-oops-to-lwp.md), exact rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [FLR-0404 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0404-default-sequoia-runtime.md)
- Working log: [FLR-0404 working log](../logs/2026-10-02-flr0404.md)

## Objective

Classify one ordinary installed Example Demo run on the exact patch-0334 image,
with optional diagnostic selectors/material/light/camera controls absent.
Capture a full QMP frame while the exact app identity is alive, then stop at the
first visual or runtime-health failure. A negative run completes this bounded
test ticket, not the product objective: Sequoia + HUD acceptance remains open.

## Facts, inferences, hypotheses, and UNKNOWN

### Initial ownership-gate history (resolved)

- The first probe examined a dirty home checkout whose tracker marks FLR-0019
  In Progress. That checkout was not the active layer configured in the fixed
  build and was never modified or used to launch QEMU.
- A later read-only provenance check found the separate authoritative receiver
  at `54c02bdcddbf80be579c4fd7d493f5bd24f6df6c`, clean outside its evidence
  directory, with exactly one matching configured trial-layer entry and the
  prior FLR-0403 raw evidence present. The apparent ownership conflict was
  resolved without touching the dirty checkout.

### Facts

- FLR-0404 used rootfs SHA-256
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, kernel
  SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot SHA-256
  `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`.
  All three were rechecked after teardown and remained identical. No build,
  Devtool, recipe, patch, source, or bundle operation occurred.
- The QEMU harness passed preflight on the one clean receiver. It started one
  6144-MiB QEMU with ports 10930–10932; guest-ready passed. The ordinary
  Example Demo 3.32.5 bundle ran once as UID 1001 (`agl-driver`) with
  `HOME=/home/agl-driver`, `PATH=/usr/bin:/bin`,
  `XDG_RUNTIME_DIR=/run/user/1001`, and `WAYLAND_DISPLAY=wayland-0` only; no
  diagnostic model/material/light/camera/render/sync variables were set.
- The live app identity was PID 645, UID 1001, start token 23230. QMP still
  captures were immediately bracketed by the same identity. The initial and
  10-second full-screen 1280×800 captures and all eight frames in the 4-second
  sequence have the same PPM SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  The complete frame shows a white field and a large black polygon, with no
  CPU/GPU/FPS HUD or recognizable Sequoia. Identical frames do not prove that
  valid presents continued.
- The app log reached two `FLR0026_VK_QUEUE_PRESENT_BEGIN` events but only one
  successful `FLR0026_VK_QUEUE_PRESENT result=0`; the second begin had no
  matching return in the preserved log. At guest uptime 266.762166 s, the
  kernel recorded a user-mode page fault/Oops on CPU 2, PID/TID 691,
  `Comm=FEngine::loop`, RIP `0x7f08e5185541`, CR2/RSP
  `0x7f08827f8750`. TID 691 was absent from the later thread list while the
  parent `flutter-auto` process remained alive.
- The RIP maps in this process to `libLLVM.so.18.1`, file offset `0xb1d541`,
  Build-ID `359c1108040bc6bc1af64bb639d0b25385858051`; `addr2line` reports
  `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`. This is location
  correlation only, not proof that LLVM caused the present stall or bad pixels.
- A bounded GDB attach was attempted after preserving QMP. It listed newly
  attached LWPs but did not reach thread stacks before the 12-second timeout
  (rc=137). A subsequent exact-identity check showed the app resumed in state
  `S`, 38 threads, zero stopped threads, and no GDB/timeout process. `coredumpctl`
  reported no dumps. The post-Oops memory snapshot showed 4,650,236 KiB
  `MemAvailable`; no OOM/kill record was found in the bounded kernel query.
  Peak memory before the fault was not sampled.
- Exact cleanup sent SIGTERM only to PID 645 after verifying UID/start token,
  then negotiated QMP `quit`. Postflight found no QEMU/runqemu/flutter-auto/GDB
  process, no QMP socket, and no listeners on 10930–10932. The receiver
  remained clean outside evidence.
- Review artifacts: [full QMP PNG](../evidence/FLR-0404-0001/ordinary-live-initial.png),
  SHA-256 `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`;
  [4-second QMP MP4](../evidence/FLR-0404-0001/ordinary-live-8frames.mp4),
  SHA-256 `3032e371b682702568ae0477eb44b1e6b6762650e8563e37d4c0296895d4134e`.
  Both are local review files excluded by repository `.gitignore`; exact raw
  PPMs and logs remain under `$BUILD_EVIDENCE/flr0404-0001/qemu/` on Mini.
- FLR-0049 iterations 8/10/23 show production Sequoia pixels and red lamps,
  but not together with the Flutter HUD; those captures used special
  selection/environment conditions and are historical references.
- FLR-0394 shows a self-created LIT fixture and HUD together, not production
  Sequoia.
- FLR-0403 used the exact 0334 image with diagnostic LIT-material/SUN
  overrides. The QMP frame showed HUD/Scenes and a black Sequoia ROI; a kernel
  Oops was recorded, but capture identity was not bracketed and no GDB LWP or
  current ELF Build-ID was obtained.
- Static review of the pinned layer shows the model filter/limit and the added
  LIT material/SUN are opt-in. Omitting optional diagnostics restores the
  ordinary full load plan and original scene material/light behavior. Default
  loading can include more models and raise memory pressure; measure model
  count/memory rather than silently limiting selection. A historical OOM
  followed repeated model/Scene insertion but does not prove this exact image
  will OOM.
- An absent override does not alone prove runtime texture sampling or effective
  lighting. Positive material/texture/light claims require recognizable
  full-vehicle visual detail and any available effective asset/material/light
  evidence; a black fixed ROI can also mean the car is outside that rectangle.
- FLR-0141 records that the old Dart/native API lacks post-launch camera
  mutation methods. Whether this installed UI offers a supported camera/view
  interaction is UNKNOWN until checked on the live screen.

### Inferences

- This run establishes that the ordinary launch did not yield an acceptable
  screen and that rendering/presentation did not remain healthy. Because a
  present was unmatched and an FEngine thread faulted, the black polygon and
  missing HUD cannot yet be treated as an isolated material, lighting, camera,
  or Wayland-composition negative.
- TID 691's RIP location, missing post-fault TID, and the unmatched present
  occurred in the same run. Their causal order is not fully established; the
  symbol name alone is not a root cause.
- The available memory snapshot and absent OOM marker weaken an OOM explanation
  for this point in the run, but do not replace a peak-memory time series.

### Hypotheses

1. **An FEngine/LLVM-side fault prevents the second present from completing.**
   Support: one successful return, a second pending present, and an Oops in an
   FEngine thread mapped to LLVM in the same run. Refute: an instrumented run
   proves the present was already blocked before that thread faulted, or the
   pending present belongs to an independent thread/path.
2. **A synchronization/present stall begins first, with the Oops secondary or
   independent.** Support: the second present has no return and historical
   records include present/fence waits. Refute: a timestamped stack/state trace
   shows the fault precedes and removes the producer required by that present.
3. **Flutter/Wayland composition is independently invalid in this ordinary
   profile.** Support: the white field/black polygon and missing HUD recur
   while instrumented present continues healthily. Refute: the full HUD/scene
   returns when the render/present path recovers without a composition change.

### UNKNOWN

- Whether the black polygon is the Sequoia, another scene object, or a native
  surface/background artifact; no vehicle identification is possible here.
- Whether the original GLB material, embedded textures, scene lights, and
  effective camera were reached and sampled.
- Whether the FEngine Oops caused, followed, or was independent of the pending
  present; GDB did not capture the relevant stack and there is no core dump.
- Whether app scene-composition behavior changes when present progresses.
- Whether a supported viewpoint control, pointer/hover/click, 300-second
  present, or second independent boot can pass on the final candidate image.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | Original Sequoia, HUD composition, input/repaint, advancing present |
| Where | Exact Mini patch-0334 image, ordinary Example Demo 3.32.5, QMP framebuffer |
| When | One fresh QEMU boot; capture while app identity is live; stop at the first abnormal boundary; do not run five minutes without a healthy positive frame |
| Who | Mini runtime operator, guest `agl-driver`, QMP capture and runtime evidence roles |
| How | One allow-listed clean environment; no model/material/light/camera diagnostic overrides; same image and one QEMU |

## Scope and controls

- Runtime-only. Do not edit product source, Devtool state, recipe, patch stack,
  image, or build/cache; do not run BitBake or transfer a bundle.
- Confirm the canonical workspace and the immediate FLR-0403 evidence first.
  Recheck Mini receiver, exact image hashes, process ownership, free ports,
  fresh run ID, memory/storage, and video-capture support read-only before one
  QEMU start. Stop if any gate is UNKNOWN or another owner exists.
- Use one fresh run ID `flr0404-0001`, the existing fixed QEMU profile, and
  6144 MiB. Do not start parallel QEMU or build work; do not copy the VM image
  to Mac or make duplicate temporary directories.
- Default loading was not capped. The run did not emit a collected model/Scene
  count or effective camera record, so those remain UNKNOWN. The whole frame
  was reviewed rather than using the 0403 fixed ROI alone.
- Launch the normal Example Demo as `agl-driver` using only the session values
  needed for XDG/Wayland, executable PATH, and account home. Do not export
  optional model-selection, material, lighting, camera, render, or sync
  diagnostics. Preserve original scene camera/material/embedded textures and
  scene-authored lighting.
- Use the known full-screen QMP-only capture path. Save the selected still and
  a short MP4 on Mini; transfer only the small review PNG/MP4 after hashing.
  Keep raw PPM series/full logs on Mini. Capture immediately around recorded
  PID/UID/start identity snapshots; before/after identity must match.
- Do not change viewpoint by setting an environment override. Use only an
  existing visible and supported UI interaction. If no such camera control is
  available, record UNKNOWN and make it the next separate ticket rather than
  claiming the viewpoint/depth criterion passed.
- If the full-frame Sequoia+HUD baseline is healthy, test pointer motion,
  hover, UI click/open-close, and the available view control while input and
  normal repaint stay enabled. Then measure 300 s of present progress and
  bounded kernel/OOM state. If any Oops, OOM, process loss, HUD whitening,
  vehicle disappearance, or sustained present stop occurs, capture the first
  boundary and stop early; do not run a blind five-minute wait.
- A second independent boot is not part of this ticket; keep the overall goal
  open until its separate ticket passes on the same final image.

## Success criteria — bounded test completion, not product acceptance

1. Exact 0334 rootfs/kernel/qemuboot hashes, authoritative receiver identity,
   clean non-evidence receiver state, free ports, fresh run ID, and one evidence
   directory are proven before start.
2. The ordinary Example Demo starts once as `agl-driver` with recorded
   PID/UID/start identity and only the required session environment; optional
   diagnostic selectors/material/light/camera/sync overrides are absent.
3. At least one full QMP still is bracketed by the same live app identity; the
   complete frame and a short QMP frame sequence are preserved with hashes.
4. The first visual/runtime abnormal boundary is recorded; no five-minute wait
   or input trial is attempted after a negative/unhealthy baseline.
5. The exact app/QMP/QEMU teardown and postflight prove no owned residual
   process or listener, the receiver remains clean, and all image hashes remain
   unchanged.

These criteria classify the run only. The production Sequoia+HUD goal is NOT
MET by this ticket.

## Plan / Do / Check / Act

### Plan

- Use the same image as FLR-0403, but remove the diagnostic profile entirely.
- Start one runtime only after fresh Mini receiver/hash/process/port/storage/ID
  gates. Launch the app directly with a minimal allow-list environment.
- Capture the full QMP screen while bracketing exact app identity before any
  debugger work. Continue to input/repaint and 300-second present only after a
  live Sequoia+HUD baseline; otherwise stop at the first abnormal boundary.
- No source/build/image change.

### Do

- `scripts/assert-canonical-repository.sh` was first invoked directly and the
  shell returned permission denied; the documented `bash` invocation then
  passed before any workspace edit.
- Read-only Mini preflight resolved the authoritative receiver, exact image
  hashes, one BBLAYERS entry, clean source state, available resources, no
  process/port owner, and fresh `flr0404-0001`. One new evidence directory was
  created; the official harness preflight/start and guest-ready passed. The
  start SSH response omitted its final marker, so a read-only process/QMP
  inventory confirmed the already-started QEMU; no duplicate was launched.
- The first guest-ready invocation expanded local `$HOME` and failed before
  reaching the Mini command; the corrected remote-shell invocation passed.
  Guest preflight confirmed UID 1001, Wayland socket, bundle, and no stale app.
- Direct ordinary launch passed and recorded PID 645 / UID 1001 / start 23230.
  Identity-bracketed initial and delayed QMP captures showed the same full
  frame; the delayed still plus eight-frame sequence were byte-identical.
- The app/present/Oops snapshot recorded two present begins, one successful
  return, Oops TID 691, no coredump, and the live parent process. Post-Oops
  `MemAvailable` was 4,650,236 KiB; this was not a peak-memory sample.
- The first RIP-map guest command was rejected because a multiline command
  violated the serial-exec one-line contract. A single-line retry mapped the
  RIP to LLVM 18.1 / Build-ID `359c1108040bc6bc1af64bb639d0b25385858051` and
  `llvm::CmpInst::isOrdered`; this does not establish cause.
- GDB attach was bounded to 12 seconds after preserving the live QMP evidence.
  It timed out at rc=137 before stacks. A post-GDB check proved the same app
  had resumed, with zero stopped threads and no GDB process.
- The complete guest app+GDB transcript, QMP PPMs, command/output records, and
  their hashes were retained on Mini under
  `$BUILD_EVIDENCE/flr0404-0001/qemu/`. Only the small review PNG/MP4 were
  streamed to Mac; no rootfs, QEMU disk, cache, or deploy artifact was copied.
- Exact recorded app SIGTERM and QMP quit passed. Postflight verified all
  three image hashes, clean receiver, zero target process/listener/socket.

### Check

- **Bounded ordinary-profile result: NEGATIVE / UNHEALTHY.** Full-frame QMP is
  white plus one black polygon with no HUD or recognizable Sequoia, and every
  sampled frame is identical. The app identity was live around captures.
- **Present/runtime health: FAIL.** Two present begins, one successful return;
  FEngine thread TID 691 Oops. GDB stacks and causal order were not obtained.
- **Product acceptance: NOT MET.** Original Sequoia materials/textures/light,
  HUD composition, camera/depth, interaction stability, five-minute present,
  and independent second boot remain unverified.
- **Cleanup/provenance: PASS.** Exact three image hashes, clean receiver,
  stopped app/QEMU, absent socket, and free ports verified.

### Act

- Close FLR-0404 as a completed negative ordinary-profile test, not a feature
  pass. FLR-0405 is the sole In Progress follow-up: repeat the same image and
  ordinary environment with early, bounded GDB/LWP capture so the pending
  present and first FEngine fault can be ordered in one run-scoped log.
- Do not patch product code based solely on the LLVM symbol name. Use FLR-0405
  evidence to choose the smallest source/runtime boundary ticket. Keep original
  material/light, composition, viewpoint/depth, input stability, five-minute
  present, and second-boot acceptance separate.

## Impact

- **Build-time / packaging:** none.
- **Runtime:** one 6144-MiB QEMU run, one ordinary app, one bounded GDB attach;
  no parallel build or second QEMU.
- **Integration risk:** product input/repaint remains enabled; capture identity
  brackets and QMP-only owner-specific teardown prevent false visual verdicts
  or disturbing another runtime owner.
