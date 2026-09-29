# FLR-0309 — probe zero-intensity production light

- Status: Done
- Priority: High
- Owner: production default-Scene SUN / LLVM-llvmpipe runtime boundary roles
- Created: 2026-09-25
- Predecessor: [FLR-0308](FLR-0308-diagnose-fengine-loop-page-fault.md)
- Working log: `work/logs/2026-09-25-flr0309.md`

## Objective

Separate creation/presence of the production diagnostic SUN from the non-zero
lighting/shader contribution that may trigger the current FEngine/libLLVM fault.
This is a discriminator for the real 3D goal; it is not a claim that zero
intensity is an acceptable final lighting configuration.

## Known-good acceptance baseline

The target is not merely a surviving Flutter process. Historical evidence
proves that the repository has produced both HUD and native 3D in the same
QMP frame:

- FLR-0070: production Sequoia plus HUD/color pixels.
- FLR-0066: controlled combined HUD plus diagnostic Sequoia.
- FLR-0251: self-made native fixture plus HUD.
- FLR-0286: self-made lit Filament fixture plus HUD.

The current production run is a regression against that baseline: the HUD can
be present, while the production native ROI is `0/144000`. The final success
criterion remains Sequoia/HUD composition with visible non-black 3D/light
pixels, not only a light-setup log.

## Facts

- FLR-0308 one-model light-enabled control reproduced an FEngine loop page
  fault in `/usr/lib/libLLVM.so.18.1` before production asset/material/draw
  markers.
- The same one-model control with the FLR-0305 light omitted avoided the
  fault but stalled before present, so it is not a successful 3D control.
- The existing normal diagnostic SUN uses intensity `110000.0`.
- The Mac Devtool source change is committed as
  `81060181b637280612c675152fa872fd83b04abe`.
- The official Devtool-generated patch was produced from baseline
  `9dc263b894a1f89b7ccde6668f24dafa862a6066`; its SHA-256 is
  `15e7494a3664eb3361af2cbd3a8931b69e89e0b43de2564c100d53703a839519`.
- The default path is unchanged. Only when
  `FLR0309_PRODUCTION_SCENE_LIGHT_ZERO_INTENSITY` is present does the probe
  use intensity `0.0`; the setup log records `mode=zero-intensity`.
- Mac Podman reused the fixed machine/container and fixed state bind. The
  mount-permission contract passed.
- The canonical layer commit is `58531738d01e891654a012c35e8248f4229e7273`.
- Bundle handoff passed with SHA-256
  `9ca22a650435ff105d2a9452f5c0ce12f7be8cec7a47ff0c08f4bbd4eb559c21`.
- Mini `do_patch`, `flutter-auto do_compile` (2686 tasks), and full image
  build (11758 tasks) all passed.
- The fixed QEMU harness preflight, start, guest-ready, serial-exec launch,
  QMP capture/video, and negotiated QMP quit passed. The final independent
  residual check passed with `residual_targets=0 residual_qmp=0`.
- Zero-intensity runtime logged
  `FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE ... intensity=0 mode=zero-intensity`
  and reached Vulkan queue submit/present markers before the fault.
- The guest journal recorded the same `FEngine::loop` page fault and `#PF`
  boundary as FLR-0308. The parent `flutter-auto` remained alive and
  `coredumpctl` was empty.
- QMP still and all eight QMP video frames share SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  Native ROI `(440,220,400,360)` was `0/144000`; HUD ROI was uniform white
  (`12800/12800` changed from black but `0` chromatic).
- Runtime marker evidence SHA-256 is
  `660ee23c2d802c6408e13ccce3ed802e1c24b3d949daef5a26d0c911105c23a6`;
  guest fault evidence SHA-256 is
  `853dedf9f88046aca2ba7aaa68a12497698f8e76c167206fbde45f5dd17725b9`.

## Inferences

- A zero-intensity SUN keeps the light entity and Scene attachment path while
  removing non-zero irradiance from the discriminator.
- This is the smallest useful next experiment because it preserves the
  one-model payload, QEMU memory, launcher, and QMP capture contract from
  FLR-0308.

## Hypotheses

1. If zero intensity reaches present or avoids the LLVM fault, non-zero
   lighting/shader evaluation is implicated more strongly than light entity
   creation. Result: the fault was reproduced, so this branch is falsified.
2. If zero intensity reproduces the same fault, light creation/Scene
   attachment or the earlier renderer-present path remains implicated. Result:
   supported as the next boundary; the exact owner is still UNKNOWN.
3. If zero intensity also stalls before present, the light is correlated with
   the transition but is not yet proven causal. Result: falsified for this
   run; present was reached.

## Verification plan

1. Commit the canonical patch and refreshed baseline lock locally.
2. Send one Git bundle from the canonical commit to the fixed Mini receiver.
3. Run the fixed Mini recipe patch gate, compile, and full image build; record
   `do_patch`, compile, image, and artifact hashes.
4. Run exactly one QEMU through the fixed harness with one-model Sequoia,
   `FLR0305_PRODUCTION_SCENE_LIGHT=1`, and
   `FLR0309_PRODUCTION_SCENE_LIGHT_ZERO_INTENSITY=1`.
5. Capture QMP-only screenshot, bounded QMP video, runtime markers, guest
   journal fault summary, and native/HUD ROI counts. Tear down QEMU and
   verify no residual process.

## PDCA

### Plan

Use one variable only: the SUN intensity. Keep the known one-model production
selection and all Mini/QEMU paths fixed.

### Do

Mac source commit and official patch generation are complete. Mini transfer,
authoritative build, and runtime capture are pending.

### Check

The zero-intensity SUN reaches present and reproduces the same FEngine/libLLVM
fault as the normal-intensity SUN. It does not restore native pixels. The
normal-light versus zero-light comparison therefore rejects intensity as the
distinguishing variable, while the no-light control remains a separate
present-before-load stall.

### Act

Close this ticket and hand the first differing operation boundary to FLR-0310.
Do not change camera/composition or hand-edit the generated patch. Compare the
production light-registration call order and ownership against the known-good
lit fixture before choosing another runtime control.

## UNKNOWN

- Whether the exact fault owner is light entity registration, scene ownership,
  or the first renderer queue/present operation.
- Whether the production asset reaches material/draw setup after this fault
  boundary is bypassed.
- Whether the final vehicle silhouette is merely camera-framed out or remains
  absent after the light boundary is fixed.
