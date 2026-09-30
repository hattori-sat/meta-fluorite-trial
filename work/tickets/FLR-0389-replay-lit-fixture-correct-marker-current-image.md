# FLR-0389 — replay the LIT fixture with correct readiness markers on the exact image

- Status: Waiting — geometry contract proved, but final present stalled and the app timed out before live QMP capture
- Priority: High
- Created: 2026-10-01
- Predecessors: [FLR-0387 selector audit](FLR-0387-replay-parameterized-lit-on-current-image.md), [FLR-0388 Sequoia LIT runtime](FLR-0388-test-sequoia-lit-on-exact-image.md), [FLR-0371 positive fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Candidate rootfs SHA-256: `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate qemuboot SHA-256: `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`
- Branch: `feature-flr-0389-correct-fixture-ready-marker` (local; no push)
- Plan: [FLR-0389 plan](../../docs/superpowers/plans/2026-10-01-flr0389-correct-fixture-marker.md)
- Working log: [FLR-0389 working log](../logs/2026-10-01-flr0389.md)
- Evidence run: `work/evidence/FLR-0389-0001/`; raw guest evidence stays under the fixed Mini evidence root.

## Objective

Re-run one manual, known-positive self-created LIT/SUN fixture on the exact
FLR-0385 image, using the marker names actually emitted by the active layer
patches. Determine whether the fixture geometry reaches a healthy live frame
with the CPU/GPU HUD. This separates a shared same-image Flutter/Filament
render path from the production Sequoia-specific path before changing lighting,
texture, camera, or composition.

This corrects an evidence-selector defect from FLR-0387. It does not alter
FLR-0387's executed command files or reinterpret its post-gate black frame as a
live result.

## Facts

- FLR-0371 proved a self-created parameterized LIT/SUN fixture and CPU/GPU HUD
  together in one full QMP frame on an earlier rootfs, with 146 successful
  presents. That does not prove Sequoia output.
- FLR-0387 ran the intended five fixture controls and later counted 21
  successful present returns, but its readiness and final-count selectors
  searched `FLR0026_NATIVE_MINIMAL_GEOMETRY_READY`. Active patches 0234/0244
  emit `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY`; the old geometry count is
  invalid. The raw guest log was not retained, the app exit code is UNKNOWN,
  and its black QMP capture was not PID-bracketed.
- FLR-0388 tested the known LIT material on Sequoia in this exact image, but
  Profile A had one successful present, an unmatched second present, an
  `FEngine::loop` Oops, and the app exited during capture. Its black Sequoia
  ROI is not a healthy live-render verdict; Profile B was skipped.
- Patches 0234/0244 provide these exact setup markers:
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_ENABLED`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_CONTRACT`, and
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY`. The contract must report a
  renderable, at least one primitive, a bound material, and the expected
  8-vertex/36-index fixture. Geometry failure markers are
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_SCENE_FAILED`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_BUFFER_FAILED`, and
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_MATERIAL_FAILED`.
- The guest's `grep` implementation does not support GNU
  `--line-buffered`; the bounded app-log filter therefore uses a shell
  `while read` consumer that writes only selected marker/fault lines as they
  arrive. This avoids buffering the markers needed by the 15-second readiness
  polls without retaining the high-volume full Flutter log.
- FLR-0375 found 23 valid embedded PNGs and zero external URIs in the installed
  Sequoia GLB. That validates packaged image references, not runtime sampling
  by a particular material.
- The user-provided colored Sequoia image shows colored, detailed pixels on
  part of the vehicle, but has no attributable run/image hash or HUD in the
  same frame. It is not proof of current-image Sequoia+HUD acceptance.

## 4W1H

| Dimension | Scope |
| --- | --- |
| What | Known self-created parameterized LIT/SUN geometry plus CPU/GPU HUD; correct setup and present markers |
| Where | Exact rootfs/kernel/qemuboot above; one Mini-hosted QEMU; installed Example Demo 3.32.5; guest `agl-driver` UID 1001 |
| When | One bounded run; readiness may remain pending across at most three 15-second samples (45 seconds total); app limit 60 seconds |
| Who | Mini image/runtime, guest Flutter, and QMP evidence roles; no source/build change |
| How | Existing runqemu harness and ports 10930–10932; manual one-process launch; exact `FLUORITE_*` marker selectors; live PID/UID/start-token bracket around QMP still/video |

## Competing hypotheses

1. **Same-image fixture setup and rendering are healthy.** The exact READY and
   contract markers, at least eight successful presents, a stable app identity,
   and blue fixture pixels plus HUD would establish the shared path on this
   image. The remaining gap would be Sequoia/production-scene-specific.
2. **Fixture setup is reached, but the current image has a shared draw/present
   or process-liveness fault.** Missing contract fields, Oops, failed/unmatched
   present, app exit, or no native pixels under a valid live gate would keep
   the boundary before any Sequoia material conclusion.
3. **The scene/presentation is healthy but the fixture is not visible in the
   expected region.** This would be a valid visual negative only after setup,
   repeated successful presents, stable identity before/after capture, and
   positive HUD measurement. It would prompt a narrow camera/target/viewport
   comparison, not an assumed texture or light fix.

The alternatives are one same-image fixture control before further Sequoia
analysis versus continuing to change production model/light/material inputs
without knowing whether the shared fixture path is healthy. The fixture control
is the narrower discriminator and changes no product input.

## Run contract

- First verify canonical repository, sole-active-ticket checkpoint, exact
  candidate hashes, helper hashes, target process count zero, and ports
  10930–10932 free. Use the saved successful `external/poky/scripts/runqemu`
  path, fixed build directory, and fixed Mini evidence root. No new TMPDIR,
  QEMU image copy, container, or cache cleanup.
- Start exactly one 6144-MiB QEMU. Manually launch exactly one
  `/usr/bin/flutter-auto` as UID 1001 against the installed Example Demo 3.32.5
  bundle, with explicit `XDG_RUNTIME_DIR=/run/user/1001` and
  `WAYLAND_DISPLAY=wayland-0`.
- Set exactly the known fixture behavior flags:
  `FLUORITE_NATIVE_PURE_FIXTURE=1`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`,
  `FLUORITE_NATIVE_FIXTURE_LIGHT=1`,
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`, and the narrow
  `FLUORITE_PRESENT_TRACE=1`. Explicitly unset hardcoded material color,
  Sequoia material/model-selection overrides, production-scene light, and
  per-frame ViewTarget trace.
- Preserve the child exit result and a bounded selected log under the fixed
  Mini run evidence path before ending the guest session. Do not rely on
  volatile `/run/user/1001` files surviving logout. Use a per-line shell
  filter (the guest grep lacks `--line-buffered`) so readiness markers are
  visible immediately without retaining the high-volume full Flutter log.
  Keep raw PPM on Mini; only the reviewed full-frame PNG and short MP4 are
  copied for local inspection.
- Search the exact strings emitted by the layer patches. Require material
  branch `hardcoded=false shading=lit source=parameter`, pure-fixture setup,
  geometry ENABLED, CONTRACT with `has_renderable=true`, `primitives>0`,
  `bound_material=true`, vertex/index counts 8/36, geometry READY, and SUN
  setup. Stop immediately on a geometry failure marker, app exit, failed
  present, Oops, or persistent present-enter/return mismatch.
- A `PENDING` 15-second sample is a successful observation (exit status 0),
  not a terminal error. Continue up to three samples through 45 seconds.
  Capture once only; do not retry this run if it is unhealthy.
- A positive runtime gate requires at least eight
  `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0` and eight
  `FLUORITE_VK_PRESENT_DONE` markers, no Oops/failed return/unmatched present,
  and the same app PID/UID/start token immediately before and after a full
  QMP still plus eight-frame video. Capture the full 1280×800 frame even on an
  early classified failure, but mark it failure-only unless both liveness
  checks pass.
- Score the fixture ROI `(440,220,400,360)` and HUD ROI `(1120,0,160,80)`;
  record image hash, dimensions, pixel metrics, selected marker output, child
  exit, and teardown. Quit only this QEMU and verify zero target processes,
  socket absence, free ports, and unchanged candidate hashes.
- No Devtool, source/recipe/patch edit, bundle transfer, BitBake, image build,
  camera/light/texture/composition change, or broad/raw log dump is in scope.

## Success criteria

1. Exact candidate identity, official harness preflight, Mini idle/process/port
   checks, and preflight helpers pass.
2. The manual guest app runs once with the exact allowlist/unset contract and
   its child exit status plus bounded marker evidence are retained.
3. The exact geometry contract and repeated healthy presents are established,
   or the first missing/fault boundary is captured without mislabeling UNKNOWN.
4. A full QMP frame and eight-frame video are captured with PID/UID/start token
   checks immediately before and after. Positive acceptance requires visible
   self-made chromatic geometry and the CPU/GPU HUD together.
5. QMP teardown, independent postflight, artifact hashes, PDCA, and local
   evidence are recorded. No product source/build state changes.

## Runtime result

Run `flr0389-0001` completed on the exact hash-pinned FLR-0385 image. No
Devtool, source/recipe/patch, bundle, build, image, or cache changes occurred.

- Official runqemu preflight passed; one 6144-MiB QEMU started. Guest preflight
  passed for kernel `6.6.111-yocto-standard`, `agl-driver` UID 1001, Wayland
  socket/compositor, Example Demo 3.32.5, and GDB/journal/coredump tools.
- The manually launched app was PID 697 / UID 1001 (wrapper 687). Exact
  selected markers prove the LIT parameter branch, pure fixture, minimal
  geometry ENABLED, SUN setup, and a valid geometry contract:
  `has_renderable=true`, `primitives=1`, `bound_material=true`,
  `material_instance=true`, `vertex_count=8`, `index_count=36`, `scene=true`.
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY` appeared. Geometry setup failures
  were zero.
- The material/pure-fixture branch appeared at 21:54:22. The geometry/light
  contract appeared at 21:55:04, about 42.4 seconds later. Runtime totals were
  `present_enter=8`, `present_return_ok=7`, `present_done=7`: the eighth
  present entered but did not return. The bounded `timeout 60` child exited
  `124`. No kernel Oops/fault was found in the launch-scoped warning scan and
  `coredumpctl` reported `No coredumps found.` The immediate observed boundary
  is therefore a non-returning final present followed by the test timeout;
  the precise blocked thread/call remains UNKNOWN.
- The live-capture gate ran after the app exited and correctly reported
  `FAIL`, PID absent, while preserving the 8/7/7 counts. The QMP full still and
  eight frames were therefore captured as **post-timeout failure evidence**,
  not a live-render verdict. The complete 1280×800 image is uniformly black:
  `0/1,024,000` changed/edge/chromatic pixels; native ROI
  `(440,220,400,360)` is `0/144,000`; HUD ROI `(1120,0,160,80)` is
  `0/12,800`. All eight raw QMP frame hashes match
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- [Full QMP still — post-timeout, failure-only](../evidence/FLR-0389-0001/fixture-post-timeout-full.png)
  SHA-256 `05713dbacb00cfa92e8cad1581147b0f1349f6ee14c97d122440aff36011bd53`.
  [Eight-frame QMP video](../evidence/FLR-0389-0001/fixture-post-timeout.mp4)
  SHA-256 `e1cd12d484871c53ac253c5ceb850c3f7448fe459317031354eae8b4fb56103f`
  (1280×800, 8 frames, 4 seconds).
- The exact app was already gone; the stop check found no `flutter-auto` or
  `timeout` residual and child exit `124`. QMP quit was accepted. Independent
  harness postflight passed: no QEMU/runqemu/Flutter/BitBake/pseudo targets,
  QMP socket absent, ports free, and rootfs/kernel/qemuboot hashes unchanged.
  Raw PPM/frames and Mini runtime evidence remain on Mini; only PNG/MP4 review
  derivatives and bounded command outputs were copied locally.

## Decision

The corrected selector proves geometry creation and the Renderable/material
contract; it does not prove visible 3D. The present loop reached seven
successful returns and then one unmatched enter before the 60-second timeout.
Because the QMP capture occurred after the app disappeared, its black pixels
cannot be used to conclude that the live scene was black. This is not a
light/texture/camera/composition verdict. Static inspection confirms the
Sequoia LIT override already uses the same `baseColor.rgb` expression and
linear blue value as the positive fixture; patch 0332 changes the existing
override to LIT. The remaining untested positive condition is the fixture's
known SUN on the production scene. FLR-0390 restores the fixed Podman project
bind; a new runtime ticket will use the existing LIT material and SUN profile
with QMP capture at the first successful present. No source/build state
changed in FLR-0389.

## UNKNOWN

- Whether any live frame contained visible fixture pixels; the only captured
  QMP frame was after timeout and all black.
- Which thread/call blocked on the eighth present and whether a kernel/driver
  wait is involved; no live GDB attach or coredump was available in this run.
- Whether a healthy same-image fixture makes the Sequoia path the remaining
  boundary. This ticket does not test Sequoia material/texture, camera,
  lighting, routing, or production composition.
