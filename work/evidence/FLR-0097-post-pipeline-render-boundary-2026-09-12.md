# FLR-0097 evidence manifest — post-pipeline render boundary

- Date: 2026-09-12 (Asia/Tokyo)
- Ticket: [FLR-0097](../tickets/FLR-0097-post-pipeline-render-boundary.md)
- Image role: fixed authoritative Mini PC image
- Evidence root: `$RECEIVER/evidence/flr0097-post-pipeline/`
- Runtime profile: one QEMU at a time, QMP-only visual captures, one
  `flutter-auto` process per case
- Raw PPM, command, and serial files remain outside Git; this manifest records
  selected hashes and the result.

## Inputs

- qemuboot SHA-256:
  `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`
- kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- rootfs SHA-256:
  `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`
- Existing post-pipeline observation controls were enabled for this run. The
  older marker names are existing image instrumentation only; no new legacy
  directory, receiver, TMPDIR, control, or marker was created.

## Fixture case

- Launch controls: neutral pure fixture, neutral minimal geometry, neutral
  pipeline-input trace, and existing scene/camera/view/resource/frame/draw
  observations.
- QMP-before SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP-early SHA-256:
  `6e2677944ea2f897e36181d1757db5ea4d2e443a0c34407316f76b934f10aee0`.
- QMP-late SHA-256:
  `d56c83e0dab8b3327b31d8342d90aa60195ef92bf9ac70b06aba956b8665f59b`.
- Selected serial log SHA-256:
  `b181d0a933afbb68717acc47b13de39f490c9ceaaaa4bfe05d9677a1ffa725c8`.
- Native candidate region `[300,80,620,360]`: `41,750/223,200` changed pixels;
  bounding box `[501,278,278,162]`.
- HUD region `[200,100,400,250]`: `6,089/100,000` changed pixels.
- The selected trace contains `TARGET_DRAW2`, renderer commit enqueue, queue
  submit, queue present, and present-boundary completion markers.

## Production case

- Launch controls: same existing observation profile, without fixture controls.
- QMP-before SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP-early SHA-256:
  `f3ff71f1f1fce901f0ad932cb0ff0572350be794cdd0bae17db34d13bd3f043a`.
- QMP-late SHA-256:
  `f5dd786ee6060d4eb89be8440ce01410f5b07e13a971bf71a9f9090c7d51a950`.
- Selected serial log SHA-256:
  `5e81edcbdb14d320910055410237711c91bf002b5aab66d39403cfae7bfbeb5b`.
- Scene state: `scene=true`, `entities=1115`, `renderables=837`,
  `lights=13`, viewport `1280x800`.
- Camera/view state: position `(5,0,-5)`, near `0.050`, far `1000.000`,
  `view_scene=true`, `system_scene=true`, `same_scene=true`, visible layers
  `255`, `blend_opaque=false`.
- Renderable/resource samples: six samples, each `primitives=1` and
  `material_valid=true` (`lit` or `textured_pbr`).
- First frame boundary: `FRAME_BEGIN seq=730 started=false`, followed by
  `FRAME_EVENT_RETURNED`; no `TARGET_DRAW2`, renderer commit enqueue, queue
  submit, queue present, or present-boundary completion appeared in the
  selected bounded output.
- `FRAME_SKIP_STATUS status=1` repeated. Static source/history maps value `1`
  to `TIMEOUT_EXPIRED` for this FrameSkipper diagnostic.
- Native candidate region `[300,80,620,360]`: `0/223,200` changed pixels.
- HUD region `[200,100,400,250]`: `1,236/100,000` changed pixels;
  bounding box `[200,113,29,66]`.

## Harness and cleanup

- QEMU start, guest-ready, QMP-before, serial launch, and QMP captures passed
  for both cases.
- One intermediate `summary` call failed with
  `log-not-readable` because a guest log path was passed to a host-side
  summary command. This was a harness invocation error, not a runtime result;
  serial-exec then extracted the guest log successfully.
- Both cases ended with negotiated QMP `quit`; residual checks reported zero
  QEMU/runqemu/flutter-auto targets and zero QMP sockets.

## Classification

The production path has valid scene, camera, renderable, and material state,
but the current run stops at the frame-start decision before native draw
submission. The fixture reaches draw/submit/present and produces native pixels
under the same image. This run therefore confirms a production frame-skip
boundary as the first missing operation; it does not prove that repairing the
frame loop alone will make the production 3D visible. FLR-0098 rechecks the
existing unlinked-fence-ready control against the current image before any
source patch is considered.
