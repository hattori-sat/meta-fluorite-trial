# FLR-0107 evidence — Gallivm/LLVM input correlation (2026-09-12)

## Outcome

The bounded observation identifies the observed Gallivm call as shared Vulkan
device-initialization work, not a production-scene-specific draw operation.
The call stack is `lvp_CreateDevice` →
`llvmpipe_create_texture_handle` → `compile_sample_function` →
`gallivm_compile_module` → `LLVMRunPasses`. Both pass invocations returned
normally. The later `isOrdered+1` OOPS occurred after GDB detached in a
different `FEngine::loop` thread, so its causal relation remains `UNKNOWN`.
No LLVM/Mesa patch is justified by this unit. Production native 3D remains
`0/223200`.

## Runtime identity

- Image role: FLR-0104 debug image
- Layer revision in the fixed Mini receiver: `7334066615b361cfb8e55dba3d8af1519b301dec`
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Qemuboot SHA-256:
  `ba6711550d96677f66e99f3a06af308a61c1e58a7b776f7489b42c8cc470136d`
- Evidence directory:
  `$RECEIVER/evidence/flr0107-r4/`
- Run contract: one QEMU, one guest `flutter-auto` under one GDBserver,
  bounded GDB, QMP-only capture, and QMP teardown.

## Static facts

- Effective Mesa recipe: `24.0.7`, `gallium-llvm`, `vulkan`, and `wayland`
  enabled; `llvm` and `llvm-native` are dependencies.
- The project layer does not append or patch Mesa. The resolved Mesa appends
  are from the existing AGL/SELinux layers.
- The build uses the fixed role `DL_DIR`; the expanded Mesa source was removed
  by `rm_work`, so the exact `mesa-24.0.7.tar.xz` in that DL_DIR was read
  without changing the build tree.
- Mesa tarball SHA-256:
  `7454425f1ed4a6f1b5b107e1672b30c88b22ea0efea000ae2c7d96db93f6c26a`
- In `lp_bld_init.c`, `gallivm_compile_module()` calls
  `LLVMRunPasses(..., "default<O0>", ...)` first, then calls
  `LLVMRunPasses(...,
  "sroa,early-cse,simplifycfg,reassociate,mem2reg,instsimplify,instcombine<no-verify-fixpoint>", ...)` at line 620.

## Dynamic GDB evidence

The first Gallivm entry was:

```text
FLR0107_GALLIVM_ENTRY hit=1 pc=0x7fffed40ea30
=> 0x7fffed40ea30 <gallivm_compile_module>: push %rbp
FLR0107_GALLIVM_REGS rdi=0x555558558190 rsi=0x55555855b568 rdx=0x55555855b568 rcx=0x1
#0  gallivm_compile_module (...) at lp_bld_init.c:558
#1  compile_function (...) at lp_texture_handle.c:209
#2  compile_sample_function (...) at lp_texture_handle.c:487
#3  compile_sample_functions (...) at lp_texture_handle.c:600
#4  llvmpipe_register_texture (...) at lp_texture_handle.c:665
#5  llvmpipe_create_texture_handle (...) at lp_texture_handle.c:66
#6  lvp_CreateDevice (...) at lvp_device.c:1546
```

The two `LLVMRunPasses` entries used the same module/target/options pointers:

```text
FLR0107_RUNPASSES_ENTRY hit=1 pc=0x7ffff167bdc0
FLR0107_RUNPASSES_REGS rdi=0x555556a62800 rsi=0x7fffffffc2f0 rdx=0x55555855c700 rcx=0x555556a45690
0x7fffffffc2f0: "default<O0>"
FLR0107_RUNPASSES_ENTRY hit=2 pc=0x7ffff167bdc0
FLR0107_RUNPASSES_REGS rdi=0x555556a62800 rsi=0x7fffffffc2f0 rdx=0x55555855c700 rcx=0x555556a45690
0x7fffffffc2f0: "sroa,early-cse,simplifycfg,reassociate,mem2reg,instsimplify,instcombine<no-verify-fixpoint>"
```

The second call reached the caller's post-call instruction and the bounded
GDB detached:

```text
FLR0107_RUNPASSES_RETURN pc=0x7fffed40eb6e rax=(nil)
=> ... <gallivm_compile_module+318>: mov %r12,%rdi
[Inferior 1 (process 645) detached]
```

The complete guest extraction is retained at
`$RECEIVER/evidence/flr0107-r4/gallivm-extract-serial.log`.

## Runtime correlation

- The GDB call chain ends at `lvp_CreateDevice`, which identifies the
  observed Gallivm work as lavapipe/llvmpipe device initialization and
  texture-handle setup.
- The observed `LLVMRunPasses` calls reached their return path; no GDB-side
  error return or stop occurred in this bounded interval.
- The guest later reported:

  ```text
  BUG: unable to handle page fault for address: 00000000913d5750
  Oops: 0000 [#1] PREEMPT SMP NOPTI
  CPU: 3 PID: 748 Comm: FEngine::loop
  RIP: 0033:0x7fffee804541
  CR2: 00000000913d5750
  ```

- At the focused sample, one `flutter-auto` remained under one `gdbserver`,
  with RSS `1142020 kB`. Guest memory was
  `MemTotal=2026992 kB`, `MemFree=21048 kB`, `MemAvailable=608824 kB`, and
  `SwapTotal=0 kB`.
- The exact LWP identity of the normal GDB breakpoint was not emitted by this
  command file; it is `UNKNOWN`. The OOPS TID/comm and the GDB inferior PID
  are retained above and are not treated as same-invocation proof.

## QMP visual evidence

- QMP PPM:
  `$RECEIVER/evidence/flr0107-r4/gallivm-boundary-late.ppm`
- PPM SHA-256:
  `fa62faded438fafc8ef8825ee10e957c6e87a3f7e9594eaffaf2bc357d4f81f8`
- Resolution: `1280x800`
- Native candidate region `[300,80,620,360]`: `0/223200` changed pixels;
  bounding box `null`
- Focused HUD region `[200,100,400,250]`: `1264/100000` changed pixels;
  bounding box `[200,113,29,66]`
- Visual result: HUD/performance controls remain visible and the central
  native 3D region remains black.

## Teardown evidence

```text
qmp=PASS capabilities=negotiated quit=accepted
cleanup=PASS residual_targets=0 residual_qmp=0
```

The QMP socket was absent after teardown and no QEMU, GDBserver, or
`flutter-auto` target remained.

## Hypothesis decision

| Hypothesis | Observation | Decision |
| --- | --- | --- |
| Invalid production LLVM input causes this Gallivm call to fail | Shared `lvp_CreateDevice` stack; both pass strings are expected; second call returns | Rejected for this observed call |
| The later OOPS is unrelated control-flow/memory corruption | OOPS occurs later at `isOrdered+1` in `FEngine::loop`; same invocation is not proven | Supported, not proven |
| Resource pressure contributes to the OOPS | Memory is low after the long run, but no pressure-to-fault causal trace exists | UNKNOWN |

## Classification

- Mesa/Gallivm static call contract: PASS
- Bounded Gallivm entry and pass identification: PASS
- Bounded pass return: PASS
- Production-specific LLVM fault cause: UNKNOWN / not established
- Production native 3D pixels: FAIL (`0/223200`)
- 2D HUD pixels: PASS
- Source/image fix: not justified

## Next gate

FLR-0108 will target the production-specific graphics-pipeline boundary
(`vkCreateGraphicsPipelines`/draw ownership) and compare it with the existing
positive fixture evidence. It must determine whether the first remaining
divergence is pipeline creation, command execution, or present before any
source patch is proposed.
