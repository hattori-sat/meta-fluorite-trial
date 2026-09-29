# FLR-0332 — trace native buffer publish trigger

- Status: Done
- Priority: High
- Owner: native render target publish / Wayland buffer attach roles
- Created: 2026-09-25
- Predecessor: [FLR-0331](FLR-0331-trace-current-native-wayland-surface-composition.md)
- Working log: `work/logs/2026-09-25-flr0332.md`

## Objective

Map the source/runtime trigger that should publish the first native buffer
after `wl_surface@39` creation and `wl_subsurface@40` registration. Start with
static source and existing marker/patch inspection; add a single Devtool probe
only if the first missing call remains unresolved. Do not change Light,
camera, material, Scene ownership, or compositor stacking.

## Success criteria

- Identify the owning source module and call path from Filament present/draw to
  native buffer attach.
- Compare the active patch order and persistent Mac Devtool source against the
  current Mini image before proposing a change.
- If needed, add one opt-in probe through the official Devtool workflow, then
  commit, bundle, and build only after the static boundary is known.
- Preserve QMP-first full-frame evidence and zero-residual teardown for any
  runtime run.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0331 saw native surface creation and subsurface registration but no
  native surface attach/damage/commit.
- Parent Flutter surface commits and HUD pixels are visible.
- Filament reaches fixed-color replacement, Scene add, `beginFrame=true`, and
  draw submit.

### Hypotheses

1. The native target publish callback is never invoked after draw/present.
2. The callback exists but is gated by a surface-ready, buffer-release, or
   frame-callback condition that current runtime never satisfies.
3. A native buffer is produced elsewhere, but the current trace misses its
   attach path because the owning module is outside the existing Filament
   markers.

### UNKNOWN

- Whether the `vkQueuePresentKHR` page fault is caused by the WSI semaphore,
  llvmpipe/LLVM path, or a stale image/source ABI mismatch remains UNKNOWN and
  is owned by FLR-0333.

## Plan / PDCA

1. Inspect layer recipe patch order, active source ownership, and existing
   Wayland/native publish markers.
2. Trace the call path statically and compare it with FLR-0219/0269 history.
3. Create one minimal source probe only if static evidence cannot identify the
   missing trigger; use Mac Devtool source commit and official patch flow.

## Result

- The surface observed in the current run is the Filament `ViewTarget` surface,
  not `NavRenderSurface`: the NavRenderSurface probe strings are present in the
  binary but no probe marker fires, while the Wayland trace shows the
  ViewTarget-style `create_surface → get_subsurface → place_above →
  set_position → set_desync` sequence.
- The no-commit control and the explicit `FLUORITE_NATIVE_WAYLAND_COMMIT=1`
  A/B both remain HUD-visible/native-black. The latter reaches
  `beginFrame=true`, render return, and commit, but `vkQueuePresentKHR` never
  returns and the guest reports an `FEngine::loop` page fault.
- QMP evidence and filtered runtime logs are retained under
  `/mnt/yocto/evidence/flr0332-0002/qemu/`; QEMU teardown was clean.
- Therefore FLR-0332's publish-trigger objective is complete. The next
  independent ticket is FLR-0333 for the Vulkan present-return/page-fault
  boundary.

## Stop conditions

- Do not patch `wl_surface.commit`, stacking, alpha, Light, or camera based
  only on the absence of QMP pixels.
- Do not treat parent HUD commits as proof that native 3D was published.
