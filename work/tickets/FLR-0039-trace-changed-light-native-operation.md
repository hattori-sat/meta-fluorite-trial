# FLR-0039 — trace changed-light native operation

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0038](FLR-0038-isolate-changed-light-position-setter.md)
- Working log: `work/logs/2026-09-07-flr0039.md`

## Problem

FLR-0037 showed that changing GUID `136` to a novel position produces native 3D pixels. FLR-0038 showed that changing GUID `138` to a novel position does not, even though the runtime reaches present successfully and GUID `136` remains unchanged. The current override is applied to the deserialized light object before the selected-light setup completes, so the responsible downstream operation is not yet identified.

## Purpose

Trace the GUID136-specific changed-position path from the deserialized light setter through entity/resource application and the first native render operation. Determine which operation differs from the GUID138 case before proposing a production fix.

## Success measure

- Static source inspection identifies the setter, entity mapping, resource creation/update, and render-boundary calls involved in the selected-light path.
- Runtime evidence compares a fresh no-override control, GUID136 changed-position, and GUID138 changed-position under one fixed image/profile.
- Logs identify the selected GUID, native entity/resource identity, setter/update ordering, Present result, and fault state.
- Preserve QMP-only screenshots and clean teardown for every decisive variant.
- Do not change production scene data or mark a diagnostic switch as a production fix.

## Facts

- FLR-0037: GUID136 changed-position produced visible native 3D pixels.
- FLR-0038: GUID138 changed-position produced HUD-only pixels with successful Present and no native fault marker.
- The current diagnostic override calls `setPosition` on the selected deserialized light before the selected-light setup plan is applied.

## Hypotheses

1. GUID136 maps to a different native entity/resource operation than GUID138. Prediction: entity/resource trace differs before render.
2. The changed setter is applied at a different ordering point for GUID136. Prediction: setter/update ordering or first render operation differs.
3. The observed difference is still a capture/runtime timing artifact. Prediction: a fresh no-override control or repeated fixed profile changes the result without a native operation difference.

## PDCA

### Plan

- Read the Devtool-managed source and existing 0190/0191 patch context before editing.
- Add only a diagnostic trace if static evidence identifies an unobserved native boundary.
- Reuse the persistent Mac Devtool container, generate the patch through official Devtool finish, commit it in `meta-fluorite-trial`, bundle from the Mac, and build on the existing Mini PC receiver/build/TMPDIR.
- Run QMP-only control/GUID136/GUID138 cases on the same authoritative image and close every QEMU session deterministically.

### Do

- Read the existing Devtool-managed `SceneTextDeserializer::setUpLights`, `LightSystem::BuildLightAndAddToScene`, `BuildLight`, and the transform message handler.
- Confirmed the diagnostic override calls `Light::setPosition` before the selection-limit check. The selected path then creates an ECS entity, adds the Light component, calls `BuildLightAndAddToScene`, creates a Filament entity, sets `LightManager::Builder::position`, and builds the native light.
- Confirmed the FLR-0038 GUID138 variant did not exercise that native path: with `FLR0026_NATIVE_LIGHT_LIMIT=6`, the selected prefix is GUID126,128,130,132,134,136; GUID138 is seventh and the loop breaks before ECS/native insertion. Its property log therefore proves only deserialized-object mutation.
- No source patch was made. The next runtime comparison must target selected GUID134 or raise the limit to include GUID138.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Static native path | setter/entity/resource/render boundary identified | `setPosition` → selection → ECS entity/component → Filament builder/build → scene add identified | source trace | PASS |
| GUID136 changed position | reproduce FLR-0037 native 3D | Known from FLR-0037; not rerun in this static ticket | prior QMP photo + log | OBSERVED |
| GUID138 changed position | selected-light contrast | Not a selected-light test at limit 6; loop stops before GUID138 native insertion | FLR-0038 log + source trace | INVALID TEST |
| Runtime health | Present succeeds without fault | Observed in FLR-0038, but not evidence for selected GUID138 | FLR-0038 app log | OBSERVED |
| Teardown | no residual QEMU process/socket | FLR-0038 QEMU cleanup completed after targeted process cleanup | FLR-0038 working log | PASS |

### Act

- If the native operation difference is confirmed, create one minimal diagnostic or production-fix ticket around that boundary.
- If no operation difference is found, split the next ticket around entity/resource identity or frame scheduling; do not broaden this ticket into Planetarium or route testing.

## Conclusion

FLR-0039 is complete as a static-path and test-validity check. The native operation boundary is identified, and the prior GUID138 runtime variant is explicitly invalid for the intended selected-light comparison because GUID138 was outside the selected prefix. No production conclusion is drawn from that invalid comparison.

## UNKNOWN

- Which native entity/resource is associated with GUID136 and GUID138 after selected-light setup.
- Whether the position setter changes a resource update, renderable state, or only the deserialized object.
- Whether production-scene and Planetarium paths share the same native operation.
