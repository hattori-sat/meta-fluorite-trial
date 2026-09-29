# FLR-0109 evidence — static present/WSI boundary (2026-09-12)

## Outcome

The fixed Mini build contains three observable present layers: Filament's
outer swapchain wrapper, Filament's platform swapchain implementation, and
the Vulkan `vkQueuePresentKHR` call. The next dynamic probe will distinguish
which layer is actually entered and where the return disappears.

## Fixed metadata

- Receiver revision: `e23d50418e5c96364c4da1c80070c34dda0c0da6`.
- Target recipe: `filament-vk` PV `1.65.4`, SRCREV
  `2a86c0c60ecce9443fc34631570e924721b20b40`.
- Build role: `$BUILD_DIR`.
- TMPDIR role: `$BUILD_TMPDIR`.
- The effective `filament-vk` patch order includes `0182` (outer present
  call), `0183` (queue-present return), `0184` (submit/present semaphore
  ownership), and `0185` (fence status), followed by `0186` and `0187`.

## Static call path

The resolved source contains this path:

```text
VulkanDriver::commit
  -> VulkanSwapChain::present
    -> VulkanPlatformSurfaceSwapChain::present
      -> vkQueuePresentKHR
```

The source locations and markers are:

- `VulkanDriver.cpp:1915`: `swapChain->present(*this)`.
- `VulkanSwapChain.cpp:110`: outer `VulkanSwapChain::present`.
- `VulkanSwapChain.cpp:113`: `FLUORITE_VK_PRESENT_ENTER`.
- `VulkanSwapChain.cpp:162`: `FLUORITE_VK_PRESENT_CALL_BEGIN`.
- `VulkanSwapChain.cpp:166`: `mPlatform->present(...)`.
- `VulkanSwapChain.cpp:168`: `FLUORITE_VK_PRESENT_CALL_RETURN`.
- `VulkanPlatformSwapChainImpl.cpp:361`: platform present function.
- `VulkanPlatformSwapChainImpl.cpp:388`: `FLUORITE_VK_QUEUE_PRESENT_ENTER`.
- `VulkanPlatformSwapChainImpl.cpp:394`: `vkQueuePresentKHR(...)`.
- `VulkanPlatformSwapChainImpl.cpp:396`: `FLUORITE_VK_QUEUE_PRESENT_RETURN`.

The same platform source also contains the existing queue-idle probe before
the neutral queue-present enter marker. Patch `0184` records the submit
return and the semaphore passed to present; patch `0185` records the most
recent fence status in the outer swapchain wrapper.

## Runtime correlation already available

FLR-0108's production run emitted the platform markers
`FLUORITE_VK_QUEUE_PRESENT_ENTER` and `FLR0026_VK_QUEUE_PRESENT_BEGIN`, but
did not emit the queue-present return or outer present markers in the bounded
stream. The resolved source does contain the outer markers, so this is a
real observation gap to resolve with symbol-level breakpoints; it is not yet
evidence that the wrapper is bypassed or that a second binary is loaded.

## First bounded GDB observation

The fixed debug image was started once under the existing Mini `runqemu`/QMP
contract. GDB loaded the guest `.debug` files and stopped one
`flutter-auto` thread at the loader-level `vkQueuePresentKHR` entry:

```text
FLR0109_QUEUE_ENTRY pc=0x7ffff5fde750
=> 0x7ffff5fde750 <vkQueuePresentKHR>: test %rdi,%rdi
#0 vkQueuePresentKHR() from target:/usr/lib/libvulkan.so.1
#1 0x0000555555b2a61f in ?? ()
#2 ... from target:.../libflutter_engine.so
```

The complete bounded stack and command output are retained in the fixed
receiver evidence role as `present-status-serial-2.log`. The probe did not
produce a queue return. Its return-breakpoint implementation used `tbreak`
inside a breakpoint command list; GDB resumed the target and then reported
`Cannot execute this command while the target is running`. This is a
diagnostic harness failure, not evidence of a product fault.

The output contained no outer/platform hit marker. Since the failed probe did
not retain explicit breakpoint-resolution output, the reason is UNKNOWN; the
outer or platform function may have been unresolved, not hit, or both.

## Post-probe QMP evidence

- PPM: `$RECEIVER/evidence/flr0109-r1/present-boundary-late.ppm`
- PPM SHA-256: `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`
- Resolution: `1280x800`
- Native candidate region `[300,80,620,360]`: `0/223200`
- HUD region `[200,100,400,250]`: `0/100000`
- Six QMP frames were retained under
  `$RECEIVER/evidence/flr0109-r1/present-boundary-frames/`; every frame has
  the same PPM SHA-256 as the late capture.
- QMP teardown: `qmp=PASS capabilities=negotiated quit=accepted`,
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

The late black frame was taken after the debugger probe had stopped/ended the
application. It must not be treated as the normal-running production frame;
the prior normal-running production result remains HUD-visible with a black
native region.

## Corrected callback probe attempt

A second QEMU run reused the same fixed image and build/TMPDIR. The first
command file was rejected by the guest harness for exceeding its size limit.
The compressed one-line retry passed the harness, but its generated GDB
settings file contained literal `\\n` separators, so GDB rejected the first
line. A short retry corrected that input and started GDB against the waiting
gdbserver.

GDB then loaded the guest symbols but ended with
`Cannot execute this command while the target is running`; the gdbserver
reported `Error detected on fd 5`. No `FLR0109_*` callback marker was
emitted. The target process set observed during the run was one gdbserver and
one `flutter-auto`. This is a probe-connection/symbol-loading failure, not a
product boundary result.

The r2 QMP capture was retained as
`$RECEIVER/evidence/flr0109-r2/present-return-late.ppm` with SHA-256
`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
Both analyzed regions were black (`0/223200` native and `0/100000` HUD), and
all six video frames were identical. QMP quit and residual cleanup both
passed. Because this capture followed the failed debugger interaction, it is
not a normal-running production visual verdict.

## Normal production strace observation

A third run reused the same fixed image, receiver, build directory, and
TMPDIR. The first start command had the kernel SHA in the rootfs SHA slot and
was rejected before QEMU launch. The corrected command passed preflight and
guest-ready checks, launched exactly one production `flutter-auto`, and was
cleanly torn down through QMP. No second QEMU or application process remained.

The normal-running launch used the installed Example Demo with the existing
Wayland runtime roles and present/scene markers. QMP captured the following
visual evidence before and after a bounded syscall observation:

- Early capture: `$RECEIVER/evidence/flr0109-r3/production-early.ppm`,
  SHA-256 `fe470a10e62a22f3eb0af253b0f61260b5270d7ff79b15e19b77e2dc44e02961`.
- Late capture: `$RECEIVER/evidence/flr0109-r3/production-late.ppm`,
  SHA-256 `25a88c8ce44149eb6a63228efbd125b7aad3e666a1258a88f8b3d5d31da9a0fc`.
- Both captures are `1280x800`; the native candidate region changed `0/223200`
  pixels in both. The HUD region changed `1294/100000` early and
  `1177/100000` late.
- Six late QMP frames were retained and were byte-identical to the late
  capture. This is normal-running evidence, unlike the post-probe black
  captures above.

A bounded `strace -ff -ttt -T -yy` attach covered 39 threads for 20 seconds.
The timeout return `124` was expected for the bounded observation and the
tracer detached cleanly. Event counts were `epoll_wait=1811`, `futex=11910`,
`poll=163`, `recvmsg=102`, and `sendmsg=102`. Wayland fd 3 was active: its
`sendmsg`, `recvmsg`, and `poll` operations returned promptly in the retained
sample. The main thread's `epoll_wait` operations returned immediately.

Selected worker traces showed repeated futex waits of approximately five
seconds on guest TIDs 640 and 699. Other graphics and engine workers also
waited on futexes, but no stack was captured at the wait. This is evidence of
worker synchronization activity, not proof that either TID owns the present
operation.

The application markers in the same window showed:

```text
FLUORITE_VK_SUBMIT_RETURN result=0 signal=0x7f7e50021180
FLUORITE_ENGINE_EXECUTE_ENTER
FLUORITE_VK_PRESENT_ENTER index=0 headless=false
FLUORITE_VK_PRESENT_FLUSH_DONE flushed=true
FLUORITE_VK_PRESENT_WAIT_SEMAPHORE enabled=true
FLUORITE_VK_QUEUE_PRESENT_ENTER index=0 wait=true semaphore=0x7f7e50021180
FLR0026_VK_QUEUE_PRESENT_BEGIN queue=... swapchain=... index=0
```

No queue-present return was emitted. The submit returned `result=0`, and the
same semaphore handle reached present. The run also logged the known OOPS in
guest TID 679 (`FEngine::loop`), which was distinct from the long-futex TIDs.
Therefore the OOPS and futex observations are concurrent evidence only;
causality and the exact blocked owner remain UNKNOWN.

The prompt Wayland IPC weakens the hypothesis that the compositor socket is
simply stuck. The remaining high-value distinction is whether a Filament,
lavapipe, or WSI worker is waiting on a synchronization primitive after the
successful submit and before the queue-present return. No source patch is
justified by this observation alone.

## GDB attach observation

The same fixed image was run once more with the production Example Demo. A
QMP capture was taken before the debugger attach, then `gdbserver --attach`
was connected to the live production PID. The attach succeeded and GDB began
loading the guest debug files. Because the client used the default remote
target file transfer, symbol loading consumed the bounded stopped-process
window. GDB completed an `info threads` view with 19 visible threads and
top-frame names, but the requested all-thread backtrace did not complete
before the QEMU run was ended through QMP.

The completed top-frame view showed:

- the main thread in `__GI___clock_nanosleep`;
- Flutter/engine and four `llvmpipe-*` workers in glibc futex waits;
- Flutter I/O threads in `epoll_wait`; and
- one Flutter worker in `poll`.

The guest process status sampled during the attach showed more target threads
than the completed GDB view. It is UNKNOWN whether this difference was caused
by thread creation timing or by the slow symbol-loading/collection window.
No queue-present return, present-owner source frame, or OOPS causality was
established by this partial attach. The attached process was not left
running under the debugger: QMP quit reported accepted and cleanup reported
zero residual targets and sockets.

This probe changes the diagnostic procedure, not the product hypothesis. The
next GDB attempt must set `sysroot=/` and an explicit local debug-file
directory, disable unnecessary remote symbol transfer, and capture the
thread/top-frame map first. Filament/Vulkan symbols can then be loaded
selectively after the candidate thread is known.

## Lightweight GDB retry with local sysroot

The next run used the same fixed image and a single production launch. Before
the attach, QMP captured
`$RECEIVER/evidence/flr0109-r5/production-before-gdb.ppm` (SHA-256
`4c0a2c42d17780ae661c8bf0a645a125b5235eff92e736a0678c6cde5db7bde1`). The
image was `1280x800`; its native candidate changed `0/223200` pixels and its
HUD region changed `1229/100000` pixels. This is the normal-running visual
result for r5: HUD visible, production native 3D candidate black.

The GDB command set used `set sysroot /`, an explicit
`/usr/lib/debug:/usr/lib/.debug` debug-file directory, automatic shared
library loading, and `set remotetimeout 5`. The attach completed without the
previous long remote-file transfer. GDB enumerated 39 target threads and
executed `thread apply all bt 6`. The thread names included the expected
`JobSystem::loop`, `FEngine::loop`, `llvmpipe-*`, Flutter I/O, disk, and
DartWorker roles. However, the non-current threads reported `PC not available`
and `info sharedlibrary` reported no shared libraries loaded; only the
currently selected thread had a partially resolved libc frame. The resulting
data is not a usable blocked-owner stack.

The server reported `Couldn't reap LWP ... while detaching`, and the target
was not available for a reliable post-detach process check. A later QMP frame
was black in both the native and HUD analysis regions, so it is retained only
as post-debugger cleanup evidence:
`$RECEIVER/evidence/flr0109-r5/production-after-gdb.ppm`, SHA-256
`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
QMP quit still completed with accepted capabilities/quit and zero residual
targets/sockets.

The local-sysroot change is therefore a valid timing improvement, but the
attach mode still cannot expose the required non-current PCs. The next
diagnostic should test a launch-under-gdbserver arrangement or a minimal
register/stack request while keeping the before-GDB QMP frame as the only
normal-running visual verdict. No source patch is justified yet.

## Launch-under-gdbserver fork-following probe

The following run launched the production executable directly under
gdbserver using the same fixed image. GDB connected successfully, but the
`vkQueuePresentKHR` breakpoint was unresolved and remained pending. The
retained GDB output recorded:

```text
Function "vkQueuePresentKHR" not defined.
Breakpoint 1 (vkQueuePresentKHR) pending.
[Detaching after fork from child process 679]
```

The server log recorded a created production process followed by detachment
from process 679. No queue-present entry, return, or owner stack was captured.
The evidence therefore identifies a debugger setup gap: the child process
that is expected to load the Vulkan stack was not kept under the breakpoint
session. The exact launcher/fork ownership remains UNKNOWN.

The run's after-probe QMP image was
`$RECEIVER/evidence/flr0109-r6/after-gdb.ppm` with SHA-256
`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
It was black in both native candidate and HUD regions (`0/223200` and
`0/100000`) and is retained only as post-debugger cleanup evidence. No
normal-running visual verdict is assigned to r6. QMP quit and residual
cleanup both passed.

The next launch-under probe must set `follow-fork-mode parent` and retain
fork/exec events. It must report breakpoint resolution after the production
parent loads `libvulkan`; the auxiliary scanner child must be recorded but not
treated as the render process. Until the parent and the queue-present
boundary are both observed, no source patch is justified.

## Fork topology retry

The next launch-under-gdbserver run enabled `follow-fork-mode child` and
`detach-on-fork off`. The server created production parent PID 646. GDB then
reported:

```text
[Attaching after Thread 646.646 fork to child Thread 678.678]
[New inferior 2 (process 678)]
process 678 is executing new program: /usr/libexec/gstreamer-1.0/gst-plugin-scanner
Cannot execute this command while the target is running.
```

The selected child was the GStreamer plugin scanner, not the production
Flutter/Vulkan parent. No `vkQueuePresentKHR` hit or return was captured. The
run therefore provides process-topology evidence but no present-owner
classification. No normal-running QMP frame was taken in this diagnostic run;
the existing r3/r5 before-debugger captures remain the visual verdict.

The next launch-under procedure must select `follow-fork-mode parent`, retain
fork/exec event output, and verify that the parent loads `libvulkan` before a
pending `vkQueuePresentKHR` breakpoint is considered resolved. No source
patch is justified by the fork retry alone.

## Parent-following multi-inferior retry

The next run changed the GDB policy to `follow-fork-mode parent` while keeping
`detach-on-fork off`. GDB again left `vkQueuePresentKHR` pending and then
reported:

```text
[New inferior 2 (process 678)]
Cannot execute this command while the target is running.
```

The guest process status retained both the gdbserver-managed parent and a
second `flutter-auto` process. No queue-present breakpoint hit or return was
captured. This run therefore shows that a single `continue` is not sufficient
for the observed multi-inferior fork/exec sequence; the debugger client must
advance each event explicitly and record the selected inferior/PID and its
library map before running stack commands.

No normal-running QMP frame was taken in this diagnostic run. The existing
r3/r5 before-debugger captures remain the visual verdict, and no source patch
is justified by r8.

## Normal process-map confirmation

A separate normal production run was started without GDB. The process map
contained exactly one `flutter-auto` PID (632). Its executable maps contained
both `/usr/lib/libvulkan_lvp.so` and the installed Example Demo's
`libflutter_engine.so`, establishing a unique Vulkan/Filament owner candidate
for a normal launch.

QMP captured
`$RECEIVER/evidence/flr0109-r9/production-map.ppm` (SHA-256
`bbc44d98ad15583a8c3f295774939bb7332117b5381e8dea31853869e2bc936a`). The
image was `1280x800`; the native candidate changed `0/223200` pixels and the
HUD changed `1294/100000` pixels. QMP quit and residual cleanup both passed.

This removes the PID ambiguity from the normal production case. The extra
processes seen in the launch-under-gdbserver probes are debugger/startup
procedure artifacts and must not be used to describe ordinary production
topology. The next attach should target only the PID proven to map
`libvulkan_lvp.so`, then request individual candidate-thread stacks.

## Individual-thread attach collection failure

The next run started normal production PID 638 and confirmed
`libvulkan_lvp.so` in its maps. A gdbserver attach and GDB client were then
started for individual candidate-thread stacks. The follow-up serial
connection used to collect the GDB logs failed at
`echo-off-prompt-not-reached`; therefore no GDB backtrace or candidate-thread
classification is available from this run. QMP quit still completed with
accepted capabilities/quit and zero residual targets/sockets.

This is a collection-harness failure, not evidence that the selected PID had
no usable stack. The next attempt must run the bounded GDB client in the same
foreground serial command session and print its logs before the serial
completion marker.

## Facts, inferences, and hypotheses

### Facts

- The authoritative source and effective patch order contain the three-layer
  present path and its markers.
- The prior runtime stream reached platform queue-present enter/begin without
  a recorded return.
- The prior stream did not provide enough evidence to distinguish missing
  outer markers from a logging/path mismatch.

### Inferences

- Breakpoints at the outer wrapper, platform present, and `vkQueuePresentKHR`
  are the smallest next observation that covers the observed gap.

### Hypotheses

1. The active code reaches the platform function through a path that bypasses
   the expected outer wrapper or uses a different loaded copy.
2. The outer wrapper is entered, but the first blocking operation is inside
   platform/loader/WSI before `vkQueuePresentKHR` returns.
3. The known `FEngine::loop` OOPS interrupts the present path or leaves a
   semaphore/fence state that causes the apparent block.

## UNKNOWN

- Which of the three symbols is actually entered in the next production run.
- Whether `vkQueuePresentKHR` itself is reached and returns.
- The blocked thread, syscall, semaphore/fence status, and OOPS causality.
- Whether the failed probe's outer/platform breakpoint specifications resolved
  to the loaded Filament code.
- Whether the callback probe can complete with bounded, selective symbol
  loading before another production observation is attempted.

## r12: synchronized lavapipe wait candidate

- The corrected fixed-image run launched one normal production PID 637. The
  pre-attach QMP-only frame was
  `$RECEIVER/evidence/flr0109-r12/production-before-sync-gdb.ppm`, SHA-256
  `0f48dbb928e85925f54ca4548e014a879a97e653243248623b44374838f7884a`.
  Native candidate pixels were `0/223200`; HUD pixels were `1278/100000`.
- The production log already contained
  `FLUORITE_VK_QUEUE_PRESENT_ENTER` and
  `FLR0026_VK_QUEUE_PRESENT_BEGIN`, but no return/done marker. Low-memory GDB
  attached after that marker and detached with client RC `0`.
- FEngine threads 25, 30, 31, 32, and 33 reached
  `pthread_cond_wait` followed by `/usr/lib/libvulkan_lvp.so` frames. The
  loaded Vulkan build-id was `18eb7b64f7fcae9a4b5ef5bbe1fe58a65944a403`.
  Targeted symbolization resolved the relevant Mesa 24.0.7 frames to
  `cnd_wait` (`threads_posix.c:136`), `lvp_pipe_sync_wait_locked`
  (`lvp_pipe_sync.c:179`, with inline `lvp_pipe_sync_wait` at line 234), and
  `lp_cs_tpool_worker` (`lp_cs_tpool.c:48`).
- The UI thread was in Flutter Engine `epoll_wait`; the selected Wayland
  thread was in `poll` through `libwayland-client.so`. This weakens a simple
  UI or Wayland socket explanation but does not prove the Mesa wait is a
  violated contract.
- Post-detach QMP remained native `0/223200` and HUD `1266/100000`; PPM
  SHA-256 was
  `69a1e939ad70611d780cdd4df4eaaa0acc3643c2fb9597fa44d8e5b396abd33b`.
  QMP quit and residual cleanup passed.

### Classification

Lavapipe/Mesa synchronization is the highest-ranked owner candidate, but the
exact semaphore/command/fence and whether this is a normal worker wait remain
UNKNOWN. The next gate is a same-image pure self-made fixture comparison.

## r11: same-session GDB caused guest OOM

- The first r11 start attempt was rejected before QEMU because the selected
  `oe-init-build-env` pointed at a nonexistent `TEMPLATECONF`. The corrected
  run used the AGL checkout's `external/poky` environment and started one
  QEMU; both start records remain under `$RECEIVER/evidence/flr0109-r11/`.
- Normal production launch passed and selected PID 633, whose maps contained
  `libvulkan_lvp.so`. The QMP-only pre-attach frame is
  `$RECEIVER/evidence/flr0109-r11/production-before-gdb.ppm`, SHA-256
  `b703428e383691143b5d7d792b514ef685ffd006fd2af4c077b17f7076713f15`.
  Native candidate pixels were `0/223200`; HUD pixels were `1288/100000`.
- The combined foreground GDB command completed serial collection, but
  `set auto-solib-add on` loaded enough symbols to exhaust the 2 GiB guest
  with no swap. Kernel OOM evidence shows `gdb` RSS about 600 MiB and
  `flutter-auto` RSS about 1 GiB; the OOM killer terminated PID 633. The GDB
  client timed out with `124`, so no thread stack is accepted as evidence.
- QMP quit and residual cleanup passed. This is a diagnostic-resource
  failure, not evidence of a missing present owner. The low-memory debugger
  procedure is tracked separately in FLR-0110.
