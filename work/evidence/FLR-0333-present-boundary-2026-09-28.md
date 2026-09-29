# FLR-0333 — QMP and present-boundary evidence

- Date: 2026-09-28
- Run: `$EVIDENCE_ROOT/flr0333-0001/qemu`
- Ticket: [FLR-0333](../tickets/FLR-0333-trace-vulkan-present-return-page-fault.md)
- Source workspace revision at inspection: `0db33a2`; exact source revision
  used to produce this older retained image is UNKNOWN.
- Rootfs SHA-256:
  `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- QEMU boot config SHA-256:
  `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- QEMU memory: 6144 MiB; runqemu harness preflight and guest readiness passed.
- The production launch was a diagnostic profile, not an unmodified release
  run: it enabled the magenta unlit PaintColor override, two-model bound,
  wide camera, and explicit native Wayland commit.

## Full-frame QMP evidence

- Before-production baseline:
  `qmp-0333-before-production.ppm`,
  SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Production full frame, 1280×800:
  `qmp-0333-production-full.ppm`,
  SHA-256 `e468e624acf85b21ed086cadc222008d5fc967f153269f21006c396e6350e5e8`.
- Visual result: HUD telemetry and Scenes button visible; vehicle area black.
- Main region `(240,0,1040,800)`: 2990 changed pixels, all confined to the
  Scenes button bounding box `(1157,24,99,32)`.
- Historical vehicle ROI `(440,220,400,360)`: 0/144000 changed pixels,
  zero chromatic pixels, full black.
- HUD ROI `(0,0,240,220)`: 6298 changed pixels and 2166 chromatic pixels.
- Eight-frame QMP sequence:
  `qmp-0333-production-video/frame-00000.ppm` through `frame-00007.ppm`.
  Every frame SHA-256 is
  `e468e624acf85b21ed086cadc222008d5fc967f153269f21006c396e6350e5e8`;
  unique frames: 1. HUD appearance is therefore not evidence of ongoing
  screen updates in this run.

## Runtime and debugger evidence

- The GLB asset was loaded and two model instances were added with 12 and 22
  renderables.
- The magenta unlit PaintColor replacement marker fired; no vehicle pixels
  appeared in the QMP vehicle ROI.
- Queue submit, finished-signal acquisition, present-call begin, and
  queue-present begin were logged. No queue-present return/result followed.
- The next frame still reached render-return/draw-end; a subsequent
  begin-frame/draw-submit had no render-return in the bounded log.
- Guest journal recorded a user-mode page fault in an FEngine worker at
  monotonic `598.075730` seconds. Exact module/symbol and causal relation to
  the earlier present call remain UNKNOWN.
- GDB was available. A post-fault attach showed the faulting worker absent;
  surviving FEngine/llvmpipe threads were waiting in Mesa
  `__pthread_cond_wait` / `cnd_wait`. No matching coredump was listed.
- Filtered runtime output SHA-256:
  `cddc92f7e95e02bf22503467d8738285bd56753cd234a1b0da03c208aabc4a57`.
- GDB attach raw-output SHA-256:
  `031f108c060a22dad58924dc7e2dfd3747849dd5f95a836636bd6e00ca585d6f`.
- Filtered GDB stack-slice SHA-256:
  `95588ec9385d58ced438290f3a3f8482297bb129327e9457f494aa6ee7302331`.

## Control and cleanup

- The pure native fixture rendered a blue front face and returned from
  `vkQueuePresentKHR` with `result=0`; source inspection shows it is a cube
  viewed directly from `(0,0,5)`, so the square image does not prove depth.
- Fixture full-frame SHA-256:
  `4694c145af2174225504a48f0c6d89c901d6bb45df1cb8b6d76c48b73cfd6edd`;
  fixture ROI had 119716/144000 chromatic pixels. This is fixture-only proof.
- Exact guest process check after app stop: `flutter_processes=0`.
- QMP teardown: `qmp=PASS capabilities=negotiated quit=accepted`;
  `cleanup=PASS residual_targets=0 residual_qmp=0`.
- No source patch, recipe edit, build, or image rebuild occurred.

## Verdict

The supplied red `HeadLights_Emission` image is a static GLB texture asset,
not a QMP runtime frame. This run does not prove a broken texture path or a
lighting defect: even an unlit magenta PaintColor probe yielded no vehicle
pixels. The strongest current boundary is the production FEngine/llvmpipe
render/present path; the faulting module and exact causal chain remain
UNKNOWN. [FLR-0334](../tickets/FLR-0334-symbolize-production-fengine-render-fault.md)
owns the next diagnostic unit.
