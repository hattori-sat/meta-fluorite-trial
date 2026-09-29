# FLR-0069 — compare alternate single-light identity

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0068](FLR-0068-isolate-explicit-light-count.md)
- Working log: `work/logs/2026-09-11-flr0069.md`

## Work unit

Use the same fixed image and runtime profile as FLR-0068, exclude the first
selected light (`guid=126`), and keep `FLR0026_NATIVE_LIGHT_LIMIT=1`. This
isolates light identity from light count without changing source or creating a
new image.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, one QEMU, one compositor owner, one short
  evidence directory, and QMP-only capture.
- Keep `DEFAULT` indirect light, skybox skip/clear, Sequoia model selection,
  backend, camera, and app launch constant.
- Record the selected GUID/type, QMP pixel count/bounding box, frame hash,
  selected runtime markers, and exact cleanup.
- Decide whether a different single explicit light reproduces the zero target.
  Leave the exact native operation UNKNOWN if identity comparison is not
  sufficient.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0068 selected only `guid=126 type=POINT` at limit 1 and produced
  `0/223200` model-region pixels while the HUD remained visible.
- The p6 all-lights-skipped control produced `4905/223200` model-region pixels
  under the same default-indirect and skybox-skipped conditions.

### Hypotheses

- H1: `guid=126` or its data is special; excluding it allows another single
  light to render model pixels.
- H2: any explicit light reaches the same failing shaded path; a different
  single light remains black.
- H3: selection/exclusion changes more than identity because of ordering; the
  selector markers must be checked before attributing the result to light data.

### UNKNOWN

- Exact native light/material operation, target/attachment state, and whether
  the failure is specific to one light or to explicit-light setup generally.

## Plan / Do / Check / Act

### Plan

- Run `FLR0026_NATIVE_LIGHT_SKIP_GUIDS=126` with
  `FLR0026_NATIVE_LIGHT_LIMIT=1` on the fixed p7 profile.
- Treat a failed readiness, capture, or cleanup as UNKNOWN/FAIL and preserve
  the incomplete evidence rather than interpreting it as a render result.

### Do

- Reused the fixed candidate rootfs, Mini build/TMPDIR, one compositor owner,
  and one QEMU. The first p8 start attempt was rejected by the harness because
  of a mistyped OE init path; no QEMU was started by that attempt. The second
  start with the existing `external/poky/oe-init-build-env` path passed.
- Set `FLR0026_NATIVE_LIGHT_SKIP_GUIDS=126` and
  `FLR0026_NATIVE_LIGHT_LIMIT=1`. The runtime selected only
  `guid=128 type=POINT`.
- Captured five QMP frames under
  `/mnt/yocto/flourite-qemux86-64/qemu-evidence/flr0069/p8/light-skip126-limit1/`.

### Check

- All five frames were byte-identical with SHA-256
  `ff2b959911978dbb89d47b21a992dd2f307621130a3f3863a1f0961d1c09f5e4`.
  The final 3D candidate region `[300,80,620,360]` was `0/223200` with
  bounding box `null`, region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
  The HUD region was `972/100000`, bounding box `[200,113,29,66]`.
- The runtime log was non-empty at 118936 bytes and has SHA-256
  `2ee6857b79460c6961ee8a9b2ef21daec3095dc62d03f2b69800964bd2d96098`.
  It recorded `LIGHT_SKIPPED guid=126`,
  `LIGHT_SELECTED ordinal=0 guid=128 type=POINT`,
  `LIGHT_SETUP_PLAN total=13 limit=1 selected=1`, Sequoia scene completion,
  camera application, and repeated successful queue submit/present markers.
  No selected-log fault marker was observed.
- The official teardown returned `qmp=PASS` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`. The Mini final-state
  record has SHA-256
  `95fb535b3957350f75ac41cadc65a2e2a9e56ef9733302553ec68af5c1354b61` and
  records no residual QEMU process and an absent QMP socket.

### Act

- If the alternate light is visible, split the next boundary by light data or
  setup operation before preparing a patch.
- If it is black, inspect the common explicit-light setup path on the Mac
  Devtool source and generate only a diagnostic patch if runtime evidence
  requires it. Mini remains authoritative for applying and building it.

### Verdict

- **PASS:** a different single explicit light (`guid=128`) also reproduces the
  black production 3D target under the fixed p6/p7 conditions.
- **FALSIFIED:** `guid=126` as the unique identity cause. The result follows
  the common explicit-light path for at least two POINT lights.
- **UNKNOWN:** the exact operation after light selection and whether the
  failure is in light registration, material/pipeline interaction, target
  selection, or composition.

## Handoff

- The next observation point is the existing opt-in
  `FLR0026_NATIVE_LIGHT_OPERATION_TRACE`, which records native light state
  after `BuildLightAndAddToScene` without changing the production default.
- This is split to [FLR-0070](FLR-0070-trace-explicit-light-operation.md).
