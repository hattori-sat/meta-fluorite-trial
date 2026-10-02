# FLR-0404 — verify ordinary Sequoia materials/lighting with the HUD

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Example Demo / QMP screenshot-video / runtime evidence roles
- Branch: `feature-flr-0404-default-sequoia-runtime` (from `dev-flr-0404-ordinary-profile`, advanced to checkpoint `65f8094`)
- Depends on: [FLR-0403](FLR-0403-correlate-fengine-oops-to-lwp.md), exact rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [FLR-0404 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0404-default-sequoia-runtime.md)
- Working log: [FLR-0404 working log](../logs/2026-10-02-flr0404.md)

## Objective

Determine whether the ordinary installed Example Demo on the exact same
patch-0334 image renders the real Sequoia with its original GLB material,
embedded textures, and scene-authored lighting while the Flutter CPU/GPU/FPS
HUD is visible in the same full QMP frame. If a live positive frame exists,
continue that run through normal pointer/UI updates and five minutes of
progressing present. This is the first ordinary-profile runtime gate; it does
not prove the independent second boot required by the overall goal.

## Facts, inferences, hypotheses, and UNKNOWN

### Facts

- FLR-0049 iterations 8/10/23 show production Sequoia pixels and red lamps,
  but not together with the Flutter HUD; those captures used special
  selection/environment conditions and are historical references.
- FLR-0394 shows a self-created LIT fixture and HUD together, not production
  Sequoia.
- FLR-0403 used the exact 0334 image with diagnostic LIT-material/SUN
  overrides. The QMP frame showed HUD/Scenes and a black Sequoia ROI; a kernel
  Oops was recorded, but capture identity was not bracketed and no GDB LWP or
  current ELF Build-ID was obtained.
- Static review of the pinned layer shows the model filter/limit and the added
  LIT material/SUN are opt-in. Omitting optional diagnostics restores the
  ordinary full load plan and original scene material/light behavior. Default
  loading can include more models and raise memory pressure; measure model
  count/memory rather than silently limiting selection. A historical OOM
  followed repeated model/Scene insertion but does not prove this exact image
  will OOM.
- An absent override does not alone prove runtime texture sampling or effective
  lighting. Positive material/texture/light claims require recognizable
  full-vehicle visual detail and any available effective asset/material/light
  evidence; a black fixed ROI can also mean the car is outside that rectangle.
- FLR-0141 records that the old Dart/native API lacks post-launch camera
  mutation methods. Whether this installed UI offers a supported camera/view
  interaction is UNKNOWN until checked on the live screen.

### Inferences

- The highest-information next comparison is a clean ordinary launch on the
  same image. Repeating the 0403 overrides cannot answer whether original
  material/lighting works; reverting to FLR-0049's HUD-hidden model-only
  profile cannot answer composition.
- A black ROI only counts as a live negative if the frame is bracketed by the
  exact app identity and readiness/present state. A post-exit black screen is
  not a rendering verdict.

### Hypotheses

1. **The diagnostic profile caused or exposed the 0403 failure.** Support:
   ordinary profile produces a recognizable, textured Sequoia and HUD with
   advancing present and no Oops/OOM. Refute: ordinary profile has a live HUD
   but no Sequoia pixels, or reproduces the fault.
2. **Production Sequoia rendering is independently unhealthy.** Support:
   model/asset readiness is observed but a correctly identity-bracketed,
   healthy ordinary frame remains black/absent. Refute: actual Sequoia and HUD
   are visible together under the unchanged image/profile.
3. **The ordinary all-model load exceeds guest resources.** Support: bounded
   memory evidence rises to a kernel OOM/allocation failure. Refute: all
   default content reaches steady present with ample headroom.

### UNKNOWN

- Whether the ordinary 0334 startup visibly selects Sequoia and exposes its
  original texture/material/light path.
- The actual default model count and whether all assets reach Scene insertion
  without a memory/OOM problem.
- Whether the current effective camera frames Sequoia inside the viewport; do
  not diagnose a black fixed ROI before whole-frame visual and camera review.
- Whether the model/present/Oops behavior changes without diagnostic flags.
- Whether the app has a supported camera/viewpoint control, and whether input
  causes a repaint or surface-lifecycle regression.
- Whether 300 seconds of continuous present and the later independent boot
  can pass on one unchanged final candidate image.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | Original Sequoia, HUD composition, input/repaint, advancing present |
| Where | Exact Mini patch-0334 image, ordinary Example Demo 3.32.5, QMP framebuffer |
| When | One fresh QEMU boot; capture at first candidate frame and after interactions; continue 300 s only after a live positive frame |
| Who | Mini runtime operator, guest `agl-driver`, QMP capture and runtime evidence roles |
| How | One allow-listed clean environment; no model/material/light/camera diagnostic overrides; same image and one QEMU |

## Scope and controls

- Runtime-only. Do not edit product source, Devtool state, recipe, patch stack,
  image, or build/cache; do not run BitBake or transfer a bundle.
- Confirm the canonical workspace and the immediate FLR-0403 evidence first.
  Recheck Mini receiver, exact image hashes, process ownership, free ports,
  fresh run ID, memory/storage, and video-capture support read-only before one
  QEMU start. Stop if any gate is UNKNOWN or another owner exists.
- Use one fresh run ID `flr0404-0001`, the existing fixed QEMU profile, and
  6144 MiB. Do not start parallel QEMU or build work; do not copy the VM image
  to Mac or make duplicate temporary directories.
- Default loading is intentionally not capped: record actual selected/model
  and Scene-add counts, Sequoia asset identity, effective camera/view, and
  bounded memory samples. Monitor the whole QMP screen instead of deciding
  from the 0403 fixed ROI alone.
- Launch the normal Example Demo as `agl-driver` using only the session values
  needed for XDG/Wayland, executable PATH, and account home. Do not export
  optional model-selection, material, lighting, camera, render, or sync
  diagnostics. Preserve original scene camera/material/embedded textures and
  scene-authored lighting.
- Use the known full-screen QMP-only capture path. Save the selected still and
  a short MP4 on Mini; transfer only the small review PNG/MP4 after hashing.
  Keep raw PPM series/full logs on Mini. Capture immediately around recorded
  PID/UID/start identity snapshots; before/after identity must match.
- Do not change viewpoint by setting an environment override. Use only an
  existing visible and supported UI interaction. If no such camera control is
  available, record UNKNOWN and make it the next separate ticket rather than
  claiming the viewpoint/depth criterion passed.
- If the full-frame Sequoia+HUD baseline is healthy, test pointer motion,
  hover, UI click/open-close, and the available view control while input and
  normal repaint stay enabled. Then measure 300 s of present progress and
  bounded kernel/OOM state. If any Oops, OOM, process loss, HUD whitening,
  vehicle disappearance, or sustained present stop occurs, capture the first
  boundary and stop early; do not run a blind five-minute wait.
- A second independent boot is not part of this ticket; keep the overall goal
  open until its separate ticket passes on the same final image.

## Success criteria

1. Exact 0334 rootfs/kernel/qemuboot hashes, clean receiver, one QEMU owner,
   free ports, fresh ID, and one evidence directory are proven before start.
2. The process starts as guest `agl-driver` with a recorded PID/UID/start
   identity and allow-listed default environment. No optional diagnostic
   selector/material/SUN/camera/sync flags are active.
3. A full 1280×800 QMP capture is immediately bracketed by the same live app
   identity and includes a recognizable production Sequoia plus CPU/GPU/FPS
   HUD. The vehicle is located in the full frame (not just a preselected ROI),
   the actual GLB asset identity and effective camera/model/Scene counts are
   present in bounded runtime evidence, and texture/shading is visibly
   recognizable. Ordinary material/texture/light overrides are absent.
4. A short QMP video plus before/after full-frame screenshots and pixel
   metrics show that pointer/UI update does not whiten the HUD, hide the car,
   or turn the native surface black. A camera/viewpoint criterion passes only
   if a supported existing control yields an evidenced changed view with
   depth/occlusion/shading; otherwise it remains UNKNOWN.
5. Only after criteria 2–4 pass, counters show progressing successful present
   through at least 300 seconds after the first positive frame. No FEngine
   disappearance, kernel Oops/OOM, abnormal exit, or sustained present stop.
6. Exact app/QMP/QEMU teardown and postflight show no owned residual process
   or listener, and image hashes remain unchanged.
7. Ticket/log/evidence retain all successful and failed commands, first
   abnormal boundary, screenshot/video hashes, bounded logs, and next action.
   A negative or incomplete run is recorded honestly and is not called target
   completion.

## Plan / Do / Check / Act

### Plan

- Use the same image as FLR-0403, but remove the diagnostic profile entirely.
- Start one runtime only after fresh Mini ownership/hash/port/storage/ID gates.
- Capture full QMP visual evidence and exact app identity before any GDB work.
- Continue to input/repaint and 300-second present only after live Sequoia+HUD
  is established. No source/build change.

### Do

- Pending read-only Mini preflight and one ordinary-profile QEMU run.

### Check

- Pending. Do not accept build readiness, asset markers, fixture pixels, or a
  non-identity-bracketed frame as the requested product rendering.

### Act

- Use the first evidenced failed boundary to select the smallest next runtime
  or source/API ticket. Keep original material/light, same-frame composition,
  viewpoint/depth, interaction, five-minute, and second-boot gates separate.

## Impact

- **Build-time / packaging:** none.
- **Runtime:** one existing 6144-MiB QEMU run; full model load may increase
  memory use. No second QEMU or parallel build.
- **Integration risk:** product input/repaint remains enabled; capture identity
  brackets and QMP-only owner-specific teardown prevent false visual verdicts
  or disturbing another runtime owner.
