# FLR-0192 — defer ViewTarget creation until ECS initialization

- Status: Done
- Priority: High
- Owner: Mac persistent Devtool source + Mini authoritative build/runtime roles
- Created: 2026-09-15
- Predecessor: [FLR-0191](FLR-0191-isolate-native-readiness-3d-draw.md)
- Working log: `work/logs/2026-09-15-flr0192.md`

## Work unit

Repair the native ViewTarget bootstrap ordering exposed by FLR-0191. Keep the
existing non-blocking ECS initialization design where possible, but guarantee
that the ViewTarget creation request is delivered after the ViewTargetSystem
has been added and its handlers registered. This ticket owns the self-made
fixture path and does not yet claim that the production shaded scene is fixed.

## Problem

The 0256 runtime proves that the registration function emits
`CREATE_ENQUEUED`, while the first ViewTarget start handler later reports
`count=0` and the create handler is never observed. Static source inspection
shows that `RunOnceCheckAndInitializeECSystems()` posts system creation and
`ecs->initialize()` to the ECS strand and returns. `RouteMessage()` immediately
iterates the current `_systems` map. The initial create request can therefore be
sent while `_systems` is empty and is lost. `DeserializeDataAndSetupMessageChannels`
then waits until systems exist, so the later start request is delivered to an
empty ViewTarget list.

## Success criteria

- [x] Preserve FLR-0191 QMP/runtime evidence and use the same fixed
  build/TMPDIR/receiver/QEMU contract.
- [x] Compare and record two remedies: synchronously waiting for ECS init with
  strand deadlock analysis, and deferring the create route onto the ECS strand
  with an explicit completion boundary.
- [x] Implement the smallest current-API source change through the persistent
  Mac Devtool source workspace. Do not reuse stale 0236 APIs (`vInitSystems`,
  `vRouteMessage`) that are absent from the current ECSManager.
- [x] Generate the patch only through official Devtool update-recipe/finish,
  register it in `meta-fluorite-trial`, commit locally, bundle to Mini, and
  pass do_patch/do_compile/image gates.
- [x] Run one explicit 3.38.3 Example Demo fixture launch. Marker order must
  include the create handler and start handler with `count=1` or greater.
- [x] QMP-only capture classified the next downstream boundary: the fixed 3D
  region remained uniformly black after create/start/present succeeded.
- [x] Teardown left zero QEMU/runqemu/flutter-auto targets and no QMP
  socket.

## Facts

- FLR-0191 canonical runtime commit: `10c0b0cb311b80c6bf4df90f6f8805e2a7d14510`.
- 0256 QMP after explicit launch: 2D HUD changed 116 pixels; fixed 3D region
  changed 0/248000 pixels.
- 0256 marker order: registration enter → create enqueue → start enqueue →
  system init → start handler count=0 → C API return → C API drain. No create
  handler marker appeared.
- `ECSManager::RouteMessage()` synchronously sends to the current `_systems`
  map. `System::ProcessMessages()` swaps each system's queue and dispatches
  only handlers already registered.
- The current ECSManager exposes `initialize()`, `RouteMessage()`, `getStrand()`
  and `StartMainLoop()`; the stale 0236 `vInitSystems`/`vRouteMessage` API is
  not available and must not be reintroduced.

## Hypotheses

1. **Pre-initialization queue loss — leading.** The create request is routed
   before `_systems` contains ViewTargetSystem, so no queue receives it.
2. **Cross-thread queue ownership — secondary.** The create request reaches a
   different queue or is processed before handlers exist. The later start
   delivery to the same system makes this less likely, but a focused marker
   can falsify it.

## Plan / Do / Check / Act

### Plan

Inspect the current strand ownership and choose a bounded completion point for
the create request. Prefer a same-strand deferred route that preserves the
existing asynchronous initialization and avoids an unconditional wait on the
ECS API thread.

### Do

The selected same-strand ordering fix was implemented in the persistent Mac
Devtool source. The create and start messages are posted onto the ECS strand
after the initialization post, preserving FIFO ordering without synchronously
waiting on the ECS strand. The source commit is
`81820dfae2a7b81c270ba6b52d9dc3323dbf37e7`.

Official Devtool generation produced two ordered patches from the effective
baseline: 0257 (SHA-256
`f387ef6b165687a412a2237bc78f6ea333efbcf71186bb2da1d1603cbbda5b7a`) and
0258 (SHA-256
`8c6dad053b23899a6aa50a6c1be890a3faae00db38d0d4661fa52fa4d24f659d`).

### Check

- Mini `do_patch` passed at canonical commit `c848156`.
- The first Mini `do_compile` correctly reached the changed source but failed
  for a source type error: `ECSManager::GetInstance()` returns
  `ECSManager*`, while the call used `ecs.get()`. This is not a capacity
  failure. Mini had 109G free on `/mnt/yocto` at the time.
- The source was corrected to pass `ecs`; the official 0258 patch was
  generated without editing its body. The original full 0257 patch was
  restored as the first patch in the ordered recipe stack.
- The rebase helper was corrected to pass the declared baseline to Devtool's
  `--initial-rev`; its shell contract tests pass. This prevents a later
  source commit from being emitted as a one-line patch against the wrong
  Devtool starting point.
- Duplicate FLR-0192 Devtool/update-recipe processes left by timed-out tool
  calls were stopped by recorded PID. Fixed build/TMPDIR, caches, and evidence
  were retained because they are needed for reproducible iteration.
- Mini gates, runtime markers, QMP capture, and teardown were rerun after the
  corrected patch stack; the remaining black 3D result is owned by FLR-0193.

## Final check

- Mini clean `do_patch`, `do_compile`, and full `agl-ivi-image-flutter` build
  passed at receiver tip `0aeae3b5bbd9b344b0cffc58cbf1a830b7b7a7f0`.
- Rootfs `agl-ivi-image-flutter-qemux86-64.rootfs-20260915131734.ext4` SHA-256:
  `542bb21b68c2201cb806693c4f2c0bb68230ee7786700a8c2f4c8bbdd2619887`.
- QMP-only frame SHA-256:
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
  HUD `[200,100,400,250]` changed `116` pixels; fixed 3D
  `[300,250,620,400]` changed `0/248000`, luma `[0,0]`.
- Runtime proved `CREATE_REQUEST_ROUTED`, `CREATE_HANDLER_BEGIN/END`,
  `START_HANDLER_BEGIN count=1`, Vulkan queue submit/present result `0`, and
  Wayland commit. This closes the ECS ordering unit; it does not claim 3D
  pixel success.
- QMP teardown passed with zero residual targets and zero QMP socket.

### Act

Create handler passed but pixels remained black, so the post-create draw-content
boundary is split to FLR-0193.
