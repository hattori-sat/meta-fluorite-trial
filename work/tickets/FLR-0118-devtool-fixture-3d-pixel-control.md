# FLR-0118 — reproduce self-made 3D fixture after startup repair

- Status: Waiting
- Priority: High
- Owner: Mac persistent Devtool source + Mini authoritative runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0116](FLR-0116-flutter-auto-material-variant-crash.md), [FLR-0113](FLR-0113-isolate-explicit-light-contribution-boundary.md)
- Working log: `work/logs/2026-09-13-flr0118.md`

## Work unit

Reproduce the already-proven self-made 3D fixture on the current image after
the MaterialParameter startup repair. The source change must be made in the
persistent Mac Devtool-managed Dart source and converted into a recipe patch
by the official Yocto Devtool finish flow. The Mini PC receives one
complete-history bundle and builds the authoritative image with the existing
build/TMPDIR. This ticket owns the fixture control and its QMP evidence; it
does not claim that the full production shaded scene is fixed.

## Problem

The current repaired image reaches a visible Flutter 2D HUD and keeps
`flutter-auto` alive, but the production central 3D region remains black. An
environment-only attempt to enable neutral native fixture flags was invalid:
the process inherited the variables, but the current effective recipe did not
register the corresponding native diagnostic patches. The valid historical
control is the Dart-side self-made fixture wiring in the Example Demo, which
must be restored through Devtool.

## Success criteria

- [x] One ticket was the sole `In Progress` item and the current QEMU was fully
  stopped before source/build work starts.
- [x] Mac persistent Devtool source branch was created from the repaired source
  and the smallest Dart scene wiring change selects the existing self-made
  fixture (`models: <Model>[]`, minimal fixture scene/shapes/cameras).
- [x] Official Yocto Devtool `finish` generated the patch; the generated patch
  body is not hand-edited, and the unchanged patch is registered under
  `meta-fluorite-trial`.
- [x] Mac same-container recipe `do_patch` and targeted compile passed.
- [x] One complete-history bundle reached the fixed Mini linked-worktree
  receiver; the receiver reaches the exact layer commit and stays clean
  outside evidence.
- [x] Mini Example Demo archive/compile and full image gates passed while
  reusing the existing build directory, `downloads`, `sstate-cache`, and
  TMPDIR.
- [ ] One QEMU run launches exactly one fixture `flutter-auto`, and its log
  reaches native readiness without the initialization-race SIGSEGV.
- [ ] QMP-only screenshot shows nonzero geometry indicators in the
  HUD-excluded region `[300,250,620,400]`; retain full-frame and native-region
  hashes plus a visual artifact for the run.
- [x] QEMU was stopped through its recorded QMP socket and residual
  QEMU/runqemu/flutter-auto processes and QMP sockets are zero.

## Facts

- FLR-0042 and FLR-0076 provide historical positive controls for a self-made
  cube plus 2D HUD and for the native frame/present/SHM composition path.
- The current Example Demo recipe applies the production scene restoration
  patch after the earlier fixture patch, so its normal AOT bundle is the
  production route. Fixture selection is therefore a source-level test
  change, not an assumed runtime switch.
- The pre-FLR-0118 repaired layer tip was
  `93b91ea2e2e99ee90bab3ad89fccccb057953ea3`; FLR-0118's fixture patch is
  layer commit `f10ba7344925d3989980f9fef0446bb60b802be9`, and the Mini
  receiver/build roles were aligned to that commit.
- The FLR-0118 Mini gates passed at `f10ba73`: Example Demo `do_patch`
  `104/104`, targeted `do_compile` `2590/2590`, and full image
  `11898/11898`. The selected rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260912174911.ext4` with SHA-256
  `df51fac5fe9a8b68730e0e55944a5ac6751430b8c99648650bade2eec8438e75`.
- The first manual launch attempt was an invalid runtime condition: it
  omitted `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`,
  and the log reported Wayland permission denied. The corrected command
  inherited the compositor's socket environment and reached Vulkan surface
  creation, AOT load, and native readiness.
- The corrected fixture launch used exactly one recorded PID (`660`) but
  terminated with `SIGSEGV` five seconds later. `coredumpctl` reports the
  `/usr/bin/flutter-auto` core as present; no QMP frame was produced beyond
  the all-black framebuffer.
- The QMP-only frame
  `fixture-qmp-late.ppm` is 1280x800 with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  Both the HUD candidate and the HUD-excluded region `[300,250,620,400]`
  are uniform black; the latter is `0/248000` changed pixels, edge `0`,
  chromatic `0`, and luma `[0,0]`.
- Symbol-file GDB resolves the SIGSEGV to
  `plugin_filament_view::ECSystem::vSetupMessageChannels(this=0x0)` at
  `ecsystem.cc:146`, reached while processing Flutter's
  `flutter/platform_views` create message. The GDB output SHA-256 is
  `444de4924c203f6ef5f359c37b8725480e501afcc45625a7b2bafdeac1d46ba2`.
- The current repaired production QMP frame has 2D HUD pixels but zero pixels
  in the HUD-excluded central 3D candidate. This is the baseline to compare
  with the fixture result; it is not a 3D success or a compositor root-cause
  verdict.

## Inferences

- A valid fixture result must be selected by the Dart source actually bundled
  into the image, or by a native patch proven present in the effective recipe.
  An environment variable alone is insufficient evidence.
- If the fixture produces nonzero native pixels on the repaired image, the
  remaining black result is production-scene-specific and can return to
  FLR-0113's explicit-light/present analysis.
- If the fixture is also black, the next boundary is common runtime
  frame/present/surface behavior and must be split into a new ticket only
  after the fixture log and QMP evidence identify it.
- FLR-0118's fixture was not a valid common-renderer negative because it
  crashed before present. The identified null-system boundary is therefore
  split to FLR-0119 before any production-light conclusion is made.

## Hypotheses / UNKNOWN

1. **The existing Dart fixture still proves common native 3D output.**
   Falsifier: fixture source marker and render/present markers are present but
   the native QMP region remains zero.
2. **The recent COLOR fix changes fixture startup behavior.** Falsifier: the
   fixture reaches its native setup but fails again in another material field.
3. **Production-only resource/light work remains the cause of the black
   scene.** Falsifier: the valid fixture is also black under the same image and
   QEMU profile.
4. **UNKNOWN:** whether a fixture QMP-positive frame is visible at the same
   1280x800 extent with the current repaired production bundle and current
   patch stack. This must be measured, not inferred from historical images.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Dart scene payload selects empty models plus known fixture scene/shapes/cameras | source diff, AOT/runtime selection marker |
| Where | Example Demo scene construction before native deserialization | Devtool source and guest log |
| When | after repaired startup, before production-light diagnosis | one-QEMU run chronology |
| Who | Mac source/Devtool role creates patch; Mini role builds image; QEMU role validates pixels | bundle/build/QMP records |
| How | official Devtool finish → layer patch → bundle → Mini BitBake → QMP capture | patch SHA, build logs, QMP SHA |

## PDCA

### Plan

1. Confirm the sole active ticket and no running QEMU/process remains.
2. Inspect the persistent Devtool source and historical fixture patch, then
   create a feature branch for FLR-0118.
3. Edit only the persistent Dart source, commit it in the Devtool source
   repository, and run official `devtool finish`.
4. Register the unchanged generated patch in the canonical layer, run the Mac
   gate, commit locally, and transfer one bundle to Mini.
5. Run progressive Mini build gates, one QEMU fixture launch, QMP-only
   capture/analysis, and explicit teardown.

### Do

- Ticket created after rejecting the environment-only fixture attempt as an
  invalid control.
- Created the persistent Devtool source branch, edited only the Dart scene
  wiring, generated patch `0046-test-restore-self-made-3D-fixture-wiring.patch`
  through official `devtool finish`, registered its unchanged layer copy as
  `0053-test-restore-self-made-3d-fixture-wiring-devtool.patch`, and committed
  the layer as `f10ba73`.
- Transferred the complete-history bundle to the fixed Mini receiver. The
  receiver reached the exact commit and the progressive build gates passed.
- Ran one QEMU fixture attempt with a preserved invalid Wayland invocation,
  then a corrected environment invocation, QMP capture, coredumpctl, and
  symbol-file GDB.

### Check

- Ticket setup: **PASS**.
- Current production 2D baseline: **PASS** in FLR-0116.
- Valid fixture source patch and Mini build: **PASS**.
- Corrected fixture runtime launch: **FAIL at ECSystem initialization race**;
  QMP geometry result is **NOT A VALID RENDER VERDICT** because the process
  crashed before present.

### Act

- Keep FLR-0116's COLOR patch and the current native production analysis
  unchanged. Split the identified pre-present initialization race to
  [FLR-0119](FLR-0119-fix-ecs-platform-channel-init-race.md).

## Evidence locations

- Current production baseline: `$EVIDENCE_ROOT/flr0113-authoritative/r116-93b91ea`
- Canonical fixture recipe: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo_git.bb`
- Historical fixture patch: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/0050-test-restore-known-good-native-fixture-scene-devtool.patch`
- FLR-0118 runtime evidence: `$EVIDENCE_ROOT/flr0113-authoritative/flr0118-f10ba73/qemu`

## Iteration 1 — current-image fixture launch (2026-09-13)

### Plan

- Use the newly built `f10ba73` image and exactly one QEMU.
- Launch the source-selected self-made fixture with the compositor's actual
  Wayland user environment, then capture QMP and resolve any pre-present
  failure with the installed debug tools.
- Stop through the recorded QMP socket and leave the next independent cause
  for a new ticket.

### Do

- QEMU preflight, start, and guest-ready passed using the timestamp-matched
  kernel/rootfs and ports 42111/42112/42113. No prior QEMU, runqemu, or
  flutter-auto process was present.
- The first launch command failed with `Failed to connect to Wayland display.
  Permission denied`; the command file and output are retained as a failed
  invocation. Runtime inspection found the compositor socket at
  `/run/user/1001/wayland-0`, owned by `agl-driver`.
- The corrected launch set `XDG_RUNTIME_DIR=/run/user/1001` and
  `WAYLAND_DISPLAY=wayland-0`. It loaded `libvulkan_lvp.so`, loaded the
  fixture AOT bundle, and printed native-readiness output before PID 660
  received SIGSEGV.
- Initial GDB invocation using `file` did not resolve the main executable;
  the failed method is retained. The corrected historical
  `symbol-file /usr/bin/.debug/flutter-auto` invocation resolved the null
  `ECSystem` receiver and `ecsystem.cc:146`.

### Check

- QMP-only capture succeeded technically but was all black, including the
  corrected HUD-excluded candidate. It is classified as pre-present failure,
  not as a black 3D fixture.
- `coredumpctl` reported PID 660, UID role `agl-driver`, signal SIGSEGV, and
  a present core file. GDB's resolved receiver was `this=0x0` in
  `ECSystem::vSetupMessageChannels` while handling platform-view creation.
- QMP quit negotiation and residual cleanup passed with zero targets and zero
  QMP sockets.

### Act

- Move the async ECS initialization / immediate system lookup boundary to
  FLR-0119. Do not resume FLR-0113's production-light A/B until a valid
  fixture reaches a presented QMP frame.
