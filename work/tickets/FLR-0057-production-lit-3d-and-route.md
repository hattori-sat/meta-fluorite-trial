# FLR-0057 — production lit 3D and route transition

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + target-validation + Flutter/Filament roles
- Created: 2026-09-09
- Depends on: [FLR-0050](FLR-0050-flutter-parent-alpha-frame-loop.md), [FLR-0049](FLR-0049-production-model-render-boundary.md)
- Working log: `work/logs/2026-09-09-flr0057.md`

## Work unit

Identify the first divergent operation between the diagnostic wireframe and the
full shaded production Fluorite vehicle, then validate Radar/Planetarium route
and input transitions with the same bounded QEMU/QMP evidence contract.

## Success criteria

- [x] Reuse the existing image revision `d88d600`, fixed Mini PC build directory,
  fixed TMPDIR, one persistent Devtool provider, one QEMU, and one evidence run.
- [x] Compare exactly one lighting selector at a time for counts 1, 5, 6, and
  13. Record environment, selected model, native markers, QMP PPM/video, pixel
  statistics, runtime-log hash, and negotiated teardown for every condition.
- [x] If count is insufficient, compare same-count light identity/parameters
  before editing source or adding a workaround.
- [ ] Use bounded QMP input for Radar and Planetarium after the lighting
  boundary is captured; record route, focus, input, and resulting frame evidence.
- [ ] Distinguish HUD-only, diagnostic wireframe, shaded production 3D, and
  combined 2D+3D. Suppression controls and HUD presence alone are not success.
- [ ] Only after the divergent runtime operation is known: edit through official
  Yocto Devtool on Mac, finish the generated patch into
  `meta-fluorite-trial`, commit locally, bundle to the Mini PC, pass progressive
  BitBake gates, and repeat QMP validation.

## Out of scope

- Creating another container, build directory, TMPDIR, receiver, or concurrent
  QEMU.
- Copying a Mini PC rootfs/deploy tree to the Mac.
- Treating the 0204 diagnostic wireframe as a production vehicle fix.
- Applying a source patch before the first divergent runtime operation is
  evidenced.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0050 established stable 20/20 combined QMP diagnostic frames when shapes
  and lights were suppressed, and black candidate pixels when the full light
  set was enabled.
- FLR-0031/0032 recorded a historical light-count boundary near 5→6, while the
  current image still needs a controlled recheck.
- FLR-0049 established production Sequoia model-only native 3D pixels and
  scene-add evidence.

### Inferences

- The next smallest useful cut is the light count/identity/resource boundary,
  not another QEMU startup or parent-alpha patch.

### Hypotheses

- H1: a bounded light-count threshold will reproduce the black-frame boundary
  on the current image.
- H2: if count alone does not explain it, one light identity or parameter path
  invalidates the production render while present continues to succeed.
- H3: route/input transition is a separate Flutter/UI boundary from lighting.

### UNKNOWN

- Current-image light threshold and the exact failing light operation.
- Full shaded production-car pixels with all required lights/resources enabled.
- Whether Radar/Planetarium transitions are reachable by QMP input in the
  current guest focus state.

## PDCA

### Plan

First reproduce the 1/5/6/13 light matrix without a source change, then narrow
identity/parameters and route/input. Keep each evidence unit small and append
the result to this ticket before selecting the next one.

### Do / Check / Act

The first active run is recorded below. A failed or black result remains valid
evidence and includes the runtime log and QMP capture hashes.

## Iteration 2 — current-image light-count matrix (2026-09-09)

### Facts

- The fixed image revision `d88d600` was booted once through the official
  runqemu/QMP harness. The existing Mini PC build directory, TMPDIR, rootfs,
  qemuboot, and kernel were reused; no new image or second QEMU was created.
- The installed Example Demo was launched as `agl-driver` with
  `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`. Each case
  stopped the previous `flutter-auto` before launch. The earlier matrix
  attempt is retained as `light-argument-failure` because its shell argument
  became `guest` instead of `5`; it is not counted as a valid light case.
- Valid light limits 1, 5, 6, and 13 all reached
  `MODEL_STAGE_COMPLETE`, `CAMERA_APPLIED`, and Vulkan `QUEUE_PRESENT result=0`
  in the guest log. The later frames still reported `FRAME_BEGIN ...
  started=false`.
- QMP-only captures were 1280x800. For the fixed candidate region
  `[300,80,620,360]`, all valid cases measured `changed_pixels=0/223200` and
  shared the same black-region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- Evidence is outside Git under the fixed QEMU evidence role path. The final
  QMP PPM, runtime-log, and Mac-preview video hashes are:

  | light limit | QMP PPM SHA-256 | runtime log SHA-256 | Mac QMP video SHA-256 |
  | ---: | --- | --- | --- |
  | 1 | `07b1aff5192cf0d440db496544b50e608daf6ebec79325843e7ec9f8bc06a829` | `21e3cb25974a58f4c32b95be402ef1a98fcd2b06fe7d1ed7f2f5bb7183bda009` | `bf596b2b4c0eac046023df26633184fb4a8fd5817882a4fe2f9029a6b6fe5625` |
  | 5 | `4d00979752ffbd2004f24bd2505717e559268d12aeb06a6eea284dcde98deb35` | `5084508961d64808e4dac91dc0deb150382878728a532b7ab3bc46d9bbf0830e` | `8d44dae5b6145f80ff4e7b6c4c75332344f31e3867a63ffdc0b1dc7636364ec6` |
  | 6 | `c7a3119b7bceee5e2bceaac52ba980f0705775b4ed4aef47c4c55c039d0b0ba4` | `f7b1defa1f00016a7940f7c29bf0981d383366fe53a9cb0b4d54ac1fb0006867` | `a634a144a096551a5b249e54c251ab743263d5f981d03ec7e1f7f61dac4a09e3` |
  | 13 | `b9d3540c39ae4d1aae51fc39ddbc4f71fb59a4e123552ab2056af906b937745b` | `cda5c15ecf8016d99bfa8d96f73e5a3a7fdc715f0dca707e059d0b39472b75a9` | `6fb1d96817e4f7339954b706393d105f8a98b7c33005a954018a36834fedddbf` |

### Inferences

- The current black production region is not explained by the number of
  enabled lights. The matrix rejects the earlier 5→6 light-count threshold
  as the primary cause for this image.
- The 2D parent is alive and presenting: the QMP images show the HUD, FPS,
  CPU/GPU/System delay, Scenes control, and lower controls. The failure is
  narrower than a full Flutter or QEMU display failure.
- Because model completion, camera application, and Vulkan present all occur
  without production pixels, the next boundary is the shaded material/resource
  or frame-start/composition operation after those markers, not QEMU startup.

### Hypotheses

- H1 is rejected: light count alone does not cause the current black region.
- H2 remains plausible: one light identity, parameter, material, or resource
  operation may invalidate the shaded production path even when present
  succeeds.
- H3 remains separate and untested: Radar/Planetarium route/input may be a UI
  focus boundary independent of the shaded render failure.

### UNKNOWN

- The first failing shaded-material/resource operation and whether its output
  reaches the native surface remain UNKNOWN.
- Combined 2D plus full shaded production-car pixels remain UNKNOWN.
- Radar/Planetarium route/input reachability remains UNKNOWN.

### Plan / Do / Check / Act

- **Plan:** keep the fixed image/runtime contract, then compare same-count light
  identity or parameter selection before changing source.
- **Do:** ran the 1/5/6/13 matrix with QMP-only images and 12-frame videos per
  case, copied only evidence to the Mac, and retained the argument-passing
  failure separately.
- **Check:** all valid cases were black in the candidate region; QMP teardown
  returned `qmp=PASS capabilities=negotiated quit=accepted` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`.
- **Act:** do not create a patch yet. Next run should isolate a same-count
  identity/parameter or shaded-resource operation, then test bounded
  Radar/Planetarium input only after the render boundary is narrower.

## Handoff — split frame/fence boundary (2026-09-09)

The current-image light-count gate is complete: limits 1, 5, 6, and 13 all
reached model/camera/present markers yet remained black in the production
candidate region. The next independently verifiable boundary is tracked in
[FLR-0058](FLR-0058-restore-native-frame-loop.md); route/input and combined
2D+3D remain UNKNOWN and are not added to this completed light-count unit.

## Iteration 1 — activate runtime-first light boundary (2026-09-09)

### Facts

- FLR-0053's requested Podman scope is now a bind-mounted container contract;
  its runtime remains Waiting because no external Podman backend is available.
- FLR-0050's image/build evidence is reusable: image tip d88d600, the fixed
  Mini PC build directory/TMPDIR, and the bounded runqemu/QMP harness.

### Inferences

- Continuing with the validated Docker-built image is the shortest path to the
  user's 3D goal and does not block a later Podman container smoke test.

### Hypotheses

- H1: current-image light counts 1 and 5 retain visible native pixels while 6
  and 13 return HUD-only/black candidate pixels.
- H2: if the count boundary moves, the next comparison is same-count identity or
  parameter selection, not a new source patch.

### UNKNOWN

- Current-image light threshold, full shaded production-car pixels, and route/input
  reachability remain unknown.

### Plan / Next action

- Start one QEMU after harness preflight, launch the production demo as the guest
  runtime role, run counts 1/5/6/13 one variable at a time, keep QMP-only PPMs and
  runtime log hashes, and perform negotiated teardown after the matrix.
