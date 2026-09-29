# FLR-0081 — current-image minimal geometry pixel control

- Status: Waiting
- Priority: High
- Owner: Mini QEMU runtime + Filament/Wayland boundary roles
- Created: 2026-09-11
- Depends on: [FLR-0080](FLR-0080-current-image-frame-recovery.md), [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-11-flr0081.md`

## Work unit

Run the existing self-made minimal-geometry path on the current 0208 image
without the `NATIVE_PURE_FIXTURE` scene-content shortcut. Skip production model
loading and environment setup, create the known eight-vertex cube, and keep the
ready-fence diagnostic common. This isolates the current image's minimal native
draw/present path from production assets and the pure-fixture control.

This is runtime diagnosis only. Existing diagnostic switches are not product
behavior and no source patch is justified before the QMP pixel result.

## Success criteria

- Reuse the fixed Mini image/build/TMPDIR, one QEMU, one compositor owner, and
  the established serial/QMP harness.
- Use `FLR0026_NATIVE_SKIP_MODEL_LOAD=1`,
  `FLR0026_NATIVE_SKIP_ENVIRONMENT=1`,
  `FLR0026_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1`, sync trace, and force-render.
- Prove no pre-existing `flutter-auto`, then exactly one fixture process.
- Capture QMP-only frames and analyze the native candidate and HUD regions.
- Correlate minimal-geometry readiness with queue submit/present,
  present-boundary, commit, and actual recognizable cube pixels.
- Preserve any failed command/output and complete negotiated QMP teardown with
  zero residual targets.

## Facts

- FLR-0079 p13's pure-fixture profile was black and stopped before the
  present-boundary marker.
- FLR-0080 p14 changed frame status to ready but still produced no
  `VK_QUEUE_PRESENT` or visible pixels.
- Historical FLR-0026/FLR-0042 runs prove that the existing minimal geometry
  implementation can produce a recognizable blue cube on an earlier image.

## Hypotheses

1. **The current image's minimal native path still works.** The skip-model /
   skip-environment profile reaches present and shows the cube; the production
   or pure-fixture setup is the remaining boundary.
2. **The current image's driver/present path is broken independently of scene
   content.** Minimal geometry reaches setup but remains black or stops before
   present.
3. **The pure-fixture shortcut itself changes the command stream.** The
   minimal-geometry path differs in present markers or pixels even though both
   use the same current image.

## UNKNOWN

- Whether the current 0208 image can render the known minimal cube without a
  source change.
- Whether a successful cube would be composited with the Flutter HUD; combined
  production 2D+3D remains a separate gate.

## Plan / Do / Check / Act

### Plan

Use one new evidence directory under `$QEMU_EVIDENCE_ROOT/flr0081`, keep the
same rootfs hashes and QEMU profile as p13/p14, and vary only the scene setup
profile defined in this ticket. Stop before patching if the minimal control is
still negative.

### Do

- p15 ran the skip-model/skip-environment/minimal-geometry profile with the
  ready-fence override. It reached native minimal-geometry readiness and
  `FRAME_BEGIN started=true`, but produced no queue/present/commit marker and
  all five QMP frames were black.
- p16 repeated the same profile with the existing
  `FLR0026_COMMAND_EXECUTION_TRACE=1` switch. The preflight, start,
  guest-ready, serial-exec, single-process, QMP capture, and QMP teardown
  gates all passed. The captured `flutter-auto` owner was one `agl-driver`
  process; its PID is retained only in the external evidence log.
- p16's runtime marker output contains 31
  `FLR0026_RENDERER_COMMIT_ENQUEUE` and 31
  `FLR0026_FRAME_FENCE_WAIT_UNLINKED_READY` lines, plus three sampled
  `FRAME_BEGIN started=true` lines. It contains zero
  `FLR0026_COMMAND_EXECUTE_BEGIN`, `FLR0026_VK_QUEUE_PRESENT`, and
  `FLR0026_VK_COMMIT_DONE` lines.
- A guest `strings` check found the command-execution, commit, and present
  marker strings in `/usr/bin/flutter-auto`, so the zero execution markers are
  not explained by a missing diagnostic binary.

### Check

- p15 and p16 each produced five identical 1280x800 QMP frames with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The native candidate region was `0/223200`; the HUD region was `0/100000`.
- H1 is falsified for the current image: minimal geometry setup and frame
  begin can be reached, but no current-image cube pixels were presented.
- H2 is supported: the negative result is independent of production model,
  environment, and pure-fixture scene shortcuts. The first observed
  source-controllable candidate is between renderer enqueue and command-stream
  execution/present.
- H3 is not supported as the primary explanation: the pure-fixture and
  skip-content profiles converge on the same black QMP result, although the
  pure-fixture profile has a different fence/present marker prefix.
- This is not a production 3D success and not evidence that the 2D parent
  alone is masking a valid current-image cube.

### Act

Leave this runtime control Waiting and create [FLR-0083](FLR-0083-current-image-command-stream-boundary.md).
Inspect the current Filament command-stream worker/driver boundary before
changing production resources or composition. No product patch is justified
by p15/p16 alone.

## Visual evidence

Raw frames and runtime logs remain outside Git under
`$QEMU_EVIDENCE_ROOT/flr0081`; record paths, hashes, region counts, selected
markers, and teardown output here after the run.

- p16 evidence directory: `$QEMU_EVIDENCE_ROOT/flr0081/p16`.
  `runtime-markers-output.log` SHA-256 is
  `b394e6e033df8536e7ca07e9d5ab6ebc86535de187a4d3cce5023e11d8283e43`;
  `pixel-analysis.log` SHA-256 is
  `9aa1281d8d1f22c9e828176b09f94389c4336fdff8f9a69dc460c6ee9005a836`;
  `binary-markers-output.log` SHA-256 is
  `e4078a9774aa1b238966fba6c3c4785c787c32d1bc359d638063ecdb5414b453`.
  QMP quit accepted and cleanup reported residual process/socket counts of
  zero.
