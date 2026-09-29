# FLR-0286 — reproduce known-good combined Sequoia HUD and light pixels

- Status: Waiting
- Priority: High
- Owner: runtime validation + Flutter/Filament composition roles
- Created: 2026-09-25
- Predecessor: [FLR-0285](FLR-0285-trace-production-draw-command-boundary.md)
- Working log: `work/logs/2026-09-25-flr0286.md`

## Objective

Reproduce the historical same-frame condition containing the Flutter HUD,
Sequoia geometry, and light-colored pixels before changing the current
production scene or creating a new source patch.

## Acceptance gate

One QMP-only 1280x800 frame from the current authoritative image must show all
of the following at once:

1. Flutter HUD including CPU/FPS/Scenes pixels;
2. recognizable Sequoia geometry in the native region;
3. non-grayscale light-colored pixels, including a red-lamp candidate when the
   selected condition contains the known tail-light material;
4. runtime markers for model selection/scene-add, frame start, and present;
5. one `flutter-auto`, one QEMU, and clean QMP teardown with zero residuals.

## Historical baseline

- FLR-0066 retained a reproducible HUD plus controlled Sequoia diagnostic frame:
  `3290/223200` native candidate pixels and `3158/100000` HUD pixels,
  frame SHA-256
  `7c9f6c73b9360fa37795d71fe68fc6fd75ae09ebf7e6a4393dd93accedd5479e`.
- FLR-0070 p9 retained a one-light/operation-trace frame with HUD and Sequoia
  pixels: `5510/223200` native candidate pixels and `3961/100000` HUD pixels,
  frame SHA-256
  `3bc9fc3442750f1331f1baf43f55ec212f02b59a8c191712b461edea8254dd06`.
  FLR-0071/0072 did not reproduce this on a later image, so it is a
  historical discriminator, not a product fix.
- FLR-0049 provides the stable lighted Sequoia/red-tail visual reference, but
  its native surface masked the Flutter HUD. It is not sufficient for the
  combined acceptance gate by itself.
- FLR-0251 and FLR-0235 prove that the base current image can compose HUD and a
  self-made native 3D fixture in one QMP frame.

## Facts, hypotheses, and UNKNOWN

### Facts

- The latest FLR-0285 SSH run reached Sequoia scene-add and present.
- With production light enabled it showed HUD only; with diagnostic light and
  shape suppression it showed geometry but not the intended combined frame.
- The current failure is therefore not yet attributable to model loading or
  QEMU memory.
- The FLR-0066 historical diagnostic profile was replayed on the current
  image. It reached draw/present, but the QMP frame was grayscale and clipped;
  it did not meet the same-frame acceptance gate.
- The FLR-0070 p9 one-light profile was replayed after temporarily removing
  the guest Weston shell-client extension. It reached model/draw/present, but
  the early QMP frame was uniform gray (`224,224,224`) with zero chromatic
  pixels. The current image therefore does not reproduce the historical p9
  colored result.
- QMP teardown and compositor restoration passed. No QEMU or flutter-auto
  residual remained.

### Hypotheses

1. The historical combined frame requires the transparent skipped-skybox and
   compositor-owner/frame controls retained by FLR-0066.
2. One-light operation or observation timing changes the native output path;
   FLR-0070 p9 is the discriminator.
3. The present production-light path still fails after the combined diagnostic
   baseline, at material/resource or target composition.

### UNKNOWN

- Whether FLR-0070's historical colored result is deterministic or a
  diagnostic timing side effect; the current replay did not reproduce it.
- The first light/material/environment stage that removes the vehicle or its
  color from the same-frame result.
- The persistent runtime-log hash for this run, because the guest log was not
  copied before QEMU teardown.

## Verification plan

- Reuse the existing Mini build/TMPDIR/rootfs/QEMU roles and 4096 MiB.
- Use guest SSH for one explicit `flutter-auto` launch; do not use the
  unreliable serial-login path.
- Replay the FLR-0066 diagnostic profile first, then the FLR-0070 one-light
  trace profile, then the same profile without trace and with timing-only
  control.
- Restore environment, indirect light, direct lights, and shapes one at a
  time. Retain QMP frames, bounded logs, hashes, and cleanup for every case.
- Do not edit source or generated patches until a specific first divergence is
  identified.

## Visual evidence

Evidence is retained under the fixed Mini `$EVIDENCE_ROOT/flr0286-*` role path.
The current negative frames are:

- normal-owner diagnostic replay:
  `flr0286-0001/combined-diagnostic.ppm`, SHA-256
  `3c2769cbcff1eb225e9115968663da97433e1d8026c6065be34bdb6edbbebede`;
- owner-isolated replay:
  `flr0286-0001/owner-isolated-1280x800-late/combined-diagnostic.ppm`,
  SHA-256 `0e74c7e5535379cdb2c41340c0931c2d8091fad96d5be6cb3a86d7f5b7063877`;
- p9 one-light early replay:
  `flr0286-0001/p9-one-light/early.ppm`, SHA-256
  `a4ffc7bb0f07ccbc213989a8874f2a80755d84d808f3b85e39fdc10c68056bbb`.

No frame met the acceptance gate. Runtime-log persistence is a known evidence
gap and is recorded above; the next run must close it before teardown.

## 2026-09-25 fixture control replay

The historical HUD plus self-made 3D condition is confirmed; the earlier
interpretation that HUD plus native 3D had not been reproduced was incorrect.

- FLR-0285 run `flr0285-0004` on the same rootfs proved the self-made
  Filament fixture plus HUD: native center ROI `92352` chromatic pixels and
  HUD ROI `2845` chromatic pixels. Frame SHA:
  `f4d5eb2a32c6ef3a97ba13b3cef1a694f836f49656abc717bfc9c604dc0dffa1`.
- FLR-0286 run `flr0286-0002` with `FLUORITE_NATIVE_VISIBLE_SHM_CUBE=1`
  reached SHM ready/attached, minimal geometry ready, draw submit/end, and
  present, but QMP was completely black. This is a separate SHM diagnostic
  path, not evidence against Filament fixture rendering. Frame SHA:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Removing only `VISIBLE_SHM_CUBE` restored the direct Filament fixture plus
  HUD in the same QEMU/rootfs. Native ROI `(440,220,400,360)` had `92648`
  changed and `92648` chromatic pixels; HUD ROI `(1120,0,160,80)` had `2915`
  chromatic pixels. Frame SHA:
  `41148f5edbbfa1e7985cc1018c56e31b30c5edb88214c602c2bfb396b6988ee6`.
- The positive runtime log was copied before teardown. Log SHA:
  `bc057d0684ad66bc381c3508001fcd93ca8bfcbf6885647b359c07ebecb0b885`.

## Source change and Devtool provenance

- The fixture function was `UNLIT` and created no light entity. The opt-in
  source change adds `FLUORITE_NATIVE_FIXTURE_LIGHT=1`, switches only that
  fixture to `LIT`, creates one Filament `SUN` at intensity `110000`, and
  owns its entity in the destructor. Production and default fixture behavior
  remain unchanged.
- Mac Devtool baseline: `e716e620f127ef81cb3ce88ed5d5d0ac97590cee`.
- Source commit: `ab69cd312fe5a743517ac625dccc7f312154ac25`.
- Official generated patch: `0295-flr0286-opt-in-lit-fixture-light-devtool.patch`.
  SHA-256: `1eb6c2e762b26dd9b556f3533ac75e5e861fb3b0b7152d0c8e00e7d3c3e1035f`.
- The first update-recipe attempt exposed a stale missing sdbus-cpp
  submodule baseline (`736394...`). The existing component-rebase flow
  re-registered the component at the effective baseline and generated 0295
  deterministically; no patch body was hand-written or edited.
- The Mac `do_patch` gate parsed successfully but stopped before task
  execution because the fixed container tmpfs had `0.505GB` free. This is a
  host resource gate, not a patch application failure; the Mini PC remains
  authoritative for `do_patch` and the build.

## 2026-09-25 opt-in lit fixture runtime

The official patch was transferred as bundle SHA-256
`7329266e66f5d4e9bfd0029ce3e24918ba536c5ade1bf0cce02ffbba277fa7f5` and the
fixed Mini receiver reached commit `4e641892fbe843bd67558bc3bbe09b1f66b53992`.
Mini `do_patch`, `do_compile`, and `agl-ivi-image-flutter` all passed. The
runtime artifact identities were:

- rootfs SHA-256 `08ee47d01cced5139a724284462c6b3f23bf687c05a342202282a34122a7d65d`;
- kernel SHA-256 `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`;
- qemuboot SHA-256 `9ebc03d4fa1842fbc71c15bc8c9c91fd7d13050d588f3e5a0eef21d269b1fe81`.

One QEMU run used 4096 MiB and the direct Filament fixture with only
`FLUORITE_NATIVE_FIXTURE_LIGHT=1` added to the known-positive control. The
QMP-only frame is retained at
`/mnt/yocto/evidence/flr0286-0003/fixture-lit-light.ppm`, SHA-256
`42b731f4f71956f7d20e73e19bc72289f0a27c665ba23964e227333f70425e24`.
The bounded 12-frame QMP video is under
`/mnt/yocto/evidence/flr0286-0003/fixture-lit-light-video/`.

The same frame contains the HUD and lit fixture geometry:

- native ROI `(440,220,400,360)`: `119716/144000` changed and chromatic
  pixels, max chroma `95`, geometry indicator present;
- HUD ROI `(1120,0,160,80)`: `2845` chromatic pixels, geometry indicator
  present;
- runtime log SHA-256
  `063775800d510e58a89883573bd5f921d75fe720946ad35dfc09191759c628c3`.

The saved log contains `FLUORITE_NATIVE_MATERIAL_BRANCH ... shading=lit` and
the fixture setup/present path. The expected
`FLUORITE_NATIVE_FIXTURE_LIGHT_SETUP_DONE` line is absent because the log was
copied before the asynchronous setup output was fully flushed; this is an
evidence-timing defect, not proof that the light entity was not created. The
next run must wait for the explicit light marker before copying the log.

QMP teardown passed with `capabilities=negotiated quit=accepted` and cleanup
passed with zero residual QEMU/QMP targets. This is a positive control for the
Filament LIT/light/material/composition path, but it does not yet satisfy the
Sequoia vehicle acceptance gate.
