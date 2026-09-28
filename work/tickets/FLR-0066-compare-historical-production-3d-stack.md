# FLR-0066 — compare historical production 3D success with current patch stack

- Status: Done
- Priority: High
- Owner: source provenance + Yocto image comparison + runtime diagnosis roles
- Created: 2026-09-11
- Depends on: [FLR-0065](FLR-0065-production-target-zero-resource-boundary.md)
- Working log: `work/logs/2026-09-10-flr0065.md`

## Work unit

Determine whether the historical FLR-0049 production Sequoia 3D-only QMP result
and the controlled combined diagnostic result are reproducible on the current
patch stack, without treating the unproven combined 2D+full-shaded frame as a
regression baseline.

## Success criteria

- Identify the exact historical project tip, effective patch order, rootfs
  identity, QEMU profile, launch environment, and source behavior associated
  with the earlier visible production 3D result.
- Compare it with current `aa54396` at the layer, effective recipe, and image
  input boundaries before changing source.
- Reproduce the historical model-only pixels and controlled combined frame, or
  record UNKNOWN with the missing artifact explicitly.
- Preserve the Mac official Devtool generation role and Mini authoritative
  `do_patch`/BitBake/runtime role; do not create a second QEMU or container.

## Facts

- FLR-0049 records real production Sequoia pixels but also records that the
  native surface masked the Flutter HUD; combined 2D+3D was not accepted.
- FLR-0065 p3 reproduces HUD plus a black central region under the current
  full, no-skip, and minimal runtime conditions.
- The current tip contains many diagnostic/composition patches after the
  FLR-0049 visible-3D evidence. 0205 is opt-in sampling and is not sufficient
  to explain the earlier black result.

## Hypotheses

1. A post-success behavioral patch changed native surface or frame behavior.
2. The historical and current QEMU/image profiles differ at a hidden input
   boundary even though the bundle and launch identity look equivalent.
3. The historical artifact is not sufficiently reproducible; the cause must
   remain UNKNOWN until the missing rootfs or effective source is recovered.

## Plan / PDCA

- Plan: statically map historical and current layer patch order, source
  commits, recipe effective values, rootfs hashes, and QEMU launch profiles.
- Do: use read-only Git and fixed receiver/build metadata first; build or boot
  an old image only after the comparison identifies a bounded candidate.
- Check: require matching QMP pixel analysis and cleanup before classification.
- Act: open the next one-variable ticket only after the first difference is
  evidenced; do not create a permanent product patch from correlation.

## Result

- The current image reproduces the historical FLR-0049 model-only PPM exactly:
  `61d1c910b7bdc39893b00812ce94b25c917f603d139773aae71c935c1e04e9a2`.
- The current image also reproduces the controlled combined 2D+diagnostic-3D
  condition for 12 QMP frames. The final frame is retained under
  `$QEMU_EVIDENCE_ROOT/flr0066/p1/combined-current/frames` with SHA-256
  `7c9f6c73b9360fa37795d71fe68fc6fd75ae09ebf7e6a4393dd93accedd5479e`.
- The later 0205 patch is opt-in and default-neutral. The current black result
  is therefore not a generic regression of the 2D/3D path and is not
  attributable to 0205. It is the full production scene path that remains
  unresolved.
- FLR-0065 is left Waiting for the first production-stage boundary; FLR-0067
  owns the one-variable reintroduction matrix.

## UNKNOWN

- The historical FLR-0049 rootfs artifact is not currently present in the
  fixed Mac/Mini artifact locations checked during FLR-0065.
- The first production shape/environment/light/material operation that changes
  the current target from visible to zero is not yet identified.
