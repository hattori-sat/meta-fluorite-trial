# FLR-0067 — reintroduce production scene stages one at a time

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0065](FLR-0065-production-target-zero-resource-boundary.md), [FLR-0066](FLR-0066-compare-historical-production-3d-stack.md)
- Working log: `work/logs/2026-09-10-flr0065.md`

## Work unit

Use the current 0205-built image and the visible Sequoia model-only condition
as the fixed baseline. Reintroduce production scene stages one variable at a
time to identify the first condition that makes the QMP candidate region zero.
This ticket is runtime-only until the causal boundary is evidenced.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, one QEMU, one compositor-owner profile,
  and the existing QMP capture/analyzer.
- Establish a visible model-only control, then compare shape-only,
  environment-only, light-only, and the smallest required combinations without
  changing the image or source between runs.
- Record the first transition from non-black to zero with QMP PPM hash, region
  count/bounding box, runtime markers, and exact cleanup.
- Do not create a permanent patch until the responsible process operation is
  identified and its falsifying comparison is recorded.

## Facts

- The current image reproduces the historical model-only Sequoia pixels.
- The current image reproduces the controlled 2D+diagnostic-3D composition.
- The current full-shaded production scene remains black in the central QMP
  candidate region after model completion, target draw, submit, and present.
- Earlier same-image A/B evidence showed shape-positive/light-skipped pixels,
  light-positive/shape-skipped zero pixels, and both enabled zero pixels.

## Ranked hypotheses

1. Reintroducing the production light setup or its interaction with materials
   changes the render target to zero. Prediction: light-only is the first
   failing condition while shape-only remains visible.
2. Reintroducing production shapes with the full material set creates an
   attachment/resource condition that is hidden by shape-only controls.
   Prediction: shapes-only is visible but shape+one-light becomes zero.
3. Environment/skybox composition masks a nonzero native target. Prediction:
   environment-only changes QMP pixels without changing renderable or present
   markers; this is falsified if no-skip environment remains black with the
   same target counts.

## Plan / Do / Check / Act

- Plan: freeze the current image and owner-isolated runtime profile; select the
  smallest matrix that distinguishes the three hypotheses.
- Do: run each condition sequentially in the existing QEMU and preserve all
  QMP frames and logs under one evidence directory.
- Check: classify pixels first, then correlate only the markers for the stage
  being reintroduced. Treat absent markers and failed cleanup as UNKNOWN/FAIL.
- Act: open a new ticket for the first causal operation or prepare the minimal
  Mac Devtool source change. Mini remains authoritative for `do_patch`,
  BitBake, image, QEMU, and QMP validation.

## UNKNOWN

- The first exact shape, material, light, environment, attachment, or handoff
  operation responsible for the zero production target.
- Radar/Planetarium route and input behavior; those remain a later ticket.

## Regression classification update (2026-09-11)

- The current image still shows 2D HUD plus diagnostic native 3D pixels under
  the controlled combined condition. Therefore a generic 2D/3D composition
  regression is not established.
- The earlier production Sequoia proof was 3D-only with the native surface
  masking the Flutter HUD. A previously successful full-production
  2D-plus-3D baseline has not been evidenced.
- The current black result is isolated to the full production shaded path. The
  0205 bounded sampling patch is not causal: the same black boundary existed
  before its Mini image handoff and its default path is unchanged.
- The historical 0195 success stack and the current 0196–0205 stack differ in
  composition/surface/bind diagnostics. This is the next comparison boundary;
  no patch is deleted solely by filename similarity.
- A fresh p2 QEMU did not reach guest SSH or emit serial boot progress and was
  stopped cleanly through QMP. It is not valid display evidence.
- A static audit of 0196–0204 found their changed behavior is opt-in through
  environment variables. Those variables were unset in the recorded minimal
  and combined runs, so deleting these patches by filename would not explain
  the observed black frame and would damage reproducibility.

## Runtime matrix update (2026-09-11, p3)

The p3 comparison reused one fixed QEMU, one fixed image, and one compositor
owner-isolation profile. No source, image, build directory, TMPDIR, or
container changed between conditions.

### Facts

- The corrected diagnostic launch displayed both the Flutter HUD and native
  Sequoia pixels. The final QMP frame SHA-256 was
  `8cc1037ae3d8200e48ebfea5aa7b8e0ffc878fcda409f5ff2954a3da753f3fe1`;
  candidate 3D region `[300,80,620,360]` was `3290/223200` with bounding box
  `[367,86,489,274]`, and the HUD region was `3252/100000`.
- The full production condition used the same image and owner profile. Its
  final QMP frame SHA-256 was
  `03fa0728eed71084f4792d0e03268c965b317a39abb0bf9ad16af0d53cb74f1b`;
  candidate 3D pixels were `0/223200`, while the HUD region remained
  nonzero at `401/100000`.
- During the full production condition, model-stage completion and camera
  application markers continued, then the guest reported a page fault in
  `FEngine::loop`. The fault instruction address was mapped inside
  `/usr/lib/libLLVM.so.18.1`. Exact symbol and source operation are UNKNOWN
  because the runtime image does not include `addr2line` or `readelf`.
- The one-variable matrix found the following final 3D counts:

  | condition | 3D region | final frame SHA-256 |
  |---|---:|---|
  | shape skipped | `0/223200` | `b907c0b573770bfb558354e1d8ab3cdb0a38e59b53cc5d468767a4b5b32826d9` |
  | light skipped | `0/223200` | `6cf2ae892bcc2ba7fc593ec791dc2dac0e54859c513f6623b6f95f585b1c18a6` |
  | environment + light skipped | `4905/223200`, bbox `[300,80,620,280]` | `45e23aac365a7ff5161194445b43226de8018b10159f4da9d32fcc91c0d5aecb` |
  | environment skipped | `0/223200` | `0522a427091977a9630bee3e3efcd4fe85c12f43495f86cc7b283337a86004e6` |

- The empty host copy of `full-production.runtime.log` was an extraction
  failure, not runtime evidence, and was removed. The selected serial fault
  and marker files plus all QMP frames remain under the Mini evidence root.
- The p3 guest was restored to the compositor configuration, the app was
  stopped, and the official QMP teardown reported `cleanup=PASS` with zero
  residual targets and zero residual QMP sockets.

### Inferences

- The generic 2D/3D composition path is not shown to be regressed: the same
  current image displays 2D HUD plus diagnostic 3D pixels under a controlled
  condition.
- The first observed black boundary is in the production scene's environment
  and light interaction. Full production also has a strong runtime fault
  correlation with the software Vulkan/LLVM path, but this is not yet a
  proven single root cause.
- Deleting patches solely because their filenames look similar would be an
  invalid countermeasure. Exact duplicate content is absent, and the
  remaining patches have distinct roles or opt-in controls.

### Hypotheses / UNKNOWN

- H1: a production environment or light/material operation reaches a software
  Vulkan/LLVM shader or resource path that faults or produces zero target
  pixels.
- H2: environment/light changes select or mask a target even when the native
  render stages report completion.
- UNKNOWN: the exact light, material, environment, attachment, shader, or
  target-handoff operation that first causes the zero result.

### Check / Act

- **PASS:** same-image p3 matrix, QMP-only evidence, process cleanup, and
  compositor restoration.
- **UNKNOWN:** exact source operation and route/input behavior; no product
  patch is justified by this matrix alone.
- **Act:** keep source editing and official patch generation on the Mac via
  Devtool. Use the Mini only as the authoritative environment for
  `do_patch`, BitBake, image creation, and QEMU validation. The next runtime
  cut must isolate the first environment/light/material operation before any
  permanent patch is prepared.

## Runtime matrix update (2026-09-11, p4/p5 and candidate falsification)

### Facts

- p4 separated the environment controls with the same image and owner-isolated
  compositor. Environment plus explicit lights skipped produced the known
  model-only result (`4905/223200`); skybox skipped plus explicit lights
  skipped with HDR indirect light still enabled produced `0/223200`; indirect
  light skipped plus explicit lights skipped produced `90220/223200` with the
  skybox present. The final p4 frame hashes were respectively
  `603a7e2cbe8d57a9dfeac48de9e6ebb3d53ffda1536683c7f2a4a3ffaf8463cb`,
  `8c4355650ac79e92d18ad015fa999f819f2d0ca519207e7969210e20734eb5c2`, and
  `84b60a767b081329e5e4705e63dc9beb35a141c4fc73bbc480b11bf460d55e20`.
- On Mac Devtool source, the effective production `poGetScene()` was changed
  from `HdrIndirectLight.asset(...)` to `poGetDefaultIndirectLight()` and
  committed as source revision `3bf8eac4f494b1b8293cdfc8174e5201e24e5989`.
  Official `devtool finish --mode patch` generated the patch with SHA-256
  `fb96cef09f94e9500cce3cb3bbb4233c1fd9211405228ccbd3f370d502854fa7`.
- The generated patch passed the Mac recipe `do_patch` gate, Mini recipe
  `do_patch`, Mini app `do_compile`, and the full
  `agl-ivi-image-flutter` build. The candidate rootfs SHA-256 was
  `c8ee1fc3e4e0a467ed642a939120788040fd1dc96bd71f6cc72ebc92d60f37d1`.
- The candidate full-production p5 run used no skip variables. Five QMP
  frames were identical with SHA-256
  `21b40ac82283926e44865b289b5d10dc049eaf13c85d85df1a3773c6a5777057`;
  the 3D candidate region remained `0/223200` and HUD was `1266/100000`.
  The runtime recorded `INDIRECT_LIGHT_TYPE=DEFAULT`, Sequoia scene add,
  camera application, Vulkan submit/present completion, and no LLVM fault
  through more than 105 seconds. Runtime log SHA-256 was
  `b15238ac7b6d106401f184f8c3a162da8079046899d1aa76839d3591842b8a18`.
- With default indirect light and explicit lights skipped, the final QMP
  frame was the same `84b60a...` frame as the p4 indirect-light-skipped
  control, with `90220/223200` non-black pixels. Because the skybox was still
  present, this is scene/skybox output and is not counted as model proof.
- With environment and explicit lights skipped on the same p5 image, QMP
  produced `4905/223200` in the 3D region, bbox `[300,80,620,280]`, HUD
  `3026/100000`, and final frame SHA-256
  `3fb79b12b52aadd2ac5baf482b354f37dba9809799c2927c8cd3075ff657aa79`.
  The log recorded Sequoia scene add and repeated successful Vulkan present;
  its SHA-256 was
  `da172693c31cd5a2e7117b5b8e7ae83d7a1e58764c64603955db6b45fed3c144`.
- The p5 guest configuration was restored, the app was stopped, and the
  official QMP teardown returned `qmp=PASS` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

### Inferences

- The generic 2D/3D composition path is not regressed: the same patched image
  still shows the 2D HUD and the model-only 3D pixels when environment and
  explicit lights are excluded.
- Restoring the default indirect light did not restore production 3D. The
  generated candidate patch therefore falsifies “HDR indirect light alone is
  the cause” and must not remain as a product change.
- The remaining boundary is the production scene's environment/light/material
  interaction or its render-target handoff. The default-light plus
  lights-skipped result cannot identify explicit lights by itself because the
  white skybox dominates that frame.

### Hypotheses / UNKNOWN

- H1: a production explicit-light/material/renderable operation fails or masks
  model pixels while the Vulkan submit/present path still completes.
- H2: the remaining skybox/environment composition changes the target or
  attachment state independently of indirect-light selection.
- UNKNOWN: the first exact operation and whether the remaining production
  failure is in light data, material/pipeline creation, target selection, or
  surface composition.

### Check / Act

- **PASS:** Mac Devtool source edit and official patch generation; Mac and Mini
  `do_patch`; Mini app compile; full image build; QMP-only p5 matrix; exact
  teardown; no new machine, container, receiver, build directory, or TMPDIR.
- **FALSIFIED:** default indirect-light candidate as a production fix; it was
  removed from the canonical recipe after the runtime comparison.
- **Act:** retain the existing production patch sequence for now. The next
  runtime cut must compare skybox-skipped/default-indirect with explicit
  lights enabled versus skipped, then narrow the first light/material/render
  operation before another product patch is generated.

## Runtime matrix update (2026-09-11, p6 explicit-light boundary)

### Plan

- Reuse the candidate image that already passed the Mac Devtool and Mini
  `do_patch`/BitBake gates; do not change source or create another image for
  this runtime-only cut.
- Hold `DEFAULT` indirect light, Sequoia model selection, Vulkan backend,
  skybox skip/clear, camera, and compositor owner isolation constant. Toggle
  only the explicit production-light path.
- Capture QMP frames and selected guest markers for both conditions, then stop
  the app, restore Weston, and terminate QEMU through the official harness.

### Facts

- The tested rootfs was the historical candidate built from commit `e066ba0`
  (`c8ee1fc3e4e0a467ed642a939120788040fd1dc96bd71f6cc72ebc92d60f37d1`).
  No source, recipe, build directory, TMPDIR, or container changed during
  p6.
- Both conditions used `FLR0026_INDIRECT_LIGHT_TYPE=DEFAULT`,
  `FLR0026_NATIVE_SKIP_SKYBOX=1`,
  `FLR0026_NATIVE_CLEAR_SKYBOX_ON_SKIP=1`, Sequoia model limit 2, Vulkan,
  model-stage tracing, and the same owner-isolated compositor.
- Condition A left explicit production lights enabled. The final QMP frame
  hash was
  `c509f609400019cfb6496e3d4395b5c25cfc282a0226958e01d5064dd74afdf1`;
  the candidate 3D region `[300,80,620,360]` was `0/223200`, while the HUD
  region was `1303/100000`. The log SHA-256 was
  `03033bfe67da646a05e1fc1184854feb6a3b104e79154f30829bfbd87c51dcd8`.
- Condition B set `FLR0027_NATIVE_SKIP_LIGHTS=1`. The final QMP frame hash
  was
  `57954fc8e05571e67a84d785a4d68350167a45ff5891f51ad0cc66283d615199`;
  the same 3D region was `4905/223200` with bounding box `[300,80,620,280]`,
  and the HUD region was `3004/100000`. The log SHA-256 was
  `cb1647e60f99a24e1c438423f7295c0b82d8911aed8d5237ecbd59f6a4707292`.
- Both logs recorded skybox skip, the indirect-light type, Sequoia scene
  addition, camera application, and successful submit/present markers. No
  selected-log fault marker was observed. The p6 frame-list hashes are
  recorded in the Mini evidence directory under
  `/mnt/yocto/flourite-qemux86-64/qemu-evidence/flr0067/p6/`; the final-state
  record has SHA-256
  `efcc1533bdc7d3b529aea56ddffe20a977e7802c2ee59b2f52f0e8d370dff2b7`.
- The p6 QEMU was restored and stopped. Mini evidence records no residual
  `qemu-system`/`runqemu` process and `qmp_socket=absent`; the official
  teardown returned `qmp=PASS` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

### Inferences

- With indirect light and skybox held constant, changing only explicit-light
  participation changed the model region from zero to visible pixels. This
  is a stronger isolation than the earlier skybox-present control.
- The current 2D/3D output path is not generically broken: condition B shows
  the 2D HUD and native Sequoia pixels in the same QMP frame. The p5 default
  indirect-light candidate was therefore not a composition fix.
- The first causal boundary is the explicit production-light path or its
  interaction with shaded materials/render resources. This does not yet
  identify one light, one field, or one downstream Vulkan operation.

### Hypotheses / UNKNOWN

- H1: one explicit light's data or setup reaches a failing material/pipeline
  operation and makes the shaded target zero while submit/present succeeds.
- H2: the aggregate number or ordering of explicit lights triggers a resource
  or software Vulkan/LLVM path that the model-only path avoids.
- H3: explicit-light setup changes a target/attachment or surface handoff
  after the model is added; the common model and present markers do not prove
  the final target is the same.
- UNKNOWN: the first exact light/material/render operation and whether the
  issue is data, count/order, shader/resource creation, target selection, or
  composition.

### Check / Act

- **PASS:** fixed-image p6 A/B matrix, QMP-only frame evidence, selected-log
  evidence, and exact compositor/QEMU cleanup.
- **NOT A PRODUCT FIX:** no source patch was made from this result; the
  earlier default-indirect candidate remains removed from the canonical
  recipe.
- **Act:** inspect the existing light-limit selector and run the smallest
  runtime-only light-count cut (starting at one explicit light) before making
  another source change. If a source diagnostic is needed, edit the Mac
  Devtool source and generate the patch with official `devtool finish`; Mini
  remains authoritative for `do_patch`, BitBake, image, QEMU, and QMP.

## Handoff

- FLR-0067 is **Waiting** after isolating the first runtime boundary to
  explicit-light participation under fixed `DEFAULT` indirect light and no
  skybox.
- The one-light count/selector comparison is split into
  [FLR-0068](FLR-0068-isolate-explicit-light-count.md). No product patch is
  justified until that comparison identifies whether the trigger is the first
  light or an aggregate count/order/resource path.
