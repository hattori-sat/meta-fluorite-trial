# FLR-0089 — semaphore completion and native pixels

- Status: Done
- Priority: High
- Owner: Filament Vulkan submit completion / llvmpipe WSI boundary
- Created: 2026-09-12
- Depends on: [FLR-0088](FLR-0088-vkqueue-present-wait-owner.md)
- Working log: `work/logs/2026-09-12-flr0089.md`

## Work unit

Determine whether the application-created semaphore is signaled as expected,
whether llvmpipe/WSI blocks while consuming it, or whether native commands do
not produce pixels before the present wait. This is an evidence-only unit;
do not alter present behavior until the first missing boundary is proven.

## Success criteria

- Capture one bounded observation of semaphore/fence completion and the first
  blocking symbol or wait boundary.
- Correlate command execution, submit completion, present entry, and QMP
  native-region pixels in the same run.
- Separate native-surface rendering from the already-visible 2D HUD.
- Preserve a QMP-only screenshot, bounded video sample, selected runtime log,
  hashes, and QMP teardown evidence.
- If a product change is selected, open a new ticket for that change rather
  than mixing it into this evidence unit.

## Facts

- FLR-0088 proved that the submit signal semaphore and present wait semaphore
  are the same handle and that `vkQueueSubmit` returned success.
- The corrected QMP screenshot had `0` changed pixels in the native region and
  `1232` changed pixels in the HUD region.
- The queue-present entry marker was observed without a corresponding return
  marker in the bounded runtime log.
- The neutral fence-status patch was generated through the persistent Mac
  Devtool source and registered as patch 0185. Its SHA-256 is
  `01d60ca904f3da539e1dddcc9d7d5545a52b65fc60b7141bb56b505fe3156714`.
- The authoritative Mini metadata, `do_patch`, `do_compile`, and full image
  gates passed. The full image attempted 11748 tasks; 17 warnings were
  reported and no task failed.
- In the corrected runtime, two submit calls returned `result=0`. The
  present-side submit used signal semaphore `0x7fddb8024330` and fence
  `0x7fddb80273f0`. Immediately before present, the neutral fence query
  returned `result=1` (`VK_NOT_READY`), and the present wait semaphore was the
  same `0x7fddb8024330` handle.
- The QMP runtime screenshot showed `0` changed native pixels and `1288`
  changed HUD pixels. Sixteen runtime frames were captured, and QMP teardown
  completed with no residual target or QMP socket.

## Inferences

- A semaphore handle mismatch is no longer the leading explanation.
- The next observation must distinguish signal completion, llvmpipe/WSI wait,
  and native command/pixel production before any new source patch.
- The current evidence moves the first missing completion boundary earlier:
  the application-side queue submission is accepted, but its driver fence is
  still not ready at the present call.

## Hypotheses

1. The semaphore is submitted successfully but is not completed as expected.
2. llvmpipe or the WSI path blocks after consuming the valid wait semaphore.
3. Native commands are not executed or do not write the expected surface,
   while the Flutter HUD continues to present.

## UNKNOWN

- The semaphore's signaled state at present entry.
- The first blocking symbol after `vkQueuePresentKHR` entry.
- Whether native command execution reaches a nonzero pixel-producing path.

## Plan / Do / Check / Act

### Plan

Reuse the same fixed Mini build, QEMU profile, evidence root, and single
runtime launch. Add only the smallest bounded observation needed to identify
completion or pixel production. Record failed runs separately and end every
QEMU session through QMP.

### Do

Initial evidence is inherited from FLR-0088: corrected patch, Mini build
gates, and the QMP black-native/HUD-visible runtime are available. No source
change has been made for this ticket yet.

### Check

The bounded observation is complete. Mini evidence is stored under
`$EVIDENCE_ROOT/flr0089-273b098`; the metadata, do_patch, do_compile, and
full-image log hashes are recorded in the working log. The QMP runtime PPM is
`qemu-fence/qmp-fence-runtime.ppm`, SHA-256
`b10b88e4b0f2b48e7408bb3ae75a35a5787e7b6c764652c19ab14d6f14d0d3ab`.
Native-region analysis is `changed_pixels=0`; HUD analysis is
`changed_pixels=1288`. The runtime marker counts are submit begin/return 2/2,
fence status 1, present enter 1, queue-present enter 1, and queue-present
return 0. The single observed process was PID 652 and no crash signature was
present in the selected log.

### Act

This evidence unit is closed. The unresolved fence-completion boundary is
split into [FLR-0090](FLR-0090-fence-completion-boundary.md). No present
behavior change was made in this ticket.
