# FLR-0047 — isolate the first failing production light identity

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + target-validation roles
- Depends on: [FLR-0046](FLR-0046-production-model-lights-visible-3d.md)
- Working log: `work/logs/2026-09-07-flr0047.md`

## Problem

FLR-0046 fixed the first model-plus-light visibility boundary at 8→9
selected production lights. The ninth selected light is GUID `162`, but a
count boundary alone does not prove that this light identity is causal.

## Success criteria

- Keep `model=1` and `environment skip` unchanged.
- Compare the failing 9-light prefix with GUID `162` excluded and the next
  available light allowed to fill the ninth slot.
- Capture QMP-only screenshots, fixed-region pixel analysis, and light/model/
  frame/present/error markers for both cases.
- Decide whether the cause is GUID identity, count/resource accumulation, or
  another process boundary. Do not create a source patch without this evidence.
- Stop the recorded QEMU through QMP after each run and verify clean teardown.

## Plan / PDCA

### Plan

1. Reuse the fixed current rootfs, persistent Devtool container, fixed receiver,
   build, and TMPDIR. No source change or rebuild is planned initially.
2. Run the baseline `light limit=9` and one-variable `skip GUID=162, limit=9`
   comparison. The latter should select the first eight known-good lights plus
   GUID `164`.
3. Correlate light selection, model-stage completion, frame start, queue
   present, and error markers with QMP pixels.
4. If identity is implicated, open a separate countermeasure ticket; keep
   environment and scene-transition work separate.

### Facts

- Eight selected lights produce visible `sequoia_ngp.glb` QMP pixels.
- Nine selected lights produce HUD-only pixels; GUID `162` is the first newly
  selected light at that boundary.
- Model asset creation and asynchronous completion occur in both conditions.

### Hypotheses

1. GUID `162` or its downstream native operation is the first causal light
   identity; excluding it will restore the model pixels at nine selected lights.
2. The count/resource accumulation is causal; replacing GUID `162` with the
   next light will remain HUD-only.
3. The observed boundary is a frame/present synchronization interaction and
   will vary despite identical selected-light/resource markers.

### UNKNOWN

- Whether GUID `162` is causal or merely the first member of a later trigger set.
- Whether the replacement light GUID `164` changes the result.
- Whether environment enablement changes this boundary.
- Whether a source patch is justified.

## Result

The GUID-exclusion A/B completed on the same authoritative rootfs. The
baseline from FLR-0046 selected nine lights including GUID `162` and was
HUD-only. The exclusion case kept `light limit=9`, skipped only GUID `162`,
and selected GUIDs `126,128,130,132,134,136,138,140,164`; it was also HUD-only.

QMP-only evidence for the exclusion case:

- Image: `work/evidence/flr0047-model1-env0-light9-skip162/skip162.png`
- Dimensions: `1280x800`
- Region: `[200,100,400,250]`
- Changed pixels: `99942/100000`
- Bounding box: `[200,100,400,250]`
- PPM SHA-256: `d1f16ba1319fd793f1cc46cbb713d22c10caae51ce29004f3ed6834880e2346e`
- Marker evidence: `work/evidence/flr0047-model1-env0-light9-skip162/markers.log`

Runtime facts from the exclusion case:

- `LIGHT_SKIPPED guid=162` and `LIGHT_SELECTED ... guid=164` were recorded.
- `LIGHT_SETUP_PLAN total=13 limit=9 ... selected=9` was recorded.
- The same `sequoia_ngp.glb` reached asset creation, async begin, instance
  ready, and model-stage complete.
- `FLR0026_VK_QUEUE_PRESENT result=0` appeared once, but no present-boundary
  completion or Wayland commit completion marker was observed in the filtered
  evidence.
- No `SIGSEGV` or segmentation fault occurred during the bounded window.

The experiment rejects the hypothesis that GUID `162` alone is sufficient to
explain the failure. It does not yet distinguish a count/resource threshold
from a later light identity, because GUID `164` is a replacement candidate.
That remaining question is moved to FLR-0048. No source patch or build was
justified.

QMP teardown completed with `SHUTDOWN reason=host-qmp-quit`; the post-check
found no QEMU, runqemu, or flutter-auto process.

## Decision

FLR-0047 is closed with the identity-only hypothesis rejected. The next task
will compare native state and later-light substitutions while keeping the
model and environment conditions fixed.
