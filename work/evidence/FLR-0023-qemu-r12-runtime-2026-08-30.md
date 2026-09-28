# FLR-0023 — r12/r13 build and QEMU runtime evidence

## Outcome

The self-made fixture is present in the built AOT payload and the complete
image builds successfully. The 12-vCPU QEMU session reaches Vulkan, Filament
initialization, and AOT loading, but the app exits with status 139 before a
visible 3D frame. This is a runtime-crash boundary result, not a 3D display
acceptance.

## Build facts

- Mac feature branch tip used for the bundle: `5cf20514c97f43150455e070d412a8350e94ba8c`.
- Mini-PC receiver resolved to that exact tip and remained clean.
- The r12 bundle SHA-256 was
  `601a4a40906a3db413e37a6e9f100c4a81b99c82504acc67f8be11331db42de7`.
- Fixture recipe `do_patch`: PASS.
- Fixture recipe `do_compile`: PASS.
- Full `agl-ivi-image-flutter`: PASS; 11,748 tasks were attempted and all
  tasks completed successfully.
- The built rootfs SHA-256 was
  `93cc09ba0efd8d6c4148ccb8963ae24890a42fee61492c735283aba0d2fa7298`.
- The built kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- `libapp.so` extracted read-only from the built rootfs contained both
  `flr0023_fixture_cube` and `poGetMinimal3dFixtureScene` markers: PASS.

## Runtime facts

- QEMU profile: qemux86-64, q35, TCG multi-thread, 12 vCPU, 2048 MiB,
  `qemu64` with the fixed SSE feature set, virtio-vga, user networking,
  snapshot disk, and Cocoa display.
- Boot reached the AGL graphical session, compositor start, `applaunchd`,
  and the `agl-driver` login prompt.
- Explicit launch used the registered Fluorite bundle and Wayland display.
- Runtime reached `Application Id: fluorite`,
  `VK_KHR_surface`/`VK_KHR_wayland_surface`, Vulkan API 1.3,
  `FEngine resolved backend: Vulkan`, llvmpipe Mesa 24.0.7 / LLVM 18.1.8,
  `All systems initialized`, and `lit.filamat` loading.
- The app then terminated with exit status 139; the kernel recorded a
  `flutter-auto` segmentation fault. The QEMU window capture was black.
- The 12-vCPU window evidence is stored outside Git at
  `$QEMU_ARTIFACT_ROOT/flr0023-r12-qemu-window-12vcpu.png`; its SHA-256 is
  `6f003117950dae2755ea91856373950580bfd95e2cd15ad46518b19046d30b19`.
- The same crash boundary was also observed with the 4-vCPU runbook profile;
  it is not limited to the required 12-vCPU setting.

## Verdicts

| Boundary | Verdict | Evidence |
| --- | --- | --- |
| Build / package / AOT fixture inclusion | PASS | recipe tasks, full image, AOT marker scan |
| Boot / graphical session | PASS | serial boot and AGL session markers |
| Vulkan / Wayland initialization | PASS | instance extensions, device and API markers |
| Filament engine initialization | OBSERVED | backend, feature level, system initialization |
| Native entity/renderable/frame completion | UNKNOWN | no ordered completion markers before crash |
| Child Wayland attach/commit | UNKNOWN | no child-surface protocol evidence |
| Visible 3D pixel change | FAIL for this session | QEMU window stayed black |

## Final r13 revision revalidation

- The final reviewed feature revision was `4e76209ed778c4525075fb4e34bfffcd04bba590`.
- The r13 bundle was created on the Mac, verified before transfer, and received
  into a clean isolated mini-PC receiver at the exact same revision.
- The mini-PC reran fixture `do_patch`, fixture `do_compile`, and the complete
  `agl-ivi-image-flutter` build. All 11,748 attempted tasks succeeded.
- The r13 rootfs SHA-256 was
  `adf8a9497849a1e1c88b54b343a0772b3b3b8fdcbf3dfb62845e01a40d5c6f91`.
- The r13 kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- The r13 image qemuboot SHA-256 was
  `d01d9f726fcb2ac2ceccb4d186835100d9a549e04215f67d8a7da56715763956`.
- Mac-side hashes matched the mini-PC hashes after transfer.
- The final r13 QEMU run used q35, TCG multi-thread, 2048 MiB, 12 vCPU,
  qemu64 with the fixed SSE feature set, virtio-vga, snapshot disk, and Cocoa.
  Guest boot explicitly reported 12 CPUs and reached the AGL graphical
  session.
- Explicit `agl-driver` launch again reached Vulkan/Wayland, llvmpipe Mesa
  24.0.7 / LLVM 18.1.8, `All systems initialized`, and `lit.filamat` loading.
- `flutter-auto` again terminated with status 139 before a visible 3D frame or
  ordered native entity/renderable/frame-completion evidence. No child-surface
  attach/commit or pixel acceptance was observed.

The r13 run therefore reconciles the runtime result with the final reviewed
revision and shows that the QEMU-only quality scope correction does not move
the crash boundary. The exact crashing native symbol remains UNKNOWN.

## Inferences

- The fixture is not absent from the payload: its AOT markers are present and
  the runtime reaches native Filament initialization.
- The first unresolved boundary is after engine/system initialization and
  before visible 3D acceptance.
- The evidence is consistent with a llvmpipe/LLVM or native plugin crash, but
  does not prove the root cause.

## Hypotheses

1. The llvmpipe/LLVM path or a native Filament plugin operation crashes while
   creating or uploading the fixture material. Prediction: a software-renderer
   or native-backtrace diagnostic will fail at the same post-`lit.filamat`
   boundary.
2. A platform-runner/ECS ordering race remains after system initialization.
   Prediction: a run with native creation/frame markers enabled will show an
   incomplete ordering before the crash.
3. The AOT fixture is valid but the AGL normal-window/WSI path fails before
   presentation. Prediction: native entity and frame completion will appear
   without a child Wayland commit or pixel change.

## UNKNOWN / next action

- Exact crashing native frame and whether it is LLVM, Filament, or the
  platform-view plugin are UNKNOWN.
- Entity/renderable/frame-completion and child Wayland attach/commit remain
  UNKNOWN because the process crashes first.
- Next smallest action: collect a symbolized backtrace or add a bounded
  post-material diagnostic around native entity creation, then rerun the same
  12-vCPU profile. Do not close FLR-0023 as a display PASS.
