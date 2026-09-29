# FLR-0116 — stop Example Demo MaterialParameter pre-frame abort

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini authoritative runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0115](FLR-0115-flutter-pub-cache-lock-order.md), [FLR-0113](FLR-0113-isolate-explicit-light-contribution-boundary.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-13-flr0116.md`

> Final status: Done for the pre-frame COLOR contract and 2D first-frame
> gate. Production 3D and the valid self-made fixture control are intentionally
> separate work units in FLR-0118 and FLR-0113.

## Work unit

Make the current Example Demo startup path type-safe at the
`MaterialParameter` Dart/native bridge, then prove that `flutter-auto` reaches
its first frame before resuming the separate production 3D/present analysis.
This ticket owns the pre-frame application abort only; it does not change the
compositor or claim that the later production shaded path is fixed.

## Problem

The current image builds and contains the requested runtime-debug tools, but
the first production launch in the current QEMU run ends in `SIGABRT` before a
comparable 2D/3D frame. GDB resolves the abort to
`plugin_filament_view::MaterialParameter::Deserialize()` at
`material_parameter.cc:84`: native code calls `std::get<std::string>(snd)` for
a COLOR value, and libc++ throws `std::bad_variant_access`.

The current Dart `MaterialParameter.color` and `baseColor` constructors emit
`[color.r, color.g, color.b, color.a]`, a `List<double>`, while the native
implementation still documents and parses the older `#AARRGGBB` string format.
The current production log ends its material-map dump with a vector-valued
color immediately before the uncaught exception. This is a direct wire-format
contract mismatch, not yet evidence of a Vulkan, Wayland, surface-alpha, or
light contribution failure.

## Success criteria

- [x] Reproduce the current-image startup with one `flutter-auto` owner and
  preserve the pre-fix coredump/QMP evidence as the control.
- [x] Confirm the chosen compatibility direction against both current Dart
  serialization and native `MaterialColorValue` semantics before editing.
- [x] Edit the persistent Mac Devtool-managed source, not `tmp/work` and not a
  generated patch body.
- [x] Generate the recipe patch through the official Yocto Devtool flow and
  register the unchanged patch under the project layer.
- [x] Pass Mac source/recipe `do_patch` and compile gates, then pass the
  progressive Mini archive/compile/full-image gates using the one bundle flow.
- [x] On one fresh QEMU run, prove no `MaterialParameter` abort and capture
  QMP-only evidence of the first 2D frame. Preserve any failure evidence.
- [x] Hand off the self-made 3D fixture reproduction to the independent
  FLR-0118 ticket so this pre-frame repair remains one bounded work unit.
- [x] Teardown through the recorded QMP socket and verify zero residual
  QEMU/runqemu/flutter-auto processes and zero residual QMP sockets.

## Facts

- The current Mini image build at layer commit `5136925` passed the targeted
  Example Demo compile and the full `agl-ivi-image-flutter` image build. The
  current image has the requested GDB, coredump, LLVM, syscall, profiling, and
  targeted debug-symbol packages.
- The same-image current QEMU passed preflight, start, guest-ready, and the
  QMP-only tool probe. The two saved 1280x800 QMP PPMs for this run have the
  same SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`; the
  native region was `0/223200` and the frame was uniform black.
- The corrected production bundle path was `3.32.5/release`. The launch
  loaded both `libvulkan_lvp.so` and `libflutter_engine.so`, then logged
  repeated camera Pigeon channel errors and terminated with
  `std::bad_variant_access`.
- The coredump record identifies PID 697, UID role `agl-driver`, command
  `/usr/bin/flutter-auto -b .../3.32.5/release`, and signal `SIGABRT`.
- With `/usr/bin/.debug/flutter-auto` explicitly loaded, GDB resolves the
  abort chain through the libc++ variant-access throw helper, the typed string
  variant extraction, and
  `plugin_filament_view::MaterialParameter::Deserialize` at
  `material_parameter.cc:84`. The GDB output SHA-256 is
  `6df3400af6aec90e0ef9f851e7a964309f139a30900f0508232f188cf85a113f`.
- Current Dart source in `packages/filament_scene/lib/material/material.dart`
  assigns a four-element normalized float list in both color constructors.
  Git history attributes that wire-format change to the
  `filament_scene` vector-type commit `1410b29`, which changed the prior
  `color.toHex()` value to the float list.
- Current native source in
  `plugins/filament_view/core/scene/material/material_parameter.cc` still
  handles COLOR by passing `std::get<std::string>(snd)` to
  `HexToColorFloat4`. The native vector-type history commit `0bf068a` did not
  add a corresponding COLOR vector branch.
- The selected compatibility direction restores the existing native contract:
  the persistent Mac Devtool source now serializes both Dart COLOR fields with
  `color.toHex()`, producing the native-compatible `#AARRGGBB` string.
- The source edit was committed in the persistent Devtool source branch
  `devtool-flr0116-material-color` as `2932c30`.
- Official `devtool finish` generated the patch
  `toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/0002-fix-restore-native-compatible-material-color-wire-fo.patch`.
  The unchanged registered layer copy is
  `0052-filament_scene-restore-native-compatible-material-color-devtool.patch`
  with SHA-256
  `3494156cd1c2df0897b7f251e44a749fb50d2456cae636d0509e2ef0fcfdabffc`.
- The same persistent Podman/Devtool environment passed the Example Demo
  recipe `do_patch` gate: 104/104 tasks succeeded, BitBake parsed 3342
  recipes with zero errors, and the generated patch was not hand-edited.
- The first attempt to run Devtool `modify` with extraction disabled was
  rejected because the recipe was already registered in the persistent
  workspace. The source registration and files remained intact; this was a
  preserved workflow observation, not a source failure.
- The successful tool-only boot had no coredumps. The production launch
  created the coredump recorded above. QMP teardown then passed with
  `residual_targets=0` and `residual_qmp=0`.

## Inferences

- For this run, the black QMP frame is explained first by application abort
  before first-frame presentation; it must not be classified as the existing
  post-scene native-black/present boundary.
- The strongest current cause is a Dart/native COLOR wire-format mismatch.
  The exception type, exact native call site, current Dart serializer, and
  native parser agree independently.
- `libvulkan_lvp.so` and the Flutter engine were mapped before the abort, so a
  missing runtime library is not the leading explanation for this run.
- Historical fixture-positive and production-native-black evidence remains
  valid as a later gate. If the app survives this fix but production native
  pixels remain zero, that is a separate renderer/present problem owned by
  FLR-0113 and its descendants.

## Ranked hypotheses and falsifiers

1. **COLOR wire-format mismatch is the immediate cause.** If a compatibility
   fix makes the same production startup reach a first frame without the
   `bad_variant_access` coredump, this is supported.
2. **The Dart and native components are from incompatible revisions.** If a
   controlled string COLOR input still crashes or a vector input is rejected
   elsewhere, compare the complete Flutter package/native plugin revisions
   before changing rendering code.
3. **A separate camera-channel or compositor problem is the first failure.**
   If the material exception disappears but the app still fails before its
   first frame, isolate the camera channel and compositor startup as a new
   boundary; do not infer it from the current secondary log messages.
4. **The later production 3D black boundary is unchanged.** If the fixed app
   reaches 2D but the production native region remains `0/223200` while the
   fixture is visible, resume the existing frame/present/light analysis rather
   than widening this ticket.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | COLOR value arrives as a vector while native reads a string | Dart/native source, GDB frame |
| Where | `MaterialParameter::Deserialize` in the filament_view plugin | debug-symbol backtrace, source line |
| When | Example Demo production launch before first comparable frame | launch output, coredump, QMP frame |
| Who | Flutter package/native plugin integration roles | source histories and recipe provenance |
| How | Pigeon/EncodableValue crosses the Dart/native bridge and invokes `std::get` | serializer, native parser, runtime log |

## PDCA

### Plan

1. Preserve the current coredump, GDB, launch, QMP, and cleanup evidence as a
   pre-fix control.
2. Compare both wire-format implementations and choose the smallest
   backwards-compatible source change, including validation for malformed
   values.
3. Apply that change through the persistent Mac Devtool source, generate the
   official patch, commit the layer, and transfer one complete-history bundle
   to the clean Mini authoritative receiver.
4. Pass progressive build gates, then run one QEMU with fixture-first and
   production-second QMP captures and explicit teardown.

### Do

- Re-ran GDB with the target's `/usr/bin/.debug/flutter-auto` symbol file;
  the native abort caller is now resolved to `MaterialParameter::Deserialize`.
- Read the current Dart and native implementations and compared their Git
  history. The Dart vector serialization and native string extraction are
  confirmed as the first direct contract mismatch.
- Preserved the QMP black frame, coredump metadata, both GDB outputs, launch
  output, and QMP cleanup result under the existing evidence root.
- No source patch has been made yet; the diagnosis is separated from the
  upcoming Devtool edit.

### Check

- Immediate failure boundary: **confirmed** at native COLOR deserialization.
- Mac source/patch/do_patch gate: **PASS**; Mini compile, image, and runtime
  gates remain open.
- Current-run first-frame / 2D / 3D acceptance: **not reached** because the
  application aborted; this remains UNKNOWN after the eventual compatibility
  fix.
- Vulkan/Flutter library presence: **confirmed** for the launched process;
  this is not proof of successful rendering.
- QMP evidence: **captured**; current-run native region is `0/223200`.
- Cleanup: **PASS**, zero residual targets and zero residual QMP socket.

### Act

- Transfer the committed layer change as one complete-history bundle to the
  clean Mini authoritative receiver, then run the progressive archive,
  compile, and full-image gates with the existing caches.
- Keep the pre-fix image and evidence as the control. After the fixed image is
  built, run one QEMU with fixture-first and production-second QMP captures.
- Do not change compositor ordering, surface alpha, light counts, camera
  placement, or Mesa/LLVM behavior until the app survives this pre-frame
  contract failure.

## UNKNOWN

- Whether the restored string contract is sufficient for every material field
  after the fixed image runs; COLOR itself now has a selected direction.
- Whether the repeated camera Pigeon errors are a secondary symptom or a
  separate channel/revision mismatch.
- Whether the production shaded scene will remain native-black after the app
  reaches its first frame.

## Evidence locations

- Mini evidence root: `$EVIDENCE_ROOT/flr0113-authoritative`
- Pre-fix launch: `$EVIDENCE_ROOT/flr0113-production-launch-5136925-retry.output`
- Pre-fix coredump metadata: `$EVIDENCE_ROOT/flr0113-coredump-info-5136925.txt`
- Resolved GDB: `$EVIDENCE_ROOT/flr0113-coredump-gdb-symbolfile-5136925.output`
- QMP frames: `$EVIDENCE_ROOT/qmp-5136925-tool-probe.ppm` and
  `$EVIDENCE_ROOT/qmp-5136925-production-late.ppm`
- Working log: `work/logs/2026-09-13-flr0116.md`

## Final runtime result — 2026-09-13

- Mini commit `93b91ea2e2e99ee90bab3ad89fccccb057953ea3` passed the progressive
  Example Demo and full-image gates. A first wrapper attempt stopped at
  `oe-init-build-env` because `BBSERVER` was unset under `set -u`; the retry
  without that wrapper error passed and is preserved in the Mini log.
- In QEMU run `r116-93b91ea`, the repaired production `flutter-auto` stayed
  alive as one `agl-driver` process, loaded Vulkan/Flutter/llvmpipe, and
  produced no coredump. The QMP frame showed the 2D HUD and buttons.
- The HUD-excluded central region `[300,250,620,400]` was uniform black:
  `0/248000` changed pixels, edge `0`, chromatic `0`, luma `[0,0]`.
  The earlier region `[300,80,620,360]` includes the HUD graph lines and is
  not used as a 3D verdict.
- The environment-only fixture attempt was invalid because the current
  effective recipe did not register the neutral native fixture aliases. Its
  similarly detected graph-line pixels are not 3D evidence. A valid Dart
  fixture run is FLR-0118.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.
