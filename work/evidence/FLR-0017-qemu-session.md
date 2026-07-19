# FLR-0017 QEMU session evidence index

- Evidence subject: `qemux86-session-flr0017`
- Image identity: `qemux86-artifact-20260405160535`
- Target role: `qemux86-64-macos-tcg`
- Session mode: q35 / TCG multi-thread / 4 vCPU / 2048 MiB / Cocoa + virtio-vga / snapshot disk
- Session artifact locator: `$QEMU_ARTIFACT_ROOT/flr0017-qemu-session.log`
- Session log SHA-256: `0762b170ae9ec08efa5c0692711c31065c8cb3b5366d31f39fb393d3c1544f71`
- Evidence IDs: `E-FLR0017-QEMU-005`, `ev-target-validation-612fdcf462b63a9f6d53`, `ev-target-validation-89d0d234a95761ba762b`

## Case summary

| Case | Verdict | Basis |
| --- | --- | --- |
| boot/service | PASS | AGL compositor, applaunchd, login prompt |
| explicit app launch/readiness | PASS | Fluorite bundle, Vulkan backend, native readiness, event channels |
| render initialization | OBSERVED | Filament initialization and swapchain creation |
| stable 3D render | FAIL | `FEngine::loop` SIGSEGV in `libLLVM.so.18.1` after readiness |
| root cause | UNKNOWN | evidence is consistent with, but does not prove, llvmpipe/LLVM causality |

Raw logs remain outside Git in the role-local QEMU artifact directory. This index contains no personal path, account, hostname, IP, credential, or raw log body.
