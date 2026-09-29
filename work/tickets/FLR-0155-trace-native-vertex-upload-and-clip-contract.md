# FLR-0155 — trace native vertex upload and clip contract

- Status: Done (boundary classification)
- Priority: High
- Owner: Filament vertex/index upload, Vulkan binding, native fixture lifecycle
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0154](FLR-0154-isolate-native-materialbuilder-color-output.md), [FLR-0148](FLR-0148-reconcile-effective-viewtarget-api-contract.md)
- Working log: `work/logs/2026-09-14-flr0155.md`
- Runtime command: `work/commands/FLR-0155-fixture-entry-buffer-boundary.run`

## Work unit

Collect one bounded source/runtime trace for the current native minimal fixture:
fixture entry, vertex/index CPU upload, Vulkan buffer handles and sizes,
primitive binding, indexed draw arguments, and the vertex shader's clip-space
contract. Do not change geometry, camera, compositor, material behavior, or
the QEMU image until this boundary is evidenced.

## Problem

The current Mini image reaches a valid native renderable contract and an
indexed draw admission, but the fixed 3D QMP candidate is black while the 2D
HUD is visible. A hardcoded-material-color attempt also remained black, but its
source branch did not emit a runtime entry marker. Therefore the current
evidence does not yet distinguish an unexecuted diagnostic branch, empty or
misbound vertex/index buffers, an all-clipped vertex transform, or target
content behavior.

## Success criteria

- [x] Record the current source/API path from `setBufferAt` and `setBuffer`
  through Vulkan upload and `bindRenderPrimitive`.
- [x] Add only environment-gated diagnostic markers through the official Mac
  Devtool source flow, if source tracing is required.
- [x] Verify on Mini with the fixed build/TMPDIR and one QMP-first QEMU run;
  retain serial, QMP screenshot, and teardown evidence.
- [x] Classify the first missing boundary as fixture entry, upload/binding,
  vertex clip-space, fragment/attachment, or readback.
- [x] A concrete Fluorite fixture defect is proven and split to
  [FLR-0156](FLR-0156-restore-pure-fixture-camera-projection.md), which will
  patch the camera configuration through Mac Devtool.

## Facts

- The native geometry contract reports 8 vertices, 36 indices, one primitive,
  a bound material, and a renderable in the scene.
- The runtime state trace reports a 1280x800 viewport/scissor, color-write
  mask 15, valid shader/layout and vertex-input state, indexed draw count 36,
  queue present, and Wayland child-surface commit.
- The paired swapchain readback and QMP 3D candidate are zero; the QMP HUD
  band is non-black.
- Filament's public API accepts the current `POSITION/FLOAT3` vertex
  declaration, `USHORT` index buffer, asynchronous `BufferDescriptor` upload,
  and indexed geometry count 36. A source/API shape check alone does not prove
  that the runtime Vulkan buffers contain the expected bytes.
- A fresh FLR-0155 QEMU run using the same rootfs and fixed QEMU profile reached
  `FLUORITE_NATIVE_PURE_FIXTURE enabled=true models=0 shapes=21 lights=13`,
  `FLUORITE_NATIVE_PURE_FIXTURE_SETUP_DONE`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_ENABLED scene=true`, and
  `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA enabled=true eye=(0,0,5)
  target=(0,0,0)` in one serial-synchronised execution. The earlier marker
  gap was caused by the narrower FLR-0154 selection command, not a missing
  fixture entry.
- The FLR-0155 QMP-only screenshot is retained at
  `$RECEIVER/evidence/flr0155/qemu/qmp-post-1.ppm`, 1280x800, SHA-256
  `b1b58575212a48324d277ae65a2111897183160536971ffb9a0f1f2fc81a304e`.
  The fixed 3D candidate `[300,250,620,400]` remained `248000/248000` black
  with zero changed, edge, and chromatic pixels. The HUD band remained
  non-black with `changed_pixels=11751`, `chromatic_pixels=3391`, and
  `edge_pixels=21256`.
- Six QMP video frames are retained under
  `$RECEIVER/evidence/flr0155/qemu/qmp-video-1/`; their candidate region was
  uniformly black in every frame. QMP quit was accepted and cleanup passed
  with zero residual target processes and no QMP socket.
- The fixed Mac Podman status gate passed and reused the existing container,
  source workspaces, state bind, and container-local TMPDIR. No new machine,
  container, named volume, or ticket TMPDIR was created.
- The Fluorite Devtool source commit is `d38d25f` on baseline `3f7c7c9`; the
  official component `update-recipe` output is registered unchanged as
  `0250-diag-mark-native-material-branch-devtool.patch` with SHA-256
  `13c05bef1cf4eac8c37a4a4065bfde568e7949c1b58b55f5729a843a2d96bddf`.
  It logs which native material source branch is selected when the diagnostic
  environment is enabled.
- The Filament Vulkan Devtool source commit is `80f6b2a86` on baseline
  `d51670fd3`; the official component `update-recipe` output is registered
  unchanged as `0248-diag-trace-native-vertex-buffer-boundary-devtool.patch`
  with SHA-256
  `a439b6b44831e81ba98e765e9e48273cb5a699de21f3073934c16774ef853b62`.
  It logs only the vertex/index upload size, CPU-data checksum, target Vulkan
  handle, and draw-time vertex/index handles under
  `FLUORITE_NATIVE_VERTEX_TRACE`.
- The diagnostic full image built successfully from the fixed Mini build and
  fixed TMPDIR: all 11898 tasks succeeded. The new rootfs SHA-256 is
  `cb7d05beb7c0fd38eaf7159af9c847cbe43749c778952cf54ba072e9c66f27b7` and
  the kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- In one fresh QEMU run, the runtime emitted vertex upload `bytes=96
  checksum=3361464197`, index upload `bytes=72 checksum=101010765`, and
  draw-time Vulkan handles matching the upload handles. The same run emitted
  `index_count=36`, queue-present result `0`, and Wayland child-surface
  commits. The QMP-only frame was 1280x800 with SHA-256
  `9282b7d8a7391f4ac534b0957de7ef347ec3bbc95d258cd3adf0b43d30d75180`.
- The fixed QMP candidate `[300,250,620,400]` remained uniformly black
  (`changed_pixels=0`, `edge_pixels=0`, `chromatic_pixels=0`, luma `[0,0]`),
  while the full frame contained HUD pixels (`changed_pixels=11713`,
  `chromatic_pixels=3363`). Six QMP video frames were captured; QMP quit and
  cleanup passed with zero residual target processes and no socket.
- The current Fluorite local-camera branch calls `setCameraLookat()` and then
  returns before `CameraManager::updateCamera()` can apply the deserialized
  projection. Filament initializes an unset `mat4` projection to identity.
  The fixture cube is at world z `[-1,1]`; look-at eye `(0,0,5)` makes its
  view-space z `[-6,-4]`, which identity projection clips entirely. The same
  source's Dart camera contract supplies a default perspective projection
  (`60` degree vertical FOV), so this is a concrete Fluorite camera-contract
  defect, not a generic QEMU or Vulkan upload failure.

## Inferences

- The common QEMU, present, Wayland, and 2D path is not the first known zero
  boundary for this run.
- The next useful observation is the actual buffer/binding/clip contract, not
  another material-color variant.
- The actual buffer/binding boundary is now positive. The first zero boundary
  is the fixture-local camera projection contract; the repair is tracked in
  FLR-0156.
- The first `update-recipe --force-patch-refresh` attempt did not emit a
  component patch. The standard Yocto component `update-recipe --mode patch
  --append --no-remove` path emitted both patches after baseline registration;
  no generated patch was hand-edited.
- After bundle handoff, Mini `bitbake -e` confirmed the diagnostic patch names
  in the effective metadata. The authoritative `flutter-auto:do_patch` gate
  passed 104/104 tasks and the forced component compile passed 2686/2686
  tasks, including Filament Vulkan. The raw build logs are retained under
  `$RECEIVER/evidence/flr0155/build/`.
- The first Mini build invocation failed before BitBake because the wrapper
  sourced `oe-init-build-env` under `set -u` and Yocto referenced an unset
  `BBSERVER`. The retry sourced the standard environment before enabling
  strict unset-variable checking and passed; this wrapper failure is retained
  in the working log as a process error, not a source or patch failure.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the native fixture entry or hardcoded branch is not reached | entry/branch marker is absent despite the launch environment | marker appears immediately before fixture/material setup |
| H2: vertex/index upload or Vulkan binding is empty or wrong | upload size, handle, or bound buffer differs from the expected vertex/index object | expected non-null handles, sizes, and draw bindings are all observed |
| H3: the vertex shader transforms all vertices outside clip space | valid buffers and draw are observed, but clip-space trace/probe shows no in-volume vertices | in-volume clip coordinates or a known solid probe produces fragments |
| H4: attachment/readback content is the first zero boundary | a known in-target clear/solid probe differs between backend readback and QMP | both independent observations remain zero with a known solid probe |

H1 fixture-entry and hardcoded-branch portions are FALSIFIED by the runtime
markers. H2 is FALSIFIED by matching source/runtime checksums and handles. H3
is CONFIRMED by the camera source/API contract and coordinate calculation. H4
is not the first missing boundary. The implementation ticket is FLR-0156.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | native fixture entry, buffer upload/binding, and vertex clip output |
| Where | ViewTarget native fixture and Filament Vulkan draw path |
| When | setup/upload before the first draw and each diagnostic draw |
| Who | Fluorite native fixture, Filament Vulkan, Mini image, QMP runtime roles |
| How | bounded markers plus one fixed-profile QEMU observation |

## PDCA

### Plan

1. Read the exact current Mini Filament and Fluorite source path before editing.
2. Compare the two main explanations: missing/invalid buffer data versus
   valid data transformed outside clip space; keep attachment/readback as a
   separate fallback boundary.
3. If needed, add the smallest environment-gated trace through Mac Devtool,
   generate the official patch, register it in the canonical layer, and run
   the existing Mac → bundle → Mini build → QMP loop.

### Do

- Ticket created after FLR-0154 recorded its screenshot, six-frame video,
  serial markers, hashes, build identity, and clean QMP teardown.
- Canonical Mini source inspection confirms the native fixture uses
  `VertexBuffer::Builder().vertexCount(8).bufferCount(1)` with a
  `POSITION/FLOAT3` attribute, uploads 96 bytes through `setBufferAt`, uses an
  `USHORT` index buffer with 36 indices and a 72-byte `setBuffer` upload, then
  builds one indexed triangle primitive with count 36.
- `FVertexBuffer::setBufferAt` and `FIndexBuffer::setBuffer` both delegate to
  the driver update APIs. The Vulkan implementation records the upload through
  `loadFromCpu`, stages/copies the bytes when direct mapping is unavailable,
  inserts vertex/index input barriers, and binds the resulting buffers before
  `vkCmdDrawIndexed`.
- The effective Mini `view_target.cc` contains both the minimal-geometry branch
  and the hardcoded material branch. The retained FLR-0154 serial selection
  contains the renderable contract but zero occurrences of
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_ENABLED`,
  `FLUORITE_NATIVE_PURE_FIXTURE_SETUP_DONE`, and
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR`. This is a runtime-marker gap,
  not proof that the source branch was absent.
- The fresh run proves pure fixture entry, native geometry enablement, local
  camera, draw admission, present, and Wayland commit. No engine or runtime
  behavior patch is accepted yet: actual GPU buffer handles/content,
  hardcoded branch entry, and clip-space output remain unobserved.
- The two boundary-trace patches were compiled into the Mini build and the
  diagnostic image was rebuilt and booted. Runtime upload/binding and
  material-branch markers are positive; camera projection is the first
  missing boundary.

### Check

Static/API check: PASS for the public Filament object construction and the
Vulkan upload/bind call chain. Mini metadata, patch, component compile, and
full-image checks: PASS. Runtime fixture-entry, material-branch,
upload/binding, indexed-draw, present, and Wayland checks: PASS. QMP 3D
candidate: FAIL/black. Source/API camera analysis identifies the first zero
boundary as the skipped projection update in the fixture-local early-return
branch.

### Act

Complete. FLR-0156 is the separate implementation ticket. It must preserve
the local fixture look-at while applying the camera's projection/exposure
configuration before the look-at override, then repeat the fixed Mac Devtool
→ bundle → Mini build → one-QEMU QMP loop.

## Evidence

- [FLR-0154 discriminator evidence](FLR-0154-isolate-native-materialbuilder-color-output.md)
- Raw FLR-0154 runtime evidence: `$RECEIVER/evidence/flr0154/qemu/`
- FLR-0155 diagnostic runtime evidence is retained on the Mini receiver under
  `$RECEIVER/evidence/flr0155/qemu-diagnostic-20260914/`.
- [FLR-0156 implementation ticket](FLR-0156-restore-pure-fixture-camera-projection.md)
