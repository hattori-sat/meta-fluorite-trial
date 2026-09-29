# FLR-0065 — production target zero after successful draw submission

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-10
- Depends on: [FLR-0064](FLR-0064-nonblocking-target-content-probe.md)
- Working log: `work/logs/2026-09-10-flr0065.md`

## Work unit

Separate the production target's zero content from the already-proven Flutter
2D path, queue submission, and diagnostic readback timeout. Use existing runtime
controls and one-variable comparisons to decide whether the first missing
content is production material/resource shading or target handoff. Do not mix
route/input or a permanent lighting/composition fix into this ticket.

## Problem

FLR-0064 completed a bounded target probe. The production target reported
`nonzero_pixels=0` while model completion, 24 `TARGET_DRAW2` markers, and queue
submission succeeded. The same QMP frame contained the 2D HUD and controls.

## Success criteria

- [x] Reuse the fixed Mini build/TMPDIR and one QEMU; preserve QMP-only frames,
  runtime logs, pixel analyses, hashes, and exact cleanup.
- [x] Compare the current full-shaded case with the smallest existing
  model-only/shape-positive diagnostic control while holding the image, QEMU,
  compositor-owner state, backend, surface request, and QMP capture path fixed.
  Keep the target-probe environment enabled; treat its missing result marker as
  UNKNOWN rather than silently promoting the comparison to a completed probe.
- [ ] Identify the first boundary that changes target content: material/resource
  setup, renderable draw output, or target-to-swapchain handoff.
- [ ] Do not alter product defaults or commit a permanent fix until the causal
  process step is evidenced.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0064 proved a 2D HUD/control frame and a zero full-shaded production
  target in the same QMP capture.
- `TARGET_DRAW2` and queue submit success are not sufficient evidence that the
  shaded vehicle pixels were written to the sampled target.
- The historical shape-positive condition is reproducible on the current image
  when `--width 1280 --height 800` is explicit and the extra frame/sync
  diagnostic variables are removed. The first attempt without those conditions
  is a retained precondition miss, not a regression verdict.
- Under the same owner-isolated QEMU, the replayed shape case produced stable
  non-black QMP pixels while the full-shaded case remained black in the common
  central candidate region. Full-shaded model setup, target draw, queue submit,
  and present markers were still present.

### Hypotheses

1. The production material/resource path produces no target content while the
   render command still submits. Prediction: a model/shape-positive control
   changes the target result before swapchain composition.
2. The target contains content but the sampled target is not the target later
   displayed by the swapchain composition draw. Prediction: a target-selection
   or handoff control changes the probe result without changing model/resource
   markers.
3. The earlier combined frame was only the suppressed diagnostic path, not a
   regression. Prediction: the same full-shaded baseline remains zero when the
   latest diagnostic-only patch is held constant.

### UNKNOWN

- Which material, primitive, resource, or attachment operation first produces
  the zero target.
- Whether the existing model-only success path and the full-shaded path share
  the same production target and composition owner.
- Why `FLR0026_TARGET_PROBE=1` emitted no result or timeout marker in these two
  comparisons even though QMP capture and the earlier FLR-0064 probe were
  available.

## Plan / Do / Check / Act

### Plan

- Inspect the existing FLR-0042/0044/0049 model and shape-positive controls and
  select the smallest one-variable runtime comparison.
- Keep Mac Devtool/official patch generation reserved for a source change that
  is justified by the comparison; Mini remains authoritative for `do_patch`,
  BitBake, QEMU, and QMP.

### Do / Check / Act

- Do: run the fixed evidence harness once for the selected comparison.
- Check: classify target content and correlate it with model/material/draw
  markers; do not infer a light failure from a black frame alone.
- Act: open a new ticket for the first causal operation, or generate the
  smallest Mac Devtool patch only after the runtime boundary is evidenced.

## Evidence — historical shape-positive replay and full-shaded comparison (2026-09-10)

- One QEMU was reused under `$QEMU_EVIDENCE_ROOT/flr0065/p1`; no new build,
  TMPDIR, container, or QEMU was created.
- Shape-positive evidence:
  `$QEMU_EVIDENCE_ROOT/flr0065/p1/shape-positive-rerun`. Twelve identical
  frames, PPM SHA-256
  `fbcd0241a4c8556bab9d18bbcc56f867be043cc6153dd188b1c75f55c82db346`;
  `[200,100,400,250]` = `56701/100000`,
  `[300,80,620,360]` = `139107/223200`; runtime log SHA-256
  `ddea05d54cf845d96ef1ba3fdbf49e3918e56c4e32efbbe48f924f7e24856c18`.
- Full-shaded evidence:
  `$QEMU_EVIDENCE_ROOT/flr0065/p1/full-shaded`. Twelve identical frames,
  PPM SHA-256
  `cc9b8e1c382a141ea05273c11162288e4b99b8324af536fb86adf6cdae382c8b`;
  `[200,100,400,250]` = `1292/100000` HUD-only pixels,
  `[300,80,620,360]` = `0/223200` with region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`;
  runtime log SHA-256
  `67571156ccb1ad3bb720e27e0c24618b00e72c643217e1963bc8e20310612454`.
- Full-shaded markers: `MODEL_STAGE_SCENE_ADD_DONE=1`,
  `SHAPE_READY=45`, `TARGET_DRAW2=25`, successful queue submit `=2`, and
  queue present `=1`. Neither A/B emitted `TARGET_PROBE_RESULT` or
  `VK_READBACK_FENCE_TIMEOUT`; this is recorded as UNKNOWN.
- Cleanup: guest app stopped by recorded PID, Weston owner snapshot restored,
  compositor active, grpc owner returned, and Mini QMP harness reported
  `qmp=PASS cleanup=PASS residual_targets=0 residual_qmp=0`.

### Result of this entry

The previous simultaneous 2D+diagnostic-3D evidence is not a full-shaded
production baseline. The current image still reproduces stable 3D pixels in the
shape-positive control, while the full-shaded production path is black in the
same QMP target region. This is not evidence that the latest diagnostic patch
caused a 2D/3D regression. The exact shaded material/resource/target operation
remains the next boundary to identify; no permanent product fix is authorized
by this entry.

## Evidence — bounded production-renderable observation (2026-09-10)

- Static source review found that `FLR0026_CAMERA_GEOMETRY_TRACE` sampled only
  six renderables. The preceding full trace had 58 renderables and 13 lights,
  so the production model renderables were not yet observed.
- Mac Devtool source baseline imported from Mini effective source:
  `32f4fab`. New source commit: `32ddefc`. Official generated patch:
  `0205-diag-extend-renderable-resource-sample-limit-devtool.patch`, SHA-256
  `2ff2c861c40cb3112d0a5a3921b9b0d316c11e9e081c4c387a9d07a9a392b40b`.
- The change is opt-in through `FLR0026_CAMERA_GEOMETRY_SAMPLE_LIMIT`, with
  default 6 and maximum 128. It does not change product rendering when unset.
- The Mac recipe-level patch gate stopped on the pre-existing parent-alpha
  patch hunk 3 before reaching a 0205 verdict. Mini is the authoritative
  `do_patch` gate. No Mini build or QEMU result exists for 0205 yet.

### Current conclusion

The evidence does not support “a previously working full-shaded 2D+3D path was
regressed by the latest patch.” A shape-positive 3D condition is reproducible
on the current image, while the full-shaded production condition remains HUD
plus black. The earlier simultaneous frame was a diagnostic/controlled path,
not a proven full-shaded production baseline. The next check is to observe the
later production renderables/materials, then run the same exact tip on Mini.

## Evidence — current-image replay of the controlled 2D+3D condition (2026-09-11)

### Facts

- The existing single `flr0066/p1` QEMU and the 0205-built rootfs were reused;
  no second QEMU, container, TMPDIR, or image was created.
- The historical controlled condition was replayed with the current image:
  Sequoia model selection limited to two, environment/skybox and indirect light
  skipped, production shapes and lights skipped, transparent skipped-skybox
  clear enabled, and forced rendering after skipped frames.
- QMP captured 12 frames under
  `$QEMU_EVIDENCE_ROOT/flr0066/p1/combined-current/frames`. The final PPM
  SHA-256 is
  `7c9f6c73b9360fa37795d71fe68fc6fd75ae09ebf7e6a4393dd93accedd5479e`.
  Against black, the candidate region `[300,80,620,360]` changed
  `3290/223200` pixels with bounding box `[367,86,489,274]`; the upper HUD
  region `[200,100,400,250]` changed `3158/100000` pixels. The geometry count
  was stable across all 12 frames while HUD metrics changed normally.
- Runtime evidence for this run includes
  `FLR0026_NATIVE_CLEAR_SKYBOX_ON_SKIP enabled=true`, 98
  `FLR0026_FRAME_FORCED_AFTER_SKIP` markers, four successful Vulkan present
  markers, and no crash marker. The copied runtime-log SHA-256 is
  `ff367b193330dbd86d8cf5dbb37ecbe79295782d2f253963b4629bc3b0b2156b`.
- The current model-only run under the same image produced PPM SHA-256
  `61d1c910b7bdc39893b00812ce94b25c917f603d139773aae71c935c1e04e9a2`,
  bit-for-bit matching the earlier FLR-0049 no-readback production Sequoia
  result. Its runtime log is retained at the same evidence root.
- The current full-shaded run remains black in the same candidate region:
  `0/223200`, despite model completion, 58 renderables, 13 lights, target
  draw markers, queue submit, and present.

### Inference

The controlled 2D+diagnostic-3D path still works on the current image. The
latest diagnostic patch therefore did not regress the whole 2D/3D composition
path. The black output is specific to restoring the full production scene
stages and is not explained by 0205, whose default behavior is unchanged.
The earlier positive frame was real, but it was not a full-shaded production
vehicle baseline.

### Decision / next boundary

- This ticket is Waiting rather than Done because the exact first production
  operation that turns the candidate region from non-black to zero is still
  unknown.
- FLR-0067 owns the next one-variable runtime matrix: retain the visible
  model-only baseline and reintroduce shapes, environment, and lights one at a
  time. No source patch is justified until that boundary is observed.

### Cleanup

- The recorded app PID was stopped, the Weston configuration was restored, the
  compositor returned `active`, and the official QMP harness reported
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

## Evidence — current-image minimal A/B and regression classification (2026-09-11)

### Facts

- The full production trace on the 0205-built image sampled the real Sequoia
  resources: `sequoia_ngp.glb`, `PaintColor`, `HeadLights`, `Chrome`, `Glass`,
  and other materials. QMP final frame:
  `$QEMU_EVIDENCE_ROOT/flr0065/p3/full-trace/frames/frame-00011.ppm`, SHA-256
  `037175e1113b88ed6e2dd875c4463340e46d31952f7ed9fac6bcc138128a2904`.
  Region `[300,80,620,360]` was `0/223200`; the HUD region changed
  `438/100000`. Runtime log SHA-256:
  `f0645257833e076479ed2f6e8ec60393f5ba9307a27aae4058cd594ba90b6a29`.
- Removing the skybox and indirect-light skip controls did not restore the
  car. The run reached `MODEL_STAGE_SCENE_ADD_DONE=1`,
  `entities=82 renderables=58 lights=13`, 13 target render passes, 13
  `TARGET_DRAW2` markers, 6,044 renderable samples, and 6,962 resource
  samples. QMP final frame:
  `$QEMU_EVIDENCE_ROOT/flr0065/p3/full-no-skips/frames/frame-00011.ppm`, SHA-256
  `3bab257d9ab31c708c85f74a159ab14622fe03956ad2d51d8e4dc1fc1abd7b5f`;
  the 3D region remained `0/223200` with black-region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- A minimal launch with only Sequoia selection also remained black after more
  than 30 seconds. Late-frame PPM SHA-256:
  `5fbd893673beeeaeac50333b03e02c8dcb52dda1bb4a1a8557d15fc4c76d13f5`.
- Cleanup passed: exact app stop, Weston restore, compositor active, QMP
  `capabilities=negotiated quit=accepted`, `residual_targets=0`,
  `residual_qmp=0`, and no p3 QMP socket.

### Inference

The black result is not caused by the skybox/indirect-light skips or by the
analysis-only runtime flags. The production model/resource path reaches GLB
completion, scene insertion, material samples, target draw, and queue submit,
but the QMP 3D candidate remains zero. The precise shaded draw versus target
handoff boundary remains unresolved.

FLR-0049 proves an earlier production Sequoia 3D-only pixel result, but its
own record says the native surface masked the Flutter HUD; a combined
2D-HUD-plus-full-shaded-production frame was never accepted. Therefore this is
not yet evidence of a regression from a previously working simultaneous
2D+3D baseline. It is evidence that the current patch stack/profile no longer
reproduces the earlier 3D-only result, which must be compared separately.

0205 is not a plausible cause of the earlier black frames: it is opt-in
resource sampling with a product-default no-op, and black full-shaded output
was already present before its Mini image handoff.

### Process correction

One inspection accidentally read a guest `/tmp` path on the Mini host and one
cleanup attempt hit local quoting / same-file restoration errors. Neither was
used as runtime evidence; both were corrected, and the final teardown passed.

### Act

FLR-0065 is Waiting. The historical controlled path is now reproduced by
FLR-0066; FLR-0067 owns the one-variable production-stage comparison. Mac
remains the official Devtool patch-generation side; Mini remains the
authoritative `do_patch`, BitBake, image, QEMU, and QMP gate.
