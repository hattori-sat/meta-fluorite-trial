# FLR-0408 — replay known-positive Sequoia model-only profile on exact 0334

- Status: Waiting — no live QMP frame before SIGSEGV; Gate-A pixels UNKNOWN
- Priority: High
- Created: 2026-10-03
- Owner: Mini QEMU / UID-1001 Example Demo / shared app log / QMP and kernel evidence
- Branch: `feature-flr-0408-replay-sequoia-0334`
- Depends on: [FLR-0405](FLR-0405-capture-first-fengine-fault-present-order.md); patch-0334 rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [FLR-0408 bounded model-only replay](../../docs/superpowers/plans/2026-10-03-flr0408-known-positive-model-profile.md)
- Working log: [FLR-0408 working log](../logs/2026-10-03-flr0408.md)

## Objective and boundary

Replay the model-only conditions that produced visible production Sequoia
pixels in FLR-0049, now on the immutable 0334 image. Change only the guest
launch profile; do not edit source, patch, image, camera, lighting, material,
or the capture/observer implementation during this runtime attempt.

This is a single bounded Gate-A discriminator. Even if Sequoia pixels appear,
it does not establish original lighting, simultaneous Flutter HUD composition,
viewpoint interaction, repaint/input stability, five-minute present health, or
two-boot reproducibility. Those remain separate gates toward the user's full
product objective.

## Facts

- FLR-0049 iteration 10 used Sequoia model selection with limit 2; the readback
  probe was unset, and environment, skybox, indirect light, shapes, and lights
  were skipped. It reached `MODEL_STAGE_SCENE_ADD_DONE`, reported 25 Scene
  entities/14 renderables and successful present markers, and full-screen QMP
  images visibly contained production vehicle pixels and red lamps. The native
  surface was above the Flutter parent, so that run did not show the HUD in the
  same frame. Its image/runtime is historical, not the current 0334 candidate.
  See [FLR-0049](FLR-0049-production-model-render-boundary.md) and [its working
  log](../logs/2026-09-08-flr0049.md).
- FLR-0404 and FLR-0405-0003 used the exact 0334 artifacts with ordinary
  Example Demo launch and no optional selectors. Their identity-bound QMP
  frames showed a white field and black polygon, without recognizable Sequoia
  or HUD. FLR-0405-0003 also recorded an Oops before a later unhealthy present
  gate, with call-level event ordering UNKNOWN.
- Current expected artifact hashes, independently checked before this ticket:
  rootfs `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`,
  kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  qemuboot `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`.
  They must be rehashed immediately before QEMU startup.
- The 0408 commands use the new run-local
  `/run/user/1001/fluorite-0408-0001.*` namespace. Existing `FLR0026_*`
  controls and emitted markers are reused only to reproduce FLR-0049; no new
  legacy path, marker, or control is introduced.
- Local checkpoint `3e8727d` committed the ticket, plan, six guest commands,
  focused test, TASKS entry, and initial working log with integration-role
  metadata; it was not pushed.
- The later guest-SSH launch succeeded on the same exact image:
  `FLUORITE0408_LAUNCH=PASS pid=765 uid=1001 start=239895`, with the six
  documented FLR-0049 controls applied and readback unset. A fresh SSH identity
  check initially passed at `2026-10-02T22:12:27+0000`.
- The original scene-gate returned
  `status=LOG_INVALID ... samples=1` at `2026-10-02T22:13:40+0000` because it
  rejected the growing log before searching for the exact secondary marker.
  A later bounded full-log snapshot at `2026-10-02T22:15:38+0000` found
  `secondary_scene_add=0`, with PID/UID/start unchanged, app log 4,495,376
  bytes, present begin/return/success `76/75/75`, and kernel faults `0`
  against baseline `0`. This establishes marker absence in that snapshot, not
  a black or failed visual result.
- The bounded export completed at 925,232 bytes, SHA-256
  `80d4ba92f5591a5455d74867f70f4ff1c41c7dcfbe365288e6d67f0aec887a7e`;
  it retained the configured head/tail and explicit truncation metadata.
- A read-only host recheck at `2026-10-02T22:29:44Z` found the same sole
  runqemu/QEMU pair and QMP socket. Rootfs, kernel, and qemuboot hashes still
  match the exact 0334 values above. The active Mini source checkout is clean
  at `6e9878ba7993acf20c33ba68d9b25db9b5df5d95`; its pixel-capture helper
  matches the Mac SHA-256
  `df826ef28df367d4de42225004f74ce3d2f016a8c2aea42275a8b13b5b233ef1`.
- The supplemental pre-capture snapshot at `2026-10-02T22:46:07+0000` failed
  its identity predicate: saved PID 765 was absent and UID-1001
  `flutter-auto` count was zero. The same snapshot found app-log size
  32,080,223 bytes, secondary scene-add `0`, present begin/return/success
  `663/662/662`, and kernel faults `0` against baseline `0`. No QMP capture was
  started; an after-exit/stale framebuffer would not meet the live-identity
  requirement.
- `coredumpctl list` (the guest version does not accept `--boot`) records PID
  765, UID 1001, signal 11/SIGSEGV at `2026-10-02T22:35:52Z`, executable
  `/usr/bin/flutter-auto`, and a present 76.0-MiB compressed core. A bounded
  GDB 14.2 backtrace identifies signal thread LWP 812 and ten return addresses,
  but every application frame is `???`; GDB warns that deleted
  `/memfd:mesa-shared`, `/tmp/filament-ashmem-765-*`, and
  `/memfd:wayland-cursor` mappings cannot be opened.
- The crashed executable is a stripped PIE, SHA-256
  `e2842d3faa5d1c693f4497de4a4fb32e2fdd30d4772e369281a9d0c336564e3c`,
  Build-ID `529c5d321d81192f82f146d9d23736722aec2208`. No `.symtab`, `.debug_*`,
  `.gnu_debuglink`, or matching `/usr/lib/debug/.build-id/...debug` file was
  found in the guest. `addr2line`, `llvm-addr2line`, and `llvm-symbolizer` are
  installed. The core's main-executable mapping and identity are now
  correlated; symbolization still requires an exact matching unstripped file.
- The preserved core is `/mnt/yocto/evidence/flr0408-0001/qemu/core-pid765.elf.zst`
  on the Mini, not in Git or on the Mac. Its verified uncompressed size is
  886,116,352 bytes; compressed size is 85,823,952 bytes; SHA-256 is
  `9961abd4e8adc9fb69298e43772fd7674e486df0a85617fe8ff8f18a865548b0`.
  `zstd -t` passed.
- The bounded saved GDB transcript is
  `/mnt/yocto/evidence/flr0408-0001/qemu/gdb-core-pid765-mapped.out`, 98,986
  bytes, SHA-256
  `5fa2e889fbe4101db4217e0a1a052c83575aa9ed3ac190067be1afead1b626a7`.
  It records LWP 812 with `si_code=1` (`SEGV_MAPERR`),
  `si_addr=RAX=0x7f0a79cbc1c4`, and RIP `0x56032183498d`. The instruction is
  `mov (%rax),%rax`, an 8-byte indirect read. RIP lies in the mapped
  `/usr/bin/flutter-auto` range beginning at `0x560320ae3000`, offset
  `0xd5198d`; the fault address does not appear in the saved process mappings.
  The crashing thread's caller frames remain `???` because the executable is
  stripped. GDB's thread, register, signal, instruction, shared-library, and
  mapping sections are present, but its stderr included `/dev/stdin: Invalid
  argument` and a host-encoding warning; treat this as useful core evidence,
  not a clean/reusable debugger invocation.
- The live-capture window was missed: the 22:15:38Z snapshot still had PID 765
  alive and present counts `76/75/75`, but the next manual pre-capture check
  was delayed until 22:46:07Z, after the 22:35:52Z SIGSEGV. No QMP still or
  video was taken. This is a missed observation opportunity, not evidence of
  a black or visible frame.
- After evidence preservation, the existing Mini QMP helper negotiated and
  accepted `quit`; it reported `cleanup=PASS residual_targets=0 residual_qmp=0`.
  Ports 10930–10932 were free afterward, and the rootfs/kernel/qemuboot hashes
  still matched the exact 0334 values above.

## Inferences

- On one immutable image, this replay compares the ordinary launch with the
  historical explicit model selection and environment/skybox/indirect-light/
  shape/light skips. It does not isolate which of those several skip controls
  is necessary.
- Scene insertion and process liveness are intermediate signals only. The
  pixel verdict requires recognizable production Sequoia in a live,
  identity-bracketed full-screen QMP capture.
- The observed runtime fault is a user-space SIGSEGV, not a kernel Oops or OOM
  in the available bounded evidence. Present begin/return/success counters
  each rose by 587 between the 22:15:38 and 22:46:07 snapshots; the unmatched
  begin/return difference remained exactly one. The last observed successful
  present was at 22:35:50.640 UTC, about 1.4 seconds before the core timestamp.
  This timing is correlation only and does not identify the faulting operation
  or establish a present-caused crash.
- The core identifies the immediate fault as an unmapped 8-byte indirect read
  in the executable, but the stripped binary and unresolved caller frames do
  not identify the pointer's owner or where it came from.

## Hypotheses

1. **The historical model-only profile produces Sequoia pixels on 0334.**
   Support: exact profile, `SCENE_ADD_DONE`, identifiable vehicle geometry or
   texture/red-lamp pixels in QMP, and a live matching app identity. Refute:
   scene insertion is reached but QMP contains no recognizable car.
2. **The 0334 renderer/presentation path remains unhealthy with this profile.**
   Support: scene-add completes but QMP stays white/black/blank, or an Oops or
   present fault precedes usable pixels. Refute: visible production geometry
   and progressing successful presents during the bounded capture.
3. **The historical profile is not reproduced in the current runtime.**
   Support: launch, process identity, asset selection, or scene-add gate fails
   before the expected marker. This makes the visual result UNKNOWN, not proof
   that the renderer cannot draw Sequoia.
4. **The bad pointer originates in the faulting code or in an upstream caller.**
   The core locates the dereference but does not distinguish those paths;
   matching symbols and caller resolution are required.

## UNKNOWN

- Whether the historical model-only profile is sufficient to produce visible
  Sequoia pixels on the current 0334 artifact set.
- Which individual model/environment/light/shape control mattered in FLR-0049;
  this ticket deliberately does not split those controls.
- Whether original lighting/material behavior, Flutter HUD composition,
  interactive camera/depth, pointer/repaint stability, five-minute health, or
  two independent boots pass.
- Whether any current Oops/present symptom shares a cause with the older
  FLR-0049 renderer observations.
- Whether the SIGSEGV originated in Flutter, embedded Filament, Mesa/LLVM,
  another library, or damaged control flow; core mappings and the executable
  Build-ID are recorded, but the exact unstripped symbols and caller functions
  are not.
- Whether the crash has any causal relation to the one unmatched present or to
  Sequoia scene construction.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | production Sequoia scene-add, full-screen QMP pixels, present counts, first kernel fault |
| Where | Mini fixed qemux86-64 artifacts, QEMU guest UID 1001, QMP framebuffer |
| When | one fresh QEMU boot; capture after the secondary Sequoia scene-add marker |
| Who | runtime operator, Example Demo/Filament scene owner, QEMU evidence owner |

## Success criteria — Gate-A experiment only

1. Immediately before startup, confirm no conflicting QEMU/runqemu/Flutter/
   BitBake owner, ports 10930–10932 free, evidence directory unused, active
   source/build/receiver roles unchanged, and all three 0334 hashes exact.
2. Start exactly one QEMU with the fixed runqemu harness and 6144 MiB. Launch
   exactly one `flutter-auto` as UID 1001 with `env -i` and only required
   HOME/PATH/XDG/Wayland settings plus the six historical controls:
   `MODEL_MATCH=sequoia`, `MODEL_LIMIT=2`, `SKIP_SKYBOX=1`,
   `SKIP_INDIRECT_LIGHT=1`, `SKIP_SHAPES=1`, `SKIP_LIGHTS=1`, and
   `MODEL_STAGE_TRACE=1`. `NATIVE_READBACK_PROBE` stays unset. Detach the
   process using the existing `nohup` plus `/dev/null` stdin contract so it
   survives the one-shot SSH session. No camera, material, global
   environment-skip, input, or sync override is permitted.
3. Require the same live PID/UID/start token around a full-screen QMP still
   immediately after `MODEL_STAGE_SCENE_ADD_DONE` and eight QMP frames 0.5 s
   apart. Preserve raw PPMs, command/serial-setup/app/kernel evidence on the Mini
   before teardown; record their hashes in the evidence manifest.
4. Report separate `SCENE_ADD`, `GATE_A_PIXELS`, `PRESENT_HEALTH`, and
   `RUNTIME_FAULT` verdicts. Pixel PASS requires recognizable production
   Sequoia, not a diagnostic shape or black polygon. Present health here is a
   short-window observation, not the five-minute gate.
5. Stop only the recorded app identity, QMP-quit only this QEMU, prove exact
   process/socket/port cleanup and unchanged deploy hashes, and preserve
   failures and UNKNOWNs in the ticket, working log, and evidence manifest.

## Visual evidence

- Required artifact: full-screen QMP PPM still after secondary Sequoia
  `SCENE_ADD_DONE` and an eight-frame QMP sequence, bracketed by the same
  guest PID/UID/start token. Record exact hashes, resolution, visible content,
  and evidence-manifest link here after capture.
- Current state: no QMP image was captured. The committed marker gate failed
  `LOG_INVALID` at its oversized-log check; a later full-log summary found no
  secondary marker. The fresh manual pre-capture identity check then found PID
  765 absent and no UID-1001 `flutter-auto`, so the diagnostic branch correctly
  did not capture a stale frame. The prior live snapshot at 22:15:38Z was not
  followed promptly by QMP capture; the app crashed at 22:35:52Z before the
  22:46:07Z pre-capture check. Gate-A pixels remain UNKNOWN; neither a black
  result nor Sequoia visibility is established by this run. See the
  [evidence manifest](../evidence/FLR-0408-0001.md).

## Plan / Do / Check / Act

### Plan

- Reuse the exact 0334 runtime image without bundle transfer or build.
- Replay FLR-0049 iteration 10 as one combined model-only control; change no
  source, artifact, camera, material, or observer variable.
- Bracket full-screen QMP evidence with guest PID/UID/start identity and keep
  scene-add, visual pixels, present health, and kernel-fault verdicts separate.
- Stop at the first abnormal boundary; do not extend a short capture into a
  stability claim.

### Do

- The six one-line commands are in `work/commands/FLR-0408-guest-*.cmd`; their
  paths are confined to the 0408 run namespace.
- `python3 -B tests/test_flr0408_profile.py` passed 4/4.
- Initial read-only baseline branch point was `ffafe4394a73`; local records
  were committed as `3e8727d` and `29dd087`, without push.
- One 6144-MiB QEMU is currently running as the only target: harness PID
  `3089625`, QEMU child PID `3089652`, QMP socket present; guest SSH readiness
  passed. No build or image change occurred.
- Serial-exec preflight failed `echo-off-response-unexpected` before the guest
  command was dispatched. Its saved setup transcript is 197 bytes: one setup
  marker with status 0 and one exact final prompt; command output is empty.
  Source inspection shows the helper accepts a 50 ms socket timeout as a
  successful quiet window and rejects any non-timeout read. Since the saved
  transcript ends exactly at the prompt with no extra bytes, the failure is
  consistent with EOF at the serial setup boundary; why that endpoint closed
  remains UNKNOWN. No app was launched.
- Read-only guest SSH `id -u` returned 0, and the same committed guest
  preflight returned `FLUORITE0408_PREFLIGHT=PASS`. Use this route for remaining
  commands, streaming their contents into guest `/bin/sh -s` and saving output
  on the Mini.
- A `pgrep -x qemu-system-x86_64` check returned zero because Linux's `comm`
  truncates the longer executable name; the harness PID file and `ps` confirm
  the live runqemu/QEMU pair. Use recorded PID/argv evidence, not that exact
  comm match.
- Before app launch, review found three evidence-gate gaps: scene readiness
  accepted any model's generic scene-add marker, identity reported but did not
  reject a new kernel fault, and export stopped without evidence if the app log
  exceeded its cap. The local commands now require `sequoia_ngp.glb` in
  `mode=secondary`, reject fault-count increases, preserve a bounded log
  head/tail on overflow, and use the historical detached
  `/usr/bin/nohup ... </dev/null` contract. Focused verification passed 6/6;
  the changes were locally committed as `58d8d3e` without push. A later guest-
  SSH launch did succeed; its result and the first observer failure are
  recorded under Facts above.
- After the `LOG_INVALID` result, a candidate marker-first/overflow-tolerant
  change to the guest gate and identity check passed the focused suite 6/6.
  Sol reviewed the ticket's explicit ban on observer changes during a running
  attempt and advised not to deploy it. Those local candidate command/test
  edits were restored to the committed versions; no observer change was sent
  to the Mini or used for this runtime. The next capture will use manual
  read-only identity/fault/present snapshots and the unchanged QMP helper.
- The latest read-only Mini preflight confirms one configured
  `meta-fluorite-trial` layer, qemux86-64, fixed build TMPDIR, active source
  clean at `6e9878ba7993`, and separate fixed receiver clean at `969d93c331be`.
  The fixed inbox bundle SHA-256 is
  `28d6a01916504fb665269b6b3155e3ebbc5b0af35b82a80674a54b3faa4af62e` and
  advertises the active source commit. No bundle handoff or build is needed.
- Recomputed rootfs/kernel/qemuboot hashes exactly match the expected 0334
  values above. QEMU harness and pixel-capture helper hashes match Mac and
  Mini; the Mini capture helper exposes `capture` and `video`. The qemuboot
  profile is qemux86-64/ext4 and includes the USB-tablet device.
- Read-only runtime preflight found no QEMU/runqemu/flutter-auto/BitBake
  owners, no listener on 10930–10932, no existing 0408 evidence path, about
  28 GB available RAM, and about 64 GB free under `/mnt/yocto` (92% used).
- One helper lookup first targeted the configured layer subdirectory rather
  than the containing Git project root; `sha256sum` stopped on the missing
  sibling path before any other command ran. `git rev-parse --show-toplevel`
  resolved the existing repository root, and the corrected read-only helper
  hash/CLI check passed. No Mini state changed.

### Check

- The candidate observer correction passed 6/6 focused tests before it was
  restored; it was not deployed or used. On the unchanged committed commands,
  `python3 -B tests/test_flr0408_profile.py -v` passes 6/6, and canonical,
  privacy, file-size (2,098 files), shell syntax (59 files), runtime
  checkpoint (`active=1`), and `git diff --check` all pass.
- Final closeout reran canonical, privacy, file-size, shell, focused tests
  (6/6), runtime checkpoint (`active=1`), and `git diff --check`; all pass.
  `make check-markdown` fails only on the same 11 historical missing targets
  in FLR-0338/0339/0340/0391/0395; no new FLR-0408 link fails.
- The local closeout change set is limited to TASKS, this ticket, its plan and
  working log, this evidence manifest, and the bounded GDB command source.
- Runtime is no longer pre-app: guest-SSH launch and the first fresh identity
  passed. The old scene-gate `LOG_INVALID` is an observer failure. The
  independent full-log snapshot found no secondary Sequoia scene-add marker,
  and later the app terminated with SIGSEGV after hundreds of successful
  present returns. Kernel faults remained zero. The pre-capture identity gate
  failed, so no visual result or Gate-A/product acceptance is claimed.
- Core evidence now confirms a user-space unmapped-pointer dereference in the
  `flutter-auto` executable; caller symbols and pointer origin remain UNKNOWN.
  The compressed core and GDB output are preserved on the Mini. Exact 0334
  artifact hashes, QMP shutdown, process/socket cleanup, and forwarded ports
  were rechecked successfully. A delayed pre-capture check missed the live
  window; no pixels were obtained.

### Act

- Preserve the committed observer/gate commands. The manual pre-snapshot
  failed because PID 765 was already absent; no diagnostic frame was taken.
  The 22:15:38Z live snapshot was not followed promptly, and the process
  SIGSEGV'd at 22:35:52Z before the 22:46:07Z pre-capture check. The core and
  GDB output are now preserved; only this QEMU was QMP-quit, with no residual
  target, QMP socket, or forwarded port. Classify `RUNTIME_FAULT=YES`,
  `SCENE_ADD=UNKNOWN`, `PRESENT_HEALTH=FAIL at process termination`, and
  `GATE_A_PIXELS=UNKNOWN`.
- FLR-0409 owns the bounded read-only search for the exact Build-ID symbols
  and caller chain. This replay is Waiting because its live visual gate was
  missed and cannot be recovered from the preserved core; do not call the
  missing frame black or visible. Do not attribute pointer origin to
  Flutter/Filament/Mesa or causality to present/scene loading without symbols
  and further evidence. The user goal is not complete.
- Do not claim original lighting, HUD composition, interaction/repaint
  stability, five-minute health, or two-boot acceptance from this ticket.
