# FLR-0388 — test the known LIT material directly on Sequoia

- Status: Waiting — Profile A ran but failed the healthy-present/live-capture gate; Profile B was correctly skipped
- Priority: High
- Owner: Mini QEMU / manual guest Flutter / Sequoia LIT material / conditional SUN / QMP evidence roles
- Created: 2026-10-01
- Predecessors: [FLR-0385 patch 0332](FLR-0385-apply-lit-material-to-sequoia.md), [FLR-0387 same-image fixture control](FLR-0387-replay-parameterized-lit-on-current-image.md), [FLR-0371 known LIT/SUN fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Candidate rootfs SHA-256: `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate qemuboot SHA-256: `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`
- Historical image-build receiver tip: `fe92b7760deaf9feb2e09b5370565be7798b4eca`; current receiver is not an input and will not be changed.
- Branch: `feature-flr-0388-direct-sequoia-lit-runtime` (local, no push; stacked on the FLR-0385/0387 evidence chain because patch 0332 and this exact image provenance are only in that unmerged feature lineage)
- Implementation plan: [FLR-0388 plan](../../docs/superpowers/plans/2026-10-01-flr0388-sequoia-lit-exact-image.md)
- Working log: [FLR-0388 working log](../logs/2026-10-01-flr0388.md)
- Evidence run: `work/evidence/FLR-0388-0001/` locally; raw guest logs/PPM remain on Mini.

## Objective

On the exact already-built image containing patch 0332, manually launch the
Example Demo with Sequoia selected and the known parameterized LIT/RGB override
enabled. Prove from one live, full-frame QMP capture whether colored Sequoia and
the CPU/GPU HUD render together. This is a runtime verification only: do not
edit source, recipes, patches, image inputs, or camera settings, and do not
rebuild.

If Profile A is healthy and shows the HUD but no Sequoia chroma, run one
conditional Profile B that changes only the existing
`FLR0305_PRODUCTION_SCENE_LIGHT=1` opt-in using FLR-0371's known SUN settings.
Profile B distinguishes default-scene illumination from an unchanged geometry,
camera, asset, material-binding, or presentation boundary; it does not by itself
prove which of those is causal.

## Facts

- Patch 0332 changes the existing Sequoia diagnostic override to a LIT material
  with the fixture-proven shader assignment, FLOAT3 linear-RGB parameter
  `(0.05, 0.45, 1.0)`, and binding across every primitive slot for matching
  Sequoia renderables. The override is `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`.
- Mini `do_patch`, `do_compile`, and image build passed for the candidate image.
- FLR-0385 Profile A logged material `READY=1` and 24 bind events and captured
  a live HUD/Scenes frame, but the center Sequoia ROI was black while an
  unmatched present and `FEngine::loop` Oops made the rendering comparison
  unhealthy. It did not establish that the material fails to draw.
- FLR-0387 selected the parameterized fixture and later logged SUN setup plus
  21 successful present returns. Its geometry verdict is UNKNOWN: the poll
  searched `FLR0026_NATIVE_MINIMAL_GEOMETRY_READY`, while the active patches
  emit `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY`. Its black QMP capture was not
  PID-bracketed.
- FLR-0371 is the positive LIT/SUN reference: SUN color `(1.0, 0.9, 0.8)`,
  intensity `110000`, direction `(0.7, -1.0, -0.8)`, angular radius `1.9`;
  the self-created fixture and CPU/GPU HUD were visible together.
- The exact Mini artifacts and helper hashes were checked in FLR-0387. This
  task must recheck them and current process/port state before runqemu; the
  current receiver tip is not a substitute for candidate artifact hashes.

## Ranked hypotheses and test-path comparison

1. **The Sequoia LIT override can draw, but default scene illumination is
   inadequate.** Healthy Profile A has bound-material records and a visible
   HUD but no Sequoia chroma; adding only the known SUN in Profile B yields
   colored Sequoia pixels.
2. **The remaining boundary is not just scene illumination.** Healthy A and B
   both bind the material and present repeatedly, but the car ROI remains
   achromatic/black. This leaves camera/framing, draw/scene attachment, or
   later native presentation/composition to isolate; it does not justify a
   texture-path fix because the same material replaces the GLB material for
   this test.
3. **A shared renderer/present fault prevents a valid material verdict.** A
   bad/unmatched present, Oops, app exit, or identity change occurs before a
   healthy capture gate. Preserve QMP and bounded fault evidence, stop, and
   classify the pixel result as non-positive/UNKNOWN rather than blaming the
   material.

Two plausible paths are (A) test normal production lighting, then add only the
known SUN if A is healthy but visually negative; or (B) start with the SUN to
maximize the chance of color. Choose A/B because the light contribution is the
specific variable in question and changing it first would collapse the useful
comparison.

## Run contract

- One Mini QEMU, one existing fixed run directory
  `$BUILD_EVIDENCE/flr0388-0001/qemu`, 6144 MiB, existing ports 10930–10932.
- Exact FLR-0385 artifact hashes above; no BitBake, Devtool, bundle transfer,
  cache cleanup, new TMPDIR, extra container, or image copy to Mac.
- Guest `agl-driver` UID 1001, exactly one Example Demo 3.32.5
  `flutter-auto`, explicit XDG/Wayland session. Profile A sets Sequoia match,
  model limit 2, and `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`; production SUN
  and all unrelated diagnostic overrides are unset.
- Persist the timeout/child exit status in the guest run directory. Treat each
  15-second readiness result as `READY`, `PENDING`, or `FAULT`; PENDING is not
  terminal, continue at most three chunks through the 45-second gate. Every
  serial-exec command must be syntax-checked and at most 4096 bytes before SCP.
- A healthy profile requires `READY=1`, `BOUND>0`, at least eight successful
  present-return and present-done markers, no Oops/application fault/nonzero
  present, no persistent unmatched present, and the same app PID/UID/start
  token immediately before and after capture.
- QMP-only full 1280×800 still and eight-frame video. Review the entire frame
  plus Sequoia ROIs `(440,220,400,360)` and `(0,100,320,310)` and HUD ROI
  `(1120,0,160,80)`. Raw PPM and guest logs stay on Mini; keep the reviewed PNG
  and MP4 beside this ticket and record SHA-256, dimensions, frame count, and
  ROI pixel counts.
- Run B only if A passes the healthy-present gate, HUD is visible, and both
  Sequoia ROIs lack chroma. B changes only
  `FLR0305_PRODUCTION_SCENE_LIGHT=1`; all other launch inputs remain identical.
- On a fault, capture the QMP screen and video before QMP quit if possible, but
  label it post-fault/non-positive unless PID/liveness checks pass. Do not run
  B after an unhealthy A. Stop only exact run-scoped processes; QMP quit and
  independent postflight must prove zero residual target processes/socket and
  free ports.

## Success criteria

1. Canonical guard, sole-active-ticket checkpoint, exact image/helper hashes,
   Mini idle/process/port checks, and strict runqemu preflight pass.
2. Profile A's command file passes local syntax/size validation; the runtime
   marker proves exactly one intended app with persisted child exit status.
3. Material `READY`/`BOUND`, healthy repeated presents, and the liveness-bracketed
   QMP full frame determine the direct Sequoia result. Acceptance requires
   recognizable colored Sequoia and the CPU/GPU HUD together in the same frame.
4. If A is healthy but visually negative with HUD visible, Profile B changes
   only the existing SUN opt-in and is evaluated under the same health and
   capture gates. A healthy positive B with negative A proves the added SUN
   changes visible output in this profile, not that lighting is the sole root
   cause.
5. If both healthy profiles remain visually negative, preserve evidence and
   state the narrowest observed boundary; do not change camera, texture, or
   composition in this ticket. Open the next ticket around the first missing
   runtime/render boundary.
6. Exact QMP shutdown, postflight, artifact hashes, evidence links, PDCA, and
   local commit are recorded. No push.

## Runtime result — Profile A (`flr0388-0001`)

- The Mini-hosted official runqemu harness started one QEMU at 6144 MiB on
  ports 10930–10932, using the exact candidate rootfs, kernel, and qemuboot
  hashes recorded above. Guest preflight passed: kernel
  `6.6.111-yocto-standard`, `agl-driver` UID 1001, Wayland compositor/socket,
  and Example Demo 3.32.5 were present. Only Profile A ran; Profile B was
  skipped because A did not pass the health gate.
- One manual Example Demo launch ran as UID 1001 with
  `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`. Selected markers were
  `READY=1`, `BOUND=24`, `BUILD_FAILED=0`, `present_enter=2`,
  `present_return_ok=1`, and `present_done=1`. The second present remained
  unmatched. The timeout child exit status was `124`.
- Kernel evidence records an Oops in TID 710 (`FEngine::loop`), supervisor
  read access in user mode, CR2 `0x27ffb750`, RIP `0x7fed8e532541`, at
  20:43:46 guest time. Material READY/BOUND markers appeared at 20:44:02,
  after that Oops; this ordering does not establish causality. No coredump was
  found. The run therefore failed the repeated-present/no-Oops health gate.
- The pre-capture app identity check passed, but the post-capture check failed
  because the app had exited. The full QMP PNG shows the CPU/GPU HUD and
  Scenes control over an otherwise black scene; Sequoia ROI
  `(440,220,400,360)` has `0/144000` changed/edge/chromatic pixels, while HUD
  ROI `(1120,0,160,80)` has 2845 chromatic pixels. This is retained as
  failure-only evidence, not a live-render verdict or proof that Sequoia failed
  to draw while the app was healthy.
- [Profile A full QMP frame](../evidence/FLR-0388-0001/profile-a-qmp-full.png)
  SHA-256 `f898e6265fa504f921ad0b9cd0b52ccf037f8366fe224301e3f725423ad0eeb6`;
  [eight-frame QMP video](../evidence/FLR-0388-0001/profile-a-qmp-8frames.mp4)
  SHA-256 `d8e93ec88fdfa688aee36b6a70b88c4fa6ddbb20bb6c25f6fc85b5240db9abaa`
  (1280×800, 8 frames, 4 seconds). Both are complete-frame QMP derivatives.
- QMP quit was accepted. Independent Mini postflight found no QEMU/runqemu/
  Flutter/BitBake target processes, QMP socket, or occupied ports; the exact
  candidate artifact hashes were unchanged. No source, patch, build, transfer,
  or cache state changed.

## Decision and UNKNOWN

- FLR-0388 is Waiting because the run was not healthy enough to interpret
  pixels. `READY=1`/`BOUND=24` prove material construction/assignment only;
  they do not prove Sequoia geometry reached a live framebuffer. The Oops
  preceded those markers, so the material is not established as its cause.
- Profile B was correctly skipped. This run does not determine whether SUN,
  texture sampling, camera/framing, Sequoia scene attachment, or composition
  changes the result. The black ROI was not captured under a stable
  before/after PID gate.
- Next discriminator: FLR-0389 first verifies the known self-created LIT/SUN
  fixture on this exact image with correct markers, persisted bounded logs,
  and live QMP. Do not modify Sequoia material/light/camera based on this
  unhealthy capture.
