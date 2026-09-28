# FLR-0046 — co-enable selected production GLB and lights

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + target-validation roles
- Depends on: [FLR-0045](FLR-0045-production-full-scene-visible-3d.md)
- Working log: `work/logs/2026-09-07-flr0046.md`

## Problem

FLR-0045 proves that the selected production `sequoia_ngp.glb` can reach QMP
pixels when environment and production lights are skipped. Earlier runs also
showed a light-count boundary, but the model-plus-light combination has not
yet been compared on the current rootfs with one variable changed at a time.

## Success criteria

- Run model=1 with environment skipped and bounded production light prefixes.
- Capture QMP-only screenshots and pixel analysis for the first visible and
  first divergent cases.
- Correlate selected model, model-stage, light/resource, camera, frame/present,
  and error markers.
- Decide whether a source change is justified. If so, edit only the persistent
  Mac Devtool source, generate the official Yocto patch, commit it under
  `meta-fluorite-trial`, transfer by bundle, and build on the fixed Mini PC.
- Keep one QEMU at a time and record clean QMP teardown.

## Plan / PDCA

### Plan

1. Reuse the current rootfs, fixed QEMU profile, persistent Devtool container,
   and fixed receiver/build/TMPDIR.
2. Start with model limit=1, environment skipped, and the smallest light
   prefix; then increase only after a screenshot is captured.
3. Enable model-stage trace for the decisive model case if the runtime budget
   permits, without changing source first.
4. Separate facts, inferences, hypotheses, and UNKNOWN before selecting a
   patch.

### Facts

- FLR-0045 model-only QMP pixels pass with lights skipped.
- FLR-0044 production shapes pass under the historical shape-only condition.
- The current rootfs and QMP capture path are fixed and reusable.

### Hypotheses

1. A small number of production lights will coexist with the selected model,
   while a bounded light/resource interaction will cause the first divergence.
2. The model is visible only because lights are skipped, and enabling any
   production light will suppress or invalidate the render path.
3. The prior light-count boundary is independent of model loading and will
   reproduce with model limit=1.

### UNKNOWN

- First light prefix that diverges with model=1.
- Whether the `Light not found` messages are causal or only a skip-condition
  artifact.
- Whether environment stages change the result after model+lights pass.
- Whether any source patch is necessary.

## Result

The runtime-only matrix on the fixed authoritative rootfs completed without a
source change. The selected production GLB reached model-stage completion in
all cases. The first reproducible light-count divergence with `model=1` and
environment skipped is between 8 and 9 selected lights:

| Condition | Selected lights | QMP result | QMP image |
| --- | ---: | --- | --- |
| `FLR0026_NATIVE_LIGHT_LIMIT=8` | 8 (`126..140`) | production GLB visible | `work/evidence/flr0046/model1-env0-light8-trace/light8.png` |
| `FLR0026_NATIVE_LIGHT_LIMIT=9` | 9 (`126..140,162`) | HUD-only; native region black | `work/evidence/flr0046/model1-env0-light9-trace/light9.png` |
| `FLR0026_NATIVE_LIGHT_LIMIT=10` | 10 | HUD-only; native region black | `work/evidence/flr0046/model1-env0-light10-trace/light10.png` |
| `FLR0026_NATIVE_LIGHT_LIMIT=13` | 13 | HUD-only; native region black | `work/evidence/flr0046/model1-env0-light13-trace/light13.png` |

The 8-light QMP frame had `changed_pixels=77107/100000` in region
`[200,100,400,250]`, bounding box `[200,134,400,216]`, and PPM SHA-256
`aa0f262851c44fa18bf5ca8e777a6ecb98666e390c3100e8192e699b4276cc8a`.
The 9-light frame had `changed_pixels=99942/100000`, bounding box
`[200,100,400,250]`, and PPM SHA-256
`ad35e69b3687856ff66f5bcd62fd6df0afe7b954d23f05b036b9e1e9c78ce156`.
The visual difference is the 8-light GLB polygon versus the 9-light HUD-only
black native region; both screenshots are QMP-only.

Runtime markers show the same model path in the boundary cases:

- `MODEL_SELECTED ... assets/models/sequoia_ngp.glb`
- `MODEL_STAGE_ASSET_CREATED ... bytes=13671064 entities=22`
- `MODEL_STAGE_ASYNC_BEGIN`, `INSTANCE_READY`, and `COMPLETE`
- `LIGHT_SETUP_PLAN total=13 limit=8 selected=8` for the passing case
- `LIGHT_SETUP_PLAN total=13 limit=9 selected=9` for the failing case
- frame 1/2 started, then frame 3 `started=false`
- `QUEUE_PRESENT result=0` appears in the passing 8-light case; it is absent
  from the captured 9-light marker set

The first newly selected light at the failure boundary is GUID `162`; whether
that identity is causal remains UNKNOWN and is moved to FLR-0047.

QMP teardown was completed after every run with `SHUTDOWN reason=host-qmp-quit`
and a post-check found no QEMU, runqemu, or flutter-auto process. No source
patch, bundle, or Mini PC rebuild was justified by this diagnostic-only result.

## Decision

FLR-0046 is closed. The next task is to exclude GUID `162` while keeping the
model and environment conditions unchanged, then compare the QMP frame and
light/resource markers. Environment enablement and scene transitions remain
out of scope for this ticket.
