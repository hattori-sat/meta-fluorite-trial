# Plan: FLR-0122 native present/surface diagnosis

## Goal

Find the first divergence between the self-made blue-cube fixture's successful
native shape/queue-submit path and a nonzero 3D pixel in the QMP-visible
region. Keep this as a diagnostic checkpoint; do not patch the product until
the failing process step is known.

## Evidence-first sequence

1. Run the canonical-repository guard and confirm FLR-0122 is the only
   In-Progress ticket.
2. Inspect the effective recipe patch order and existing source markers for
   frame completion, Vulkan present, Wayland attach/damage/commit, and surface
   geometry. Record two or more falsifiable hypotheses.
3. Reuse the fixed Mini build and evidence root. Run one official QEMU fixture
   only, with one `flutter-auto` process and bounded guest status collection.
4. Capture QMP-only early/late frames and analyze the full frame plus
   `[300,250,620,400]`; retain coredump and process checks.
5. Stop through negotiated QMP `quit`, verify zero residual targets and no
   socket, and commit the raw-evidence references and interpretation.
6. If the first divergence is identified, create a separate implementation
   ticket. If not, preserve UNKNOWN and create a narrower diagnostic ticket.

## Decision rule

- Frame/present markers absent or incomplete: keep focus on native render/WSI
  execution.
- Present and Wayland attach/commit present but QMP region unchanged: focus on
  surface geometry, stacking, alpha, or compositor handoff.
- Pixels appear outside the target region: correct the capture/geometry model,
  not the renderer.
- No branch is promoted to root cause without paired runtime and pixel
  evidence.

## Stop conditions

- Never start a second QEMU while the official harness reports an active one.
- Stop before any source edit if the evidence does not identify an owner.
- Keep FLR-0121 immutable except for its completed outcome and link to this
  diagnostic ticket.
