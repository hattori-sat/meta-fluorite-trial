# FLR-0078 — isolate explicit-light Scene attachment boundary

- Status: Waiting
- Priority: High
- Owner: Mac Devtool source + Mini QEMU runtime roles
- Created: 2026-09-11
- Depends on: [FLR-0077](FLR-0077-isolate-full-production-shaded-boundary.md), [FLR-0067](FLR-0067-reintroduce-production-scene-stages.md)
- Working log: `work/logs/2026-09-11-flr0078.md`
- Plan: `docs/superpowers/plans/2026-09-11-explicit-light-scene-attachment.md`

## Work unit

Determine whether the first explicit-light boundary is inside Filament light
construction or at `Scene::addEntity`. The test must keep the image, launch
profile, selected one-light input, and QMP capture contract fixed, and change
only whether a successfully built Filament light entity is added to the
Scene.

This is a diagnostic ticket. It must not silently change the product default.

## Success criteria

- Reuse exactly one existing rootful Podman machine and one bind-mounted
  Devtool container on Mac; do not create a second machine, container, or
  project volume.
- Edit the persistent Mac Devtool source and create the recipe patch through
  the official Yocto Devtool update/finish flow. Do not hand-author the patch
  body.
- Transfer the committed layer by the existing bundle handoff to the fixed
  Mini receiver. Mini must pass `do_patch`, component compile, and the full
  `agl-ivi-image-flutter` build before runtime testing.
- Run the same one-light profile with Scene attachment enabled and disabled.
  The only diagnostic difference is `FLR0026_NATIVE_LIGHT_SKIP_SCENE_ADD`.
- Preserve QMP-only frames, frame hashes, region counts/bounding boxes,
  runtime markers, artifact hashes, teardown output, and any failed or
  invalid execution. Do not delete evidence to make the result cleaner.
- Classify the result as construction-side, Scene-attachment-side, or
  UNKNOWN. A nonzero pixel count without a recognizable object is not a 3D
  success claim.

## Facts

- FLR-0067 p6 established the first stage-level boundary: explicit lights
  enabled produced `0/223200` candidate pixels, while the same profile with
  lights skipped produced `4905/223200`.
- FLR-0077 proved that attaching the built default indirect light to the Scene
  alone does not restore full-production pixels. The corrected opt-in run
  reached model, renderable, Vulkan submit, Wayland swapchain, and present
  markers while remaining at `0/223200`.
- Static source inspection shows
  `BuildLightAndAddToScene(Light&)` calls `BuildLight(light)` and then
  `AddLightToScene(light)`. `BuildLight` creates the Filament entity and
  configures `LightManager::Builder`; `AddLightToScene` calls
  `Scene::addEntity`.
- The Mac Devtool source edit is source commit `544f451`. The official
  split-component Devtool flow generated `0004-diag-isolate-explicit-light-scene-attachment.patch`;
  the canonical layer copy is `0208-diag-isolate-explicit-light-scene-attachment-devtool.patch`
  with SHA-256
  `0b62862e0ef04c7bf77a71439604ffbfce3a24527adf549f65d0c1a8cfeaa163`.
- Generated `0001`, `0002`, and `0003` were byte-identical to canonical
  `0205`, `0206`, and `0207`; only the new `0208` was added to the layer.
- The fixed FLR-0077 rootfs is identified in its ticket and must not be mixed
  with a different artifact during this ticket.
- Historical combined 2D+Sequoia evidence remains in FLR-0066 and FLR-0070;
  later exact-image repetitions did not establish a stable full-production
  baseline.

## Ranked hypotheses and falsifiers

1. **Scene attachment is the first failing operation.** If skipping only
   `Scene::addEntity` preserves the model-only positive while attachment
   enabled returns to zero, the boundary is attachment/resource interaction.
2. **Light construction or its parameters is the first failing operation.**
   If both attachment states remain zero with the same built light, the
   failure is upstream of Scene registration or inside the light/material
   resource path.
3. **The one-light cut is not sufficient to isolate the production fault.**
   If the A/B is identical but runtime markers or cleanup differ, the result
   is UNKNOWN and the next ticket must select a smaller resource/material
   operation; it must not be promoted to a product fix.

## UNKNOWN

- The exact Filament operation that changes a valid Sequoia renderable into a
  zero-pixel production target.
- Whether the historical FLR-0070 p9 combined frame can be reproduced with a
  complete artifact and launch identity.
- Whether a one-light Scene attachment has the same failure as the full
  production light set.

## Plan / Do / Check / Act

### Plan

See `docs/superpowers/plans/2026-09-11-explicit-light-scene-attachment.md`.

### Do

- The source edit is opt-in and bounded by operation markers. The default
  light Scene-add path is unchanged.
- The official Devtool component flow was recovered after a `No recipe named
  'fluorite-plugins'` failure: baseline branch `32f4fab` → `component-add` →
  source branch `544f451` → `update-recipe --mode patch --append --no-remove`.
- The bounded retry parsed 3342 `.bb` files with 0 errors and generated the
  new patch. The patch was copied unchanged and registered after 0207.
- The baseline layer lock was refreshed using the repository test algorithm
  for 273 files. `make verify` passed all repository, MCP, link, file-size,
  and QEMU/runtime contract gates.

### Check

Pending for Mini. Mac-side source and official patch generation are PASS;
Mini `do_patch`, compile, full image, and QMP A/B evidence are required before
classifying the rendering boundary.

### Act

Pending. Keep any diagnostic patch opt-in and split a new ticket for the next
operation; do not broaden this ticket with unrelated compositor, route, or
cleanup changes.

## Evidence locations

- Mini evidence root: `$QEMU_EVIDENCE_ROOT/flr0078`
- Mini artifact index: receiver-side `evidence/flr0078/artifacts.txt`
- Raw QMP frames and runtime logs remain on the Mini and are referenced by
  hash from this ticket and its working log.

## Runtime gate correction — 2026-09-11

The Mac Devtool patch and Mini image gates are complete. FLR-0055 corrected
the runtime contract and its live p6 gate passed, so this ticket can resume.
The earlier evidence must still not be interpreted as the requested A/B result:

- p3 launched the self-made fixture and reached native setup, Vulkan submit,
  present, and commit markers, but its QMP candidate region was `0/223200`.
  This is a current-image black observation, not a fixture success.
- p4 and p5 reached QMP start but did not reach guest SSH or serial readiness;
  their start/empty-serial logs remain on the Mini under
  `$QEMU_EVIDENCE_ROOT/flr0078/p4` and `p5`.
- The failed QMP teardown and exact-PID cleanup are recorded in
  `work/logs/2026-09-11-flr0055.md` and the FLR-0078 working log. No second
  QEMU was started while another target process was live.

The corrected `guest-ready` and QMP teardown gates passed on one fresh QEMU,
but p7 lost guest SSH immediately after the readiness probe. FLR-0055 now
captures the secondary boot serial stream. Resume the force-render-matched
pure-fixture control only after that post-readiness stability gate passes.

## Control-path handoff — 2026-09-11

FLR-0079 p10/p11 is now the active control-path ticket. The current forced
fixture reached an `agl-driver`-owned `flutter-auto` PID, fixture setup,
Wayland surface creation, minimal geometry, and three queue-present markers, but
QMP remained black with `PRESENT_BOUNDARY_DONE=0`. The explicit-light Scene-add
A/B is therefore Waiting and no one-light conclusion is accepted until the
current-image fixture control is reproduced or its first missing boundary is
classified.
