# FLR-0405 — capture ordinary-profile FEngine fault and present order

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Example Demo+GDB / shared app log / QMP and kernel evidence
- Branch: `feature-flr-0405-first-fault-present-order` (from local `dev-flr-0404-ordinary-profile` transition checkpoint)
- Depends on: [FLR-0404](FLR-0404-run-default-sequoia-on-0334.md); exact rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: bounded runtime discriminator; no product-source edit or build
- Working log: [FLR-0405 working log](../logs/2026-10-02-flr0405.md)

## Objective

On one unchanged patch-0334 image and ordinary Example Demo launch, determine
the event order between the second unmatched Vulkan present and the first
FEngine page fault/Oops. Capture the relevant live LWP/thread state and module
identity early enough that the faulting thread has not already disappeared.
This is a runtime-boundary ticket, not a product rendering pass or final root
cause claim.

## Facts, inferences, hypotheses, and UNKNOWN

### Facts

- FLR-0404 used the exact patch-0334 rootfs/kernel/qemuboot and no optional
  selector/material/light/camera/render/sync override. Its QMP frame showed a
  white field and one black polygon, with no HUD or recognizable Sequoia.
- The identity-bracketed app log recorded two present begins and one successful
  return. Guest kernel Oops at uptime 266.762166 s names TID 691
  `FEngine::loop`; the parent `flutter-auto` remained alive and TID 691 was
  absent from the later thread list.
- The Oops RIP maps to `libLLVM.so.18.1`, Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`, and `addr2line` reports
  `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`. This location alone
  does not establish causality.
- A GDB attach after the Oops exceeded its 12-second bound, returned rc=137,
  and produced no backtrace. The exact app resumed; no stopped thread or GDB
  process remained. `coredumpctl` reported no dump.
- FLR-0400/0401/0403 and older present tickets contain related incomplete
  present/Oops observations. They are comparison evidence, not proof that the
  same producer or root cause is involved.

### Inferences

- The next useful observation must capture thread identities/stacks before the
  faulting TID disappears, and align them with the app's present markers and
  kernel Oops timestamp in one run.
- Another material, lighting, camera, surface-order, or input change would
  confound this runtime-boundary discriminator and has lower information value
  until a healthy present baseline exists.
- GDB attachment can perturb timing. Any changed or prevented failure under
  the debugger must be reported as an observer effect, not a product fix.

### Hypotheses

1. **The FEngine fault removes work required by the pending present.** Support:
   timestamped GDB shows the faulting LWP executing render/submit work and its
   disappearance precedes a dependent present stall. Refute: present is already
   stalled in an independent WSI/synchronization wait before the fault.
2. **The present/synchronization stall precedes or is independent of the Oops.**
   Support: a live stack shows an incomplete wait before the Oops, or the Oops
   LWP is unrelated to the pending present. Refute: captured dependency state
   shows the faulting LWP owns the only producer for the pending present.
3. **The late GDB timeout was caused by attaching to the already-large thread
   set, not an unavailable debugger.** Support: early bounded attach completes
   with LWP IDs and selected stacks. Refute: the same attach stalls before
   thread enumeration while the app has few threads.

### UNKNOWN

- Whether the Oops precedes, follows, or causes the unmatched present.
- Which current LWP owns the pending present and whether it shares a dependency
  with TID 691.
- Whether the white/black-polygon screen is a scene, renderer, or Wayland
  composition result; FLR-0404's unhealthy present path prevents isolation.
- Whether the original Sequoia material/texture/light path is reached or
  sampled, and whether a supported viewpoint control exists.
- Whether a debugger changes or suppresses the fault.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | LWP stacks, mapped ELF Build-IDs, present begin/return, first kernel Oops, full QMP pixels |
| Where | Exact Mini patch-0334 image, ordinary Example Demo 3.32.5, guest/QMP framebuffer |
| When | One fresh boot; collect initial state, attach GDB as soon as the live app identity exists, stop at the first abnormal boundary |
| Who | Mini runtime operator, guest `agl-driver`, bounded GDB observer, QMP and kernel evidence capture |
| How | One image/profile; one QEMU; direct launch with allow-listed environment; shared timestamped app/GDB/observer log |

## Scope and controls

- Runtime-only. Do not modify Devtool source, recipe, patch stack, layer, image,
  cache, or build directory. Do not run BitBake or transfer a bundle.
- Before the one QEMU start, recheck canonical local repository, authoritative
  receiver tip/cleanliness, exact rootfs/kernel/qemuboot hashes, configured
  layer identity, no existing runtime owner, free ports, storage/memory, and a
  fresh run ID `flr0405-0001`. Use only the recorded fixed receiver and the
  exact 0334 artifact; do not touch the unrelated dirty FLR-0019 checkout.
- Use the existing QEMU runtime harness, one 6144-MiB instance, and ports
  10930–10932. No second QEMU and no copied rootfs/image on Mac.
- Launch the same ordinary Example Demo as `agl-driver`, with only
  `HOME`, `PATH`, `XDG_RUNTIME_DIR`, and `WAYLAND_DISPLAY`; do not set optional
  model-selection, material, light, camera, render, or synchronization flags.
- Preserve a full QMP still before debugger attachment. Record PID/UID/start
  identity immediately before and after every selected capture/observer action.
- Attach GDB once as early as possible after launch. First capture `info threads`
  with target IDs/LWPs and mapped modules/Build-IDs, then bounded relevant
  `FEngine::loop`/renderer backtraces. Use one 30-second hard bound; do not use
  an unbounded `thread apply all` on a late large thread set. Append GDB output
  to the same guest app log used for readiness and present observations.
- Capture the first Oops/present boundary and a full QMP frame before teardown.
  If present is still unhealthy, stop; no pointer/hover/click trial or blind
  five-minute wait. Do not infer root cause from a symbol name alone.
- Keep raw PPM/log evidence on Mini and transfer only small review PNG/MP4 files
  after hashing. Record every failed as well as successful command.
- If the first boundary is localized enough to justify a source change, create
  a separate patch ticket. Do not add that fix to this observation ticket.

## Success criteria — bounded diagnostic completion, not product acceptance

1. The exact image/receiver/process/port/run-ID gates pass before start, with
   image hashes unchanged.
2. One ordinary Example Demo launches with the recorded app identity and no
   diagnostic override; the debugger/observer uses the shared run-scoped log.
3. Full-screen QMP captures are identity-bracketed. GDB records thread/LWP IDs,
   relevant stacks, and current ELF mapping/Build-ID, or reports the exact
   bounded failure and observer impact.
4. Present markers and kernel fault data are timestamped in the same run so the
   event order is classified as supported, refuted, or UNKNOWN. No symbol-only
   root cause claim.
5. Exact app/QMP/QEMU cleanup, free reserved ports, unchanged artifacts, and
   all command results/evidence hashes are recorded.

The user-visible Sequoia+HUD goal remains open regardless of this ticket's
diagnostic result.

## Plan / Do / Check / Act

### Plan

- Reuse exact 0334 and the direct ordinary launch that FLR-0404 established.
- Move bounded GDB observation to immediately after app identity capture, not
  after the pending present/Oops. Preserve QMP first and share one log sink.
- Change no scene, material, texture, light, camera, surface order, input, or
  build variable. Stop at the first unhealthy boundary.

### Do

- Not started. FLR-0404 postflight is clear; its existing run was shut down and
  its evidence remains under `$BUILD_EVIDENCE/flr0404-0001/qemu/`.
- Create exactly one fresh FLR-0405 run directory only after the immediate
  preflight gates pass. Record exact command and output hashes here.

### Check

- Awaiting the one bounded instrumented runtime. No FLR-0405 QEMU, app, GDB, or
  build has started. Product rendering status remains NOT MET/UNKNOWN.

### Act

- If the Oops/pending-present ordering and LWP dependency are evidenced, open a
  separate smallest-fix ticket for that boundary. If GDB perturbs or misses the
  failure, keep causality UNKNOWN and use the next discriminator with evidence
  from FLR-0400/0401/0403/0404; do not repeat the same late-attach command.

## Impact

- **Build-time / packaging:** none planned.
- **Runtime:** one fresh 6144-MiB QEMU and one ordinary guest app; a bounded
  debugger attach can perturb timing. No parallel QEMU/build.
- **Integration risk:** no product source/image changes. Exact identity checks,
  QMP-only captures, and scoped teardown limit interference with other work.
