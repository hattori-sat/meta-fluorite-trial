# FLR-0303 — fix production transform probe compile contract

- Status: Done
- Priority: High
- Owner: production ModelSystem transform/scene boundary role
- Created: 2026-09-25
- Predecessor: [FLR-0302](FLR-0302-probe-production-world-transform.md)
- Working log: `work/logs/2026-09-25-flr0303.md`

## Objective

Make the FLR-0302 opt-in world-transform probe compile against the authoritative
Filament version without changing its observation scope or production render
behavior.

## Facts

- Mini `flutter-auto do_patch`: PASS at receiver tip `fe5be74e4140689c82723937869f20095f4d49f2`.
- Mini `flutter-auto do_compile`: FAIL before linking in
  `plugins/filament_view/.../model_system.cc`.
- The compiler reported three errors: `filament::math::length` is not a
  member of this Filament version.
- The required observation is root/child world translation and parent ID;
  world scale is optional and is removed from the probe.

## Current execution result

- Source correction commit:
  `a8a365088e8a3d13743957d03797d72e69115929`.
- Official component rebase/update: `PASS` from baseline
  `b4f0760e9c54c85b9440eb64b918fbc0fecee35e`.
- Registered patch:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0298-flr0303-fix-transform-probe-api-devtool.patch`.
- Patch SHA-256:
  `430ebac4e7c976b5dfb142c2b8af9051c84ab9dcc32993f1b46927d1f622254a`.
- Mini validation of this new tip is recorded in the completion section below.

## Completion

- Fixed Mini `flutter-auto do_patch`: PASS at receiver tip
  `4ab701306b063baa8e649a493468e6fdd397b5c3`.
- Fixed Mini `flutter-auto do_compile`: PASS; all attempted tasks succeeded.
- Full `agl-ivi-image-flutter` build: PASS; `11758` tasks attempted and all
  succeeded.
- The resulting image was used for the FLR-0302 QMP runtime probe.

## Success criteria

1. The source correction is committed in the existing Devtool local Git.
2. Official component patch generation produces a byte-stable patch registered
   under `meta-fluorite-trial`.
3. Mini `do_patch` and `flutter-auto do_compile` both pass.
4. No production behavior is changed when the opt-in variable is absent.

## Hypotheses

1. Removing the unsupported optional scale calculation will make the probe
   compile; the translation/parent API calls are already used by the source.
2. If compilation then passes but runtime evidence is unchanged, the next
   ticket remains a runtime boundary investigation, not a lighting patch.

## UNKNOWN

- Runtime root/child world transform values until the corrected image runs.
- Whether the world translation will prove an out-of-camera placement.

## Plan / PDCA

- Plan: create a source-only follow-up commit from source HEAD `b4f0760`.
- Do: regenerate a separate official Devtool patch and hand it off by bundle.
- Check: Mini `do_patch`, then `do_compile` only.
- Act: run QEMU with the probe only after both build gates pass.
