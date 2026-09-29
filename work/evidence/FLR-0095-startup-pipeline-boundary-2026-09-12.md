# FLR-0095 — startup and pipeline-boundary evidence

## Outcome

The same authoritative image was run through the same QMP harness for the
neutral fixture and production scene. The fixture selection marker and its
pipeline completion were captured live, and its native pixels appeared in the
late QMP video. Production reached four pipeline inputs: the first three
completed with result `0`, while the fourth had no completion marker in the
bounded observation and the native region stayed unchanged. This identifies
the first observed divergence at the fourth production pipeline-create
completion boundary; it does not yet prove the underlying driver or shader
cause.

## Fixed identity

- Image layer revision: `054e3c549246d93d1d0ba16afdcd277d9c525433`.
- Kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Rootfs SHA-256: `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`.
- Qemuboot SHA-256: `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`.
- Machine: `qemux86-64`.
- Raw evidence root: `$RECEIVER/evidence/flr0095-startup-pipeline/`.

## Fixture case

The fixture was launched as `agl-driver` with `FLUORITE_NATIVE_PURE_FIXTURE=1`,
`FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`, and
`FLUORITE_VK_PIPELINE_INPUT_TRACE=1`.

- Live markers: `FLUORITE_NATIVE_PURE_FIXTURE enabled=true`,
  `FLUORITE_NATIVE_PURE_FIXTURE_SETUP_DONE`, one pipeline input, and
  `FLUORITE_VK_PIPELINE_CREATE_RESULT result=0`.
- QMP before-launch SHA-256: `42e89ea3ab86ac7a216e372ca1cca16c63cdbd5bca3c62457dd5d8aae2b8caab`.
- QMP late-frame SHA-256: `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- Late QMP video frame SHA-256: `899ddef948321920abc6aee49aee08c761ce9a72178d1cae5fcb3888697edf7a`.
- Native region `[300,80,620,360]`: `41,750/223,200` changed pixels;
  bounding box `[501,278,278,162]`.
- HUD region `[200,100,400,250]`: `116/100,000` changed pixels in the
  late frame.
- Runtime marker output SHA-256:
  `9808b3eec82a3daa70381bdf09c908e523e8e15bdcb048dc832f5de97c12a8fa`.
- Process count: one `flutter-auto`; QMP quit and residual cleanup: PASS.

The first seven-second QMP sample was still unchanged, while the last video
frame at approximately thirteen seconds contained the same native fixture
shape observed in FLR-0094. This is a timing observation, not a fixture
failure.

## Production case

Production was launched with only `FLUORITE_VK_PIPELINE_INPUT_TRACE=1`.

- Live application marker: `Application Id: fluorite`.
- Pipeline 1: `color_targets=1 samples=1 blend=0 depth_write=0
  depth_compare=6`, create result `0`, elapsed `19775` microseconds.
- Pipeline 2: `color_targets=0 samples=1 blend=0 depth_write=1
  depth_compare=1`, create result `0`, elapsed `5908` microseconds.
- Pipeline 3: same fields as pipeline 2, create result `0`, elapsed `2863`
  microseconds.
- Pipeline 4: `color_targets=1 samples=1 blend=0 depth_write=1
  depth_compare=1`; no matching `CREATE_RESULT` appeared in either the early
  or late bounded extraction.
- QMP before-launch SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP late-frame SHA-256:
  `e33e2a6aae9c9734a9a9fd94357e771fc0354fe539bc7505a4b185f0c6d06dbf`.
- Late QMP video frame SHA-256:
  `e0cd8a0dda8c77bed1f814badd1d616d003cb9020f6970b29b67e0d7863dbd8c`.
- Native region `[300,80,620,360]`: `0/223,200` changed pixels.
- HUD region `[200,100,400,250]`: `1,284/100,000` changed pixels;
  bounding box `[200,113,29,66]`.
- Early marker output SHA-256:
  `14061fd7ec4620ef4584f0181532916e412acaa91c02d07c71447a205ed51e81`.
- Late marker output SHA-256:
  `48e2e778257328cf68db90622be24883f8b373db99e696a920e75933ee28934b`.
- Process count: one `flutter-auto`; QMP quit and residual cleanup: PASS.

## Run-control evidence

- The first fixture attempt failed before QEMU startup because the deep
  receiver path exceeded QEMU's Unix socket length limit. The second attempt
  started QEMU but used the wrong serial prompt and was cleaned through QMP.
- The production preflight first rejected a missing run directory before QEMU
  startup; the directory was then created in the fixed receiver and the
  production run passed.
- A single short `/tmp/fluorite-qemu-run` symlink was used only as a socket
  path alias; the actual screenshots, logs, and frame sequence were written
  through it into the fixed receiver. No build/TMPDIR or second QEMU was
  created.

## Classification

- QEMU start, guest readiness, Wayland launch identity, QMP capture, and
  teardown: PASS.
- Neutral fixture selection and late native pixels: PASS.
- Production 2D HUD: PASS; production native region: FAIL.
- First observed production divergence: after three successful pipeline
  creates, the fourth create has no completion marker within the bounded
  window.
- Causal operation inside the fourth create (shader compilation, driver
  wait, or another runtime condition): UNKNOWN.
- Wayland stacking/present is not implicated by this run because production
  does not yet provide a completed fourth pipeline operation or native pixels.
