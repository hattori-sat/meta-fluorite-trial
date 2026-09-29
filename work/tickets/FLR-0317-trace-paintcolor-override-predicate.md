# FLR-0317 — reproduce the historical tail-light positive baseline

- Status: Waiting
- Priority: High
- Owner: Filament material predicate / production Sequoia render roles
- Created: 2026-09-25
- Predecessor: [FLR-0316](FLR-0316-inspect-paintcolor-material-and-selfmade-light.md)
- Working log: `work/logs/2026-09-25-flr0317.md`

## Objective

Reproduce and compare the historical Sequoia result where the vehicle
silhouette was black but red tail-light pixels were visible. This is the
correct first boundary before changing Light or `PaintColor`: a tail-light
emissive/texture output should not require scene Light contribution. The
FLR-0316 `baseColorFactor` probe is held and is not a tail-light fix.

## Success criteria

- The historical tail-light-positive image, rootfs, source/patch identity,
  model limit, camera, Light flags, and runtime markers are recorded.
- One no-source-change run reproduces the historical launch profile as closely
  as possible on the fixed Mini build/TMPDIR.
- The same fixed Mini build/TMPDIR and one QMP-only runtime are used.
- The result states whether the next issue is material parameter application,
  texture/sampler content, camera/framing, or target composition.
- QMP screenshot/video, bounded runtime log, hashes, and teardown are retained.

## Facts / hypotheses / UNKNOWN

### Facts

- The historical `no-readback-60s.png` shows a black vehicle silhouette and
  red tail-light pixels.
- FLR-0316 shows no vehicle or tail-light pixels, while the HUD remains
  visible.
- The first FLR-0317 historical-profile run was not judgeable: it reached
  repeated `BEGIN_FRAME_FALSE` and emitted no Sequoia asset/material/Scene
  markers. It was stopped without treating the missing vehicle pixels as a
  material result.
- With `FLR0026_TREAT_UNLINKED_FENCE_READY=1`, the frame-ready boundary was
  restored: `BEGIN_FRAME_TRUE=23`, `BEGIN_FRAME_FALSE=0`, one asset load, two
  Scene add completions, 34 renderable markers, 42 material markers, and 23
  draw submits. The initial camera was `(5,0,-5)`, so that frame was not used
  for vehicle appearance judgment.
- With the same frame-ready setup and
  `FLR0285_NATIVE_PRODUCTION_CAMERA=wide`, the effective camera was
  consistently `(800,450,800)` at a 1280x800 viewport. The run reached one
  asset load, two Scene add completions, 34 renderable markers, 42 material
  markers, 20 draw submits, and 20 `BEGIN_FRAME_TRUE` markers with zero
  `BEGIN_FRAME_FALSE` markers. Vulkan submit/present also completed.
- The wide-camera QMP frame shows the HUD and CPU/GPU graph, but no vehicle
  or red tail-light pixels. Its production ROI `(440,220,400,360)` is
  `0/144000` changed/chromatic/edge pixels with luma `[0,0]`; the HUD ROI is
  `2990` changed and `2845` chromatic pixels.
- FLR-0316 loaded and added the Sequoia asset and enumerated body entity 336
  primitive 0 as `PaintColor` with `baseColorFactor` in the parameter list.
- The FLR-0316 environment flag reached the child process and the compiled
  binary contains the diagnostic marker.
- The branch marker remained zero and the production ROI remained uniform
  black while HUD pixels remained present.

### Hypotheses

1. The current production GLB material/texture/sampler resource path is not
   producing the tail-light pixels, independently of scene Light. This is
   now the leading hypothesis because the frame-ready, camera, asset, Scene,
   material, submit, and HUD paths all pass while the production ROI remains
   black.
2. A production draw/material pipeline condition rejects or discards the
   vehicle primitives after material creation. This would explain why
   renderable/material markers exist without vehicle pixels.
3. The current image/profile still differs from the historical
   tail-light-positive condition at an unobserved asset/resource or
   patch-stack boundary. This remains possible until the historical image and
   current GLB material/texture inventory are compared directly.

### UNKNOWN

- The exact historical launch/profile difference that restores red tail-light
  pixels.
- Which current material primitive or sampler provides the tail-light output.

## Plan / PDCA

### Plan

1. Map the historical positive run and current FLR-0316 inputs without source
   edits.
2. Run the closest no-source-change historical profile on the fixed Mini
   receiver/build/TMPDIR.
3. Only after the first difference is evidenced, add one material/resource
   probe through the persistent Mac Devtool source.

### Do

- The FLR-0317 predicate-only source commit and generated patch are held; the
  patch is not registered in the canonical recipe and was not built.
- Reused the FLR-0316 image with the historical FLR-0070-style single-POINT
  profile: skip GUID 126, limit one light, and enable the native light
  operation trace. No source patch or image rebuild was used for this run.
- Repeated the same profile with the explicit frame-ready treatment, first
  at the default camera and then with the wide production camera. No source
  patch or image rebuild was used.

### Check

- The QMP frame SHA-256 is
  `b60520d20c999ff90683bade144af631918086621b6a0b13d0247b5bec46b270`.
- The production ROI `(440,220,400,360)` remained uniform black: `0/144000`
  changed, chromatic, and edge pixels, luma `[0,0]`. HUD remained visible with
  `2990` changed and `2845` chromatic pixels.
- The bounded runtime slice reached repeated
  `FLUORITE_VIEWTARGET_BEGIN_FRAME_FALSE` and did not reach the Sequoia asset,
  material, or Scene-stage markers. This is an invalid reproduction of the
  historical tail-light-positive render, not evidence against the tail-light
  material itself.
- QMP video converted on the Mac has PNG SHA-256
  `bbc23c23c0defcf02be940ff1641999e5b8e539d3ff0ed01d68732e897f6078a` and MP4
  SHA-256 `ac24f1c454d998036bdcd0413273063fb9266835555a857df1c393385105347c`.
- QMP quit was negotiated and cleanup found zero residual targets and no QMP
  socket.
- The frame-ready/default-camera QMP frame SHA-256 is
  `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`.
  It showed a black polygon on white and was rejected for appearance judgment
  because the effective camera was `(5,0,-5)`.
- The frame-ready/wide-camera QMP PPM SHA-256 is
  `19a9f81da507a159f9947d04105c2267fd825d40e82bd4562b03895e37cd5931`.
  The Mac-converted PNG SHA-256 is
  `68128f4c2002840e30257a7ae283e423c018c866b3f4af062584ced259881be6` and
  the MP4 SHA-256 is
  `cca36b5387b8aae26122db405e1bb22f5fb6046d56d0542097827e6718f53830`.
- The wide-camera QMP run was terminated through QMP with negotiated quit;
  cleanup reported zero residual targets and zero residual QMP sockets.
- Source comparison found that the historical render path did not add the
  primary model to the Scene, while current source commit `d138e54` adds both
  the primary and secondary model instances. The current run consequently
  reports two Scene additions, 34 renderables, and 42 materials versus the
  historical 25 entities and 14 renderables. This is a concrete alternative
  to a Light-only explanation, but it has not yet been runtime-tested.

### Act

- Do not change Light or force body `PaintColor` in this ticket. The next
  independently verifiable unit is [FLR-0318](FLR-0318-ab-primary-secondary-scene-attachment.md),
  which tests whether duplicate primary/secondary Scene attachment hides the
  vehicle and tail-light pixels. Only after that A/B is rejected should the
  material texture/sampler resource path be probed.
