# FLR-0035 — isolate light position versus identity

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0034](FLR-0034-identify-light136-production-fix.md)
- Working log: `work/logs/2026-09-06-flr0035.md`

## Problem

FLR-0034 found that GUID `136` and the working replacement GUID `138` have matching traced light properties except position. The current evidence cannot distinguish a position-dependent rendering failure from a GUID/entity-order or downstream identity failure.

## Purpose

Use one controlled diagnostic dimension at a time to determine whether the failure follows the position or follows the light identity. Keep any position override gated and diagnostic; do not change production scene data yet.

## Success measure

- Test at least one same-position identity comparison and one position override comparison at the same six-light count.
- Preserve QMP-only screen evidence, property/selection markers, app-log hashes, and clean QMP teardown.
- If the failure follows position, create a separate ticket for scene-data correction or coordinate validation.
- If the failure follows identity, create a focused ticket for entity/bridge handling.
- Close this ticket before starting full model/environment or Planetarium scene-transition validation.

## Hypotheses

1. The failure follows GUID `136`'s position. Prediction: moving `136` to `138`'s position restores 3D, or moving `138` to `136`'s position makes it fail.
2. The failure follows GUID/entity identity or insertion order. Prediction: changing position does not move the failure boundary.
3. The observed boundary depends on model/environment skip controls. Prediction: restoring one skipped control changes the result; split that into a new ticket.

## PDCA

### Plan

- Add one diagnostic position override for selected GUIDs through the existing Mac Devtool source.
- Generate the patch with official `devtool finish --mode patch`, commit the layer registration, hand off by bundle, and reuse the fixed Mini PC build/TMPDIR.
- Compare QMP screenshots and runtime trace markers for the controlled matrix.

### Do

- A gated position override was added in the Devtool-managed source. It accepts `FLR0026_NATIVE_LIGHT_OVERRIDE_GUID` and `FLR0026_NATIVE_LIGHT_OVERRIDE_POSITION=x,y,z`; unset variables preserve default behavior.
- Source commit: `6c1e4c4 diag: override selected light position`.
- Official Devtool generated the patch, and the byte-identical registered layer patch is `0191-diag-override-selected-light-position-devtool.patch` with SHA-256 `50a0b2ed6b4eefd62781c6c19cf116cad934b9e3d3c66ec486a82fd36e405ef0`.
- Bundle `work/flr0035-71be6b7.bundle` was delivered to the fixed receiver at commit `71be6b78a39b18f7b14db33e0922c8e8266b88a5`.
- The fixed Mini PC path passed `bitbake -e agl-ivi-image-flutter`, `do_patch`, `do_compile`, and full image build. Rootfs SHA-256: `4ffb5405cedfd7efd5889e227a8e33706a33a0a7eb8730c24333c699a9cfdf1a`; kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`; qemuboot SHA-256: `b066e3d6047a2f20ac7112a1459fe6c71f1b29c303edc7469c27f4878698d47b`.
- Variant A overrode GUID `136` to GUID `138`'s position. Both traced lights then had position `(69.5,1,68.85)` and the QMP image showed visible 3D.
- Variant B overrode GUID `138` to GUID `136`'s position. Both traced lights then had position `(74.5,1.2,67.15)` and the QMP image also showed visible 3D.
- Both variants returned successful Present results, had no `page fault`, `SIGSEGV`, `CPU:` or `Comm:` marker, and were stopped by QMP `quit` with no residual socket/process.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Same-position identity | position override tested | both GUIDs at GUID138 position produced 3D | working log + QMP photo | PASS |
| Reversed position | working identity at failing position tested | both GUIDs at GUID136 position also produced 3D | working log + QMP photo | PASS |
| QMP visual evidence | each decisive variant photographed | both variants have visible 3D | `work/evidence/flr0035/` | PASS |
| Teardown | no residual QEMU process/socket | QMP quit and post-check clean for both | working log | PASS |

### Act

- Position value alone is not sufficient to explain the baseline failure. Split the next task around the setter/timing control before changing production data.

## Facts / Inferences / UNKNOWN

### Facts

- GUID `136` is HUD-only at six selected POINT lights; replacing it with GUID `138` restores visible 3D.
- Traced rendering properties match except position.
- Both position override variants produced the same visible-3D PPM SHA-256 `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b`.

### Inferences

- Position-vs-identity is the smallest remaining discriminator.

### UNKNOWN

- Whether invoking the setter/override path, rather than the replacement value, changes the result.
- Whether the baseline HUD-only capture is timing-sensitive.

## Evidence

- Variant A QMP photo: `work/evidence/flr0035/override136-to138-late.png` — visible 3D; PNG SHA-256 `141ae3c5897c651b45a3ad84ed0959fdd6e312bc56a4a5d4dea4fe11d871a44b`.
- Variant B QMP photo: `work/evidence/flr0035/override138-to136-late.png` — visible 3D; same PNG SHA-256 `141ae3c5897c651b45a3ad84ed0959fdd6e312bc56a4a5d4dea4fe11d871a44b`.
- Variant A app-log SHA-256: `962143ec695587d7142c9595a2cbe599e93b845ed1564609b38ffb676adbdd08`.
- Variant B app-log SHA-256: `b4c4d5f3e84f099640393df42f23e05e8fbc57a0a11add65a45da0f3d57e33c0`.
- Both QMP PPM SHA-256: `2439948803d165ae4339224099baf4428d2f972d63b8ceadf46ebb114856bb9b`.

## Handoff

- New independent task: [FLR-0036](FLR-0036-isolate-light-setter-timing.md).
