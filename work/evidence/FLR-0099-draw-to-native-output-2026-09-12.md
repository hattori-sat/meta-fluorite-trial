# FLR-0099 evidence manifest — draw to native output boundary

- Date: 2026-09-12 (Asia/Tokyo)
- Ticket: [FLR-0099](../tickets/FLR-0099-draw-to-native-output-boundary.md)
- Image role: fixed authoritative Mini PC image
- Evidence root: `$RECEIVER/evidence/flr0099-draw-to-native/`
- Raw QMP, video-frame, command, and serial files remain outside Git.

## Common input and process gates

- Source/image layer commit used by the fixed image: `054e3c549246d93d1d0ba16afdcd277d9c525433`.
- qemuboot SHA-256: `deb45510d9bc12a26f59f1c6871e3355f17d9a3c76aac918dbc3c4ca32afa2ee`.
- kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- rootfs SHA-256: `4fb772730e3d27fc0fa3ebe85ae0ab208938d04f7ae548106c148438ca4f6b7d`.
- Both cases used the fixed receiver, existing build/TMPDIR, one QEMU at a
  time, the existing short QMP run alias, and QMP-only captures.
- Both cases passed preflight, start, guest-ready, serial launch/extraction,
  QMP capture, six-frame QMP video, negotiated QMP quit, and residual checks.
- The guest process evidence shows one `flutter-auto` process and one
  compositor process in each case.
- No failed invocation occurred in this ticket. The earlier fixed-script-path
  typo is retained as FLR-0098 process evidence and was not repeated here.

## Runtime controls

Both cases enabled the existing scene/camera/resource, target, sync, pipeline,
neutral driver-lifecycle, present, fence, and effective-pipeline-input traces.
The fixture additionally enabled the existing pure-fixture/minimal-geometry
controls. The recovered production additionally enabled the existing
unlinked-fence-ready control. No new legacy directory, receiver, TMPDIR,
control, or marker was created.

## Fixture — positive native-pixel control

- QMP-before SHA-256: `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP-early SHA-256: `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- QMP-late SHA-256: `9add8308cff7d30f97f29b0f181edd21036ac732d08536a30247490172f9059e`.
- Selected serial extraction SHA-256:
  - early: `abd0e5b419e3fb73b4173279aff969f3383e922a896dc9460408050345d72cc2`
  - late: `45777d27d8a60bd5203ace3e0ba96d3052306ef56e3263c731a8f3c7ce2ce9a4`
- Native region `[300,80,620,360]`: early `0/223200`; late
  `41750/223200`, bounding box `[501,278,278,162]`.
- HUD region `[200,100,400,250]`: late `6240/100000`, bounding box
  `[200,113,400,237]`.
- Ordered markers reached `TARGET_DRAW2 swapchain=true extent=1280x800
  index_count=36`, `FLUORITE_VK_QUEUE_PRESENT_ENTER`,
  `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0`,
  `FLUORITE_VK_PRESENT_CALL_RETURN result=0`, and
  `FLUORITE_VK_PRESENT_DONE`.
- Six QMP video frames were captured. Their first-frame SHA-256 is
  `f79fc86cc62e07c6448619cdf33dcc1b6a72bf1faa0ce76f5b11f90d44ede69c`;
  the six frame hashes are retained in the external evidence directory.

## Recovered production — native-black comparison

- QMP-before SHA-256: `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- QMP-early SHA-256: `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- QMP-late SHA-256: `99b4c538b0ea413ec2855fed30cd8d6c9d72ed497033685df093879638e7fa9c`.
- Selected serial extraction SHA-256:
  - early: `6a6f2198e4f724e680c6fb9fa894eb6b717829a6851686937b159db8977f5786`
  - late: `2db2c0accedae0e983776c46b9b7e687a97243a9ceb4a6dc9570df672eb67f82`
- Native region `[300,80,620,360]`: early and late `0/223200`.
- HUD region `[200,100,400,250]`: late `984/100000`, bounding box
  `[200,113,29,66]`.
- Scene markers reported `scene=true`, `entities=1115`, `renderables=837`,
  `lights=13`, a valid camera/view, and valid sampled materials.
- `TARGET_DRAW2` included offscreen `1024x1024` targets and a final visible
  `swapchain=true extent=1280x800 index_count=3` target.
- The trace reached `FLUORITE_VK_QUEUE_PRESENT_ENTER index=0 wait=true`,
  but had no `FLUORITE_VK_QUEUE_PRESENT_RETURN`, no outer present-call return,
  and no present-done marker before bounded collection ended.
- All six production QMP video frames had the same SHA-256:
  `99b4c538b0ea413ec2855fed30cd8d6c9d72ed497033685df093879638e7fa9c`.

## Boundary classification

The first observed divergence is the return from `vkQueuePresentKHR`: the
positive fixture returns `result=0` and produces native pixels, while recovered
production reaches the call but does not return and remains HUD-only. This
distinguishes a present-call execution boundary from a simple absence of
draw-target setup. The blocked thread/wait owner is still UNKNOWN; FLR-0100
owns runtime backtrace and syscall-timing analysis.
