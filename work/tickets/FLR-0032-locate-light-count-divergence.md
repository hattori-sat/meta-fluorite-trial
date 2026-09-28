# FLR-0032 — locate the light-count divergence

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0031](FLR-0031-isolate-lit-light-trigger.md)
- Working log: `work/logs/2026-09-06-flr0032.md`

## Problem

FLR-0031 established a real QMP-visible 3D result with one and two selected `POINT` lights, while the same image and scene setup with all thirteen selected lights shows only the 2D HUD. Both variants reach `VK_QUEUE_PRESENT result=0`; the first failing count is not yet known.

## Purpose

Find a reproducible prefix-count boundary where the QMP result changes from visible 3D to HUD-only, without changing the image, QEMU profile, launch path, or diagnostic skip controls.

## Success measure

- Test only the unverified range 3–12, using one variable per run.
- Record selector markers, QMP-only screenshot, screenshot hash, present/fault markers, and clean teardown for every decisive boundary.
- Record whether the result proves only a prefix boundary or also identifies a particular GUID/parameter; leave the latter UNKNOWN if the selector cannot make a same-count alternative.
- Keep the diagnostic selector out of the default production behavior.
- Close this ticket before choosing a permanent fix or beginning scene-transition validation.

## Hypotheses

1. A count threshold exists between two and thirteen selected lights. Prediction: a prefix count becomes HUD-only and binary search narrows the threshold.
2. A particular later light or parameter is responsible. Prediction: a same-count alternative selection changes the result.
3. The full-scene model/environment path is required. Prediction: the threshold disappears when the diagnostic skip controls are removed; that must be a separate explicitly recorded comparison.

## PDCA

### Plan

- Reuse the exact rootfs and fixed QEMU profile from FLR-0031.
- Start with counts 7 and 4, then narrow the interval; retain guest SSH launch and QMP-only screenshots.

### Do

- Use the existing Mac-generated diagnostic patch and the already-built Mini PC image.
- Do not create a new container, volume, TMPDIR, receiver, or generated patch for this runtime matrix.

### Runtime evidence

All runs used the Mini PC image from commit `6b33295`, the same QEMU profile and guest SSH launch as FLR-0031, and the diagnostic environment with model/environment loading skipped. QMP screenshots were captured before QMP `quit`; no run left a QEMU process or QMP socket.

| Prefix | Selector evidence | QMP PPM SHA-256 | Visual result | Runtime markers |
| --- | --- | --- | --- | --- |
| 4 | `total=13 limit=4 selected=4`; GUIDs `126,128,130,132`, all `POINT` | `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b` | same multi-primitive 3D image as 1/2 | 26 present-result-0 markers; no fault marker |
| 5 | `total=13 limit=5 selected=5`; GUIDs `126..134`, all `POINT` | `98e8046205895e0779a1f49f00e4c03f1cc75bc5ce2936ee9b03b658427bf694` | large black 3D polygon; no HUD | 17 present-result-0 markers; no fault marker |
| 6 | `total=13 limit=6 selected=6`; GUIDs `126..136`, all `POINT` | `7da7bd29c653321817ea9d81f4eb4f847e25fcb513d28a5a65587aa25c1a9d12` | HUD-only; 3D candidate region remains black | 16 present-result-0 markers; no fault marker |
| 7 | `total=13 limit=7 selected=7`; GUIDs `126..138`, all `POINT` | `070b7f99a6c240e3c634a37355dd63283a6ded2df06f91497248b9ab173db77b` | HUD-only; 3D candidate region remains black | 1 present-result-0 marker in captured log; no fault marker |

Photos: `work/evidence/flr0032/light-limit4-ssh-late.png`, `light-limit5-ssh-late.png`, `light-limit6-ssh-late.png`, and `light-limit7-ssh-late.png`. The count-4 image is byte-identical to the FLR-0031 one/two-light 3D image. Count 5 remains visibly 3D but changes geometry; count 6 is the first failing prefix observed.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| First failing count | count or bounded range identified | Prefix 5 is 3D; prefix 6 is HUD-only | runtime table above | PASS |
| Count vs GUID | threshold distinguished from a particular light | Prefix boundary proven; sixth-light identity remains UNKNOWN | next ticket | PASS with handoff |
| QMP visual evidence | decisive variants have photos | four QMP-only PNGs attached | `work/evidence/flr0032/` | PASS |
| Teardown | no residual QEMU process/socket | every completed run ended by QMP and left no socket/process | Mini PC checks | PASS |

### Act

- Close FLR-0032 with the prefix boundary: 1–5 selected lights show visible 3D, 6–13 selected lights show HUD-only in the current diagnostic scene.
- Create FLR-0033 to distinguish a sixth-light-specific trigger from a count/resource threshold and to remove the diagnostic skip controls only after that comparison is designed.

## Facts / Inferences / UNKNOWN

### Facts

- One and two selected POINT lights produce identical QMP PPM bytes and visible 3D primitives.
- All thirteen selected POINT lights produce a HUD-only QMP image while present returns zero.

### Inferences

- The prefix-count boundary is between 5 and 6; because the selected list is ordered, this does not yet prove the sixth GUID is causal.
- Present remains successful at the first failing count, so the first visible divergence is after present success rather than a queue-present error.

### UNKNOWN

- Whether GUID `136` or another light parameter is causal, versus an aggregate count/resource limit.

## Handoff

This independent count-boundary task is complete. Continue with [FLR-0033 — isolate the sixth-light identity](FLR-0033-isolate-sixth-light.md); do not reuse FLR-0032 for that comparison.
