# FLR-0038 — isolate changed-light position setter identity

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0037](FLR-0037-isolate-duplicate-light-position.md)
- Working log: `work/logs/2026-09-06-flr0038.md`

## Problem

FLR-0037 showed that GUID `136` becomes visibly 3D when its position changes to either another light's position or a novel nonduplicate position. FLR-0036 showed that a same-value setter does not restore 3D. The remaining question is whether the behavior is specific to GUID `136` or follows any changed selected-light position.

## Purpose

Determine whether a changed position setter on GUID `138` or another selected light produces the same QMP 3D pixels while GUID `136` remains unmodified. Keep the diagnostic override gated and do not change production scene data.

## Success measure

- Run a fresh distinct-position control and at least one changed-position variant targeting a GUID other than `136`.
- Keep light count, scene skip controls, image identity, QEMU profile, bundle, launcher user, and QMP timing fixed.
- Preserve QMP-only photos, runtime logs, hashes, and clean teardown for every decisive variant.
- Close this ticket before changing the production scene or starting Planetarium/route validation.

## Hypotheses

1. Any selected-light changed position setter restores 3D. Prediction: changing GUID `138` to a novel position produces the same visible frame as FLR-0037.
2. The effect is GUID136-specific. Prediction: changing GUID `138` leaves the candidate region black.
3. The effect requires a particular downstream light order/resource state. Prediction: changing another light changes logs or pixels differently from GUID136.

## PDCA

### Plan

- Reuse the fixed FLR-0035 image and diagnostic position-override path.
- Use one QEMU run directory per fresh control/variant and QMP-only early/late captures.
- Use six selected POINT lights and trace GUIDs `136,138`; keep model/environment skip controls unchanged.

### Do

- Built project commit `1e4a08e` from a Mac-produced narrow bundle on the existing Mini PC receiver, fixed build directory, and fixed TMPDIR.
- Metadata, `flutter-auto` `do_patch` (104/104), `do_compile` (2686/2686), and full image (11748/11748) all passed.
- Used the fixed new rootfs with official runqemu, slirp, guest SSH launch as `agl-driver`, and QMP-only screendump. The framebuffer was 1280x800.
- The distinct control used six POINT lights with model/environment loading skipped. The GUID138 variant left GUID136 unchanged and applied the novel position `(100,10,100)` only to GUID138.
- The variant log confirmed the six-light selection, the changed GUID138 position, successful `Present result=0`, and no native fault marker.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Fresh distinct control | HUD-only | 2D HUD with CPU/GPU/graph/Scenes; candidate region 857/100000 HUD pixels | QMP photo + log | PASS |
| Changed GUID138 position | distinguishes identity | Same HUD-only frame at 18 s and 38 s; 895/100000 HUD pixels | QMP photo + log | PASS |
| Runtime health | Present succeeds without fault | Present result `0`; no `SIGSEGV`, `SIGBUS`, or page-fault marker | app log | PASS |
| Teardown | no residual QEMU process/socket | QMP quit, targeted cleanup, final process/socket check clean | working log | PASS |

### Act

- If any changed selected light restores 3D, split the next ticket around the native changed-position operation and production-scene data.
- If only GUID136 restores 3D, split the next ticket around GUID136/entity identity handling.

## Facts / Inferences / UNKNOWN

### Facts

- FLR-0037 changed GUID136 to both duplicate and nonduplicate positions and obtained identical visible QMP geometry.
- FLR-0036 same-value GUID136 control remained HUD-only.

### Inferences

- The changed-value position mutation is the current smallest confirmed discriminator.

### UNKNOWN

- Whether GUID138 or another selected light has the same effect.
- Which native light/resource operation makes the geometry visible after the mutation.

## Evidence

QMP-only images are the visual record. The control visibly contains the 2D Fluorite HUD and a black native region; the GUID138 variant is visually identical in the native candidate area:

- Distinct control: [control-30s.png](../evidence/flr0038/distinct-control/control-30s.png)
- GUID138 changed position, 18 s: [variant-18s.png](../evidence/flr0038/changed-guid138/variant-18s.png)
- GUID138 changed position, 38 s: [variant-38s.png](../evidence/flr0038/changed-guid138/variant-38s.png)

## Conclusion

FLR-0038 is complete as a discriminator: changing GUID138 alone does not reproduce the native 3D pixels obtained by changing GUID136 in FLR-0037. This is not a production fix, and the real production scene/Planetarium path remains open.
