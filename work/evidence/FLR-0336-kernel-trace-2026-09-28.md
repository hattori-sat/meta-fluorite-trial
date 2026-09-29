# FLR-0336 evidence — kernel page-fault trace trial

- Date: 2026-09-28
- Ticket: [FLR-0336](../tickets/FLR-0336-capture-kernel-context-of-fengine-page-fault.md)
- Run ID: `flr0336-0001`
- Raw QMP/serial evidence: `$EVIDENCE_ROOT/flr0336-0001/qemu` (Mini PC only)
- Image identity: same FLR-0335 rootfs, qemuboot, and kernel; hashes are recorded in FLR-0335 evidence.
- QEMU memory: 6144 MiB; one QEMU; existing build/TMPDIR reused.
- No Devtool, patch, BitBake, source, recipe, or image build ran.

## Facts

- Guest preflight passed before app launch. `perf` 6.6.111 and both
  `exceptions:page_fault_kernel` and `exceptions:page_fault_user` were present;
  `perf_event_paranoid=2`, `CONFIG_PERF_EVENTS=y`, and
  `CONFIG_FRAME_POINTER=y`. A one-second kernel-event perf probe produced
  call-chain samples without changing a sysctl or mounting tracefs.
- The production Example Demo was launched once without GDB at guest uptime
  `393.74`, using the saved FLR-0335 diagnostic profile. Perf recorded only
  `exceptions:page_fault_kernel` for its bounded 400-second maximum.
- At guest monotonic time `422.495545` (about 28.76 seconds after launch), the
  kernel logged the recurring fault:

  ```text
  BUG: unable to handle page fault for address: 00000000d1486750
  #PF: supervisor read access in user mode
  #PF: error_code(0x0000) - not-present page
  Oops: 0000 [#1] PREEMPT SMP NOPTI
  CPU: 0 PID: 710 Comm: FEngine::loop
  RIP: 0033:0x7f452fe98541
  RSP: 002b:00007f44d1486750
  CR2: 00000000d1486750
  ```

- The app log has 19 scene draw-end and 19 native Wayland commit markers,
  one Vulkan queue-present begin, zero queue-present return, and zero
  `FLUORITE_VK_PRESENT_DONE`. The Oops followed the present begin by about a
  second. Parent `flutter-auto` PID 664 survived; faulting TID 710 was absent
  afterward.
- The finalized perf data had 488 `page_fault_kernel` events. Its bounded
  `422.49–422.51` window had no kernel-event sample, and no sample was
  attributed to TID 710. It did record unrelated kernel page-fault events
  from TID 709 earlier in the app run. The user page-fault event was not
  enabled in this trial. Therefore the fault-time call chain was not captured.
- No causal relation between the FEngine Oops and missing present return is
  proven. The user-mode saved RIP plus absence from the kernel-event stream
  makes the `page_fault_user` tracepoint a useful next discriminator, not a
  confirmed explanation. Perf lost-event accounting was not collected.

## QMP visual evidence

- Pre-app QMP-only frame SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Full QMP frame after app launch and after the fault:
  `7b5039f54a9795c0b6d245be131f89ecb3947b1d730176f3660910105668508e`;
  pre- and post-fault frames are byte-identical.
- The full frame visibly contains the 2D Fluorite HUD/telemetry and Scenes
  control. The lower viewport ROI `(0,200,1280,600)` is uniformly black:
  `changed_pixels=0`, `chromatic_pixels=0`, `luma_range=[0,0]` across 768,000
  pixels. No Sequoia/3D object is visible in this run.
- Each pre-fault and post-fault eight-frame QMP sequence has exactly one
  unique frame hash. The saved post-fault eight-frame sequence was encoded
  into an 8-second MP4 replay for viewing; this is a playback of QMP samples,
  not a continuous host-window recording.
- QMP evidence is from the QEMU framebuffer; no desktop screenshot was used.

  ![QMP-only post-fault full frame](FLR-0336-qmp-postfault.png)
  PNG SHA-256: `8732e7149b55b8216c942a061a4bbc6d0bee409c94f2e7542b227d555dc12320`.

  [8-second QMP frame-sequence replay](FLR-0336-qmp-postfault-sequence.mp4)
  (SHA-256 `41387e0dad7d88b336f0d681d7d945593eab28c2df6b82a688cddb3612b3fc96`).

## Teardown and selected evidence hashes

- Exact guest app PID was stopped after its `comm` matched `flutter-auto`;
  guest process count became zero.
- QMP quit was accepted. Final host checks: `residual_targets=0`,
  `residual_qmp=0`, QMP socket absent.
- Selected Mini evidence outputs:

  | Artifact | SHA-256 |
  | --- | --- |
  | `serial-0336-trace-preflight.output` | `06a7bbdad9c9429ceebb885658fddde951c8f935dcd799099a18257b2f0d07e7` |
  | `serial-0336-perf-capability.output` | `85965527972a5b3d0d9a4d2def511dd29c5854224a66418b766dcc2838af561b` |
  | `serial-0336-launch.output` | `6aeebdffe4d9a21d54b547b1660a3a243d50220bb1a9ad30a541fc7eb724dce1` |
  | `serial-0336-fault-window.output` | `2f8f66cbb427fce3db98157c88a10c6da27ce45ab4ad62daf7564c18055d3d85` |
  | `serial-0336-perf-trace-index.output` | `a603086bdcdfb3bdcfc87d332f1a27e0a17c61c3bbf93dea445b05426fcd5197` |
  | `serial-0336-perf-fault-events.output` | `eb073937cc78cbd14848a257cd0ed460cb1ba3b999c75208f1f5ae2ef2d61b2e` |
  | `serial-0336-final-current-state.output` | `1bc839996aadd9cf1fb7f0f6f1fa42849b3ba97ff777f594a32e2ab2a205946d` |
  | `serial-0336-stop-app.output` | `2447ca36794897b949d5adcccb4c5967de99accada81deb8e5821751f2c126cf` |

- The raw perf data and full decoded trace were kept in guest `/run` and were
  lost when the QEMU guest was shut down. The Mini evidence directory retains
  the bounded trace extracts and command outputs; FLR-0337 must preserve its
  selected fault-window trace before teardown.

## Process corrections

- One post-capture `pgrep`/`cat /run/...` check ran on the Mini PC host rather
  than inside the guest. Its “zero app/missing PID” output was invalid for
  guest state. The guest serial command later established the actual app and
  perf state; no reboot had occurred.
- A stop-and-correlate command used `exit` on an error inside the interactive
  serial shell, closing that shell before the harness completion marker. The
  captured output showed a stale perf PID after the 400-second recording had
  already ended. Later short guest checks established the finalized trace
  existed; indexing was split into a separate bounded `perf script` command.
- Future serial-exec command files must not `exit` the interactive login
  shell; report status and always allow the harness marker to be emitted.
- Future diagnostics must label host-side versus guest-side checks explicitly,
  and must archive the selected raw/decoded trace before QMP teardown.

## Verdict

The current image still shows the 2D HUD but no 3D Sequoia; the 3D viewport is
uniformly black. The recurring FEngine page fault and missing present return
reproduced. Kernel-only perf proved usable but did not capture the faulting
TID's event or call chain. Root cause and its causal relationship to present
remain UNKNOWN. No product patch or rebuild is justified. FLR-0337 owns the
next user-plus-kernel exception trace trial.
