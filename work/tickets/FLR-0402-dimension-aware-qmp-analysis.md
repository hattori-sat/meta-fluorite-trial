# FLR-0402 — make QMP analysis dimension-aware

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mac observer/test source / QMP pixel-analysis helper / evidence roles
- Branch: `feature-flr-0402-dimension-aware-qmp-analysis` (create from the FLR-0401 tip)
- Dependency: [FLR-0401](FLR-0401-capture-live-fengine-present-stack.md), run `flr0401-0001`
- Plan: [FLR-0402 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0402-dimension-aware-qmp-analysis.md)
- Working log: [FLR-0402 working log](../logs/2026-10-02-flr0402.md)

## Objective

Make the QMP postprocessor analyze a PPM's actual dimensions. A smaller valid
capture must not turn an otherwise completed runtime into an observer failure;
fixed named ROIs outside that capture must be recorded as explicitly skipped.
Malformed PPMs and real analyzer errors must still fail closed.

## Facts, inferences, hypotheses, and UNKNOWN

### Facts

- In FLR-0401, the first valid QMP PPM was 720x400. `_analyze_capture()` in
  `scripts/flr0399_live_capture.py` supplied a hard-coded full region
  `0,0,1280,800`; `scripts/qemu-pixel-capture.py` correctly rejected it with
  `region extends outside the PPM image`.
- That error occurred after the exact-image runtime, live QMP still, GDB stack,
  kernel query, and teardown had completed. The observer therefore exited
  `FAIL` even though valid runtime evidence existed.
- The live READY/PRESENT_UNMATCHED captures are 1280x800 and were successfully
  analyzed with the existing fixed HUD and Sequoia ROIs when those dimensions
  were supplied.
- The pixel reader already parses width and height from the P6 PPM header, and
  `_parse_region()` must continue rejecting out-of-bounds explicit coordinates.
- FLR-0401's raw 720x400 pre-launch PPM remains on Mini at
  `$BUILD_EVIDENCE/flr0401-0001/qemu/FLR-0399-pre-launch.ppm`; the visual/runtime
  result is in [its evidence manifest](../evidence/FLR-0401-0001.md).

### Inferences

- The first divergence is in host-side analysis geometry, after QMP capture.
  Enlarging or rewriting the PPM would falsify pixel measurements; deriving
  `full` from the parsed header and explicitly skipping unavailable named ROIs
  preserves the evidence.
- This correction does not alter Flutter, Filament, QEMU, the image, or the
  display. It prevents a tooling failure from obscuring an already captured
  runtime result.

### Hypotheses

1. **Fixed caller geometry is the complete FLR-0401 post-analysis failure.**
   Support: a synthetic 720x400 PPM fails with `full` before the change and
   succeeds after; the Sequoia ROI is marked out of capture, while HUD analysis
   runs. Refutation: the same fixture still fails after `full` uses parsed
   dimensions or the analyzer identifies a second malformed-data condition.
2. **The source PPM itself is malformed.** Support: `_read_ppm()` rejects its
   header/payload independently of requested region. Refutation: the raw P6
   header/payload is valid and dynamic `full` analysis returns dimensions and
   pixel metrics. Do not weaken PPM or explicit-region validation to make this
   hypothesis pass.

### UNKNOWN

- Whether the next product runtime reproduces the same lower-resolution first
  capture; FLR-0401 already provides the exact 720x400 regression artifact.
- Product rendering remains separately UNKNOWN/negative: FLR-0401's live
  Sequoia ROI was black. This ticket cannot change that result.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | Full-frame analysis follows PPM dimensions; fixed named ROIs skip only when unavailable |
| Where | `qemu-pixel-capture.py` and FLR-0399 observer post-processing on Mac/Mini roles |
| When | For every saved QMP PPM, including pre-launch and live captures |
| Who | Observer/test source and QMP analysis helper |
| How | Regression tests, then replay analysis on the exact FLR-0401 PPMs; no QEMU |

## Scope and controls

- Change only QMP post-processing and its tests. Do not change product source,
  patch stack, image, launch flags, camera, materials, lighting, build/cache,
  Mini TMPDIR, or QEMU runtime.
- Keep explicit numeric ROI bounds strict. `full` means the complete PPM as
  read; `sequoia` and `hud` retain their current absolute pixel coordinates.
- When a named ROI does not fit, write a machine-readable
  `SKIPPED_OUTSIDE_CAPTURE` result with capture dimensions and ROI coordinates,
  then continue with other available ROIs. Do not turn malformed PPM, invalid
  JSON, subprocess failure, or in-bounds analysis failure into a skip.
- No BitBake, build, new QEMU, or cache operation is in scope. The exact
  FLR-0401 raw capture is replay input; do not reuse its consumed runtime ID.
- Local commits are allowed; do not push. Before a later Mini runtime, transfer
  the exact committed helper through the official bundle workflow.

## Success criteria

1. `qemu-pixel-capture.py analyze --region full` uses the image's parsed
   dimensions and preserves strict validation for explicit coordinates.
2. `_analyze_capture()` on a valid 720x400 PPM records successful full/HUD
   analysis and explicit out-of-capture Sequoia ROI skip, then returns without
   raising. A malformed PPM or genuine analyzer failure still raises and is
   logged.
3. On the exact FLR-0401 1280x800 `PRESENT_UNMATCHED` PPM, full/HUD/Sequoia
   analysis succeeds and preserves the established counts (full changed 8,139,
   HUD chromatic 1,192, Sequoia 144,000 black).
4. The 720x400 and 1280x800 regressions pass in the focused tests; no QEMU,
   BitBake, image, or product change occurs.
5. Record the red/green test outputs and exact replay outputs in this ticket's
   working log, then commit the scoped helper/tests/records locally without
   push.

## Plan / Do / Check / Act

### Plan

- Add one direct pixel-helper regression for the `full` sentinel and observer
  integration coverage for smaller dimensions, unavailable ROIs, valid 1280x800
  ROIs, and fail-closed malformed input.
- Change the pixel helper to resolve `full` from `_read_ppm()` dimensions.
  Change the observer to run full analysis first, consume its JSON dimensions,
  and explicitly log only those fixed named ROIs that do not fit.
- Replay the exact FLR-0401 pre-launch and live PPMs locally. Do not launch
  QEMU or build an image for this tooling-only task.

### Do

- TDD red: the direct `full` test failed with “region must be
  x,y,width,height”; the valid synthetic 720x400 observer test failed at the
  fixed full-frame ROI. The malformed PPM test passed by remaining fatal.
- Implemented the exact `full` sentinel in the pixel analyzer. The observer
  now analyzes full first, requires positive integer dimensions and the exact
  full rectangle in JSON, and logs `SKIPPED_OUTSIDE_CAPTURE` only for named
  fixed ROIs that do not fit. Numeric ROI parsing and bounds remain unchanged.
- Exact Mini PPMs were retrieved read-only to one temporary local directory
  after verifying their Mini SHA-256 values. The initial historical
  `/mnt/yocto/evidence` assumption was wrong and `BUILD_EVIDENCE` was unset in
  a clean noninteractive SSH; the run was found by its exact ID under the
  authoritative receiver's `evidence/` tree. No raw file was modified or
  committed.

### Check

- Focused suite: `python3 -B -m unittest tests.test_qemu_pixel_capture
  tests.test_flr0399_live_capture -v` → 78/78 PASS.
- Exact PPM replay preserved Mini hashes: pre-launch
  `2c8f4afeae360ccd450c79ccb74408db6a3b38bc526b062aed91989f7d98f8b4`
  (720x400; Sequoia ROI skipped; HUD 0 chromatic) and live
  `5511064a97cbef85b76cd44809e258f334cf9b18298fd1bfd47c2c894e740f1c`
  (1280x800; full 8,139 changed; HUD 1,192 chromatic; Sequoia 144,000 black,
  0 edge/chromatic). This is analyzer regression evidence; product rendering
  remains negative.
- `git diff --check` passed. A supplemental `py_compile` attempt failed
  because Python tried to write bytecode into a host cache outside the
  workspace; the focused unittest imported all four changed Python modules
  successfully. Canonical, privacy, runtime-checkpoint, whitespace, and
  file-size gates passed. Markdown reports only 11 historical missing links;
  no FLR-0402 link is missing.

### Act

- Keep this ticket scoped to analysis dimensions. The Oops TID-to-GDB LWP/ELF
  mapping is a separate product diagnostic after this helper is verified.
  The clean-SSH `BUILD_EVIDENCE` role discovery gap is separate and must not
  be hidden inside this tooling fix.

## Impact

- **Build-time / packaging:** none; no Yocto recipe or image change.
- **Runtime:** none in this ticket; only previously captured QMP PPMs are
  replayed.
- **Integration risk:** silently clipping or skipping a real rendering error
  could hide evidence. Preserve numeric-region validation, emit explicit skip
  records only for bounds that exceed the actual PPM, and keep all other
  subprocess/parse errors fatal.
