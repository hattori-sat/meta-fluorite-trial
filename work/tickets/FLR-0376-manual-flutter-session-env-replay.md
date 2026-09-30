# FLR-0376 — manually replay Flutter with the explicit Wayland session environment

- Status: Done
- Priority: High
- Owner: Mini QEMU / strict guest SSH / `agl-driver` / Flutter / QMP roles
- Created: 2026-09-30
- Predecessor: [FLR-0375 Sequoia GLB image-path inspection](FLR-0375-inspect-production-sequoia-glb-image-paths.md)
- Branch: `feature-flr-0376-manual-flutter-session-env-replay` (local, no push)
- Working log: [FLR-0376 working log](../logs/2026-09-30-flr0376.md)
- Candidate rootfs SHA-256:
  `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`.

## Objective

Establish whether the latest production Flutter black/gray frame is explained
by a missing Wayland user-session environment in the manual launch. Reuse the
exact existing candidate image. Start one app manually over strict guest SSH
as `agl-driver`, explicitly setting the environment used by the known-good
historical commands. Capture startup, present, kernel, process, and complete
QMP evidence before exact teardown. Do not edit or invoke an app-launch script.

## Facts

- FLR-0371's successful manual fixture launch and historical commands set
  `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0` for
  `agl-driver`.
- FLR-0374 ran one `/usr/bin/flutter-auto` as UID 1001 and reached GLB loading
  and queue-present, but its ticket/log does not establish those two
  environment variables at `exec`; its full QMP frame showed no HUD or
  recognizable Sequoia and the known FEngine Oops recurred.
- The exact candidate image displayed self-made LIT/SUN geometry plus HUD in
  FLR-0371. The production GLB's 23 embedded PNGs and every texture/material
  reference validate in FLR-0375.
- In `flr0376-0001`, the active compositor, UID-1001 Wayland socket, Example
  Demo 3.32.5 bundle, and zero stale Flutter processes passed preflight. The
  interactive guest shell was manually switched to `agl-driver`; `/proc/657/environ`
  confirms the requested XDG/Wayland variables and present trace.
- With explicit session variables, the full QMP PPM SHA-256 is
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`,
  byte-identical to FLR-0374. The complete 1280x800 frame shows a white field
  and large black polygon, with no recognizable Sequoia or HUD.
- Native ROI `(440,220,400,360)` is uniform black (`0/144000` chromatic,
  `max_chroma=4`). The top-right ROI `(1120,0,160,80)` is uniform white
  (`0/12800` chromatic); CPU/GPU/Scenes pixels are absent.
- There are 2 exact queue-present enters and 1 successful return. At guest
  monotonic 278.958223 s, TID 697 (`FEngine::loop`) faulted at RIP
  `0x7faaffc96541`, CR2 `0x000000009e7f8750`. Parent PID 657 survived, TID
  697 disappeared, and no coredump was listed. Causality remains UNKNOWN.
- Full 103,410-byte app log SHA-256:
  `3f0cf43b59e5cc948e2365cc0de9b36c06f49a0d364771bc10a9e0192625b043`.
  Pre-Flutter QMP hash:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP-only review PNG SHA-256:
  `771f074f9455a74bc37ef921ea1f15528f7a6067af2f96d182712942b4fd4514`;
  eight-frame MP4 SHA-256:
  `614950238f8e6725e1e59ed0cfe10e56250369ce69c3c93e43cecca7a917728f`.
- Exact PID 657 was stopped after UID/comm/executable verification. QMP quit
  was accepted; independent checks found zero app/QEMU/runqemu processes,
  absent QMP socket, and free ports 10930–10932. No script/source/build
  changed, and no disk image was copied to Mac.
- Historical commands and environment evidence are in FLR-0285/0286/0371;
  no command named `ffh` appears in the repository. This test uses the
  documented direct guest-SSH/manual Flutter route, not a new wrapper.

## 4W1H (excluding Why)

| Dimension | Current evidence | Needed discriminator |
| --- | --- | --- |
| What | Production Example Demo reads Sequoia GLB but current frame lacks visible car/HUD | Flutter with explicit display-session variables and complete QMP frame |
| Where | Exact FLR-0371 rootfs on Mini QEMU; Example Demo 3.32.5 | Same rootfs and bundle path; guest user `agl-driver` |
| When | Previous app reached one successful queue-present then faulted | Capture at first successful return and immediately on Oops/exit |
| Who | Direct guest SSH as root for inspection; app process as `agl-driver` | Verify UID, command line, session variables, and exactly one process |
| How | Manually set XDG runtime and Wayland display, launch one `/usr/bin/flutter-auto`, inspect QMP | No app launcher helper, script edit, build, or patch |

## Hypotheses

1. **Session environment omission caused the missing Flutter surface/HUD.**
   Explicit session variables reach the app, but the byte-identical QMP frame
   and absent HUD falsify this as the explanation for current production
   pixels.
2. **The recurring renderer/Present failure is independent of session vars.**
   Supported for this comparison: the exact present/Oops pattern and full
   frame hash recur with the explicit environment.
3. **The run does not reach Flutter because guest/compositor/session preflight
   fails.** Falsified: compositor, Wayland socket, app bundle, manual launch,
   GLB loading, and present markers all passed.

## UNKNOWN

- Whether FLR-0374 inherited a usable Wayland session remains UNKNOWN; however,
  explicit session variables reproduce its exact QMP frame and Oops signature.
- Whether the hidden/non-rendered Scenes control receives input and whether a
  Planetarium route change alters the current QMP output is assigned to
  FLR-0377.

## Scope and success criteria

- Reuse only the recorded candidate rootfs/kernel/qemuboot and existing Mini
  QEMU/runtime roles; one fresh run ID and one evidence directory.
- Read-only preflight: no stale QEMU/runqemu/flutter-auto, QMP socket, or
  forwarded-port owner; verify image hashes, guest kernel, compositor,
  `/run/user/1001/wayland-0`, Example Demo bundle, and zero stale app process.
- Through strict root guest SSH, run a small explicit command as `agl-driver`
  that sets `XDG_RUNTIME_DIR=/run/user/1001` and
  `WAYLAND_DISPLAY=wayland-0`, then manually starts exactly one
  `/usr/bin/flutter-auto -b <exact Example Demo 3.32.5 release path>` with only
  `FLUORITE_PRESENT_TRACE=1`. Preserve the actual exec environment values in
  the run evidence without dumping unrelated environment or secrets.
- Wait at most 45 seconds for the first successful queue-present return or
  stop early on app exit/Oops. Capture the complete 1280x800 QMP frame and
  short QMP sequence at the first returned present; capture selected bounded
  log/kernel/process evidence before stopping. If no successful return occurs,
  record that fact and capture the last available frame before teardown.
- Visually inspect the entire QMP frame and separately score HUD/metrics and
  recognizable Sequoia/native color. A Flutter/2D-only success is not a 3D
  pass; a prelaunch black frame is not a runtime verdict.
- Stop only the verified app PID and this QEMU through its recorded QMP socket;
  independently verify zero residual app/QEMU/runqemu processes, socket, and
  reserved ports.
- No source/recipe/script edit, Devtool, BitBake, image transfer, or build.

## Impact

- **Build-time:** none; reuse the exact candidate.
- **Packaging:** none.
- **Runtime:** one bounded manual launch with explicit session variables.
- **Integration risk:** no software changes; a session-only pass would identify
  a launch-contract issue without proving production Sequoia rendering.

## Plan / Do / Check / Act

### Plan

Use the prior direct SSH → `agl-driver` → manual Flutter route. Compare the
known-good explicit display environment against FLR-0374's unrecorded
environment, with all other app settings fixed. Capture the first useful
present/frame and bounded errors before exact teardown.

### Do

- Reused the exact existing Mini candidate and the byte-identical proven QEMU
  and QMP-capture helpers. Started one 6144 MiB QEMU after exact hash and
  process/port checks.
- Manually opened strict guest SSH, switched to `agl-driver`, explicitly set
  XDG/Wayland variables, and started one Flutter app directly. Captured
  process environment, bounded/full app log, kernel Oops, coredump state,
  full QMP PPM, fixed ROI analyses, and eight QMP frames before teardown.
- Stopped only the verified app PID, quit this QEMU through QMP, and verified
  zero residual processes/socket/listeners. No launcher script or source was
  changed.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate and guest preflight | Exact image; compositor/session ready; no stale targets | Exact hashes; active compositor; Wayland socket; no stale app | PASS |
| Manual user/session contract | One `agl-driver` app with explicit XDG/Wayland variables | PID 657 UID 1001; `/proc` confirms XDG/Wayland/present trace | PASS |
| Flutter readiness | Startup and at least first successful queue-present or bounded classified failure | GLB read; 2 enters/1 success; known TID 697 Oops | PASS for classification; rendering FAIL |
| QMP visual evidence | Complete QMP frame and HUD/native regions analyzed | Exact FLR-0374 PPM hash; white field/black polygon; native black; HUD white; 8-frame replay | PASS for evidence; visual acceptance FAIL |
| Exact teardown | App/QEMU/socket/ports cleared | Exact PID stopped; QMP quit accepted; no process/socket/listener | PASS |
| Script discipline | No launcher script changes before manual proof | No source/recipe/script/build changes | PASS |

### Act

- Close this bounded session-environment experiment: correct manual user and
  Wayland variables do not change the production QMP output. Do not modify a
  launcher script to encode this environment as a rendering fix.
- FLR-0377 sends one measured tap at the Scenes control coordinate from the
  same image's positive HUD frame, then checks the Planetarium activation
  marker and complete QMP output. No coordinate sweep or patch is authorized.

- Jira is intentionally not used; this Markdown ticket and working log are the
  source of truth.
- `FLR-0026` and historic `FLR0026_*` identifiers remain historical only.
