# FLR-0402 Dimension-Aware QMP Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make QMP analysis use each PPM's real dimensions and report unavailable fixed ROIs without hiding genuine analysis failures.

**Architecture:** Add a `full` region sentinel to the existing pixel analyzer, resolved only after `_read_ppm()` has read image dimensions. Have the live observer analyze `full` first, parse its JSON dimensions, and skip only named fixed ROIs that do not fit; malformed PPMs, subprocess errors, and in-bounds failures remain fatal.

**Tech Stack:** Python 3, `unittest`, P6 PPM parser, JSON subprocess result, QMP evidence files.

**Spec:** `work/tickets/FLR-0402-dimension-aware-qmp-analysis.md`

## Global Constraints

- Do not change product source, image, recipe, launch profile, materials, lighting, QEMU, build, caches, or Mini TMPDIR.
- Keep explicit numeric ROI validation strict; do not clip or resize captures.
- Only mark a named ROI skipped when its rectangle exceeds the actual PPM dimensions, and log the actual dimensions and requested coordinates.
- Keep raw captures on Mini; local QMP review data is limited to the exact FLR-0401 regression inputs.
- Commit locally without push; use the official bundle helper before a later Mini runtime needs this helper revision.

---

### Task 1: Add failing tests for full-frame dimensions and missing fixed ROIs

**Files:**
- Modify: `tests/test_qemu_pixel_capture.py`
- Modify: `tests/test_flr0399_live_capture.py`
- Test inputs: temporary synthetic 4x3 and 720x400 P6 PPM files; exact 720x400 and 1280x800 FLR-0401 captures for replay

**Interfaces:**
- Consumes: `qemu_pixel_capture.analyze(path, region, reference, background, threshold)` and `live_capture._analyze_capture(run_dir, image)`.
- Produces: `analyze(..., "full", ...)` dimensions and per-region observer logs.

- [x] **Step 1: Test `full` against a tiny PPM.** Write a 4x3 black P6 image with the existing `write_ppm()` helper and assert `MODULE.analyze(image, "full", None, "0,0,0", 8)["width"] == 4` and `height == 3`.
- [x] **Step 2: Test 720x400 observer behavior.** Add a small PPM writer to `tests/test_flr0399_live_capture.py`; create a temporary P6 PPM with header `P6\n720 400\n255\n` and exactly `720 * 400 * 3` zero bytes. Call `_analyze_capture()`, then assert full/HUD logs contain successful JSON dimensions and the Sequoia log contains `SKIPPED_OUTSIDE_CAPTURE` with `[440,220,400,360]`.
- [x] **Step 3: Test fail-closed behavior.** Pass a malformed PPM and assert `_analyze_capture()` raises instead of emitting a skip result. Retain the existing explicit numeric-region out-of-bounds test unchanged.
- [x] **Step 4: Run the new tests and confirm red.** Ran `python3 -B -m unittest tests.test_qemu_pixel_capture.QemuPixelCaptureTests.test_analyze_full_region_uses_ppm_dimensions tests.test_flr0399_live_capture.QmpAnalysisTests -v`: direct `full` parsing and the valid 720x400 observer case failed as expected; malformed PPM remained fatal.

### Task 2: Implement only dimension-aware full/ROI analysis

**Files:**
- Modify: `scripts/qemu-pixel-capture.py`
- Modify: `scripts/flr0399_live_capture.py`
- Test: both test files from Task 1

**Interfaces:**
- `qemu-pixel-capture.py analyze --region full` returns the existing JSON result over `[0,0,width,height]` from the PPM header.
- `_analyze_capture(run_dir, image)` writes the existing full/HUD/Sequoia logs; unavailable fixed ROIs produce a JSON status record and do not stop later in-bounds regions.

- [x] **Step 1: Resolve the `full` token in `_parse_region()`.** After dimensions are known, return `(0, 0, width, height)` only for the exact token `full`; retain the current parser and bounds errors for numeric input. Nonpositive dimensions fail closed.
- [x] **Step 2: Analyze full first in `_analyze_capture()`.** Invoke the existing subprocess with `--region full`, write stdout/stderr to the full log, and keep a nonzero return fatal. Parse the returned JSON and require positive integer `width` and `height` plus the exact full rectangle; malformed output fails rather than silently skipping.
- [x] **Step 3: Gate named ROIs against those dimensions.** For each fixed numeric ROI, compare `x + roi_width <= width` and `y + roi_height <= height`. If false, write JSON containing status `SKIPPED_OUTSIDE_CAPTURE`, width, height, and ROI, then continue. Otherwise invoke the unchanged analyzer and treat any nonzero result as fatal.
- [x] **Step 4: Run focused tests green.** Ran `python3 -B -m unittest tests.test_qemu_pixel_capture tests.test_flr0399_live_capture -v`; all 78 tests passed, including strict numeric bounds and malformed PPM failure.

### Task 3: Replay the exact FLR-0401 captures and close locally

**Files:**
- Verify: exact FLR-0401 720x400 pre-launch and 1280x800 PRESENT_UNMATCHED QMP PPMs
- Update: FLR-0402 ticket, working log, `TASKS.md`, implementation plan

- [x] **Step 1: Replay the 720x400 pre-launch PPM.** Required `full` analysis reported 720x400 and Sequoia was explicitly skipped; HUD analysis completed without observer failure.
- [x] **Step 2: Replay the 1280x800 live frame.** Full/HUD/Sequoia metrics remained 8,139 changed / 1,192 HUD chromatic / 144,000 black Sequoia pixels.
- [x] **Step 3: Run canonical, privacy, whitespace, runtime-checkpoint, focused test, and file-size gates.** Do not start QEMU or BitBake. Canonical/privacy/whitespace/runtime-checkpoint/focused-test/file-size pass; Markdown still reports only the 11 documented historical missing links.
- [x] **Step 4: Commit only this ticket's helper/tests/records locally.** The closeout is included in the atomic transition to FLR-0403; no push and no unrelated product files. FLR-0401 PNG/MP4 evidence remains unchanged.

## Self-review

- Spec coverage: exact PPM dimensions, strict numeric ROI validation, explicit skip logging, real analysis-error propagation, and both observed resolutions are tested.
- No resizing, clipping, target input, product source, build, or QEMU action can create a false visual pass.
- The exact 1280x800 pixel counts remain an acceptance regression; 720x400 tests only the helper boundary and cannot establish rendering.
