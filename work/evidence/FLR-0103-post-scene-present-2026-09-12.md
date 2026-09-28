# FLR-0103 evidence — post-scene Vulkan/LLVM present boundary (2026-09-12)

## Outcome

On the same fixed image and one QEMU instance, the self-made fixture completed
the Vulkan present call and produced native 3D pixels. The production Example
Demo reached the same scene-pass and submit boundaries, entered the queue
present call, produced no present-return marker, and later caused a guest
`FEngine::loop` page fault/Oops. The first observed divergent boundary is
therefore inside or below `vkQueuePresentKHR`; the exact source operation and
root cause remain UNKNOWN.

## Static call-chain evidence

The persistent Mac Devtool source was inspected without editing:

```text
FEngine::execute()
  -> VulkanDriver::commit()
    -> VulkanSwapChain::present()
      -> VulkanPlatform::present()
        -> VulkanPlatformSurfaceSwapChain::present()
          -> vkQueuePresentKHR()
```

`VulkanSwapChain::present()` flushes the command queue and obtains the finished
semaphore before calling the platform present function. The platform function
constructs `VkPresentInfoKHR`, calls `vkQueuePresentKHR`, and returns its
`VkResult`. The return marker is immediately after that call, so its absence
does not prove which internal driver instruction faulted, but it does bound the
first missing application boundary.

## Runtime identity

- Documentation/evidence commit: `119fa88ab8a2651d92fa5e721863d2aa61de1ca6`
- Bundle SHA-256: `ef025142ad0af066151453753acf4efbb0b060f97afa415553ba8168c62bd18d`
- Mini receiver tip: `119fa88ab8a2651d92fa5e721863d2aa61de1ca6`
- Fixed image and artifacts: the FLR-0102 rootfs, kernel, qemuboot, receiver,
  build directory, and TMPDIR were reused.
- Runtime role: one QEMU, snapshot rootfs, QMP-first harness, guest Example
  Demo BUNDLE, `app_id=fluorite`, and guest user `agl-driver`.
- QMP evidence root: `$RECEIVER/evidence/flr0103-post-scene-present/`
- Ports: the run used one unique serial/SSH/telnet triplet; no parallel QEMU
  was started.

## Fixture control

Launch controls were:

```text
FLUORITE_NATIVE_PURE_FIXTURE=1
FLUORITE_NATIVE_MINIMAL_GEOMETRY=1
FLUORITE_SCENE_PASS_TRACE=1
FLUORITE_PRESENT_TRACE=1
FLUORITE_DRIVER_LIFECYCLE_TRACE=1
```

- QMP PPM: `fixture-late.ppm`
- PPM SHA-256: `a19d6fe5c82b347b2a5365c11ebe6eddc0faec28dfe0b78faec302f642b67473`
- Native region `[300,80,620,360]`: `41750/223200`, bbox
  `[501,278,278,162]`
- HUD region `[200,100,400,250]`: `6234/100000`, bbox `[200,113,400,237]`
- QMP video: `fixture-frames/`, 6 frames, all hashes unique
- Present trace: queue-present return `result=0` and present-call return
  `result=0` observed repeatedly
- Nonfatal application log: one `Entity(164): Light not found` handler error
  was observed, but fixture present and native pixels continued. It is not a
  sufficient explanation for the production-only failure.

## Production case

Only the neutral trace controls were enabled:

```text
FLUORITE_SCENE_PASS_TRACE=1
FLUORITE_PRESENT_TRACE=1
FLUORITE_DRIVER_LIFECYCLE_TRACE=1
```

- QMP PPM before the post-Oops capture: `production-late.ppm`
- PPM SHA-256: `4ff3dfa92f46a4d5a08f266cd899ae2854d4bc1fb187ae857a51f3960cbd1477`
- Native region `[300,80,620,360]`: `0/223200`, no bounding box
- HUD region `[200,100,400,250]`: `1091/100000`, bbox `[200,113,29,66]`
- QMP video: `production-frames/`, 6 frames, all hashes unique
- Application identity: `Application Id: fluorite`
- Scene trace: BEGIN/END observed for command counts including `552`
- Submit: `FLUORITE_VK_SUBMIT_RETURN result=0` observed
- Present: `FLUORITE_VK_PRESENT_CALL_BEGIN` and
  `FLUORITE_VK_QUEUE_PRESENT_ENTER` observed; no corresponding
  `FLUORITE_VK_QUEUE_PRESENT_RETURN` was observed
- Post-Oops QMP PPM: `production-post-oops.ppm`
- Post-Oops PPM SHA-256:
  `d557bea0fa3c821b800a2941571753069c617bccfe95931e94246df4eacb0554`
- BusyBox-compatible `dmesg` evidence: page fault at approximately
  `298.990626`, `CPU: 2 PID: 747 Comm: FEngine::loop`, RIP
  `0x7effebed2541`, CR2 `0x85787750`

## Guest GDB production run (`gdb-r1`)

This run reused the FLR-0104 debug image and the fixed Mini receiver. It used
one QEMU instance, one `gdbserver`, one `flutter-auto`, and QMP-only frames.
Preflight, QEMU start, guest-ready, and QMP capture passed. The retained
command and serial outputs are under
`$RECEIVER/evidence/flr0103-post-scene-present/gdb-r1/`.

- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`
- GDB loaded the guest `.debug` files for `flutter-auto`, Flutter Engine,
  Mesa/lavapipe, and LLVM. The client did not report a normal
  `Program received signal` stop when the kernel OOPS occurred.
- The retained frame records continued through at least sequence `990` with
  `started=false`; the QMP mid and late frames remained HUD-only. PPM SHA-256:
  `31ba97e46be0d2e81f01c086e1e053aa2ddef66afa26fa6ecaa3dfc979d1f437` and
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- At approximately 347 seconds, the guest kernel reported:
  `BUG: unable to handle page fault for address: 0000000091006750`,
  `CPU: 1 PID: 699 Comm: FEngine::loop`,
  `RIP: 0033:0x7fffee804541`, and
  `CR2: 0000000091006750`.
- `/proc/644/maps` placed the RIP in the executable mapping
  `/usr/lib/libLLVM.so.18.1`, whose executable segment began at
  `0x7fffee51f000` with file offset `0x838000`. The resulting file offset is
  `0xb1d541`.
- Guest `llvm-symbolizer --obj=/usr/lib/libLLVM.so.18.1 0xb1d541` resolved the
  address to `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)` with no
  source line. The result matches the earlier FLR-0030 mapping and identifies
  a symbol boundary, not a root-cause producer.
- `coredumpctl list --no-pager` was empty. This does not distinguish an
  expected kernel-OOPS path from a missing coredump capture and remains
  UNKNOWN.
- A later `addr2line` invocation used for additional symbol inspection caused
  guest OOM at approximately 646 seconds and the kernel killed
  `flutter-auto` with SIGKILL. This is a separate diagnostic-resource failure;
  it must not be conflated with the earlier LLVM OOPS.
- QMP quit was accepted and post-run cleanup reported zero residual target
  processes and zero residual QMP sockets.

### GDB collection interpretation

The debugger tooling is installed and usable, but this failure form is not a
normal signal stop that the batch `continue` command captured. The current
next observation is therefore a breakpoint at the LLVM symbol entry with a
small caller/register capture, while avoiding guest-side broad symbol
inspection and all-thread dumps. The exact source line, caller, and producer
remain UNKNOWN.

## Failed or corrected observations

- The first pixel-analysis invocation passed unsupported `--baseline black`
  arguments and failed. It was not used as evidence. The supported
  `--background 0,0,0` invocation was rerun and its results above are valid.
- A prior log extraction used `tail` after a high-volume camera marker stream
  and omitted the earlier present markers. It was rerun with marker counts and
  line numbers; the focused extraction above is the accepted log evidence.
- The first GDB run loaded the guest debug files but did not receive a normal
  signal-stop backtrace for the kernel OOPS. The later guest `addr2line`
  extraction triggered OOM; both limitations are retained and corrected by
  the next breakpoint-based plan.

## Teardown

- QMP capabilities negotiation and `quit`: PASS
- Residual target processes: `0`
- Residual QMP socket: `0`
- The fixture was stopped using its recorded guest PID before the production
  launch; no second `flutter-auto` was allowed.
- Bundle transfer and receiver update: PASS; the remote bundle hash and exact
  receiver tip match the local handoff result.

## Classification

- 2D HUD path: PASS
- Self-made native 3D and present: PASS
- Production scene draw/command-recording seam: reached and closed
- Production queue-present return: FAIL/not observed
- LLVM symbol boundary: PASS (`libLLVM.so.18.1` / `llvm::CmpInst::isOrdered`)
- Exact source line, caller, and ownership: UNKNOWN
- Product fix: not justified by this evidence unit
