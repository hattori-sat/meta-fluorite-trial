# FLR-0033 — isolate the sixth-light identity

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0032](FLR-0032-locate-light-count-divergence.md)
- Working log: `work/logs/2026-09-06-flr0033.md`

## Problem

FLR-0032 found a prefix boundary: five selected POINT lights show visible 3D, while six selected POINT lights show HUD-only and still return successful present results. The sixth prefix entry is GUID `136`, but the current selector cannot distinguish that light from an aggregate count/resource threshold.

## Purpose

Determine whether GUID `136` or the aggregate six-light state is responsible, using one new diagnostic selector dimension at a time and the established Mac Devtool → official patch → bundle → Mini PC build flow.

## Success measure

- Add only the minimum diagnostic selection needed to compare an alternate six-light set or exclude GUID `136`; default production behavior remains unchanged.
- Build through the existing container/receiver/build/TMPDIR; do not hand-edit a generated patch.
- Capture QMP-only photos and runtime markers for the baseline six-prefix and the alternate selection.
- Close this ticket before making a permanent renderer or scene change.

## Hypotheses

1. GUID `136` or its parameters are causal. Prediction: excluding it or selecting another six-light set restores visible 3D.
2. Aggregate light count/resource pressure is causal. Prediction: any six-light set is HUD-only, while five remains 3D.
3. The skipped model/environment controls hide a separate full-scene interaction. Prediction: restoring one control changes the boundary; treat that as a separate production-scene comparison.

## PDCA

### Plan

- Reuse FLR-0032's fixed rootfs/profile for the baseline and design the smallest selector extension for a same-count alternative.
- Edit only the Devtool-managed source on Mac; generate the registered patch with official `devtool finish --mode patch`.

### Do

#### Mac Devtool source handoff

- The official recipe name is `flutter-auto`; the light code is the split `ivi-homescreen-plugins` source. A direct `devtool modify flutter-auto` extraction was attempted first and stopped on the existing empty-commit failure for `0002-wayland-vulkan-drop-vk-detail.patch`; no source change was accepted from that failed attempt.
- The existing source snapshot was registered through component-scoped `devtool add` at baseline commit `94c05e7`, then source commit `49e2575` added `FLR0026_NATIVE_LIGHT_SKIP_GUIDS`. The default path is unchanged when the variable is unset.
- Official `devtool finish fluorite-plugins ... --mode patch` generated `0001-diag-select-alternate-scene-lights-by-guid.patch`. The generated patch and registered layer copy `0189-diag-select-alternate-scene-lights-devtool.patch` are byte-identical with SHA-256 `62e3977406867b2f4b04e1e3a135c3e7c19a6db189687161eab60c54a08e67af`.
- The generated patch body was not edited. The component-scoped recipe is only a Devtool generation aid; the actual project handoff is the patch under `meta-fluorite-trial` and its `flutter-auto` `SRC_URI` registration.

- Bundle `work/flr0033-20e0976.bundle` was delivered to the fixed receiver inbox. The receiver tip is `20e0976c961881036bb9fc503433ecea3e2d8a58`.
- The fixed build path passed `bitbake -e agl-ivi-image-flutter`, `bitbake -c do_patch -f flutter-auto`, `bitbake -c do_compile -f flutter-auto`, and the full `agl-ivi-image-flutter` image build. The rootfs SHA-256 is `7f03201b07c170b09e053359e4b891089f2fa2c59c950752b7d15755cd89c49d`; kernel SHA-256 is `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`; qemuboot SHA-256 is `4558ca942a1384893c0494f51ddde5398ef37c6bd317dbed479a6ba5188bf4ba`.
- A fresh QEMU baseline with `FLR0026_NATIVE_LIGHT_LIMIT=6` selected GUIDs `126,128,130,132,134,136`. QMP captured HUD-only output; the 3D region remained black.
- The same rootfs/profile with `FLR0026_NATIVE_LIGHT_LIMIT=6` and `FLR0026_NATIVE_LIGHT_SKIP_GUIDS=136` logged `FLR0026_LIGHT_SKIPPED guid=136` and selected `138` as the sixth light. QMP captured visible 3D primitives.
- Both runs returned `FLR0026_VK_QUEUE_PRESENT result=0` and contained no `page fault`, `SIGSEGV`, `CPU:` or `Comm:` marker. Both QEMU instances were stopped by QMP `quit`; their QMP sockets and QEMU processes were absent after teardown.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Same-count alternative | six-light alternate is tested | `136` excluded; `138` selected as ordinal 5 | working log and app log | PASS |
| GUID vs count | causal dimension is distinguished | same count 6 changes HUD-only to visible 3D | QMP PNGs and light markers | PASS |
| QMP visual evidence | baseline and alternate photos attached | baseline HUD-only and alternate visible 3D | `work/evidence/flr0033/` | PASS |
| Teardown | no residual QEMU process/socket | QMP quit and post-check clean for both runs | working log | PASS |

### Act

- The result is GUID-specific enough to justify a new ticket for the light-data/parameter path. This ticket does not change production selection behavior permanently.
- If count/resource-specific, create a ticket for renderer resource or scene-composition isolation.
- If restoring model/environment changes the result, create a separate full-production-scene ticket.

## Facts / Inferences / UNKNOWN

### Facts

- Prefix 5 is visibly 3D; prefix 6 is HUD-only; present returns zero in both.
- The sixth prefix GUID is `136`, type `POINT`.
- The six-light baseline selected `136` and was HUD-only in a fresh QEMU run.
- The equal-count alternate skipped `136`, selected `138`, and showed visible 3D primitives in a QMP-only screenshot.
- The baseline app-log SHA-256 is `360139fb6735811285834ec9f82f584ef97bba878fe9aafc247034ba05c647a4`.
- The alternate app-log SHA-256 is `a3fe934bbd5950be859ca19b8b4ce028e299522962a2b514d318a3c4dc80261f`.
- The baseline QMP PPM SHA-256 is `86c3ffda13000ffec4d5b55826e6364bcaf918c1c4de4eb3584b95ee05079792`.
- The alternate QMP PPM SHA-256 is `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b`.

### Inferences

- Excluding one ordered light and restoring the same six-light count changes the pixel result, so the aggregate count alone is insufficient to explain the boundary.
- The runtime selector is a diagnostic discriminator, not yet a production fix.

### UNKNOWN

- Which light-data field or downstream operation makes GUID `136` produce HUD-only output.
- Whether the same GUID-specific behavior occurs with model/environment loading enabled and on the intended production scene transitions.

## Evidence

- Baseline QMP photo: `work/evidence/flr0033/limit6-baseline-fresh-late.png` — HUD-only.
- Alternate QMP photo: `work/evidence/flr0033/limit6-skip136-late.png` — visible 3D primitives.
- Runtime details and teardown checks: `work/logs/2026-09-06-flr0033.md`.

## Handoff

- New independent task: [FLR-0034](FLR-0034-identify-light136-production-fix.md).
- No permanent production light-selection change was made in FLR-0033.
