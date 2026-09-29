# FLR-0284 — restore direct production lights for the attached model

- Status: Done
- Priority: High
- Owner: production direct-light contribution
- Depends on: [FLR-0283](FLR-0283-restore-production-lighting-ab.md)
- Working log: `work/logs/2026-09-24-flr0284.md`

## Problem

The production model is attached and has valid `base_lit_*` materials, but
QMP remains black after restoring the default indirect light. FLR-0283 still
skipped all 13 direct production lights.

## Hypotheses

1. Direct lights are required for visible production materials; restoring them
   produces chromatic QMP pixels.
2. Direct-light setup is broken or unsafe; restoring it produces a bounded
   fault or remains black.
3. The black result is independent of lighting and remains a camera/target
   composition problem.

## Scope and success criteria

- Reuse the existing image and one 4096 MiB QEMU.
- Restore direct lights only; retain the primary scene-attachment patch and
  indirect light setting from FLR-0283.
- Capture bounded light/material/draw logs and ten QMP frames.
- Stop through exact guest PID and QMP quit. Record whether 3D pixels appear or
  whether the direct-light boundary faults.

## Verification plan

1. Set `FLR0027_NATIVE_SKIP_LIGHTS` off while leaving model limit=1 and frame
   event skip enabled.
2. Compare QMP chroma, present, and runtime fault evidence with FLR-0283.

## Result

- Reused the same image and one 4096 MiB QEMU. Preflight, guest-ready, QMP
  capture, and teardown all passed.
- Direct-light skipping was removed while the primary scene attachment and
  default indirect light remained unchanged. The model loaded and attached
  with 12 renderables and production `base_lit_*` materials.
- Frame begin/render/end and Vulkan present remained positive. No SIGSEGV,
  page fault, OOM, or killed-process marker appeared.
- QMP-only frame `production-direct-light-video/frame-00009.ppm` retained SHA
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`, with
  changed=0, chromatic=0, and max_chroma=0.
- Guest memory remained healthy: Total 4087260 kB, Free 2996576 kB,
  Available 3365092 kB.
- The bounded direct-light log showed `FLUORITE_SCENE_PASS_EXECUTE_BEGIN
  commands=1`; FLR-0282's primary run had recorded `commands=36`. This is a
  new draw-command boundary, not a memory boundary.

## Conclusion

Restoring direct lights also did not restore production pixels. Lighting is not
the sufficient cause. FLR-0285 owns the draw-command/render-queue difference
between the attached production model and the QMP target.
