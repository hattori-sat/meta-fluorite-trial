# FLR-0387 — replay the parameterized LIT fixture on the FLR-0385 image

- Status: Waiting — geometry gate verdict invalid because the poll searched an obsolete marker; corrected-selector replay is FLR-0389
- Priority: High
- Owner: Mini QEMU / manual guest Flutter / parameterized LIT fixture / QMP evidence roles
- Created: 2026-10-01
- Predecessors: [FLR-0385 Sequoia LIT material](FLR-0385-apply-lit-material-to-sequoia.md), [FLR-0386 invalid fixture attempt](FLR-0386-replay-lit-fixture-on-0385-image.md)
- Positive control: [FLR-0371 parameterized LIT/RGB fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Candidate rootfs SHA-256: `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate qemuboot SHA-256: `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`
- Mini receiver tip: `fe92b7760deaf9feb2e09b5370565be7798b4eca`
- Current Mini receiver preflight: clean detached `969d93c331befba7579f5f376bcf03c80c771aa0`; it no longer contains patch 0332, so the candidate remains identified only by the exact FLR-0385 artifact hashes and its recorded build provenance.
- Branch: `feature-flr-0387-parameterized-lit-current-image` (local; no push)
- Implementation plan: [FLR-0387 plan](../../docs/superpowers/plans/2026-10-01-flr0387-parameterized-lit-current-image.md)
- Working log: [FLR-0387 working log](../logs/2026-10-01-flr0387.md)

## Objective

Determine whether the exact FLR-0385 image can still render the **same
parameterized LIT/RGB material path** that FLR-0371 proved and patch 0332 now
assigns to Sequoia. This isolates a shared image/runtime failure from the
production Sequoia model/scene path. This fixture control is not itself proof
that the Sequoia vehicle is visible.

## Capability contract

| Dimension | Contract |
| --- | --- |
| What | A self-created dark-blue LIT fixture and 2D CPU/GPU HUD are visible in the same full QMP frame, with a healthy bounded draw/present loop. |
| When | One manual launch on the exact existing FLR-0385 image; readiness within 45 seconds and a 60-second app bound. |
| Where | One Mini-hosted headless QEMU, the installed Example Demo 3.32.5 bundle, guest UID 1001 `agl-driver`, and the existing Wayland compositor. |
| Who | Mini image/runtime and QMP evidence roles; no source or build mutation. |
| How | Pure native fixture + minimal geometry + local camera + fixture SUN, force-render control, parameterized FLOAT3 material, one targeted `FLUORITE_PRESENT_TRACE` switch, and QMP-only capture. Camera use is established by the explicit launch flag and source wiring; the per-frame `FLUORITE_VIEWTARGET_FRAME_TRACE` remains unset. |

## Facts

- FLR-0371 on a different rootfs showed `hardcoded=false shading=lit
  source=parameter`, SUN intensity 110000, an 8-vertex/36-index fixture, 146
  successful presents, `119716/144000` chromatic native pixels, and `2845`
  chromatic HUD pixels in a complete QMP frame.
- FLR-0385 patch 0332 uses that parameterized LIT/RGB material for matching
  `sequoia_ngp.glb` renderables. Its runtime reached 24 binding log records,
  but the live Sequoia ROI was black during an unmatched-present/FEngine Oops
  run; visible production Sequoia is not proven.
- FLR-0386 is invalid as a fixture comparison: four fixture-selection/render
  flags were omitted and hardcoded color was enabled. Its ordinary-startup
  Oops is not a material verdict.
- The final Mini preflight matched all three candidate hashes; the existing
  QEMU/capture helper hashes matched the repository; target/build processes
  were zero and ports 10930–10932 were free. The fixed receiver was clean but
  had moved past the historical FLR-0385 build tip. It was not changed.
- The official runqemu harness started one 6144-MiB QEMU; guest preflight
  passed for kernel `6.6.111-yocto-standard`, UID 1001, Wayland socket and
  compositor, Example Demo bundle, GDB 14.2, `journalctl`, and
  `coredumpctl`.
- The one fixture launch used all five required behavior flags and
  `FLUORITE_PRESENT_TRACE=1`, with hardcoded color and all Sequoia/model/light
  overrides unset. It launched `flutter-auto` as UID 1001. At the first
  15-second sample the output was
  `branch=1 pure=1 sun=0 geometry=0 present_enter=0 present_ok=0 present_done=0`.
- The first 15-second poll and final-count command reported
  `geometry_ready=0`, but both searched the obsolete
  `FLR0026_NATIVE_MINIMAL_GEOMETRY_READY` string. The active patches 0234 and
  0244 emit `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY`; therefore the geometry
  count and any conclusion that readiness was absent are invalid. The exact
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_*` state is UNKNOWN because the raw guest
  log under `/run/user/1001` was not retained after the user session ended.
  Other bounded counts remain `material_branch=1 pure_fixture=1 sun_setup=1
  present_enter=22 present_return_ok=21 present_done=21`. No application
  fault, kernel Oops, or failed return was found in the bounded scan.
  Launch-scoped `coredumpctl` returned status 1 with the explicit output
  `No coredumps found.` The app's exit status is UNKNOWN because this launch
  wrapper did not persist it.
- The complete QMP still is 1280×800 and uniformly black: 0/1,024,000 changed,
  edge, or chromatic pixels; native ROI `(440,220,400,360)` is 0/144,000 and
  HUD ROI `(1120,0,160,80)` is 0/12,800. All eight QMP frames have the same
  PPM SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The capture was not PID-bracketed, so it is post-gate/non-positive evidence,
  not proof of a live all-black renderer.
- GDB 14.2 was present, but the exact application PID had already exited when
  the liveness check ran; no GDB attach was attempted against another process.
- QMP `quit` was accepted. Harness postflight passed: zero QEMU/runqemu/Flutter
  and BitBake/worker/pseudo processes, no QMP socket, ports free, and all
  candidate artifact hashes unchanged.

## Ranked hypotheses

1. **The fixture geometry became ready and may have rendered, but the old
   selector failed to observe it.** The corrected marker query and a live QMP
   capture decide this; the old `geometry=0` is not evidence against it.
2. **The fixture reached geometry setup but a later present/runtime boundary
   prevented a healthy image.** The old run did record 21 successful present
   returns and no bounded Oops, but the unmatched enter and missing process
   exit status leave the exact termination boundary UNKNOWN.
3. **The fixture setup and present loop are healthy on the exact image, while
   production Sequoia remains specific to its scene/model path.** This requires
   a correct setup contract, repeated healthy presents, and a PID-bracketed
   full QMP frame; it has not yet been shown on this image.

## Scope

### In scope

- One run on the exact kernel/rootfs/qemuboot above, with the existing Mini
  receiver, build, TMPDIR, cache, and 6144 MiB QEMU profile; ports 10930–10932.
- Exactly one manual launch as `agl-driver` with all five functional flags:
  `FLUORITE_NATIVE_PURE_FIXTURE=1`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`,
  `FLUORITE_NATIVE_FIXTURE_LIGHT=1`, and
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`.
- Explicitly unset `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR`, all Sequoia or
  model-selection overrides, and `FLR0305_PRODUCTION_SCENE_LIGHT`.
- Set `FLUORITE_PRESENT_TRACE=1` only as a narrow observation switch for
  present enter/return/done markers; do not enable `FLR0026_SYNC_TRACE`,
  `WAYLAND_DEBUG`, or broad tracing. Explicitly unset
  `FLUORITE_VIEWTARGET_FRAME_TRACE`; it logs repeatedly per frame. The camera
  profile is checked from the launch environment and existing source wiring.
- Full 1280×800 QMP still and eight-frame video, captured only while the exact
  app PID/UID/start-time is alive immediately before and after capture.
- Bounded setup/draw/present/Oops/coredump evidence and exact-run teardown.

### Out of scope

- Devtool, source/recipe/patch edits, bundle transfer, BitBake, image rebuild,
  cache cleanup, changing Sequoia material/camera/light/texture, scene routing,
  launcher scripts, or retries under this ticket.
- Treating fixture visibility as production Sequoia acceptance.
- Copying raw QEMU images, raw PPMs, or full guest logs to the Mac or Git.

## Success criteria

1. Preflight proves exact artifact hashes, one QEMU only, zero stale app
   processes, free ports, and unchanged image inputs.
2. The launch command explicitly lists the five required flags and explicitly
   unsets hardcoded color, Sequoia/model overrides, and production-light
   override. The launch runs one `flutter-auto` as UID 1001.
3. Runtime evidence shows the parameterized LIT branch, pure-fixture setup,
   geometry, and SUN setup; the exact launch environment explicitly selects
   the local-camera profile. At least eight
   `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0` and
   `FLUORITE_VK_PRESENT_DONE` markers occur with no Oops or failed present;
   a present-enter/return mismatch persisting across two one-second samples
   fails closed. The 15-second serial probes fit the harness's 30-second
   command deadline and run at most three times within the 45-second gate.
4. A full QMP still and eight-frame video are liveness-bracketed. The full
   frame visibly contains both recognizable chromatic 3D fixture geometry and
   the HUD; record native ROI `(440,220,400,360)` and HUD ROI `(1120,0,160,80)`
   separately, with image hash and frame dimensions.
5. If an Oops, failed present, persistent unmatched present, or app exit occurs
   before readiness or during capture, preserve the first run-scoped fault
   evidence, stop the exact app/QEMU, and classify the fixture verdict UNKNOWN
   or as a shared pre-fixture runtime fault. Before QMP quit, still capture the
   full QMP framebuffer and eight-frame video as explicitly labeled failure
   evidence, even if Flutter has exited. Do not count that capture as a positive
   material result, retry the run, or infer a material failure.
6. Exact QMP shutdown, app/QEMU/socket/port postflight, and candidate-image
   hashes pass. No source/build state changes.

## Visual evidence

This is failure-only evidence after the 15-second readiness sample, not a
positive fixture result and not a liveness-bracketed runtime frame.

![FLR-0387 post-gate QMP full frame — entire framebuffer black](../evidence/FLR-0387-0001/qmp-parameterized-lit-post-gate.png)

[FLR-0387 eight-frame QMP video](../evidence/FLR-0387-0001/qmp-parameterized-lit-post-gate.mp4),
1280×800, eight identical frames. PNG SHA-256
`7d7a698be10be29b7801f97f056e404808fe50b3a6cacca14e846d10880906b2`; MP4
SHA-256 `65e4f55f5f0f17bd5a93d4ac1f422089453b5df97eada49da4bf77d6aa3767e4`.
Raw PPM and frames remain on Mini; only PNG/MP4 previews were streamed to the
local review directory.

## Unknown

- Whether the parameterized LIT fixture reaches visible pixels on the exact
  `ff0f801c…` FLR-0385 rootfs.
- Whether the current image's FEngine/present Oops recurs with the correctly
  selected fixture, and whether it is causal.
- Whether `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY` appeared; the old check used
  the wrong `FLR0026_*` prefix and the raw guest log was not retained.
- Whether the QMP still was captured while the app remained alive; the
  pre/post liveness gate was not executed successfully.
- The exact `flutter-auto`/timeout exit status; the asynchronous launcher
  retained PID identity but not its child exit result.
- Whether a healthy fixture run will allow the production Sequoia override to
  show the vehicle; FLR-0389 owns the corrected same-image fixture control.
