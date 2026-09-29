# FLR-0096 evidence manifest — production pipeline runtime snapshot

- Date: 2026-09-12 (Asia/Tokyo)
- Ticket: [FLR-0096](../tickets/FLR-0096-production-pipeline-runtime-snapshot.md)
- Image role: authoritative Mini PC image from the fixed receiver/build/TMPDIR
- Evidence root: `/mnt/yocto/flourite-receivers/flr0023-835a04e/evidence/flr0096-production-runtime/`
- QEMU visual evidence: QMP-only PPM files in the evidence root
- Raw evidence remains outside Git; this manifest records the role path,
  selected hashes, and interpretation.

## Image identity

- qemuboot: `agl-ivi-image-flutter-qemux86-64.rootfs-20260911201143.qemuboot.conf`
  SHA-256 `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`
- kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- rootfs SHA-256:
  `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`

## Runtime execution

- The first two observations exposed a harness/SSH lifecycle mistake: a short
  QMP alias was removed when the observation shell exited while QEMU remained
  alive. Each instance was recovered through a recreated short alias and QMP
  `quit`; no process was force-killed. The third run kept the alias until
  negotiated teardown and completed the intended observation.
- The successful run used one QEMU, one installed `flutter-auto`, and one
  production launch. Its runtime state reported PID 632, 38 threads, and the
  expected `llvmpipe-0..3` plus `FEngine::loop` threads.
- Available target tools: `/usr/bin/gdb`, `/usr/bin/strace`, `/usr/bin/ps`,
  and `/usr/bin/timeout`.
- Early state log SHA-256:
  `039c34907a8eb523ef52e6683e4ba47a840a0aae7c41777143ed0f311498c0ab`.
- GDB snapshot SHA-256:
  `8f40e0ffe0c42e3c71e5e4e6c688f59ffaafd49fb433246189660f1b80ef549d`.
  The main thread was in `clock_nanosleep`; `FEngine::loop` and llvmpipe
  threads were in Vulkan/condition/futex wait paths. No crash or signal was
  observed. Symbols were mostly stripped.
- Five-second allowlisted syscall snapshot SHA-256:
  `27f77ef1fc3c350c5b23bf8f09cbe7d3e7901d957bb10e8f31d5ededdb40d18a`.
  All 38 threads attached and detached cleanly. The captured tail was mainly
  repeated `futex` and `epoll_wait`; no repeated ioctl boundary was observed.
  One diagnostic section label emitted `printf: -- invalid option`; this is
  harness output noise, not a syscall result.
- Late state log SHA-256:
  `b52ed274b80c4745fafc7a8711e243ee088453402db6e9d06a9d4db0276fe11e`.
  Pipeline creates 1, 2, 3, 4, 5, and 6 all returned `result=0`. The fourth
  create returned after `21368217` microseconds (about 21.4 seconds), followed
  by successful creates 5 and 6.

## QMP visual evidence

- QMP-before SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP-early SHA-256:
  `a64f3ed31e680b3a4aaaa42eae8b98c2f5c9c3910d912b091e4bd9580abd1552`.
- QMP-late SHA-256:
  `77c487ee37385cc28805582b8a8874bb1aceb0570ddea31aba80da495b461d08`.
- Frame size: `1280x800`.
- Production native candidate region: `0/223200` changed pixels.
- HUD region: `1264/100000` changed pixels; bounding box `[200,113,29,66]`.
- The late frame therefore proves continued HUD activity but no accepted
  production native 3D pixels.

## Cleanup and classification

- QEMU was stopped through QMP `quit`.
- Post-check found no QEMU, `runqemu`, `flutter-auto`, or `bitbake` process and
  no QMP socket under the active evidence root.
- Classification: the fourth pipeline-create boundary is a long software
  Vulkan/llvmpipe compilation and eventually completes successfully. It is not
  the final cause of the black production native region.
- Next boundary: post-pipeline resource/renderable readiness, frame/draw
  submission, or native-surface handoff. See FLR-0097.
