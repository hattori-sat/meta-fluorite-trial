# FLR-0395 — capture the first fault in the Sequoia known-material run

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / guest debugger / QMP evidence roles
- Created: 2026-10-01
- Branch: feature-flr-0395-sequoia-first-fault
- Work unit: One bounded runtime-only Sequoia run with GDB armed before Flutter starts
- Predecessors: [FLR-0391](FLR-0391-apply-constant-lit-material-to-sequoia.md), [FLR-0394](FLR-0394-capture-live-fixture-over-ssh.md)
- Plan: [FLR-0395 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0395-sequoia-first-fault.md)
- Working log: [FLR-0395 working log](../logs/2026-10-01-flr0395.md)
- Rootfs SHA-256: 54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690
- Material: existing patch 0333, constant blue LIT expression vec3(0.05, 0.45, 1.0); no new source patch/build in this unit

## Problem

### Purpose

The requested material replacement is already in patch 0333 and in the exact
FLR-0391 image. FLR-0394 proves the simple constant-blue LIT/SUN fixture and
HUD visibly render on that same image. FLR-0391's Sequoia run reached material
setup/binding markers but its live Sequoia ROI was black during an unmatched
present / FEngine::loop Oops sequence. Capture the first runtime fault so the
next countermeasure targets the failing boundary instead of changing the same
shader again.

### Success measure

One attributable run yields either a live QMP frame showing diagnostic-blue
Sequoia plus HUD, or a pre-armed GDB capture of the first relevant stop with
thread backtrace, PC/registers, loaded libraries, and contemporaneous live
QMP. A GDB-only result completes this diagnostic ticket, not product 3D
acceptance.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Sequoia ROI black under constant-blue LIT; Oops followed unmatched present | FLR-0391 manifest |
| Where | Mini QEMU; Example Demo 3.32.5; Flutter/FEngine/Filament | FLR-0391/0394 manifests |
| When | Exact image with patch 0333; fault during bounded manual run | FLR-0391 focused log |
| Who | Mini runtime, guest Flutter, debugger, QMP evidence responsibilities | Role-based records |
| How | Exact Sequoia selector/material/light profile under GDB from process start | Saved FLR-0391 launch profile |

### Priority selection

- Compared: repeat material edit/build; change texture/camera; capture first
  runtime fault.
- Selected: pre-arm GDB on the already-built exact image. Patch 0333 already
  contains the known constant LIT expression, and FLR-0394 proves a fixture
  path on the same rootfs.
- A second source edit without a new failing boundary would duplicate the
  previous countermeasure.

### Process analysis

| Step | Expected | Actual | Evidence |
| --- | --- | --- | --- |
| Image | Exact rootfs/kernel/qemuboot | Fixed in FLR-0391 | FLR-0391 manifest |
| Launch | One Sequoia Flutter inferior under pre-armed GDB | Pending | This ticket log |
| Render | Blue Sequoia pixels plus HUD | FLR-0391 black ROI and unmatched present/Oops | FLR-0391 manifest |
| Capture | First-stop stack and live QMP frame | Pending | This ticket evidence |
| Teardown | No target/socket/port residue | Pending | This ticket evidence |

### Problem point

UNKNOWN between Sequoia renderable/material setup and the first failed native
frame/present. FLR-0394 shows the same image can render a simple fixture but
does not identify the Sequoia failure.

### Ideal condition

Sequoia geometry appears blue with the HUD, without a renderer fault.

### Current condition — Facts

- Patch 0333 changes Sequoia's diagnostic material to LIT and the same
  constant blue base-color expression as the positive fixture; image build,
  Mini do_patch, and do_compile passed.
- FLR-0394 shows fixture plus HUD on the exact rootfs; full-frame PNG SHA-256:
  1926492368bbe7b0d6a1523a6b45cdb233421d090d765edd25931eabf70bbc7c.
- BOUND=24 denotes 24 binding log records, not 24 primitives without separate
  primitive-count evidence.
- FLR-0391 Sequoia ROI was 0/144000; present was 2 begins/1 return; the app
  recorded FEngine::loop Oops #2 and status 124.

### Gap

No GDB stop was captured before the Sequoia fault, and no healthy QMP frame
proves the replacement material appears on the car.

### Impact

Another material, texture, lighting, or camera change without the first-fault
boundary risks another uninformative build/runtime loop. This ticket is
diagnostic and does not alter packaging or production defaults.

### Point of occurrence

UNKNOWN between Sequoia renderable/material setup and the first failed native
frame/present.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result |
| --- | --- | --- | --- |
| Sequoia renderable/material use reaches an invalid path | GDB stops after setup; stack/PC implicates model/render path before visible frame | Capture GDB at launch and QMP at stop | Pending |
| LLVM/Lavapipe fault is downstream or correlated | Blue Sequoia may appear before a later fault, or stop stack is outside material/geometry setup | Capture first completed frame and signal stop in one run | Pending |
| Assignment or generated variant differs from simple fixture | READY/BOUND but black ROI without a fault in the interval | Compare focused markers and first live frame | Pending |

### Confirmed root cause

UNKNOWN. Oops and black pixels are correlated in FLR-0391, not proven causal.

### Minimal countermeasure

Do not alter the material again yet. Arm GDB before the exact Sequoia launch,
capture one bounded first-fault stack plus live QMP frame, and change source
only after that evidence distinguishes the failing boundary.

## Scope

### In scope

- One 6144-MiB Mini QEMU run on the exact FLR-0391 image.
- Existing Sequoia selector, patch-0333 LIT override, and production SUN
  profile, with GDB configured before flutter-auto starts.
- Bounded GDB thread/backtrace/register/shared-library/PC capture.
- Full-frame QMP capture with identity and teardown checks.

### Out of scope

- Source edits, Devtool patch generation, bundle transfer, BitBake, or rebuild:
  the image already contains the requested material replacement.
- Texture/GLB edits, camera/culling changes, new light/composition changes,
  new debug toggles, broad log dumps, global kills, cache cleanup, Mac image
  copy, or a second QEMU.

## Success criteria

1. Exact image identity and one run-owned QEMU are confirmed; one Flutter
   inferior uses the FLR-0391 Sequoia/material/SUN profile under GDB.
2. GDB is armed for SIGSEGV before startup. Preserve the first stop's
   thread/PC/backtrace/register/library evidence. If no signal occurs in the
   bounded run, record UNKNOWN, not a fix.
3. Capture a complete QMP framebuffer at the first successful present or
   while the inferior is stopped at the first fault; record Sequoia/HUD ROIs.
4. QMP quit and postflight prove exact process/socket/port cleanup.
5. Update Facts/Inferences/Hypotheses/UNKNOWN and PDCA; if no code fix is
   justified, create a new narrow ticket.

## Visual evidence

- QMP-only screenshot: pending.
- Target: diagnostic-blue Sequoia plus HUD; a black frame or stopped debugger
  is not a positive visual result.
- Run/image/time: pending; exact hashes inherited from FLR-0391 and rechecked.
- Pixel count/bounding box/SHA-256/evidence ID: pending.
- Artifact link: pending in the FLR-0395 manifest.

## Hypotheses

1. Sequoia renderable/material path faults before replacement material appears.
2. The recurring LLVM/Lavapipe fault is downstream or correlated; Sequoia may
   have pixels before it.
3. Material assignment or generated variant differs from the simple fixture
   despite the same GLSL base-color expression.

## PDCA

### Plan

- Reconfirm canonical repository and exactly one active ticket; preserve exact
  FLR-0391 image hashes and the existing fixed Mini runqemu profile.
- Verify guest GDB exists and QEMU/Flutter/QMP/forwarded ports are clean.
- Start one QEMU. Launch exact Sequoia Example Demo profile under GDB as the
  existing guest user; set the SIGSEGV catch rule before run. No source,
  material, image, or build-state change.
- At first signal stop, capture threads, 30-frame backtrace, registers,
  shared libraries, PC symbol, and 12 instructions at PC; capture QMP while
  QEMU remains live.
- If no signal occurs within 180 seconds, capture the live frame, focused
  counters, and bounded kernel/coredump result; do not call this fixed.
- Stop only recorded inferior and QEMU; verify PID, QMP socket, and ports clear.

### Do

- See [FLR-0395 working log](../logs/2026-10-01-flr0395.md).

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Identity/preflight | Exact artifacts; no stale process/occupied ports | Pending | Working log | UNKNOWN |
| GDB-before-launch | Signal catch configured before Flutter starts | Pending | GDB output | UNKNOWN |
| First-fault capture | First-stop evidence or bounded no-stop recorded | Pending | GDB output | UNKNOWN |
| Live QMP visual | Full frame and fixed ROIs while QEMU live | Pending | QMP manifest | UNKNOWN |
| Teardown | No target process, socket, or port residue | Pending | Postflight | UNKNOWN |

### Act

- If GDB captures the first fault, open a separate ticket for the smallest
  stack-supported source countermeasure, then use Devtool → layer commit →
  verified bundle → Mini build.
- If a healthy blue Sequoia frame appears, preserve it as a visual milestone;
  track any later fault separately.
- Product completion still requires a live attributable frame with Sequoia
  and HUD visibly co-present.

## Decision log

- 2026-10-01: reuse patch 0333; no duplicate material patch or rebuild.
- 2026-10-01: use a new ticket because FLR-0394's fixture gate is complete and
  first-fault capture is independently verifiable.

## Unknowns

- Whether the first fault is a GDB-catchable SIGSEGV.
- Whether its stack implicates material use, geometry, present, LLVM, or other.
- Whether Sequoia can render before the fault.
- Whether fixture and Sequoia compile to equivalent shader variants.

## PDCA checker

- Status: NOT CHECKED
- Checked by: pending
- Findings: pending fresh runtime evidence and teardown.
