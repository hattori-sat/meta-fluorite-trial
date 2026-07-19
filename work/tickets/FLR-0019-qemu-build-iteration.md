# FLR-0019 — QEMU build-to-render iteration

Status: Waiting (FLR-0025 monitored build loop)

## Outcome

Repeat the bounded qemux86 cycle: effective metadata check, BitBake using the existing Mini PC caches, replace only the active QEMU artifacts, launch with the registered snapshot runbook, and classify Fluorite readiness and stable rendering.

## Facts

- The merged `dev-fluorite-demo` runbook requires qemux86-64, TCG, snapshot mode, and a bounded 120-second launch.
- The current Mini PC image attempt failed before image generation at `vkcube:do_package` during `perform_packagecopy`.
- The failure reports pseudo/tar `*at()` unknown-directory errors and cannot create `usr/bin` under the package directory.
- Disk and inode capacity were healthy; no cache deletion or clean task was used.
- Mini PC layer provenance is dirty, so any resulting artifact is not canonical until provenance is resolved.
- `vkcube` is an optional Vulkan diagnostic package in `fluorite-common.inc`, not a Fluorite runtime dependency; its packagecopy failure blocks image assembly.
- The bounded image run `run-7fbfa826928f4ca8` reproduced the same failure at exit 1: `vkcube:do_package` emitted pseudo/tar unknown-directory errors under `usr/share`.

## Inferences

- This build failure is an environment/package staging issue, not evidence of a Fluorite rendering defect.
- Replacing QEMU artifacts is not yet justified because no new image was produced.
- Excluding `vkcube` is a scoped build unblock, but it means Vulkan diagnostic coverage is deferred and must not be reported as PASS.
- With `vkcube` excluded, the image build reached Fluorite demo `do_compile`, but the BitBake worker stalled at Flutter's internal `dart pub --directory . get --example`; direct execution of the same bundle command completed in about seven seconds.

## Hypotheses

1. The pseudo/tar interaction is transient or task-workdir-specific; a bounded `vkcube -c package` retry may succeed without source changes.
2. The pseudo-native/tar combination is persistently incompatible in this checkout; the smallest safe fix is to document/escalate the build environment issue rather than patch Fluorite.

## Unknowns

- Whether a single bounded `vkcube:do_package` retry succeeds after orphaned workers are gone.
- Whether the existing image artifact corresponds to the merged revision.
- Whether the previously observed post-readiness `libLLVM.so.18.1` SIGSEGV persists with a fresh artifact.
- Whether the BitBake worker environment, rather than Flutter source or pub cache, causes the `dart pub get --example` wait.

## Evidence IDs

- `ev-flr0019-bitbake-vkcube-packagecopy-20260719`
- `ev-flr0019-flutter-auto-metadata-20260719`
- `ev-flr0019-flutter-worker-pub-hang-20260719`

## Smallest next action

Remove only the optional `vulkan-tools` image package, retain Vulkan/mesa loader packages and Fluorite runtime unchanged, then rerun the fixed image build. Treat Vulkan diagnostic coverage as deferred and do not report it as PASS.

## PDCA

- Plan: use merged runbook and existing caches; no destructive clean tasks.
- Do: metadata gate passed; package retry reproduced `vkcube:do_package`; image then reached Fluorite `do_compile` but stalled.
- Check: demo compile completed with exit 0, but image failed at `vkcube:do_package`; no deploy artifact was generated and QEMU/scp gates remain blocked.
- Act: apply the smallest image-input exclusion, then repeat image build; do not change Fluorite code or clear caches.
