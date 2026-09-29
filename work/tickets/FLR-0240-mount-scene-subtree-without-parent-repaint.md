# FLR-0240 — mount scene subtree without parent repaint

- Status: Done
- Priority: High
- Owner: Flutter scene-state and platform-view composition roles
- Created: 2026-09-20
- Predecessor: FLR-0239

## Objective

Implement the smallest production-shaped scene transition that changes only
the scene widget subtree, not the parent `Stack` that owns the native
`SceneView`. Use the existing Planetarium scene widget and native fixture
unchanged. Prove whether the Planetarium scene becomes visible in actual QMP
pixels while the 2D HUD remains composed.

## Facts

- FLR-0235 proves simultaneous 2D HUD and self-made native 3D cube pixels.
- FLR-0236 proves the Scenes input callback and Planetarium selection marker.
- FLR-0237 proves removing the route's full-surface gesture build does not
  remove the white frame.
- FLR-0238 proves route-state mounting is not required: marker-only parent
  `setState` still produces HUD `0`/uniform white while native ROI stays
  `24178`.
- FLR-0239 proves parent `setState` is sufficient to trigger the white frame:
  the identical QMP tap with no parent `setState` retains HUD `2845` and
  native ROI `24178`.
- FLR-0240's `ValueListenableBuilder` child-only update mounted the actual
  `PlanetariumSceneView`; the post-tap HUD still became uniform white while
  native ROI stayed `24178`.
- The FLR-0240 marker was
  `FLR0240_SCENE_SUBTREE_ACTIVATION id=3 name=Planetarium`; pointer button
  down/up and a post-tap `wl_surface@14.attach` were recorded.
- The FLR-0240 Mini image completed with `IMAGE_RC=0` after 11,758 tasks; the
  rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260920142911.ext4` with SHA-256
  `ad3d8878efd3693656b5b79b7239395cfa86859a7d555b23434ebd3259824985`.
- The qemuboot SHA-256 was
  `b67b988c715fdc729f792d6cda9b84da23fc5913c0b7a7335d8e039833ea5002` and
  the kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | A listenable scene subtree update avoids the parent repaint boundary | Planetarium selection marker appears; HUD stays chromatic and native ROI remains visible | child subtree may still request a platform-view repaint |
| 2 | Mounting `PlanetariumSceneView` itself causes the white frame | isolated subtree mount reproduces HUD white | scene widget lifecycle/native callbacks may be required for the production scene |
| 3 | Planetarium native scene content is independently black/faulting | HUD stays visible but Planetarium ROI is black or faulted | this separates composition from camera/light/material work |

The first implementation uses a `ValueNotifier`/`ValueListenableBuilder`
boundary around `_sceneView` and calls `_setScene(3)` without parent
`setState`. It changes no camera, light, material, fixture, or engine code.

## Result

The child-only update avoids the direct parent `setState` call, but mounting
the actual `PlanetariumSceneView` still produces HUD `0`/uniform white after
the tap. Native fixture pixels remain `24178`, so native 3D is not lost. The
failure is therefore associated with the mounted Planetarium widget or its
lifecycle/native commands, not only the parent rebuild. FLR-0241 owns that
lifecycle split.

## Verification

- Mac source commit: `ea824e41a4cb83afdcc2cf9189221b4a5d90df3c`.
- Canonical patch:
  `0072-flr0240-mount-scene-subtree-devtool.patch`.
- Canonical patch SHA-256:
  `041084c02a8e1db05d7bc578051db758613d5c05fb1db17f3b7b68fa2cb76eb4`.
- Canonical layer commit: `cb08088`.
- Mini bundle SHA-256:
  `00460525e739e9ec1e3017f88587091285d6d2d58c0f910624e3bcc2a1f9f590`.
- Mini `do_patch`, compile, and image gates passed for the exact bundle tip.
- QMP evidence: `$EVIDENCE_ROOT/FLR-0240/qmp-scene-subtree/` and
  `$EVIDENCE_ROOT/FLR-0240/pixel-analysis.jsonl`.
- Bounded runtime evidence:
  `$EVIDENCE_ROOT/FLR-0240/app-runtime-scene-subtree.raw` and
  `$EVIDENCE_ROOT/FLR-0240/app-marker-scene-subtree.out`.
- Runtime and marker SHA-256 values:
  `041c2192a220ee96edb57259c32010bb81e69f6a8a6ffb53d2ecb839b8bcfc51` and
  `ae092de4827bf39fc41ac6fce2a9766679bbf4e146c7303f33469aba64162710`.
- QMP quit and cleanup passed with zero residual target processes and no QMP
  socket.

## Success criteria

- The source change is generated through the official Mac Devtool flow from
  the FLR-0239 effective source commit.
- Mini `do_patch`, compile, and full image gates pass for the exact bundle tip.
- QMP initial and post-tap frames retain the same ROI/threshold contract and
  show whether Planetarium pixels appear while HUD pixels remain present.
- Guest marker/log, artifact hashes, and clean QEMU teardown are retained.
- If composition passes but Planetarium is black, open a separate ticket for
  camera/light/material diagnosis; do not mix it into this ticket.

## Evidence

- Predecessor: [FLR-0239](FLR-0239-isolate-parent-setstate-repaint.md)
- Working log: [2026-09-20-flr0240.md](../logs/2026-09-20-flr0240.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0240/`

## UNKNOWN

- Whether inert Planetarium lifecycle callbacks preserve the Flutter HUD.
- Which Planetarium native command first alters the platform composition.
