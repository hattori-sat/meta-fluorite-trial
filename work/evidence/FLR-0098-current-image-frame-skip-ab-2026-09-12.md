# FLR-0098 evidence manifest — current-image frame-skip A/B

- Date: 2026-09-12 (Asia/Tokyo)
- Ticket: [FLR-0098](../tickets/FLR-0098-current-image-frame-skip-ab.md)
- Image role: fixed authoritative Mini PC image
- Evidence root: `$RECEIVER/evidence/flr0098-frame-skip-ab/`
- Raw QMP, video-frame, command, and serial files remain outside Git.

## Common input

- qemuboot SHA-256:
  `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`
- kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- rootfs SHA-256:
  `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`
- Both cases used one QEMU at a time, one `flutter-auto`, the same production
  launch identity, the same existing trace controls, and the same QMP regions.
- The only A/B input was the presence of the existing
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1` control in the ready variant. No new
  legacy directory, receiver, TMPDIR, variable, marker, source patch, or image
  was created.

## Control — ready control disabled

- QMP-before SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP-early SHA-256:
  `f3051f35930f49ae9e0fe4093e83302e6ea02d068b280d3407e31ed54cb7a044`.
- QMP-late SHA-256:
  `0712e826961d81826424c51185853d9833ef3e9e5e1e24d9152265d655fca3db`.
- Selected serial log SHA-256:
  `bb1625086beb41f9f2e44788de4c63e0a1b1989d64e92c632e86ba09310c1f09`.
- Frame markers: 8 `FRAME_BEGIN` records, all `started=false`, with 77
  `FRAME_SKIP_STATUS status=1` records. Existing source/history maps status 1
  to `TIMEOUT_EXPIRED`.
- No `TARGET_DRAW2`, renderer commit enqueue, queue submit, or queue present
  marker appeared in the bounded selected output.
- Native region `[300,80,620,360]`: `0/223200` changed pixels.
- HUD region `[200,100,400,250]`: `1252/100000` changed pixels;
  bounding box `[200,113,29,66]`.
- QMP video: 6 frames captured under `control/qmp-video`.

## Ready variant — existing unlinked-fence-ready control enabled

- QMP-before SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP-early SHA-256:
  `8c16aca873fda8403f6fc655adb64a8dad3d56588dbaa43a3a3105bc092b0490`.
- QMP-late SHA-256:
  `8c16aca873fda8403f6fc655adb64a8dad3d56588dbaa43a3a3105bc092b0490`.
- Selected serial log SHA-256:
  `7df524495fa796ce5648fe9c148585abb1d82933a2c28d899e7472608d4107bb`.
- Frame markers: 3 `FRAME_BEGIN` records, all `started=true`, 3
  `FRAME_END`, 3 `FRAME_EVENT_RETURNED`, 6 unlinked-fence-ready markers, and
  8 frame-skip status records with `NO_FENCE`/`0` rather than timeout.
- Draw markers: 25 `TARGET_DRAW2` records and 7 renderer commit enqueues. The
  selected output includes both offscreen targets and a `swapchain=true`
  `1280x800` target, proving that the recovered path reaches draw-target setup.
- Pipeline markers: 6 neutral pipeline inputs and 6 successful create results;
  the fourth create took `19845586` microseconds.
- Native region `[300,80,620,360]`: `0/223200` changed pixels.
- HUD region `[200,100,400,250]`: `984/100000` changed pixels;
  bounding box `[200,113,29,66]`.
- QMP video: 6 frames captured under `ready/qmp-video`; early and late frames
  had the same native-region result.

## Cleanup and classification

- Both cases passed guest-ready, QMP capture, serial launch/extraction, QMP
  `quit`, and residual checks. No QEMU/runqemu/flutter-auto target or QMP
  socket remained after either case.
- The ready variant changes the current image from repeated frame-start
  timeout to successful frame begin/end and draw-target setup, but native
  production pixels remain absent. Frame-skip recovery is therefore a real
  scheduling contributor, not the complete 3D fix.
- Next boundary: draw-target/native output and surface handoff after recovered
  frame execution. See FLR-0099.
