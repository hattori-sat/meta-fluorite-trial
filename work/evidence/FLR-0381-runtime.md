# FLR-0381 — no-Wayland-debug runtime evidence

This bounded diagnostic comparison is complete; production 2D+3D acceptance
remains open. Both runs used the unchanged candidate: kernel
`3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, rootfs
`949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`, and
qemuboot `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`.
Mini raw logs and PPMs remain under `/mnt/yocto/evidence/flr0381-0001/qemu`
and `/mnt/yocto/evidence/flr0381-0002/qemu`; no QEMU disk image or raw PPM was
copied to Mac.

## Run 0001 — liveness at still capture UNKNOWN

- Manual `flutter-auto` ended with guest SSH/timeout status `124`.
- The QMP still is uniformly RGB `(224,224,224)`; PPM SHA-256
  `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`.
  It was written at 15:44:15.205; the status file was written at 15:44:17.589.
  Liveness at the still is not claimed.
- By the later video bracket Flutter was absent. All eight frames are the
  pre-Flutter black PPM with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- [QMP still](FLR-0381-0001/qmp-bounded-pre-timeout.png) ·
  [post-timeout 8-frame video](FLR-0381-0001/qmp-post-timeout-8frames.mp4).

## Run 0002 — live-capture gate passed

- Capture triggered on the first successful-present marker after 53
  250-ms polls. Strict guest SSH showed Flutter alive as UID 1001 immediately
  before the still and after the 8-frame capture.
- Two Vulkan queue-present calls returned `result=0`; a third entered without
  a matching return. The bounded SSH/timeout status was `124`.
- The QMP still is 1280×800, entirely RGB `(224,224,224)`: 1,024,000 changed
  pixels from the black pre-Flutter frame, zero edges, zero chromatic pixels.
  Vehicle ROI `(0,100,320,310)` and HUD ROI `(960,0,320,120)` are uniform, with
  zero edges and zero chromatic pixels. All eight live-video PPMs have the
  same SHA-256 as the still.
- Runtime setup reached 2 `FLR0026_MODEL_SELECTED` records, one model-load
  plan, 34 `FLR0280_MODEL_RENDERABLE`, and 42 `FLR0280_MODEL_MATERIAL` records.
  Model/material setup and successful present returns did not produce visible
  geometry in QMP.
- Stdout: 1,491,916 bytes, SHA-256
  `3d7e62faa72d233a9802f3e2a5b689b963de8043fcc3e28ed572c17489c71000`.
  Stderr: 5,404 bytes, SHA-256
  `7c296567c33af08a494c10f51a7dd4cb341f5c246a2643ae1cb179c3a19d07f2`.
- [Live QMP full-frame still](FLR-0381-0002/qmp-live-first-present.png) ·
  [live 8-frame video](FLR-0381-0002/qmp-live-8frames.mp4).

Both videos are 1280×800, 1 fps, eight frames/eight seconds. Both PNGs have
SHA-256 `1d6da53fb4f74155a3eccb75a0db07488bfbd88e8f7f93684888c19ab15f351c`.
MP4 SHA-256 values are `70f732f2b339d50b9920b1ea8e2311c3d6edaae6e7408089822c11d588db1dff`
(run 0001) and `dab67b9561d0c528095b9015dd9bf346a175b9bb1d5e16e97e36df3f5c2260b2`
(run 0002).

Both exact QMP sockets accepted `quit`; independent checks found no
QEMU/runqemu/flutter-auto process, no QMP socket, and ports 10930–10932 free.
Run 0001's bounded guest `dmesg`/`coredumpctl` check found no selected
Oops/OOM/segfault and no coredump. Run 0002 guest kernel/core state was not
separately collected and remains UNKNOWN.

## Interpretation

Compared with FLR-0380's black QMP frame, removing `WAYLAND_DEBUG` correlates
with a stable gray framebuffer on two runs; it does not restore the Sequoia or
HUD. FLR-0378's silhouette used `FLR0026_SCENE_STAGE_TRACE=1`, unlike these
low-volume runs. This is the next isolated runtime comparison, not evidence
that tracing fixes rendering. The no-light profile cannot diagnose normal
light or texture output.

Historical controls remain distinct: FLR-0371/FLR-0286 prove a self-made
Filament fixture plus HUD; FLR-0049/FLR-0070 are historical production
Sequoia/tail-light or Sequoia+HUD candidates, not repeatable current-image
acceptance. See [FLR-0371](../tickets/FLR-0371-lit-parameter-rgb-assignment.md),
[FLR-0286](../tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md),
[FLR-0317](../tickets/FLR-0317-trace-paintcolor-override-predicate.md), and
[FLR-0357](../tickets/FLR-0357-refresh-3d-visibility-retrospective.md).
