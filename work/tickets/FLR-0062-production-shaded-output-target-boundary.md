# FLR-0062 — production shaded output target/readback boundary

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Flutter/Filament roles
- Created: 2026-09-10
- Depends on: [FLR-0061](FLR-0061-production-shaded-resource-boundary.md)
- Working log: `work/logs/2026-09-10-flr0062.md`
- Handoff: [FLR-0064](FLR-0064-nonblocking-target-content-probe.md)

## Work unit

Under FLR-0060's validated snapshot-only compositor-owner condition, map the
full shaded production `draw`/`draw2` command execution to its render target
and native readback result. FLR-0061 proved that the current image creates
pipelines, executes draw commands, submits, and presents, but QMP remains black
and the existing readback callback emits no `NATIVE_READBACK_RESULT`. Identify
the first missing or black output boundary with the smallest runtime trace.

## Success criteria

- [ ] Reuse the fixed image/build/TMPDIR, one runtime provider, one QEMU, and
  QMP-only evidence; do not create another container, build, TMPDIR, or QEMU.
- [ ] Reuse FLR-0061's owner-isolated full shaded negative and its shape-positive
  control before changing a diagnostic variable.
- [ ] Map production shaded draw execution to a render target, attachment, or
  native readback result, or record UNKNOWN with the exact missing evidence.
- [ ] If a source diagnostic is justified, edit only through the persistent Mac
  Yocto Devtool workspace, finish the generated patch into
  `meta-fluorite-trial`, commit locally, bundle to the fixed Mini PC receiver,
  pass progressive BitBake gates, and repeat QMP validation.
- [ ] Retain QMP screenshots, bounded videos, raw runtime logs, analyses, and
  hashes; stop the exact app, restore Weston, QMP-quit the single QEMU, and
  verify no residual runtime process.
- [ ] Keep full shaded production 3D, combined 2D+3D, and route/input UNKNOWN
  until their own QMP gates pass.

## Out of scope

- Repeating the completed light-count, surface-placement, or compositor-owner
  discoveries without a new output-target/readback variable.
- Treating a diagnostic trace, shape suppression, or snapshot-only owner
  isolation as a product fix.
- Editing generated patch files, Mini PC build trees, or runtime `tmp`.
- Route/input and Planetarium validation before full shaded native pixels are
  proven in a stable frame loop.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0061's owner-isolated full shaded run reported 57 renderables after the
  Sequoia scene was added, five successful graphics pipeline creations, one
  `draw`, 23 `draw2`, successful Vulkan queue submits, and a successful queue
  present.
- The same run's QMP candidate region `[300,80,620,360]` was black in all 12
  captured frames (`0/223200` nonblack pixels).
- The same run emitted `NATIVE_READBACK_VIEW_RENDERED`, `...QUEUED`,
  `...FENCE_CREATED`, and fence `status=1`, but no `NATIVE_READBACK_RESULT`.
- The Mac Podman provider now has `selinux=0` at the development-VM boot
  boundary, one persistent container, the canonical project/state binds, and
  one container-private TMPDIR tmpfs. The provider xattr gate passes.
- The source baseline was imported from the effective existing recipe result
  at `90a9fe4a8`; the target/readback trace was edited in the Devtool-managed
  source tree and committed as `3e50ecaf5de4a53fbcf189fa087f062c02702b5c`.
- Official Devtool `update-recipe --mode patch --append --no-remove
  --force-patch-refresh` generated the 43-line diagnostic patch. Its
  registration is after the existing `0100` through `0170` Filament series.
- After `devtool reset --no-clean`, Mac Podman applied the full recipe patch
  graph successfully: `filament-vk:do_patch` 104/104. This proves the new
  generated patch is applicable on the Mac-side recipe graph; the Mini PC is
  still the authoritative build gate.
- The first Mini PC authoritative `filament-vk:do_compile` run reached the
  Filament source build but failed at `VulkanDriver.cpp` line 1915 because the
  new trace bound `getColor0()` as `const` while the existing
  `getImageView()` API is non-const. No full image or QEMU run was started from
  this failed gate.
- The source-level repair was made in the persistent Mac Devtool source tree:
  the local reference was changed to mutable and committed as
  `e712f5c77849f3e45eba7e747e91f953b8a3dc25`. Official `update-recipe` was
  rerun after aligning its initial revision to the existing diagnostic source
  commit; it generated only the one-line compile-fix patch. The byte-identical
  patch is registered after the diagnostic patch as
  `0171-filament-vulkan-target-trace-compile-fix-devtool.patch`, with SHA-256
  `213026e2e8168e34ee77f4550ba0b9863a8d2a23f998668a5ef3402c12eaca9b`.
- After `devtool reset --no-clean`, Mac Podman applied the updated patch graph
  successfully again: `filament-vk:do_patch` 104/104. The existing Podman
  machine/container and state root were reused; no additional provider or
  build directory was created.

### Inferences

- The next useful cut is after command execution and before or at the output
  target/readback boundary; repeating scene-add or camera checks is unlikely to
  reduce the current unknown.
- The existing command trace proves global draw execution, but does not map a
  command to a production entity or attachment. That mapping is still needed
  before attributing the black pixels to a specific shaded resource.

### Hypotheses

| ID | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| H1 | The observed `draw`/`draw2` commands are system/fixture draws, not the production shaded renderables. | A per-draw/entity or render-pass trace will show no production model draw, while the shape control will show its own draw target. |
| H2 | Production shaded commands execute against a black/incorrect attachment or are discarded before the native surface. | Target/attachment evidence is black or invalid after a successful draw and submit, while the control target contains nonblack pixels. |
| H3 | The render target contains pixels but the current readback callback/pump loses the result. | A direct target probe or corrected callback trace reports nonblack data even when QMP remains black. |

### UNKNOWN

- Which entity/material/attachment corresponds to the 24 observed draw
  commands.
- Whether production shaded pixels exist in any target before Wayland/QMP.
- Why the existing readback result callback does not appear after a ready
  fence.
- Stable full shaded 3D, combined 2D+3D, and route/input behavior.

## PDCA

### Plan

Use the already captured FLR-0061 command/pipeline evidence as the baseline.
Inspect existing Devtool diagnostics for render-target, attachment, and draw
correlation. Add only the smallest source diagnostic through the persistent Mac
Devtool workspace if the current image cannot identify the boundary. Finish
the generated patch into the layer, commit and bundle it, build on the fixed
Mini PC workspace, and repeat one bounded QMP run only after the expected
runtime signal is defined.

### Do / Check / Act

- **Do:** use the persistent Mac Devtool source workspace to add the smallest
  render-target/readback trace, generate the patch with official Devtool, and
  register it after the existing Filament patch series.
- **Check:** Mac provider setup, workspace de-duplication, effective patch
  order, generated patch cleanliness, and Mac `filament-vk:do_patch` 104/104
  all pass. The exact evidence is in the working log.
- **Act:** commit the compile-fix registration and evidence, create one Git
  bundle, update the fixed Mini PC receiver, rerun the authoritative
  `bitbake -e`, `filament-vk:do_patch`, and `do_compile` gates, and continue to
  image/QMP only after compile succeeds; keep the runtime 3D verdict UNKNOWN.

## Entry 9 — authoritative full image and QEMU target trace (2026-09-10)

### Facts

- The fixed Mini PC build at project commit
  `2e34c199fcfe257c3fb024e1fc56e6db5915f5a4` passed metadata, `filament-vk`
  `do_patch` (104/104), `do_compile` (1965/1965), and the full
  `agl-ivi-image-flutter` build (11748/11748). The qemux86-64 rootfs SHA-256
  is `bafbc8d6b6849994439efdf964c4f1e12c2d4e6c94cb02f42aaac63129cb6d9f`.
- One runqemu-harness QEMU passed artifact preflight, guest SSH, QMP-only
  capture, QMP quit, and residual checks. SSH was used after the serial TCP
  prompt synchronization failed to produce the app log; this was recorded as
  a harness precondition issue, not a render result.
- Owner-isolated full-shaded execution reached scene-add, camera, frame,
  submit, and present without a crash. QMP showed the complete Fluorite 2D
  HUD and metrics, but the candidate 3D region `[300,80,620,360]` was black
  in all 12 frames. The QMP PPM SHA-256 is
  `156d8a9bb03294716084a298ca93a1ecd751f1503f3bdd9a6855d7c675935533` and
  the black-region SHA-256 is
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- Target trace showed repeated non-swapchain targets with `color_view=(nil)`,
  a later swapchain target, one `TARGET_DRAW`, no `TARGET_DRAW2`, and no
  `NATIVE_READBACK_RESULT`; submit/present still succeeded. The exact app,
  owner-isolation change, and QEMU were cleaned up with residual count zero.

### Inferences / UNKNOWN

- 2D HUD and the Vulkan frame loop are proven in this run. Production shaded
  3D is still not proven; the target trace does not yet distinguish whether
  the draw is non-production, targets an invalid/black attachment, or reaches
  pixels that are lost in readback/composition.
- UNKNOWN: the production renderable-to-target mapping, the target contents
  before Wayland/QMP, and the missing readback callback result.

### Check / Act

- **Check:** QMP-only frames, derived bounded media, raw runtime log, target
  trace, analysis, hashes, and cleanup evidence are retained under the fixed
  QEMU evidence root using role-based paths.
- **Act:** add only an environment-gated `draw2` target trace through the
  persistent Mac Devtool source tree; do not change rendering behavior until
  that evidence narrows the boundary.

## Entry 10 — Devtool-generated draw2 target trace (2026-09-10)

### Facts

- The persistent Mac Podman Devtool source tree was edited through
  `devtool modify --no-extract`. The source commit is
  `044524ede363b096d15ba315fe17dbe9dac16d8c`; the change only adds an
  environment-gated `VulkanDriver::draw2` target log.
- Official Devtool patch generation produced
  `0172-filament-vulkan-draw2-target-trace-devtool.patch`. It was copied
  byte-for-byte into the Canonical layer and registered after patch `0171`.
  The generated/registered SHA-256 is
  `eec91bc004aafa630db922fa1a16cf538cb02698a9ebcc3ad00dc4c8973e2381`.
- The canonical Podman wrapper and project-mounted Devtool runner now accept
  the persistent `/workspace/state/build` path, and the static wrapper tests
  pass. Mac Podman applied the complete recipe patch graph: `do_patch`
  104/104. The development VM has `selinux=0` so Yocto's standard xattr copy
  remains available; the target image's SELinux policy was not changed.

### Inferences / UNKNOWN

- The Mac source/patch/do_patch chain is now PASS using one persistent
  container and one state bind. Mini PC compile/image/runtime gates remain
  authoritative.
- UNKNOWN: whether `draw2` identifies a production shaded draw or explains
  the black QMP region.

### Check / Act

- **Check:** Devtool commit, generated patch, byte identity, patch order, Mac
  `do_patch`, and wrapper tests are recorded.
- **Act:** commit the canonical patch and evidence, send one bundle to the
  fixed Mini PC receiver, and run the progressive build/QMP loop.

## Entry 11 — draw2 runtime boundary on the latest image (2026-09-10)

### Facts

- The bundle for project commit
  `2b90c98853da81ff49ec327215b5823d0e9b610a` reached the fixed receiver.
  Mini PC metadata, `filament-vk:do_patch` (104/104), `do_compile`
  (1965/1965), and the full image (11748/11748) passed. The final rootfs
  SHA-256 is `56ee76d03e78c5573c3213bdb848c4394063eec716b444b0bd63cb726a5596c2`.
- The first QEMU start failed because its long run-directory name made the
  QMP Unix socket path exceed the path-length limit. The exact runqemu PID was
  stopped after command-line identity verification; socket and target
  residuals were cleared. This is a harness failure, not a 3D verdict.
- A short fixed evidence child `d2` then passed preflight and QMP greeting.
  The first owner-isolation launch did not produce its expected guest
  log/backup and was not treated as valid runtime evidence. A direct guest
  launch proved the app, AOT, Planetarium entries, and Vulkan backend; the
  formal sample is therefore normal grpc owner.
- Formal QMP-only evidence shows the Fluorite HUD/metrics and a black
  `[300,80,620,360]` candidate in all 12 frames (`0/223200`). The PPM
  SHA-256 is `939afcc20be4559909f14cfc187c6456d70cf044754def012bbfbc80c279c4ff`;
  the region SHA-256 is
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- Runtime counts are scene-add `1`, camera `14`, `FRAME_BEGIN` `5`, submit
  `2`, present begin `1`, target render pass begin `9`, exact `TARGET_DRAW`
  `0`, `TARGET_DRAW2` `24`, `NATIVE_READBACK_RESULT` `0`, and `SIGSEGV` `0`.
  The final target trace includes non-null-color-view offscreen draws, a
  non-swapchain 1280x800 draw (`index_count=36`), and a final swapchain
  1280x800 draw (`index_count=3`).
- Negotiated QMP quit and residual cleanup passed with zero targets and zero
  sockets. The Mac-derived QMP video SHA-256 is
  `7af4cb94c0dd706583eb2c48f90eb0a5247dec575dfe7d4857cdc52aa183d627`.

### Inferences / UNKNOWN

- 2D HUD and normal-grpc Vulkan frame/submit/present are proven; production
  shaded 3D remains FAIL. `draw2` is reached, but the evidence does not yet
  show the non-swapchain target's pixels or prove that the final swapchain
  primitive samples the Sequoia output.
- UNKNOWN: target contents before swapchain, target-to-entity/material
  identity, missing readback result, owner-isolated full-shaded result, and
  combined 2D+3D/route behavior.

### Check / Act

- **Check:** QMP-only image/video material, runtime log, selected target
  analysis, failed startup evidence, hashes, and cleanup evidence are kept in
  the fixed QEMU evidence root by role path.
- **Act:** choose the smallest target-content/readback probe without changing
  rendering behavior. The socket path defect is tracked separately in
  `FLR-0063`.

## Entry 12 — production target-content probe generated (2026-09-10)

### Facts

- Static source and runtime review identifies the 1024x1024 `format=124`
  passes as D16 depth/shadow targets. The main production color target is the
  non-swapchain 1280x800 RGBA16F target. The prior depth-target `color_view`
  lines are not proof that the main shaded color attachment is missing.
- The remaining hypotheses are: main target black before composition,
  nonblack main target lost at swapchain handoff, or readback synchronization/
  callback incomplete. No rendering behavior was changed.
- A one-shot environment-gated `FLR0026_TARGET_PROBE` was added through the
  persistent Mac Podman Devtool source. At the end of the 1280x800 RGBA16F
  render pass it reads the target once before swapchain composition and logs
  non-zero pixel count and a half-word sum.
- The Devtool source commit is
  `42509d76592dde7c6873d357d35bac4a7d0d4457` with the privacy-allowed
  `Codex Devtool <codex-devtool@localhost>` identity. Official Devtool
  generated and the Canonical layer registered
  `0173-filament-vulkan-target-content-probe-devtool.patch`; its generated and
  registered SHA-256 is
  `7aed257f3f29dce4a5797862af0879cfa04265c5ab053b061371501f1dd2c04f`.
- Mac Podman `filament-vk:do_patch` passed 104/104, and the final repository
  verification passed. The layer baseline lock is updated to 268 files.

### Inferences / UNKNOWN

- The probe separates light/material/main-target failure from the final
  composition boundary with one bounded runtime sample.
- UNKNOWN: the probe result and callback behavior on the authoritative Mini
  image; full shaded 3D is still not proven.

### Check / Act

- **Check:** Devtool edit/commit/patch generation, privacy correction, byte
  identity, Mac patch gate, and repository checks are recorded. QEMU has not
  yet been started for this probe.
- **Act:** commit, bundle to the fixed Mini receiver, pass progressive Mini
  gates, then run one short-path QEMU with `FLR0026_TARGET_PROBE=1` and retain
  QMP/runtime/probe/cleanup evidence.

## Entry 13 — Mini compile boundary and official fix (2026-09-10)

### Facts

- The `a6d6756` bundle reached the fixed receiver. Mini metadata and the
  effective 0173 patch series passed, including `filament-vk:do_patch` 104/104.
- Mini `do_compile` stopped before image generation. The first error in the
  task log is `VulkanDriver.cpp:1841`: the target probe callback used local
  `PIXELS` without capturing it. This is a compile-only diagnostic-code error,
  not evidence about light behavior or runtime pixels.
- The same Mac Devtool source was updated with the minimal capture/rename fix
  in source commit `9acfd304e`. Official Devtool generated the incremental
  patch registered as
  `0174-filament-vulkan-target-content-probe-compile-fix-devtool.patch`; its
  generated/registered SHA-256 is
  `b65aa258ffd2d7fa4bca5c66c5c0eb5fdce8778891c9f148cceaddb33519fb69`.
- Mac Podman applied the complete 0173+0174 series with `do_patch` 104/104
  PASS. The fix changes only diagnostic callback capture and local naming.

### Inferences / UNKNOWN

- The 0173 probe design remains untested at runtime until the corrected image
  compiles. UNKNOWN: full-image result and target probe result.

### Check / Act

- **Check:** Mini compile error, Devtool source fix, official 0174 patch
  generation/identity, and Mac patch gate are recorded. No QEMU was started
  after the compile failure.
- **Act:** commit, handoff the updated bundle to the same receiver/build, rerun
  `do_compile`, then full image and one short-path QEMU after compile success.

## Handoff

FLR-0061 established the owner-isolated draw/pipeline/submit/present baseline.
This ticket owns only the missing mapping from production shaded draw execution
to a nonblack output target or native readback result. Mac-side source and
recipe patch generation is now proven; Mini PC authoritative build and runtime
evidence remain open.

## Entry 14 — target readback synchronization boundary

- QMP-only capture still proves the 2D HUD/CPU/FPS layer, but the central
  candidate 3D region is black in all 12 frames (`0/223200`). The application
  exits cleanly and QMP cleanup leaves no residual process.
- The target probe reaches queue submit success and then waits at the
  readback fence without producing a target or native readback result.
  Therefore the current evidence points first to the diagnostic readback
  synchronization boundary, not to a proven light failure.
- Devtool source commit `25510190f491841f5c180695dfa54b985683e7dc` generated
  the byte-registered `0175-filament-vulkan-target-probe-queue-sync-devtool.patch`
  (SHA-256 `0477aae55ef36c69d26f031d2bf40998b5d2fbcf278edd181bb88387e96f3e27`).
  It adds an environment-gated graphics-queue idle diagnostic immediately
  before the target readback.
- The referenced older trace patch was restored to the canonical `files/`
  directory with generated/registered SHA-256
  `ce1e38fc7d6fbf7199c756851f387f1f0744894393ce0086e16ebc8e216a1060`.
  Devtool transient outputs were quarantined in the fixed Podman state, not
  included in the canonical layer.

### Current decision

Keep light/material and final composition as competing hypotheses. Build 0175
on the Mini PC and obtain a completed target pixel result before changing
rendering or light behavior.

## Entry 15 — duplicate audit and compile gate

- A byte-level audit found one exact duplicate pair, `0025` and `0027`, but
  source-order analysis showed a redundant `0025`/`0026` toggle cycle between
  the mock-enabled `0022` and the final native-only `0027` state.
- The corrected cleanup removes both `0025` and `0026`, retains `0027`, and
  keeps the final switch value unchanged. The canonical layer now has 267
  files and the baseline lock was refreshed accordingly.
- The first cleanup bundle `d125dc6` exposed the stale toggle dependency:
  Mini do_patch failed at `0026` after `do_clean`/`do_unpack` because `0022`
  had already set the switch to `true`. This is recorded as a process finding,
  not treated as a new rendering failure.
- Bundle `7378065c` reached the fixed Mini receiver before cleanup correction.
  Its metadata included 0175, `filament-vk:do_patch` passed 104/104, and
  `filament-vk:do_compile` passed 1965/1965 in the same build/TMPDIR. No QEMU
  was started before these gates.

### Current decision

The diagnostic source compiles on the authoritative target. Re-send the
corrected toggle cleanup, pass the app recipe do_patch gate from a clean task
state, then build the full image and run one QMP-only probe before changing
light or material behavior.

## Iteration 16 — authoritative 0175 probe run (2026-09-10)

### Facts

- Corrected commit `49089ba` was delivered to the fixed Mini receiver by one
  bundle. The corrected app patch graph passed `do_patch` 104/104, and the
  same fixed build/TMPDIR passed the full image gate 11748/11748 with no
  errors. The redundant `0025`/`0026` toggle removal therefore did not break
  the application recipe or image.
- The explicit guest launch had one `flutter-auto` and one
  `agl-compositor`. QMP captured 12 frames; the final central candidate region
  `[300,80,620,360]` changed `0/223200` pixels against black. Final PPM
  SHA-256: `19ffbe0a3886a7de2e450a44eef3e6629c003ad44cf7641e468f8887665f2ead`.
- Runtime reached model completion, camera application, depth/shadow passes,
  the non-swapchain 1280x800 target, `TARGET_DRAW2`, queue submit result `0`,
  and fence status `1`. It then stopped at
  `TARGET_PROBE_QUEUE_IDLE_BEGIN`; no queue-idle completion, target pixel
  result, or native readback result was emitted.
- The process stayed alive with 38 threads. gdb showed the lavapipe/llvmpipe
  Vulkan workers waiting in driver futex paths, with no SIGSEGV. Runtime-log
  SHA-256: `73909eedbb17749eaf0a8c5fcece20fe402ab8d19fcd7b3d9df327405bf6252c`.
  gdb SHA-256: `17c78a171a6bd4769d53ef058e67b506cebff68e5d720a4ea894607c98c0031e`.
- Exact guest-PID termination, QMP quit, and residual cleanup all passed;
  `residual_targets=0 residual_qmp=0`.

### Inferences / Hypotheses

- The duplicate cleanup is packaging/reproducibility work, not a rendering
  regression: the final switch state is unchanged and the authoritative build
  passed.
- This run cannot classify the light result. Light/shadow setup, draw2, and
  queue submit are active before the diagnostic stop, but the target sample is
  never completed.
- 0175 is not a safe production-pixel verdict in this form: its queue-idle
  diagnostic can block the rendering/readback path before it reports pixels.
  The current black frame is therefore evidence of a diagnostic-side blocking
  boundary, not evidence that lighting alone made the vehicle black.
- The prior cube-plus-HUD frame was a self-made native-above-parent A/B, while
  the prior Sequoia proof was model-only. Those are not proof of combined
  full-shaded production 2D+3D, so the current state is not established as a
  regression from a previously working production-combined path.

### UNKNOWN / Act

- UNKNOWN: full-shaded target contents without the blocking 0175 operation.
- UNKNOWN: actual light/material contribution and final parent/native alpha
  composition in the production path.
- Do not change light or material behavior yet. Generate the next diagnostic
  only through the persistent Mac Devtool source and official Devtool patch
  output, making it non-blocking or timeout-bounded. Apply `do_patch`, build,
  and validate on the Mini PC; its target-side task is authoritative because
  the Mac `EXTERNALSRC` workspace has no executable `do_patch` task.
- Keep this ticket In Progress and repeat one bundle → progressive Mini gates
  → one QMP-only capture before opening a separate lighting/composition ticket.
