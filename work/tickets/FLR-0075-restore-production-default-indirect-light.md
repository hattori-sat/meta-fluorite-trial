# FLR-0075 — restore production default indirect light

- Status: Done (restoration applied; QMP display criterion not recovered)
- Priority: High
- Owner: Mac Devtool source + Yocto build + runtime diagnosis roles
- Created: 2026-09-11
- Depends on: [FLR-0074](FLR-0074-isolate-explicit-light-render-target.md), [FLR-0067](FLR-0067-reintroduce-production-scene-stages.md)
- Working log: `work/logs/2026-09-11-flr0075.md`

## Work unit

Restore the production Example Demo scene's DEFAULT indirect-light source
state associated with the historical p6 pixel-positive control. Treat the
historical pixel count as a control signal, not as proof of a visibly rendered
3D object. Use the existing
Mac Podman Devtool workspace and its official source-edit/patch-generation
lifecycle. Do not hand-edit a generated patch or mix the restoration with a
new light/material diagnostic. Mini remains authoritative for `do_patch`,
BitBake, image creation, QEMU, and QMP validation.

## Success criteria

- Reuse the one existing Podman machine, container, bind-mounted state, Mini
  receiver, build directory, TMPDIR, and QMP evidence root.
- Establish the correct Devtool source baseline after the existing app recipe
  patches, edit only the production indirect-light line, and commit the source
  change in the Devtool local Git.
- Generate the official Devtool patch and copy it unchanged into
  `meta-fluorite-trial`; register it in the app recipe after the existing
  production-scene patches without retaining an exact duplicate.
- Commit the layer change locally, create one verified Git bundle, and send it
  to the fixed Mini receiver.
- Pass Mini recipe `do_patch`, component compile, and full image gates before
  QEMU. Record image/kernel/qemuboot hashes.
- Run a QMP-only p6-style control with effective runtime log
  `INDIRECT_LIGHT_TYPE=DEFAULT`, force-render precondition enabled, skybox and
  explicit lights skipped, and Sequoia selected. Require nonzero 3D pixels,
  nonzero HUD, selected runtime markers, and clean QMP teardown.
- If DEFAULT restoration is visible, open a new independent ticket for the
  next explicit-light condition. If it is not visible, record the exact
  missing evidence and split the next display boundary into a new ticket.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- Historical p6 used rootfs `c8ee1fc3e4e0a467ed642a939120788040fd1dc96bd71f6cc72ebc92d60f37d1`,
  built from `e066ba0`, and recorded `DEFAULT` indirect light plus
  `4905/223200` 3D pixels.
- Current `a94f877` rootfs `d401ed8ab0e3522e1828ae5688966763284e65aa6a4246e4da3b83879f10d66a`
  records `HDR` and `0/223200` under the otherwise requested p6-style
  conditions.
- `e066ba0..a94f877` deletes
  `0001-fix-use-default-indirect-light-for-production-scene.patch` from both
  the layer and the demo recipe `SRC_URI`.
- Existing `0050-test-restore-known-good-native-fixture-scene-devtool.patch`
  restores `poGetScene()` to the production route but changes its indirect
  light from DEFAULT to HDR. The removed `0001` was the later DEFAULT restore.
- FLR-0073 showed that 0206 removal alone does not restore the black result.
- The new Mini gates passed on the fixed receiver/build/TMPDIR. The rootfs
  SHA256 is `2a19dbee65f1d2ae7787b781af4234818b68357447fe78583414f33f26a106d0`,
  the kernel SHA256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  the matching qemuboot SHA256 is
  `08fc320f6bd2c80bdb2ca52da323574cd639117e982afcda3857318157e6edd6`.
- The fixed QMP run under
  `$QEMU_EVIDENCE_ROOT/flr0075/qmp-control` reached effective DEFAULT,
  Sequoia model selection, renderable shapes, camera application, forced
  frames, and successful Vulkan present markers. The runtime log SHA256 is
  `4deba9b693cc7038e120d4d780c621d42c7d206f5d18fd80e727cc834f0de898`.
- The QMP final frame was `1280x800`; its 3D candidate region changed only
  `620/223200` pixels in a one-pixel horizontal line at `y=398`, and the HUD
  region changed `0/100000`. The full QMP frame showed a black field with a
  horizontal boundary and lower Flutter buttons; no visible car/3D object was
  accepted.
- The app configuration log still reported `1280x720`, while the native
  Wayland/Vulkan surface marker reported `extent=1280x800`. Historical p6
  reported both the app size and native surface as `1280x720`.
- Historical p6's `4905/223200` count is retained as comparison evidence, but
  its QMP image does not visibly prove a car; the count alone is insufficient
  for the 3D success criterion.
- App stop, QMP capability negotiation/quit, and final residual checks passed:
  no QEMU, runqemu, flutter-auto, or QMP socket remained.

### Ranked hypotheses

1. DEFAULT restoration is correct, but the current native surface is sized to
   `1280x800` while the Flutter parent is `1280x720`, causing the native child
   to cover or displace the parent HUD and candidate content. Prediction:
   surface-extent/parent visibility controls change QMP pixels without a new
   light patch.
2. The current QEMU/compositor launch timing or display profile differs from
   p6 and determines the native extent. Prediction: a clean compositor-ready
   relaunch changes the extent while source and image remain fixed.
3. DEFAULT restoration changes the first source boundary, but a separate
   render-target/material issue remains. Prediction: exact 720p composition is
   recovered while a production-light condition remains black.

### UNKNOWN

- Whether the `1280x800` native extent is caused by compositor timing, target
  configuration, or a later surface patch.
- Whether any current p6 pixel-positive diff was a visibly meaningful object
  or only a non-black line/overlay artifact.

## Plan / Do / Check / Act

### Plan

- Confirm the current canonical branch and fixed Podman/Devtool contract.
- Register or recover the app source through official Devtool operations using
  the already-mounted state; establish the post-existing-patches baseline
  before editing.
- Generate the official patch, then send the layer commit as one bundle to
  Mini. Mac's workspace recipe-level do_patch is not authoritative.
- Run progressive Mini gates and one QMP control before any next patch.

### Do

- Reused the fixed Mac Podman Devtool state and the existing attic source
  archive; no duplicate machine, container, named volume, TMPDIR, or QEMU was
  created.
- Edited only the production indirect-light line in the Devtool-managed source
  and committed it locally as `0f696a7`.
- Ran the official Devtool recipe update with force patch refresh. It produced
  `0001-fix-restore-production-default-indirect-light.patch`; SHA256 is
  `a53f8a983b5ddb5466990c983730989317e570ef0d5675fa7c44121f2a841c98`.
- Copied that generated patch unchanged into the canonical layer and appended
  it to the Example Demo recipe after the existing production-scene patches.
- Mac's auto-created Devtool workspace recipe has no `do_patch` task, so its
  bounded recipe-task check returned the expected task-not-found result. The
  Mini regular layer recipe remains the authoritative do_patch gate.
- Refreshed the baseline lock and passed `make verify`.
- Created local commit `42850fd` and transferred one verified bundle with SHA256
  `5ec7ee427069c3baea0d97646bec46701475fe1e1373cad923bcb26a83680750`.
- Mini `do_patch`, target `do_compile`, and full `agl-ivi-image-flutter` all
  passed in the existing fixed build/TMPDIR. The QMP run used one QEMU and
  QMP-only capture; no second runtime owner was created.
- Effective runtime DEFAULT and all required scene/present markers were
  recorded, but the QMP display criterion failed as described above.

### Check

- Repository checks, Mini gates, runtime marker identity, and QMP teardown
  pass. Visible 3D and nonzero HUD do not pass.
- The requested environment variable alone was not used as proof; effective
  runtime marker and QMP pixels were checked separately.

### Act

- Restoration is complete as this ticket's source/build unit, but it does not
  close the overall 3D goal. FLR-0076 owns the new surface-extent/composition
  discriminator. Preserve this QMP evidence and do not delete it as a
  duplicate.
