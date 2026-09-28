# FLR-0307 — probe production fragment output versus target handoff

- Status: Waiting
- Priority: High
- Owner: production Sequoia fragment/output and target-boundary roles
- Created: 2026-09-25
- Predecessor: [FLR-0306](FLR-0306-probe-production-material-output.md)
- Working log: `work/logs/2026-09-25-flr0307.md`

## Objective

Determine whether a production Sequoia primitive can emit visible fragments
when its material path is reduced to a controlled diagnostic, or whether the
render target/handoff remains zero even for a known-output draw.

## Facts

- FLR-0304: effective camera and culling A/B did not change the native ROI.
- FLR-0305: a self-made SUN reached the production default Scene but did not
  change the native ROI.
- FLR-0306: production materials are present and write-enabled; a sampled
  `base_lit_opaque` material exposes base-color and emissive parameters, while
  draw/present markers remain positive and native ROI is `0/144000`.
- FLR-0251/FLR-0286: the same QMP composition path can display HUD plus a
  self-made native 3D fixture, including a lit fixture.
- FLR-0070 p9: a historical combined HUD plus Sequoia/color frame exists and
  is the visual discriminator, but its timing/trace side effect was not
  reproduced on the later image.

## Hypotheses

1. A one-primitive emissive-parameter diagnostic override will produce native
   pixels. Prediction: setting the existing `emissiveFactor` to a saturated
   color makes the native ROI nonzero while camera, Scene, draw, and present
   markers remain stable; this localizes the failure to the production PBR
   material evaluation path.
2. The override will still produce zero native pixels. Prediction: a known
   color-output draw also disappears, moving the boundary to render-target
   selection, attachment, or target-to-swapchain handoff.
3. The override changes timing but not pixels. Prediction: a timing-only
   control reproduces the same result; the previous FLR-0070 observation is
   classified as a diagnostic side effect rather than a fix.

## Scope and acceptance

- Reuse the fixed Devtool source workspace, Mini receiver/build/TMPDIR, one
  QEMU, and QMP-only capture.
- Use one opt-in diagnostic material/output control at a time; do not change
  camera, culling, Wayland stacking, or production defaults.
- Require one settled 1280x800 QMP frame, native/HUD ROI analysis, bounded
  runtime markers, exact image identity, and clean QMP teardown.
- Do not call the vehicle visible from entity/material metadata alone.

## Plan / PDCA

### Plan

The existing `RenderableManager::setMaterialInstanceAt` API can replace a
primitive material, but that would require a new material lifetime and would
mix material replacement with output diagnosis. The smaller first discriminator
is to use the existing `MaterialInstance::setParameter` seam on one selected
production primitive, guarded by `Material::hasParameter("emissiveFactor")`,
and set only that existing parameter when an opt-in environment variable is
present. The retained runtime material log confirms `emissiveFactor` is among
the production parameter names.

### Do

Completed the source-side discriminator in the persistent Mac Devtool source.
The source commit is `9dc263b894a1f89b7ccde6668f24dafa862a6066`. The official
Devtool rebase helper generated exactly one patch and registered it in the
existing `flutter-auto_2.0.bbappend`:

- Patch: `0307-flr0307-probe-production-emissive-output-devtool.patch`
- Patch SHA-256: `73c2251f524654040077c702e73f868acbc5a3c1a092197f14130c9bceb63e9f`
- Registration: `patchdir=ivi-homescreen-plugins`
- Privacy check: `PASS`

The generated patch is unchanged from Devtool output. The opt-in control is
inactive unless `FLR0307_PRODUCTION_EMISSIVE_OVERRIDE` is present.

The fixed Mini receiver advanced to `ee395aefccf3076d8fd87f75ada0e1b6783809d8`
through the Git bundle flow. The recipe-clean patch gate, `flutter-auto`
compile, and complete `agl-ivi-image-flutter` build all passed. The new image
artifacts were:

- rootfs SHA-256: `55338735a3c7b227facf9edbdc010b11166cd27cf9e00433f22f472c4a316f25`
- qemuboot SHA-256: `20a5a18b3c73504a8f73f58ff44e0219110e1d9edf245f68accb579381a61e64`
- kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`

QMP evidence is under the fixed Mini role path
`$EVIDENCE_ROOT/flr0307-0001/emissive/`. The first `serial-login` attempt only
sent the command and did not prove execution; it produced an all-black frame
and no app log. That failed launch is retained as a process mistake. The
corrected `serial-exec` launch passed its completion marker and started
`flutter-auto` as PID 650.

The corrected runtime then reached ViewTarget creation, selected
`sequoia_ngp.glb`, installed the FLR-0305 SUN, and submitted/presented Vulkan
frames. However, before any production asset/material/draw marker or the
FLR-0307 override marker, the guest journal recorded a page fault in
`FEngine::loop` (PID 692): `#PF`, `Oops: 0000 [#1]`. The parent `flutter-auto`
remained alive but the engine loop stopped; no OOM or coredump was recorded.
The settled QMP frame therefore has native ROI `0/144000` and no chromatic
pixels. The same frame is visually a white surround with a black polygon and
does not prove a vehicle. QMP video frames 0 and 7 are byte-identical.

The QMP run ended with negotiated quit and zero residual QEMU/runqemu/
flutter-auto processes. The engine page fault is split to FLR-0308; this ticket
does not claim that emissive output or production 3D has been disproved.

### Check

Completed the Mini `do_patch`, compile, image build, and one-variable QMP run.
The QMP frame SHA-256 is
`f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
The FLR-0307 override was not reached because the engine fault occurred first.

### Act

The output boundary remains UNKNOWN because the engine loop fault precedes
material setup. FLR-0308 now owns fault reproduction and a bounded model-load
control. After that fault boundary is removed or explained, return to this
ticket's emissive/material discriminator; do not infer a light failure from
this run.
