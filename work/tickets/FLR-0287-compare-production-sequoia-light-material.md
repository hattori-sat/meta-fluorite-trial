# FLR-0287 — compare production Sequoia camera, material, and light visibility

- Status: Waiting
- Priority: High
- Owner: production scene camera/material/light runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0286](FLR-0286-reproduce-known-good-combined-sequoia-hud.md)
- Working log: `work/logs/2026-09-25-flr0286.md`

## Objective

Use the successful FLR-0286 self-made LIT fixture as the control and identify
the first production Sequoia stage that diverges. The purpose is to restore
the known HUD plus vehicle/light condition, not to add another global Vulkan,
Wayland, or SHM diagnostic.

## Acceptance gate

One QMP-only 1280x800 frame from the fixed Mini image must show, at the same
time:

1. Flutter HUD pixels including CPU/FPS/Scenes;
2. recognizable Sequoia geometry in the native region;
3. non-grayscale vehicle/light pixels, with a red-tail candidate when the
   selected asset contains it;
4. runtime evidence for camera selection, Sequoia model selection/scene-add,
   light attachment, frame, and present;
5. one `flutter-auto`, one QEMU, and clean QMP teardown with zero residuals.

## Facts

- FLR-0286 proves the fixed QEMU/Wayland/QMP path can compose HUD and colored
  Filament 3D, and the opt-in LIT fixture builds and renders.
- The production Sequoia path has previously reached model load, scene-add,
  draw, and present while the QMP native region stayed grayscale or black.
- The current image is built from receiver commit
  `e70932f9ac6587a9fab93165658c187cb0ce23b2`; the production path is
  unchanged by the opt-in fixture-light patch.

## Hypotheses

1. Camera framing may place Sequoia outside the visible native ROI.
2. The production material/resource binding may produce geometry without
   chromatic output, while the self-made material contract is valid.
3. The production light attachment/environment path may not reach the model,
   even though the explicit fixture SUN path does.
4. Surface composition is a lower-priority hypothesis because the same image
   already composes the lit fixture with the HUD.

## Verification plan

- Reuse the existing Mini receiver, build, TMPDIR, 4096 MiB QEMU profile, and
  one-QEMU harness. Do not create another image, receiver, or TMPDIR.
- Run the production Sequoia control with an explicit wide camera and one
  model match. Keep normal production lighting first; do not mix SHM cube,
  opaque-surface, place-below, or readback controls.
- Save the guest log before teardown, waiting for camera/model/light markers
  rather than copying at a fixed early delay.
- Capture one QMP frame and a bounded QMP video, analyze the same native/HUD
  ROIs as FLR-0286, and record the first missing marker.
- Only after the first divergence is identified, open a separate change ticket
  for one minimal patch.

## Unknowns

- Whether the currently selected Sequoia camera frames the vehicle in the
  1280x800 native target.
- Whether the production model's material is lit, unlit, or missing its
  resource bindings at draw time.
- Whether the production direct/indirect light entities are attached to the
  same scene that owns the Sequoia renderables.

## 2026-09-25 production control result

The fixed image at rootfs SHA-256
`08ee47d01cced5139a724284462c6b3f23bf687c05a342202282a34122a7d65d` was
run once with 4096 MiB QEMU. The launch selected one
`assets/models/sequoia_ngp.glb` model, requested the explicit `wide` camera,
and kept normal production lighting. The runtime reached:

- camera contract `eye=(800,450,800) target=(0,0,-80) viewport=(0,0,1280,800)`;
- model selection, asset load, 12 renderable entities, and scene-add;
- `FLR0280_MODEL_MATERIAL` records for `PaintColor`, `HeadLights`, `Glass`,
  and other materials with `present=true`, `shading=1`, and color writes;
- draw submit/end and the normal present path, with no bounded error/OOM/
  SIGSEGV markers.

The QMP-only frame is retained at
`/mnt/yocto/evidence/flr0287-0001/production-sequoia.ppm`, SHA-256
`2e2447d7e2c799064e434db1069a8679a760ff6a5ac1e400c4ea284fb0085a22`.
The bounded 12-frame video is under
`/mnt/yocto/evidence/flr0287-0001/production-sequoia-video/`.

ROI analysis is decisive:

- native `(440,220,400,360)`: `0/144000` changed, `0/144000` chromatic,
  luma `[0,0]`, geometry indicator absent;
- HUD `(1120,0,160,80)`: `2845` chromatic pixels and geometry indicator
  present.

The full saved runtime log SHA-256 is
`56de7b4a8c36f41fac3bedabb6b5b6c38cef50cddd5398fd4a423b2625013568`; the
bounded selected-marker slice SHA-256 is
`1c8b065bce0554eab072b586fdd1856169395fb164d675d5b0b3a558ec9b0519`.
QMP teardown passed with zero residual QEMU/QMP targets.

### Decision

Camera selection, asset loading, material presence, scene ownership, HUD
composition, and generic present completion are not sufficient to explain the
black native ROI. The next controlled boundary is explicit production-light
attachment in the existing native diagnostic scene. No production patch is
justified yet.
