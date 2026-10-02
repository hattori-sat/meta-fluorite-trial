# FLR-0404 — ordinary-profile Sequoia runtime on exact 0334 image

## Goal

On the already-built patch-0334 image, run the installed Example Demo with a
clean ordinary runtime environment: no optional model-selection, material,
light, camera, or render-diagnostic overrides. Determine whether the real
Sequoia appears with the CPU/GPU/FPS HUD, then—only after a live positive
frame—exercise existing input/UI behavior and measure stable present for five
minutes. This is a runtime-only discriminator; it does not complete the
required independent second boot.

## Evidence basis

- FLR-0049 iterations 8/10/23 show recognizable production Sequoia pixels and
  red lamps on historical QMP frames, but the native-only/model-only profile
  hid the Flutter HUD and used special selection/environment conditions. It is
  a positive reference, not current-image acceptance.
- FLR-0394 shows a self-created LIT fixture and HUD together on a different
  rootfs; it is not production Sequoia.
- FLR-0403 reused the exact 0334 image with LIT-material and SUN diagnostic
  overrides. Its QMP frame showed HUD/Scenes over an all-black Sequoia ROI;
  an FEngine Oops was logged, but the capture was not identity-bracketed and
  no GDB LWP/ELF mapping was collected.
- Static patch review: the model selection/limit behavior is optional; without
  those controls the ordinary load plan does not select a reduced Sequoia-only
  subset. The 0332 material override and 0305 extra SUN are opt-in. Therefore
  launching with an allow-listed clean environment exercises the default
  production scene/material/light profile rather than carrying forward the
  0403 diagnostic setup.
- This ordinary profile loads the default model set, which can increase memory
  use. A historical run OOMed after repeated model/scene insertion; that is a
  risk signal, not proof the exact 0334 image will fail. Capture live model
  count, Sequoia asset/scene insertion, effective camera, bounded memory trend,
  kernel OOM state, and the whole screen. A fixed black ROI alone cannot
  distinguish a failed draw from a car outside that rectangle.
- The current image contains diagnostics and conditional patches. An unset
  override is necessary but not sufficient to prove original material,
  texture, and lighting behavior: require a recognizable full vehicle with
  visible texture/shading evidence plus any available effective material/asset
  markers. Otherwise keep the specific quality claim UNKNOWN.
- FLR-0141 records that the historical Dart/native interface did not implement
  the post-launch camera-update methods. Do not assume a drag gesture changes
  camera or claim a viewpoint test without measured before/after evidence.

## Competing hypotheses

1. **The 0403 diagnostic profile is the differentiator.** With the same image,
   removing all optional material/light/model/render overrides yields a
   recognizable, textured Sequoia and HUD with normal present progress.
2. **The production scene/render/present path is independently unhealthy.**
   The ordinary profile still shows a live HUD but no recognizable Sequoia,
   or reproduces an Oops/OOM/present stop. A fault remains a boundary finding,
   not a root cause, until tied to a concrete process/thread/API boundary.
3. **The ordinary full model load causes resource pressure.** Support requires
   bounded guest memory/process evidence and OOM or allocation failure; a
   prior OOM after many repeated selections is not enough to attribute this
   run.

## Selected approach and alternatives

- **Selected:** one exact-image ordinary Example Demo run with a minimal
  allow-listed session environment. This is the only direct comparison that
  can answer whether the unmodified production material/lighting path works.
- **Not selected:** carry forward the diagnostic LIT/SUN profile. It repeats
  FLR-0403 and cannot establish the user's target.
- **Not selected:** repeat the FLR-0049 Sequoia-only/native-above-parent
  profile. It can make the vehicle visible but hides the HUD and is not a
  same-frame result.
- **Trade-off:** default loading may retain more models and increase resource
  use. Keep the established 6144-MiB QEMU profile fixed, observe memory and
  OOM evidence, and stop at the first unhealthy boundary. Do not hide a real
  product resource problem by silently limiting the model set.

## Constraints

- Before every mutation, confirm canonical checkout, exact receiver/image
  identity, no active owner, free ports, and one fresh run ID. Use only
  `flr0404-0001`; do not retry it.
- Reuse the established Mini runqemu/QMP profile and one QEMU only. No parallel
  BitBake/build, second QEMU, image copy to Mac, cache deletion, cleanup task,
  Devtool/source edit, or image rebuild.
- Keep the exact 0334 rootfs/kernel/qemuboot hashes from FLR-0403. No change to
  camera, material, texture, lighting, model list, Flutter behavior, or image.
- Launch Example Demo 3.32.5 as guest role `agl-driver` (UID 1001), using only
  the session values required for `XDG_RUNTIME_DIR` and `WAYLAND_DISPLAY`,
  executable `PATH`, and the account's home. Do not export optional diagnostic
  controls or dump a broad environment containing unrelated data.
- Record app PID/UID/start identity immediately before and after each QMP still
  or interaction batch. Capture the full QMP frame before debugger activity.
  Never treat a post-exit frame as a live rendering verdict.
- Keep one run-scoped evidence directory. Raw QMP PPM series and full logs stay
  on Mini; retain bounded serial excerpts and transfer only the selected
  full-frame PNG and small MP4 review artifact to the workspace after hashing.
- If the real vehicle is visible, test pointer motion/hover, a normal UI
  update/click, and any existing camera/view control discoverable in the live
  UI. Do not invent coordinates from another frame or use a camera override.
  If there is no supported camera control, record UNKNOWN and split that API
  work into a new ticket.
- Only after a live, attributable Sequoia+HUD frame is established, continue
  the same run through the interaction sequence and 300 seconds of advancing
  present. No input suppression, repaint disabling, diagnostic cube, constant
  material, fake sync, or CPU SHM image is allowed.
- This is first-boot evidence only. The required independent second boot is a
  later ticket against the same final candidate image.

## Execution plan

1. Read the immediate FLR-0403 manifest/log, this canonical workspace guard,
   QEMU harness contract, and the exact saved 0334 artifact identities. Do not
   reread the whole archive.
2. On Mini, run read-only preflight: receiver/head/worktree, exact image hashes,
   BitBake/QEMU/Flutter/GDB owners, reserved ports, free memory/storage,
   evidence-ID absence, installed Example Demo, QMP video encoder availability,
   and the single fixed 6144-MiB profile. If any status is ambiguous, stop.
3. Start exactly one QEMU. Confirm QEMU PID/child, guest readiness, and tablet
   input. Manually launch Example Demo from the allow-listed environment and
   retain only one run-scoped guest log.
4. At the first app readiness and again at the first candidate frame, record
   PID/UID/start token, model/scene counts, Sequoia asset/add markers, effective
   camera, present counters, bounded memory, and kernel/OOM state. Capture a
   full QMP still and a short full-frame QMP video; verify the app identity
   immediately before/after. Analyze the whole frame plus HUD/Scenes and
   locate the vehicle dynamically; do not reject it because an old fixed ROI
   is black. Confirm visible original texture/shading and match the loaded
   asset identity.
5. If Gate A/B are visibly positive, use current-frame UI coordinates for
   hover/click and any established view control. Capture before/after full
   frames and a short MP4; verify HUD/vehicle do not white out, disappear, or
   become black. Sample present begin/return counters and bounded kernel/OOM
   state at start and after 300 seconds of normal operation.
6. Stop only the exact app identity if still running, QMP-quit only the owned
   QEMU, and verify zero new residuals/listeners plus unchanged image hashes.
7. Record facts, inferences, hypotheses, UNKNOWN, all failures, screenshot and
   video hashes, filtered logs, and next one-variable action. Do not call a
   partial diagnostic Done or the overall product target complete.

## Expected impact

- **Build/packaging:** none; use the exact prebuilt image.
- **Runtime:** one bounded first-boot test; potentially higher memory pressure
  because the ordinary load path is not artificially limited.
- **Integration risk:** keep user input and repaint enabled, capture before
  GDB, use identity brackets, and use QMP-only teardown for only the owned
  process.
