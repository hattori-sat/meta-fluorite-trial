# FLR-0094 — neutral fixture and production QMP evidence

## Outcome

The same authoritative Mini image rendered the self-made native fixture but
not the production scene. QMP captured the guest framebuffer directly: the
fixture has native pixels and the production case has only the 2D HUD. The
shared QEMU, Wayland launch, QMP capture, and teardown path therefore works;
the stable divergence is in the production scene path.

## Fixed inputs

- Canonical layer commit: `054e3c549246d93d1d0ba16afdcd277d9c525433`.
- Devtool source commits: `6517bad` and `6bce593`.
- Generated patch `0209` SHA-256:
  `a00c48f5af27d92e4c24b3c2a8a96ca2495211e6ad201e496a0d7552f4ea2f27`.
- Generated patch `0210` SHA-256:
  `8fd488c7d5cd1aaceb4a7f333e0c8193e61583051aae685d6548bae9cda76a8b`.
- QEMU qemuboot SHA-256:
  `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`.
- QEMU kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QEMU rootfs SHA-256:
  `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`.
- Machine: `qemux86-64`.
- Raw evidence root: `$RECEIVER/evidence/flr0094-neutral-fixture/`.

## Build gates

- Effective image metadata: PASS; `0209` and `0210` are present in the
  effective `flutter-auto` source URI.
- `flutter-auto:do_patch`: PASS; 104 tasks attempted and all succeeded.
- `flutter-auto:do_compile`: PASS; 2686 tasks attempted and all succeeded.
- `agl-ivi-image-flutter`: PASS; 11748 tasks attempted and all succeeded.
- Effective `TMPDIR` is the existing fixed TMPDIR; no additional build or
  cache directory was created.

## Fixture case

Conditions were `FLUORITE_NATIVE_PURE_FIXTURE=1`,
`FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`, and the existing pipeline trace. The
installed bundle was launched as `agl-driver` with
`XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, and app id
`fluorite`.

All raw files are under
`$RECEIVER/evidence/flr0094-neutral-fixture/fixture-run/`.

- QMP before-launch PPM SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP final PPM SHA-256:
  `0ff2532cb9d59c1d939ea7c4a9764641f36176845c3a7179483bb179c6cf34f3`.
- Final frame: 1280x800.
- Native region `[300,80,620,360]`: `41,750/223,200` changed pixels;
  bounding box `[501,278,278,162]`.
- HUD region `[200,100,400,250]`: `6,189/100,000` changed pixels.
- QMP video: 20 PPM frames; first SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`, last
  SHA-256 `f9b0d4ee5f0b20bc5ed63636f25eb33e785374fb5b3ce9218b01314c3ba2b5c6`.
- Runtime log tail SHA-256:
  `2d6b883613b5b6680d54281bc967f65d7b7c6a63fc8ee22542f3eda5b87b9555`.
- Process count recorded after launch: `1` `flutter-auto`.
- QMP capabilities, QMP quit, residual-target detection, and socket cleanup:
  PASS.

The fixture runtime log contains repeated `Light not found` handler messages
for entities 164, 166, 168, and 170, but it also contains successful queue
present results and the QMP native pixels. This is a non-fatal fixture-side
diagnostic inconsistency, not evidence that the display path is black.

## Production case

The same launch and capture profile was used with only
`FLUORITE_VK_PIPELINE_INPUT_TRACE=1`; fixture controls were unset.

All raw files are under
`$RECEIVER/evidence/flr0094-neutral-fixture/production-run/`.

- QMP before-launch PPM SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP final PPM SHA-256:
  `b8ea31ea008e2f4fd26f734a1dce44e1d61f49ffc11b27773c8776cbcc307670`.
- Final frame: 1280x800.
- Native region `[300,80,620,360]`: `0/223,200` changed pixels.
- HUD region `[200,100,400,250]`: `1,284/100,000` changed pixels;
  bounding box `[200,113,29,66]`.
- QMP video: 20 PPM frames; first SHA-256 is the same pre-launch frame above,
  last SHA-256 `e80c61995350649652547b0703f0d34170ab074bdef212e4f14bced6893a5733`.
- Runtime log tail SHA-256:
  `5a1a7ea983c874be80aebbd3a776febde46caaf5de97066686d834336a4d86f2`.
- Process count recorded after launch: `1` `flutter-auto`.
- The app id was `fluorite`. Four pipeline-input records were observed; the
  first three returned create result `0`, while the fourth had no completion
  marker in the bounded log.
- QMP capabilities, QMP quit, residual-target detection, and socket cleanup:
  PASS.

## Classification

- Neutral fixture native 3D: PASS.
- Production native 3D: FAIL; the 2D HUD remains visible.
- Shared QEMU/QMP/Wayland launch path: PASS.
- Fixture/production split: confirmed on the same image.
- Exact production resource/pipeline operation causing the split: UNKNOWN.
- This ticket does not change fence/present behavior and does not claim a
  production fix.
