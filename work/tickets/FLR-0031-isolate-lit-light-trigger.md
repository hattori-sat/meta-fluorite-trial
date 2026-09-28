# FLR-0031 — isolate the smallest lit-light trigger

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: FLR-0030
- Links: [FLR-0030](FLR-0030-present-boundary-fault-capture.md), [FLR-0027](FLR-0027-shape-light-rendering-separation.md), [FLR-0028](FLR-0028-production-shape-light-coenabled.md)
- Working log: `work/logs/2026-09-06-flr0031.md`
- Diagnostic patch: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0188-diag-select-scene-lights-devtool.patch`

## Problem

FLR-0027 proved that production shapes can produce visible 3D pixels when lights are skipped, while FLR-0028 through FLR-0030 showed that the co-enabled path faults after present begins and maps into LLVM/llvmpipe. The current evidence does not distinguish a general lit-material path from one light type, parameter, or diagnostic timing interaction.

## Purpose

Establish a bounded light-count A/B boundary using the same built image and a diagnostic-only selector. This ticket closes with the verified result that one and two selected lights still produce QMP-visible 3D while all thirteen produce only the 2D HUD; the unresolved 3–12 range is a new ticket.

## Success measure

- Reuse the exact rootfs, QEMU profile, receiver, build, TMPDIR, and existing Mac Devtool container.
- Change one variable per run: light count/type/parameter, material variant, or one diagnostic synchronization flag.
- Record first divergent marker, fault/RIP, QMP-only photo, image hash, serial hash, and clean teardown.
- Identify a verified pass/fail boundary, or record the remaining range as UNKNOWN with a concrete reason.
- Do not declare a light-skip, mock, or HUD-only frame as production 3D success.
- Close this ticket before selecting a production fix or scene-transition task.

## Stratification — 4W1H excluding Why

| Dimension | Current boundary | Next evidence |
| --- | --- | --- |
| What | shape+light co-enabled path faults near LLVM `isOrdered` | one-light/type/material matrix |
| Where | `FEngine::loop` → llvmpipe/Vulkan → LLVM | ordered native markers and maps |
| When | after `FLR0026_VK_QUEUE_PRESENT_BEGIN` | first marker that changes per variant |
| Who | runtime diagnosis, Filament bridge, target-validation roles | role-based working log |
| How | fixed image/profile; one variable at a time | QMP + serial + teardown evidence |

## Scope

### In scope

- Read-only scene/source inspection and existing runtime markers.
- Runtime-only A/B tests on the current rootfs before any source mutation.
- If needed, one diagnostic-only Devtool probe that reports the selected light type/count or limits the light payload without changing the default production path.

### Out of scope

- Permanent light removal, permanent mock rendering, compositor redesign, Planetarium navigation, cache deletion, new container, new receiver, or new TMPDIR.
- Hand-editing a generated patch or treating a successful build as a rendering fix.

## Hypotheses

1. Any direct light combined with a lit material triggers the llvmpipe/LLVM path. Prediction: one safe directional light with the existing shape set still reaches the same fault.
2. A specific light type or parameter triggers the path. Prediction: a single safe directional/SUN light survives while POINT/SPOT or the production mix faults.
3. The material shader variant is the trigger. Prediction: the same shape and one light with an unlit/known-safe material survives.
4. Present/synchronization diagnostics perturb timing or stack state. Prediction: changing one diagnostic synchronization flag changes the fault without changing scene payload.
5. QEMU TCG/llvmpipe is the environment-specific trigger. Prediction: a bounded backend/threading control changes the LLVM fault, but this cannot be accepted as the production fix.

## PDCA

### Plan

- Start with the existing rootfs and no source change.
- Run the smallest available runtime controls in a fixed order: one safe light, individual light type, then material/control timing only if needed.
- Capture QMP-only screenshots for every decisive variant and cleanly quit QEMU each time.

### Do

- Use the existing scene/light markers and attach maps/GDB only when the fault boundary changes.
- If the runtime has no selector for the required light dimension, make the smallest diagnostic selector through the Mac Devtool source workflow and generate the official layer patch.

#### Mac Devtool source handoff

- Existing recipe-patch changes were recorded as Devtool source baseline `5206fc7`.
- The diagnostic source commit is `94c05e7` and changes only `scene_text_deserializer.cc`.
- Official `devtool finish --mode patch` generated the patch without hand editing. The generated patch and registered layer copy are byte-identical with SHA-256 `b7f073b5f36ee002f7c1d936c4e7a1cf265cdf4668c9cfaf0510017a8c650a4f`.
- The first finish attempts exposed reusable workflow conditions: the recipe workspace must be registered from the baseline commit, the Devtool recipe directory must be writable by the non-root BitBake UID, and the existing container's Git safe.directory must include the shared source path. These were corrected without creating a new container, volume, or TMPDIR.

### Runtime evidence

All decisive runs used the Mini PC authoritative image from commit `6b33295`, the fixed QEMU profile, guest SSH launch, and the same diagnostic environment: `FLR0026_NATIVE_SKIP_MODEL_LOAD=1`, `FLR0026_NATIVE_SKIP_ENVIRONMENT=1`, `FLR0026_SYNC_TRACE=1`, and `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`. The model/environment skips are diagnostic controls; this is not yet the final full-production-scene verdict.

| Variant | Selector evidence | Runtime boundary | QMP-only evidence | Result |
| --- | --- | --- | --- | --- |
| `FLR0026_NATIVE_LIGHT_LIMIT=1` | `total=13 limit=1 selected=1`; first selected light `guid=126 type=POINT` | repeated `VK_QUEUE_PRESENT result=0`; no `page fault`, `SIGSEGV`, `CPU:` or `Comm:` marker | `work/evidence/flr0031/light-limit1-ssh2-late.png`; PPM SHA-256 `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b` | PASS: visible black 3D primitives/wireframes |
| `FLR0026_NATIVE_LIGHT_LIMIT=2` | `total=13 limit=2 selected=2`; `guid=126,128`, both `POINT` | 140 observed `VK_QUEUE_PRESENT result=0` markers; no fault marker | `work/evidence/flr0031/light-limit2-ssh-late.png`; identical PPM SHA-256 `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b` | PASS: same visible 3D primitives/wireframes |
| selector unset (all lights) | `total=13 limit=13 selected=13`; selected GUIDs `126,128,...,170`, all `POINT` | repeated `VK_QUEUE_PRESENT result=0`; no fault marker | `work/evidence/flr0031/all-lights-ssh-late.png`; PPM SHA-256 `6b46e55d73800c70357097546a7ba52a88cafc133adb9356e16f6a826170b5d1` | FAIL for 3D goal: 2D HUD only |

The one-light and two-light PPMs are byte-identical, so the observed change is not caused by the second selected light. The all-light image is visually different and contains only the HUD. Each run was terminated through QMP; the QMP socket and QEMU process were absent after teardown. Earlier PTY/socat stimulus runs are excluded from this table because command truncation or `tcgetattr` failure prevented reliable selector evidence.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Bounded light-count boundary | 1/2-light pass vs all-light 3D failure is reproducible | 1 and 2 are 3D; 13 is HUD-only | runtime table above | PASS |
| First divergent marker | selector and present markers are ordered | selector count changes; present remains result 0 | Mini PC app logs | PASS |
| QMP visual evidence | decisive variants have QMP-only photos | three PNGs attached in `work/evidence/flr0031/` | evidence files above | PASS |
| Teardown | no residual actual QEMU/Flutter/Weston process | QMP socket and QEMU absent after each completed run | Mini PC process/socket check | PASS |
| Devtool patch provenance | source commit and generated patch match | `94c05e7`; source/generated SHA-256 match | this ticket and layer patch | PASS |

### Act

- Close FLR-0031 with the bounded result and create a new ticket for the unverified 3–12 range.
- Do not select a production fix or reuse this ticket for the next matrix.

## Facts / Inferences / UNKNOWN

### Facts

- Shape-only showed visible native 3D pixels.
- Light-only reached the common present/commit path without geometry.
- Shape+light co-enabled reached present begin and faulted in the LLVM mapping described by FLR-0030.

### Inferences

- The “any direct light immediately prevents 3D” hypothesis is false: one and two POINT lights produce identical visible 3D pixels.
- The change between two and thirteen selected lights is a scene/resource/composition interaction or later light-processing effect, not a present return failure; present succeeds in both cases.
- Because the diagnostic run skips model/environment loading, the result proves a native production-shape + bounded-light rendering condition, not yet the unmodified full production scene.

### UNKNOWN

- The first failing light count is somewhere in the untested range 3–12; no threshold is claimed here.
- Whether a material variant or synchronization timing is required.
- Whether the eventual production fix belongs in Fluorite source, Filament/Vulkan integration, or the target runtime.

## Handoff

This independent bounded A/B task is complete. Continue with [FLR-0032 — locate the light-count divergence](FLR-0032-locate-light-count-divergence.md); do not reuse this ticket for the next matrix.
