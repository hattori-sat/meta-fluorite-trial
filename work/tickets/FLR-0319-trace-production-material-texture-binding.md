# FLR-0319 — trace production material/texture binding

- Status: Done
- Priority: High
- Owner: GLB resource loader / Filament material and texture binding roles
- Created: 2026-09-25
- Predecessor: [FLR-0318](FLR-0318-ab-primary-secondary-scene-attachment.md)
- Working log: `work/logs/2026-09-25-flr0319.md`

## Objective

Identify why the production `sequoia_ngp.glb` path produces no vehicle or red
tail-light pixels even when frame readiness, camera, asset load, Scene
attachment, material creation, draw submit, and present all pass. Compare the
GLB's static material/texture structure with the runtime material and resource
binding boundary. Do not change Light or force body color in this unit.

## Success criteria

- Static inventory records the production GLB material, primitive, texture,
  sampler, image, MIME, and emissive/base-color relationships using role paths
  only.
- One minimal diagnostic source change, if required, is generated through the
  persistent Mac Devtool workspace and official `devtool finish` flow.
- Mini `do_patch`, compile, full image, and artifact hashes are recorded.
- One QMP-only runtime records bounded material/resource markers and native/HUD
  ROI results; the existing red-tail-light-positive evidence is the comparison
  baseline.
- QMP teardown and residual-process checks pass.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0049 proves the same production asset path once produced a black vehicle
  silhouette with red tail-light pixels.
- FLR-0317 proves current frame-ready wide-camera production remains entirely
  black in the native ROI.
- FLR-0318 proves skipping the current primary Scene attachment does not change
  that result; secondary model/material setup still completes.
- Runtime material names include `PaintColor`, `HeadLights`, `Glass`,
  `BlackPlastic`, `Chrome`, and `SilverPlastic`; there is no material named
  `TailLight` in the bounded trace.
- The source GLB inventory is stable and the deployed Mini rootfs contains the
  same asset bytes: SHA-256
  `cde9efd067a75c1f5b99b8fb529b5bb4636956193188bd15add3bccc349109ec`,
  13,671,064 bytes.
- The GLB contains an embedded PNG image named `HeadLights_Emission`, mapped
  through the `HeadLights` material's emissive texture slot with emissive
  factor `[1,1,1]`. The extracted image is 1024x1024 and visibly contains the
  red tail-light bands; its derived-artifact SHA-256 is
  `87fa31842d2e6e97aeefdb29de38e8e070619607ef93fda071915d6856362546`.
- Therefore the historical red tail-light pixels are explained by asset data
  that exists independently of a scene Light. The current zero native ROI is
  a runtime material/texture/output-boundary problem, not evidence that a new
  Light is required to create the red pixels.
- Filament gltfio 1.65.4 source confirms that `emissiveIndex` is an integer UV
  selector, not a sampler. The actual texture path is
  `AssetLoader::createMaterialInstance` → `addTextureBinding(...,
  "emissiveMap", ...)` → `FFilamentAsset::applyTextureBinding` →
  `MaterialInstance::setParameter("emissiveMap", texture, sampler)`.
- Fluorite's current source waits for `asyncGetLoadProgress() == 1.0` before
  dispatching the queued model to Scene. The current bounded log therefore
  proves model/material setup and frame/present, but does not expose whether
  the internal gltfio dependency graph applied the texture binding.

### Hypotheses and predictions

1. The tail-light is represented by an emissive or base-color texture whose
   image/sampler is missing or not bound. A runtime binding probe should show
   a missing resource, zero/invalid texture, or an unexpected parameter path.
2. The GLB contains the tail-light data, but the Filament material pipeline
   discards it after material creation. Static resources will be complete while
   runtime binding markers are complete and the native ROI remains black.
3. The red pixels in the historical run came from a different asset or image
   revision. Static checksums or embedded JSON will differ. This hypothesis is
   rejected: the source and deployed asset SHA-256 match, and the deployed
   asset contains the red `HeadLights_Emission` image.

## Plan / PDCA

### Plan

1. Parse the deployed/source GLB without mutating it and record its resource
   inventory and checksum.
2. Inspect the existing loader and material APIs to choose one safe runtime
   boundary; do not log every frame or every resource.
3. Add one opt-in HeadLights parameter/resource-contract probe, then use the
   fixed Mac→Mini→QMP loop only if the static evidence leaves the runtime
   binding boundary unknown.

### Do

- Parsed the source/deployed GLB and confirmed identical asset bytes and an
  embedded red `HeadLights_Emission` image.
- Inspected the actual Filament 1.65.4 headers and gltfio source. The observed
  `emissiveIndex sampler=false` is the expected integer UV-index contract, not
  evidence of a missing sampler.
- Reused the existing FLR-0318 image and TMPDIR. One QEMU with 4096 MiB was
  started, guest SSH launched the existing diagnostic profile, and one QMP
  screenshot plus bounded runtime slices were captured. No source patch or
  rebuild was performed for this probe.

### Check

- Runtime recorded `HeadLights` on entity 358 primitive 2 with
  `parameter_count=40`, and its parameter list included
  `emissiveIndex sampler=false`; the same material reached repeated
  `BEGIN_FRAME_TRUE` and queue-present markers.
- QMP PPM SHA-256:
  `5251254338d003ee7d70c4d8abee6040858bf7cac6b60a1d3461853fb323f9ed`.
  Native ROI `(440,220,400,360)` remained `0/144000` with luma `[0,0]`;
  HUD ROI remained `2990` changed and `2845` chromatic.
- The bounded targeted runtime slice SHA-256 is
  `84936ab17f74ce74540121345ee14075b3c4d8b9d113f909f0ceb1749dbc148b`;
  the full parameter slice SHA-256 is
  `a3b697102ce1a2cd4822f9bf5ad962aca2a3bbd4c5c0d1c77463202bdbd5f51f`.
- The first nested-SSH launch attempt failed before starting the app because
  shell quoting expanded guest paths at the wrong layer. The corrected
  base64-delivered guest command launched successfully; both the failed
  attempt and correction are recorded in the working log.
- QMP quit and residual-target cleanup passed.

### Act

The static asset and the Filament parameter contract are valid, but the actual
`emissiveMap` binding is internal to gltfio and is not observable from the
existing Fluorite marker set. Do not add a Light or force a body color. Close
this ticket and let FLR-0320 instrument only the gltfio texture
readiness/binding completion boundary.

## Visual evidence

QMP framebuffer artifact: `$EVIDENCE_ROOT/FLR-0319/flr0319-headlights.ppm`.
The screenshot shows the HUD and CPU/GPU graph but no vehicle or tail-light
pixels. The source/deployed GLB's derived `HeadLights_Emission` image visibly
contains the red tail-light bands; it is a resource artifact, not a QMP
acceptance frame.
