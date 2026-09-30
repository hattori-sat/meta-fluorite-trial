# FLR-0376 — manually replay Flutter with the explicit Wayland session environment

- Status: In Progress
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
   With explicit `XDG_RUNTIME_DIR` and `WAYLAND_DISPLAY`, Wayland client
   initialization and Flutter 2D HUD pixels appear; production Sequoia may
   still fail separately.
2. **The recurring renderer/Present failure is independent of session vars.**
   Explicit environment is confirmed at `exec`, but app markers/QMP still show
   the same no-HUD/no-Sequoia frame and/or the same Oops boundary.
3. **The run does not reach Flutter because guest/compositor/session preflight
   fails.** Record the exact preflight failure and stop before retry; do not
   interpret a prelaunch frame as a renderer result.

## UNKNOWN

- Whether FLR-0374 inherited a usable Wayland session despite the missing
  recorded environment contract.
- Whether the current default Example Demo route exposes interactive HUD
  controls before the Present/Oops boundary.
- Whether explicit session variables restore the 2D HUD, production Sequoia,
  both, or neither.

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

- Pending manual Mini QEMU/guest-SSH runtime run.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate and guest preflight | Exact image; compositor/session ready; no stale targets | Pending | PENDING |
| Manual user/session contract | One `agl-driver` app with explicit XDG/Wayland variables | Pending | PENDING |
| Flutter readiness | Startup and at least first successful queue-present or bounded classified failure | Pending | PENDING |
| QMP visual evidence | Complete QMP frame and HUD/native regions analyzed | Pending | PENDING |
| Exact teardown | App/QEMU/socket/ports cleared | Pending | PENDING |
| Script discipline | No launcher script changes before manual proof | No edits | PASS |

### Act

- Do not change automation based on an unverified route. If this manual
  invocation succeeds, record the exact stable command/env contract first;
  only then decide whether an existing script should be updated in a separate
  ticket. If it fails, continue from the first captured startup/runtime
  divergence, not by repeatedly editing scripts.

- Jira is intentionally not used; this Markdown ticket and working log are the
  source of truth.
- `FLR-0026` and historic `FLR0026_*` identifiers remain historical only.
