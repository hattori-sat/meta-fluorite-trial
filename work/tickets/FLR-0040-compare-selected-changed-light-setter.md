# FLR-0040 — compare selected changed-light setter

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0039](FLR-0039-trace-changed-light-native-operation.md)
- Working log: `work/logs/2026-09-07-flr0040.md`

## Problem

FLR-0039 found that GUID138 is not selected when the diagnostic light limit is six. The previous GUID138 run changed only an unselected deserialized object and cannot answer whether a changed setter on another selected light restores 3D.

## Purpose

Compare a changed-position setter on selected GUID134 (ordinal 4) against the known selected GUID136 behavior, keeping the same image, six-light prefix, model/environment skip controls, QEMU profile, and QMP-only evidence.

## Success measure

- Run a fresh six-light no-override control and a selected GUID134 changed-position variant.
- Confirm GUID134 is in the selected prefix and reaches ECS/native light creation.
- Compare QMP pixels, setter/update ordering, Present result, fault markers, and teardown with FLR-0037's GUID136 result.
- Do not use GUID138 at light limit six as a selected-light control, and do not change production scene data.

## Facts

- Selected prefix at limit six: GUID126, 128, 130, 132, 134, 136.
- FLR-0037: changing selected GUID136 produced native 3D pixels.
- FLR-0039: GUID138 at limit six is unselected and does not reach native insertion.

## Hypotheses

1. Any selected light changed before native build restores 3D. Prediction: changing GUID134 produces native 3D.
2. The effect is GUID136-specific. Prediction: changing GUID134 remains HUD-only.
3. A selected-light ordinal/resource identity matters. Prediction: GUID134 differs from GUID136 in native entity/resource trace or pixels.

## PDCA

### Plan

- Reuse the existing fixed rootfs and QEMU profile; no source patch or rebuild is needed for this runtime-only control.
- Use guest SSH as `agl-driver`, six POINT lights, model/environment skip, sync trace, and forced render.
- Capture QMP-only control and GUID134 variant frames, then QMP quit and verify no residual processes or sockets.

### Do

- Reused the fixed FLR-0038 rootfs/kernel and the same QEMU profile on the Mini PC; no Mac source edit, Devtool finish, bundle, or BitBake rebuild was needed for this runtime-only comparison.
- Control: launched the Example Demo as `agl-driver` with `FLR0026_NATIVE_LIGHT_LIMIT=6`, model/environment skip, sync trace, and forced render; no light override.
- Variant: used the same profile and set `FLR0026_NATIVE_LIGHT_OVERRIDE_GUID=134` with position `(100,10,100)`.
- Captured the display only through QMP screendump at 18 seconds, copied the PPM evidence to the Mac workspace, converted review copies to PNG, and inspected both images.
- QMP quit was sent for each case; the exact QEMU process and socket were removed/checked after each run.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Fresh six-light control | HUD-only | HUD-only; central native region remained black. QMP region comparison against black: 728/100000 changed pixels, bbox `[200,113,29,66]` (HUD edge only). | `work/evidence/flr0040/control/control-18s.png`, `control-18s.ppm`, `app-log.txt` | PASS |
| Selected GUID134 changed position | distinguishes selected identity | GUID134 logged as ordinal 4 and selected; override was `(100,10,100)`, but the central native region remained black. Compared with control: 394/100000 changed pixels, bbox `[200,114,28,64]` (HUD edge only). | `work/evidence/flr0040/changed-guid134/changed-guid134-18s.png`, `changed-guid134-18s.ppm`, `app-log.txt` | PASS; no 3D |
| Runtime health | Present succeeds without fault | Both logs contain 16 `FRAME_BEGIN`, 16 `FRAME_END`, and 16 `FRAME_EVENT_RETURNED` records. No SIGSEGV, SIGBUS, page-fault, or core-dump marker was present. A distinct Present result is not logged in this profile. | `work/evidence/flr0040/control/app-log.txt`, `work/evidence/flr0040/changed-guid134/app-log.txt` | PASS with Present result UNKNOWN |
| Teardown | no residual QEMU process/socket | `qemu-system-x86_64=none`, `flutter-auto=none`, `bitbake=none`, `bitbake-server=none`, and `qmp_sockets=0` after the second run; Mini PC `/mnt/yocto` remained at 89% used with 85G free. | `work/logs/2026-09-07-flr0040.md` | PASS |

### Act

- GUID134 did not restore 3D, so the earlier result cannot be explained by “any selected light changed setter.”
- Do not patch production or treat GUID136 as proven root cause yet: the selected GUID134 and GUID136 difference remains unresolved at the native entity/resource or downstream render boundary.
- Split the next ticket around a native-operation trace that records the actual Filament entity, component, and render-list state for GUID134 and GUID136, then compare it with the frame/present path.

## UNKNOWN

- Whether selected GUID134 reaches the same native operation and Filament resource state as GUID136; the static source path says it should, but this runtime profile does not log the operation itself.
- Whether the visible effect follows the selected ordinal, GUID identity, a resource state, or a later render-list/compositor condition.
- Present's numeric result in this profile is UNKNOWN because no dedicated Present-result marker was emitted.
