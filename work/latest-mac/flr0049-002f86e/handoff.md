# FLR-0049 latest artifact handoff

## Current latest: transparent-alpha build and QMP video (2026-09-08)

- Mac feature tip: `ffab6585d80e8adb304558b3e546a1e8ff8787c8`
- Mini PC authoritative build: `11748/11748` tasks succeeded; 22 warnings,
  no `ERROR:` marker.
- Bundle: `work/flr0049-ffab658.bundle`
- Bundle SHA-256: `eef4806a66802ae23ec16fd70892d27b3fa9c875cb94672de122da28ce392a6e`
- Registered Devtool patch: `layers/meta-fluorite-trial/recipes-graphics/filament/files/0170-filament-vulkan-transparent-alpha-devtool.patch`
- Registered patch SHA-256: `59b35281bfd31c2fbb572ef35826cc894911df50905e4d1bd53d5e93df6cc17c`
- Fixed Mini PC build/TMPDIR and persistent Mac Devtool container were reused.

### Current build artifacts

| Artifact | SHA-256 |
| --- | --- |
| `agl-ivi-image-flutter-qemux86-64.rootfs-20260908055043.ext4` | `496bbc58f6c9a334976b8315b5d483ca90b8724eea61a9585ab7f196176811ea` |
| `agl-ivi-image-flutter-qemux86-64.rootfs-20260908055043.qemuboot.conf` | `a80d65033f88e9b57a1980cffddd60115d1c46eb923d4e6660b681b88ace327d` |
| `bzImage--6.6.111+git0+50530c858c_2a17dc587a-r0-qemux86-64-20260405092846.bin` | `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74` |

Mac copy: `work/latest-mac/flr0049-002f86e/alpha-build-ffab658/`.

### Current QMP video evidence

- Video: `qmp-alpha-runtime.mp4`, SHA-256
  `35537195f38d4cfa80e54dbb3c00dd9685cffdaa273f046459a1d9925de6e209`
- Format: 1280x800, 1 fps, 39 seconds, 39 QMP framebuffer frames.
- Representative PNG: `qmp-alpha-runtime-representative.png`, SHA-256
  `765ce7cff84f18c993a6a65d247fa74478f419371bec4220b3998c2aee0f7864`
- Representative raw PPM SHA-256:
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`
- Candidate region `[200,100,400,250]` changed `40257/100000` pixels against
  white; bounding box `[337,100,263,250]`.
- All 39 frames were byte-identical, so this video proves a stable QMP-visible
  3D state but does not yet prove an input-driven transition.

### Current runtime result

- Runtime log: `alpha-build-ffab658/runtime-alpha.log`, SHA-256
  `056d446fb9b1f114d77229113e066e5b74ad66f66270d720e23315849f6f65b8`.
- `FLR0026_VK_COMPOSITE_ALPHA transparent=true supported=0x3 selected=0x2`
  was emitted; Vulkan queue present repeatedly returned `result=0`.
- Sequoia model reached `MODEL_STAGE_SCENE_ADD_DONE`, then
  `scene=true entities=25 renderables=14`, with model/resource samples.
- The QMP frame visibly contains the production Sequoia vehicle, but the
  Flutter 2D HUD/CPU/FPS layer is not visible in the same frame. Combined
  native/2D composition remains **UNKNOWN**.
- QMP teardown returned `host-qmp-quit`; QEMU, runqemu, flutter-auto, and the
  QMP socket were absent afterward.

## Identity

- Source/build artifact tip: `002f86e8c39111f0ae9622ad802310f3a311f86f`
- Latest evidence/documentation commit: `56fd895`
- Mac bundle: `work/flr0049-002f86e.bundle`
- Bundle SHA-256: `937bd70081d414a38fdafb8bc485c50dd516b6f49e6d3a15bf52d1ddc3404181`
- Mini PC receiver revision: same as feature branch tip
- Layer patch: `0195-diag-delay-GLB-readback-and-trace-resources-devtool.patch`
- Layer patch SHA-256: `7face4162ac79ca567dbe4d2fd9e3b58257baaed2efaff6d3cbc970bdd3b6d96`

## Build artifacts copied to Mac

| Artifact | SHA-256 |
| --- | --- |
| `agl-ivi-image-flutter-qemux86-64.rootfs-20260907230320.ext4` | `b35f237345ad39aade768d518b16e5d42a50dbb766187f230acdf951ce0e4d0c` |
| `agl-ivi-image-flutter-qemux86-64.rootfs-20260907230320.qemuboot.conf` | `ed04a14cf46b025107f362f0077af75996c515f73aa73955f320ca81b1fb27fb` |
| `bzImage--6.6.111+git0+50530c858c_2a17dc587a-r0-qemux86-64-20260405092846.bin` | `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74` |

## QMP evidence

- Default launch screenshot: `qmp-latest-20s.png`
- Default raw QMP PPM SHA-256: `c02ee81805ab1ff8d275c37a5bef23446b3baed01c37db6a0244d45e57ce321b`
- Latest controlled model/readback screenshot: `qmp-correct-control-18s.png`
- Controlled raw QMP PPM SHA-256: `aa0f262851c44fa18bf5ca8e777a6ecb98666e390c3100e8192e699b4276cc8a`
- Latest controlled raw QMP PPM SHA-256: `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`
- Latest controlled candidate region: `[200,100,400,250]`; changed pixels `100000/100000`; bounding box is the full region because the frame is uniform white.

The default screenshot proves 2D HUD, CPU/GPU/FPS metrics, and QMP capture. It has no production 3D object. The earlier controlled screenshot contains a black polygon, but it used an obsolete shape-skip variable and is not authoritative. The latest controlled screenshot is uniform white; it is also not a Sequoia pass. The latest runtime log should be interpreted together with the correct controls `FLR0027_NATIVE_SKIP_SHAPES` and `FLR0027_NATIVE_SKIP_LIGHTS`.

## Runtime evidence

- Default runtime log: `runtime.log`
- Earlier controlled runtime log: `runtime-2.log`
- Latest controlled runtime log: `runtime-3.log`
- Default run confirmed `Application Id: fluorite`, model plan creation, Vulkan queue submit, and 2D HUD metrics.
- Controlled run confirmed `MODEL_LOAD_PLAN total=60 limit=2 match=sequoia inspected=10 queued=2`, valid camera `(5,0,-5)`, near `0.05`, far `1000`, `blend_opaque=true`, and `scene=true` with `renderables=58`.
- The latest controlled run emitted production renderable/material resource samples, but no `MODEL_STAGE_*` markers because `FLR0026_MODEL_STAGE_TRACE=1` was not enabled in that run. It repeatedly emitted `Light not found` because diagnostic light setup was skipped; treat that as a separate diagnostic symptom.

## Reproduction

Open `qmp-latest-20s.png` first to verify the 2D baseline. Then open `qmp-correct-control-18s.png` and compare it with `runtime-3.log`. The files are already on the Mac under this directory. Do not use a host-window screenshot as evidence.

Both QEMU runs were stopped through QMP with `reason=host-qmp-quit`; the QMP socket, QEMU process, and QMP client processes were absent afterward. The fixed Mini PC build directory and TMPDIR were reused.

## Latest Mac-side recovery

The newest recovery from the Mini PC is in this directory:

- `route17-shm-cube.png`: QMP-only framebuffer showing the self-created SHM cube.
- `route18-shm-skip-stack.png`: the same self-created cube with the stack probe disabled.
- `serial-19.log`: serial output from the latest production/readback diagnostic run.

The corresponding raw QMP PPM files are retained beside the PNGs for checksum or pixel-level inspection. These two images prove that the Wayland SHM child-surface path reaches the QEMU framebuffer; they do not yet prove that the production Filament scene is visible.

The newest no-readback A/B is also in this directory:

- `no-readback-35s.png` and `no-readback-60s.png`: QMP-only production
  Sequoia framebuffer captures. Both are bit-for-bit identical and show the
  vehicle with red light pixels.
- `runtime-no-readback.log`: matching guest runtime log.
- `runtime-no-readback-summary.txt`: compact marker and crash check.

The no-readback A/B proves production 3D pixels for this runtime condition.
The earlier `serial-19.log` page fault remains an independent diagnostic
readback crash finding; do not enable that probe in display acceptance runs
until its fence/buffer lifetime is separately fixed.

The latest serial evidence also contains a kernel page fault/Oops in `FEngine::loop` (guest PID 673, around 133.4 seconds). Treat this as an independent runtime-crash finding; the production 3D result must not be marked successful while this run is unstable.
