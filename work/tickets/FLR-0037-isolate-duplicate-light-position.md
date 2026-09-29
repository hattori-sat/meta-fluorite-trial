# FLR-0037 — isolate duplicate selected-light positions

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0036](FLR-0036-isolate-light-setter-timing.md)
- Working log: `work/logs/2026-09-06-flr0037.md`

## Problem

FLR-0033 found that replacing GUID `136` with GUID `138` restores QMP 3D. FLR-0034 found matching traced light properties except position. FLR-0035 then showed that aligning either light's position with the other restores QMP 3D. FLR-0036 ruled out a same-value setter alone and simple delayed capture timing as sufficient explanations.

## Purpose

Test whether a duplicate position among the six selected lights is the smallest remaining trigger. Keep the test diagnostic and gated; do not edit production scene data or claim a permanent fix.

## Success measure

- Compare the known distinct-position six-light baseline with at least two duplicate-position variants and one changed-but-nonduplicate control while keeping light count, GUID order, model/environment controls, image, and QMP procedure fixed.
- Preserve one QMP-only photo, runtime log, hashes, and clean teardown for every decisive variant.
- Record whether the result follows duplication itself or only the specific GUID `136`/`138` pair.
- Close this ticket before beginning any production scene correction or Planetarium/scene-transition work.

## Hypotheses

1. Any duplicate position among selected lights restores 3D. Prediction: moving GUID `136` onto another selected light such as GUID `134` also produces visible 3D.
2. Only the GUID `136`/`138` pair or their relative order matters. Prediction: another duplicate-position pair remains HUD-only.
3. The apparent duplicate-position effect is a downstream identity/resource issue. Prediction: duplicate coordinates do not consistently predict the QMP pixels once the selected set changes.

## PDCA

### Plan

- Reuse the existing fixed FLR-0035 image and the existing diagnostic position-override path.
- Use one new QEMU run directory per variant and capture QMP-only screenshots after the same startup interval.
- Keep `FLR0026_NATIVE_LIGHT_LIMIT=6`, trace GUIDs `136,138`, and the model/environment skip controls fixed.

### Do

- Reused the FLR-0035 rootfs/kernel/qemuboot identity with rootfs SHA-256 `4ffb5405cedfd7efd5889e227a8e33706a33a0a7eb8730c24333c699a9cfdf1a`, kernel SHA-256 `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and qemuboot SHA-256 `b066e3d6047a2f20ac7112a1459fe6c71f1b29c303edc7469c27f4878698d47b`.
- Used the official Yocto `runqemu` path with `snapshot`, slirp networking, a unique QMP socket per run, `agl-driver`, `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, and the installed Example Demo bundle.
- Fixed runtime controls for every app run: `FLR0026_NATIVE_LIGHT_LIMIT=6`, model/environment skip controls, sync trace, and forced rendering after skipped frames. Traced GUIDs were `134,136,138` for the final matrix.
- Fresh distinct-position control selected six lights with GUID `136` at `(74.5,1.2,67.15)` and GUID `138` at `(69.5,1,68.85)`.
- A read-only property probe established GUID `134` at `(74.5,1.2,68.85)`.
- Duplicate variant A changed GUID `136` to GUID `138`'s position `(69.5,1,68.85)`.
- Duplicate variant B changed GUID `136` to GUID `134`'s position `(74.5,1.2,68.85)`.
- Changed-but-nonduplicate control changed GUID `136` to `(100,10,100)`, which does not match the traced selected-light positions.
- All runs were stopped using QMP `quit`; no recorded QMP socket or matching QEMU process remained.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Distinct-position control | HUD-only baseline is reproduced | HUD-only; candidate region changed only 818 overlay pixels | QMP photos + app log | PASS |
| Duplicate with GUID `138` | visible 3D if any duplicate is sufficient | Native frame showed black 3D geometry on white background; candidate region changed 22,893 early / 63,301 late pixels | QMP photos + app log | PASS |
| Duplicate with another selected GUID | distinguishes pair-specific behavior | Same visible frame and pixel hashes as the GUID138 duplicate | QMP photos + app log | PASS |
| Changed but nonduplicate position | falsifies duplication-only explanation | Same visible frame and pixel hashes as both duplicate variants | QMP photos + app log | PASS |
| Runtime health | no native fault during comparison | Present results 23/21/21; fault count 0 for duplicate138/duplicate134/nonduplicate | app logs | PASS |
| Teardown | no residual QEMU process/socket | QMP quit and post-check clean for all runs | remote post-check | PASS |

### Act

- Duplication-only is rejected because the changed-but-nonduplicate coordinate produced the same frame and hashes.
- Split the next ticket around changed-value position mutation: determine whether the effect follows GUID `136` specifically or any selected light's changed position setter.

## Facts / Inferences / UNKNOWN

### Facts

- FLR-0035 produced visible 3D when GUID `136` and `138` shared a position.
- FLR-0036 produced HUD-only output for the same-value setter and two delayed unmodified baseline captures.
- The fresh distinct-position control in this ticket was HUD-only.
- Both duplicate variants and the changed-but-nonduplicate variant produced the same early PPM SHA-256 `aa0f262851c44fa18bf5ca8e777a6ecb98666e390c3100e8192e699b4276cc8a` and late PPM SHA-256 `adfaa6d873dfee169c44299939f375a483c463be701f221c9bd717ec9eed5352`.
- The distinct control PPM SHA-256 was `a0cf9bca2105b2ce58a8620c30771fbbfd2753dae1b312d80a7a2d2b8b9b71f8` at both captures.

### Inferences

- A changed position value is the smallest confirmed discriminator; duplication itself is not required.

### UNKNOWN

- Whether the effect depends on GUID `136` or occurs when any selected light receives a changed position.
- Whether the changed-value setter exposes a latent native light/resource initialization defect.

## Evidence

QMP-only images are the visual record for this ticket. All captures are 1280x800 QMP framebuffers; the late duplicate/nonduplicate frames visibly contain black 3D geometry on a white native frame, while the distinct control remains HUD-only:

- Distinct control, early: [distinct-12s.png](../evidence/flr0037/distinct-control/distinct-12s.png)
- Distinct control, late: [distinct-32s.png](../evidence/flr0037/distinct-control/distinct-32s.png)
- GUID136→GUID138 duplicate, early: [dup138-14s.png](../evidence/flr0037/duplicate136-to138/dup138-14s.png)
- GUID136→GUID138 duplicate, late: [dup138-34s.png](../evidence/flr0037/duplicate136-to138/dup138-34s.png)
- GUID136→GUID134 duplicate, early: [dup134-18s.png](../evidence/flr0037/duplicate136-to134/dup134-18s.png)
- GUID136→GUID134 duplicate, late: [dup134-38s.png](../evidence/flr0037/duplicate136-to134/dup134-38s.png)
- Changed-but-nonduplicate, late: [nondup-38s.png](../evidence/flr0037/changed-nonduplicate/nondup-38s.png)

The duplicate and changed-but-nonduplicate PNGs are byte-identical within the corresponding early/late capture, which is consistent with the same rendering boundary but does not by itself identify the native cause.

## Handoff

- New independent task: [FLR-0038](FLR-0038-isolate-changed-light-position-setter.md).
