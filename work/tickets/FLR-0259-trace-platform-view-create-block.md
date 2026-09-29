# FLR-0259 — trace PlatformView create call non-return

- Status: Done
- Priority: High
- Owner: `PluginsAoiPlatformViewCreate` call path, native thread and API
  ownership
- Created: 2026-09-21
- Predecessor: [FLR-0258](FLR-0258-trace-platform-view-handler-return.md)

## Objective

Determine why `PluginsAoiPlatformViewCreate` does not return after the
`flutter/platform_views` create handler reaches it in the running Fluorite
Example Demo.

## Facts

- FLR-0258 proved handler entry and call begin, with no call return or handler
  end marker.
- The same run reached native C API registration return and rendering-loop
  routing, so process startup and the first native registration boundary are
  not sufficient to explain the missing return.
- The 2D HUD remains visible; production 3D remains unproven and the measured
  production ROI is black.

## Result

The non-return is a synchronous drain deadlock. The PlatformView handler waits
for `PluginsAoiPlatformViewCreate` to return. The C API path posts a
`ViewTargetSystem::ProcessMessages` task to the ECS strand and synchronously
waits for it, while the ECS/rendering thread is synchronously waiting for a
Flutter `BinaryMessenger::Send` response from `ViewTarget::DrawFrame`.

The repair removes only the C API-side synchronous wait and captures the
`ViewTargetSystem` shared pointer by value in the posted task. The task remains
on the ECS strand, but the Flutter handler can now return its result.

After the repair, the PlatformView surface is composited as a black trapezoid
over the white 2D surface. This proves the handler/deadlock boundary is fixed,
but it does not prove production 3D pixels. The internal Filament render
content is split to FLR-0260.

## Hypotheses

1. The create call blocks on a native synchronization or thread-affinity
   condition before it can return.
2. The create call enters a native API path that waits for a Wayland or
   renderer event which is not delivered in the current launch contract.
3. The call reaches a fault or abort path whose evidence is outside the bounded
   Flutter log, such as a systemd journal, coredump, or native backtrace.

## Scope boundary

Collect bounded native call-stack, journal, and process-state evidence around
the existing call. Do not change camera, light, material, rendering,
composition, input, or scene payload until the blocking operation is named.

## Success criteria

- [x] Identify the first blocking native frame and the cyclic wait.
- [x] Keep the existing single-QEMU/QMP evidence and exact guest launch
  contract.
- [x] Create a separate follow-up ticket for the remaining black render
  content after the blocking operation is repaired.

## UNKNOWN

- Why the now-running Filament render target still contains no chromatic
  production geometry.
- Whether the remaining black content is a camera/material/light/render-target
  issue.
