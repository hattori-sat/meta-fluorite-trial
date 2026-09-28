# FLR-0034 — identify the GUID 136 production fix

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0033](FLR-0033-isolate-sixth-light.md)
- Working log: `work/logs/2026-09-06-flr0034.md`

## Problem

FLR-0033 proved with equal-count QMP evidence that selecting GUID `136` as the sixth POINT light produces HUD-only output, while replacing it with GUID `138` restores visible 3D primitives. The selector is diagnostic only; production behavior must not be left with an unexplained exclusion.

## Purpose

Identify the light-data field or downstream operation associated with GUID `136`, then validate the smallest production-safe correction in the intended scene path. Keep the investigation separate from the completed selector experiment.

## Success measure

- Compare the serialized/runtime properties of GUIDs `136` and `138` and identify at least one evidence-backed difference or mark the cause UNKNOWN.
- Reproduce the result without changing the default production selection unless the ticket's evidence supports a minimal fix.
- If a source fix is justified, edit the Devtool-managed source on Mac, generate the patch with official `devtool finish --mode patch`, hand it off by bundle, and validate it on the fixed Mini PC build path.
- Capture QMP-only screenshots for baseline and candidate behavior, with app-log hashes and no residual QEMU process/socket.
- Close this ticket before starting a separate scene-transition or full-production validation ticket.

## Hypotheses

1. GUID `136` contains a malformed or unsupported light parameter. Prediction: a field-level difference is visible before rendering and correcting that field restores 3D.
2. GUID `136` is valid, but a specific bridge/entity operation mishandles its runtime entity. Prediction: serialized properties match the expected schema while targeted runtime logs isolate the operation after deserialization.
3. The apparent identity is an interaction with the skipped model/environment path. Prediction: the difference disappears or moves when one skipped control is restored; split that validation into a new ticket if needed.

## PDCA

### Plan

- Inspect existing scene-deserializer logs and source around light creation/property application.
- Add one bounded diagnostic dimension at a time; preserve the working Mac Devtool container and generated-patch workflow.
- Use the same fixed image/build/QMP profile for each comparison.

### Do

- Static source inspection identified the input properties and the downstream builder boundary: `Light` deserializes the light fields, then `LightSystem::BuildLight` passes them to Filament's `LightManager::Builder`.
- A diagnostic-only trace was added in the Devtool-managed source and committed as `90bcc3a diag: trace selected light properties`. It is gated by `FLR0026_NATIVE_LIGHT_TRACE_GUIDS` and does not change the default production selection.
- Official Devtool generated the patch, and the byte-identical registered layer patch is `0190-diag-trace-selected-light-properties-devtool.patch` with SHA-256 `6192d3e27041a09476dbd99384bcac90fcc586228eb13be48e2c597f5a904e54`.
- Project commit `f207dea5268d61c2b3ee595dc25f2027d655f2c5` was handed off by bundle and accepted by the fixed receiver.
- The fixed Mini PC path passed `bitbake -e agl-ivi-image-flutter`, `bitbake -c do_patch -f flutter-auto`, `bitbake -c do_compile -f flutter-auto`, and full `bitbake agl-ivi-image-flutter`.
- Runtime trace with `FLR0026_NATIVE_LIGHT_TRACE_GUIDS=136,138` recorded both input objects. GUID `136` and GUID `138` are both `POINT` with matching color `(1,0.59607846,0)`, color temperature `0`, intensity `6000000`, direction `(0,-1,0)`, `cast_light=true`, `cast_shadows=false`, falloff `2`, and zero spot/sun parameters. The observed difference is position: GUID `136` is `(74.5,1.2,67.15)` and GUID `138` is `(69.5,1,68.85)`.
- QMP captured HUD-only output for the default six-light run; no 3D pixels appeared. Present returned zero and no `page fault`, `SIGSEGV`, `CPU:` or `Comm:` marker was captured.
- The QEMU instance was stopped with QMP `quit`; its QMP socket and matching QEMU process were absent afterward.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| GUID property comparison | `136` vs `138` difference identified or UNKNOWN recorded | Position differs; all other traced fields match | working log and app log | PASS |
| Runtime boundary | one downstream operation isolated | Builder input is observed; the causal downstream operation remains UNKNOWN | app log / QMP evidence | PARTIAL |
| Production-safe candidate | default scene behavior validated | Pending | QMP PNG + app log | Pending |
| Teardown | no residual QEMU process/socket | QMP quit and post-check clean | working log | PASS |

### Act

- The position difference is not yet a defect. Create a focused same-position/alternate-identity ticket before changing production data or selection.
- Do not retain the property-trace diagnostic as permanent production behavior; it remains a gated observation aid for the next ticket.

## Facts / Inferences / UNKNOWN

### Facts

- FLR-0033: six selected POINT lights with GUID `136` are HUD-only; replacing `136` with `138` yields visible 3D in QMP screenshots.
- The property trace shows matching type and rendering parameters for GUIDs `136` and `138`; position is the observed difference.
- The new rootfs SHA-256 is `8ef17d0476aad912f1feafa16117e9b580dbbc6bff5de794ad0a0889874e32ee`.
- The kernel SHA-256 is `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- The qemuboot SHA-256 is `3c0ba218e79aa9abaeb3194672f404a4a072d9ec82d6cb8e8459ce2e6856b51b`.
- The runtime app-log SHA-256 is `b1c9080e4ad9615798f65c6ca6c1187030f358ea6784cb92e0c8da23e2301ab2`.
- The runtime QMP PPM SHA-256 is `759a6624b8b55296a8720928aa15bd84ea6c174d674e1a249d0d1b598f401527`.

### Inferences

- Position is the only difference observed by the current trace, so a position-versus-identity experiment is the highest-value next boundary.

### UNKNOWN

- Whether moving GUID `136` to GUID `138`'s position restores 3D, and whether assigning GUID `136`'s position to GUID `138` reproduces HUD-only.
- The causal operation after the Filament builder receives the light.

## Evidence

- QMP photo: `work/evidence/flr0034/trace-light136-late.png` — HUD-only.
- QMP PNG SHA-256: `b354b8f5a72c9bd0e0938e236ceeb961901e3e3216abcefb50bafcb16f42d32f`.
- Runtime details, build provenance, and teardown: `work/logs/2026-09-06-flr0034.md`.

## Handoff

- New independent task: [FLR-0035](FLR-0035-isolate-light-position-vs-identity.md).
