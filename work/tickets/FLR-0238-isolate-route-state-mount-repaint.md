# FLR-0238 — isolate route-state mount from parent repaint

- Status: Done
- Priority: High
- Owner: Flutter parent-composition and route-state roles
- Created: 2026-09-20
- Predecessor: FLR-0237

## Objective

Determine whether the post-Scenes white frame is caused by mounting a
`StatefulSceneView` into the parent `Stack`, or by the parent `setState`
rebuild itself. Keep the existing native 3D fixture and QMP evidence contract
unchanged.

## Facts

- FLR-0236 proves the Scenes tap reaches `_setScene(3)`.
- FLR-0237 retained the Planetarium state lifecycle but replaced its full
  gesture build with `SizedBox.shrink()`; the HUD still became uniform white
  after button release.
- FLR-0237 initial/move frames had HUD `2845` and native ROI `24178`; post-tap
  HUD was `0`/luma `[255,255]` and native ROI remained `24178`.
- The callback marker and Flutter surface attach after activation are recorded
  in `$EVIDENCE_ROOT/FLR-0237/`.
- FLR-0238 marker-only QMP frames had HUD `2845` and native ROI `24178` before
  input, then HUD `0`/uniform white and native ROI `24178` after the tap.
- The FLR-0238 marker was
  `FLR0238_SCENE_TAP_MARKER_ONLY id=3 name=Planetarium`; the bounded guest
  log also records the pointer button and Flutter surface attach events.
- The FLR-0238 Mini image completed with `IMAGE_RC=0` after 11,758 tasks; the
  rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260920132437.ext4` with SHA-256
  `e6f8c8396376988c308cf1bac64c2644a74df529e686f09b9c44144511ed6492`.
- The qemuboot SHA-256 was
  `14e36647c50478daeef2f0b50143cd501043481d041b1647754fb4fd608142aa` and
  the kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Mounting any non-null route state changes platform-view composition | marker-only parent setState stays chromatic; route-state mount reproduces white | route state may be required for native control ownership |
| 2 | Any parent setState repaint triggers the white surface | marker-only setState also becomes white | requires an embedder/parent repaint boundary investigation |
| 3 | Planetarium state callbacks issue the side effect | no-mount route stays chromatic, state mount turns white only after readiness/native commands | native command telemetry may need a narrower A/B |

The first experiment is a marker-only `setState` versus route-state mount,
because it separates Flutter tree mutation from the native scene payload and
does not change camera, light, material, or fixture code.

## Result

The marker-only parent `setState` reproduced the white HUD. Therefore route
state mounting is not required for the failure; hypothesis 1 is falsified and
hypothesis 2 remains the leading candidate. The native fixture remained
visible at `24178` chromatic pixels, so this ticket does not show a native 3D
failure. FLR-0239 owns the no-`setState` discriminator.

## Verification

- Mac Devtool source commit: `5c247d18e76718c04247a39a1ec495038cd94e49`.
- Canonical patch: `0070-flr0238-isolate-marker-only-parent-setstate-devtool.patch`.
- Canonical patch SHA-256: `1149e5f3e452926a4687ba24f1ea27b4190f37eacb52baed1f0c5c30e9b1d656`.
- Mini `do_patch`, compile, and image gates passed for the exact bundle tip.
- QMP evidence: `$EVIDENCE_ROOT/FLR-0238/qmp-marker-only/` and
  `$EVIDENCE_ROOT/FLR-0238/pixel-analysis.jsonl`.
- Bounded runtime evidence: `$EVIDENCE_ROOT/FLR-0238/app-runtime-marker-only.raw`
  and `$EVIDENCE_ROOT/FLR-0238/app-marker-marker-only.out`.
- Guest log SHA-256:
  `62c57263400ed36c5dc2ca3bc053464e20608ecd8208deb972539e1df55fb013`.
- Bounded marker SHA-256:
  `b533a5040176ae49bffd6c379cab51057d6da03eb2a00950c1c0cbe920044bdf`.
- QMP quit and cleanup passed with zero residual target processes and no QMP
  socket.

## Success criteria

- Mac Devtool patch is generated from the FLR-0237 source commit through the
  official split-component flow.
- Mini patch, compile, and image gates pass for the exact bundle tip.
- Marker-only control retains HUD `2845` and native ROI `24178` through QMP
  input; route-state mount result is recorded separately.
- QMP evidence, hashes, guest log slice, and cleanup are retained.

## Evidence

- Predecessor: [FLR-0237](FLR-0237-fix-planetarium-route-composition.md)
- Working log: [2026-09-20-flr0238.md](../logs/2026-09-20-flr0238.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0238/`

## UNKNOWN

- Whether a callback without parent `setState` preserves the HUD.
- Whether native `onCreate`/frame callbacks contribute to the repaint.
- Whether a route state can be kept off the parent Stack while preserving the
  desired Planetarium camera controls.
