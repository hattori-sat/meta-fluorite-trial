# FLR-0394 — capture the current-image LIT fixture while Flutter is live

- Status: In Progress
- Priority: High
- Created: 2026-10-01
- Work unit: One runtime-only live-capture attempt; no source, layer patch, or BitBake build
- Predecessor: [FLR-0393 observer-window failure](FLR-0393-replay-known-good-lit-fixture-on-current-image.md)
- Sequoia candidate: [FLR-0391 patch 0333](FLR-0391-apply-constant-lit-material-to-sequoia.md)
- Positive controls: [FLR-0369](FLR-0369-lit-hardcoded-material-control.md), [FLR-0371](FLR-0371-lit-parameter-rgb-assignment.md)
- Rootfs SHA-256: `54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690`
- Kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Qemuboot SHA-256: `58ef9a59af7df24be48b221f252fd7b604e5d968e61766af83b7cf7b8ae5b5f7`
- Branch: `feature-flr-0394-direct-ssh-live-fixture-capture`
- Working log: [FLR-0394 working log](../logs/2026-10-01-flr0394.md)
- Evidence manifest: [FLR-0394 QMP evidence](../evidence/FLR-0394-0001.md) (filled after the bounded run)

## Objective

Determine whether the exact FLR-0391 image displays the known-positive,
self-created constant LIT/SUN geometry with the CPU/GPU HUD. FLR-0393 did not
produce a visual verdict: its serial observer timed out at 30 seconds, shorter
than the observed first-present latency, and the guest app then reached its
60-second timeout. This ticket repeats the same diagnostic profile using
direct strict SSH and captures QMP while the exact app PID is live.

This is a renderer/present control, not Sequoia acceptance. A positive fixture
frame narrows the issue to production Sequoia; a negative frame with healthy
capture/present points to a shared path. Neither result alone proves root cause.

## Facts / inferences / hypotheses / unknowns

- **Facts:** FLR-0369 produced 119,716 chromatic fixture pixels plus HUD on its
  pinned image. FLR-0391 patch 0333 and the full image build passed; its live
  Sequoia ROI was black during an unhealthy present/Oops episode. FLR-0393
  observed the constant-LIT branch and six successful present returns but no
  live frame.
- **Inference:** FLR-0393's 30-second serial-exec deadline was incompatible
  with its 60-second app timeout and the roughly 52-second first present.
- **Hypotheses:** (1) the current image's generic fixture still renders and
  Sequoia setup/material is the narrowed boundary; (2) a shared draw/present
  issue also blocks the fixture.
- **UNKNOWN:** live fixture pixels and healthy repeated presents on the exact
  `54da69d…` rootfs.

## 4W1H (excluding Why)

| Dimension | Scope |
| --- | --- |
| What | Existing constant-blue LIT/SUN fixture plus CPU/GPU HUD |
| Where | Exact Mini rootfs, Example Demo 3.32.5, runqemu/QMP; no Mac VM-image copy |
| When | One bounded app launch, up to 180 seconds; capture after first successful present |
| Who | Mini QEMU role, guest `agl-driver` role, direct-SSH observer, QMP evidence role |
| How | Strict run-scoped SSH key; appended-log wait; exact PID/UID/start gates around full-frame still and eight QMP frames |

**Problem point:** the observer ended before the renderer's first present. The
corrective process changes only the observation window and evidence retention;
it does not change Flutter, material, camera, texture, light, or image contents.

## Plan / Do / Check / Act

### Plan

- Run canonical repository, privacy, and one-active-ticket checks.
- Use the exact image hashes above and the fixed Mini runqemu/QMP harness,
  6144 MiB, and one ticket-scoped evidence directory. No rebuild, bundle,
  TMPDIR change, second container, or image transfer.
- Check zero stale QEMU/Flutter and free ports. Confirm the SSH forwarded port
  belongs to the exact QEMU PID before pinning its run-scoped guest host key.
- Launch one `agl-driver` Flutter process with FLR-0393's same five fixture
  flags, but a 180-second app timeout. Do not set Sequoia-specific overrides.
- Wait over strict direct guest SSH using only appended app-log bytes; do not
  use the 30-second `serial-exec` helper or rescan the full log in a polling loop.
- Capture QMP still and eight-frame video immediately after a successful
  present, bracketed by exact PID/UID/start. Persist focused app/present
  evidence on Mini before teardown; use BusyBox-compatible `dmesg` syntax.
- Stop only the exact app process, quit QEMU through the official harness, and
  verify zero residual processes, QMP socket, and forwarded-port listeners.

### Success criteria

| Criterion | Expected |
| --- | --- |
| Image/process gate | Exact hashes; one owned QEMU; no stale Flutter |
| Live fixture | QMP full frame captured while the same app identity remains live |
| Visual outcome | Separate full-frame/native/HUD metrics; state whether both are visible |
| Runtime health | At least eight successful presents; no unmatched present/Oops during capture |
| Evidence | Still, short video, hashes, focused logs/counts persisted before QEMU teardown |
| Cleanup | Official QMP quit; zero target processes/socket/ports |

### Do

- Pending one bounded direct-SSH run; results go in the
  [working log](../logs/2026-10-01-flr0394.md).

### Check

- Pending live QMP still/video, fixed ROI metrics, present counts, identity
  bracket, and teardown.

### Act

- If fixture+HUD is visible with healthy present, create a separate
  Sequoia-only run on this exact image; no rebuild.
- If a valid live fixture frame is black, use the existing draw/present history
  to choose one narrow shared boundary.
- If the first-present gate fails again, preserve the stop point; never label a
  post-exit screen a render verdict.
