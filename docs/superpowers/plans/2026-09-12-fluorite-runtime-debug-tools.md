# Fluorite Runtime Debug Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Fluorite validation image reproducibly contain the runtime debuggers, syscall/profiling tools, coredump utilities, LLVM symbolizer, and targeted graphics/runtime debug symbols needed for the production 3D fault investigation.

**Architecture:** Add a project-owned Yocto packagegroup and include it from the shared Fluorite image include. Keep the standard AGL debug features as an existing baseline, but make the required packages explicit so the project layer remains the source of truth. Use targeted `-dbg` packages for the Flutter/Filament/Mesa/LLVM stack instead of enabling `dbg-pkgs` globally.

**Tech Stack:** Yocto Project Scarthgap, BitBake, AGL `agl-ivi-image-flutter`, `meta-fluorite-trial`, Git bundle handoff, QEMU guest runtime checks.

**Spec:** `work/tickets/FLR-0104-runtime-debug-tools.md`

## Global Constraints

- Use the canonical `meta-fluorite-trial` checkout and run its repository assertion before mutation.
- Keep one `In Progress` ticket and one Mini build/TMPDIR; do not create a new receiver, container, or QEMU instance.
- Use Yocto standard packagegroup/image integration; no hand-generated source patch is applicable to this image-configuration change.
- Do not delete `downloads`, `sstate-cache`, or active `TMPDIR`; do not run `bitbake -c cleanall`.
- Commit locally, do not push, and transfer the exact commit through the existing bundle helper.

---

## Execution status

The plan was executed inline on 2026-09-12. The project packagegroup was
implemented, the authorized baseline lock was updated, the full Mini image
build passed, and one QMP-first guest tool probe plus teardown passed. The
production 3D run remains with FLR-0103 because this plan establishes tooling
readiness rather than product behavior.

### Task 1: Record the current tool gap and package providers

**Files:**
- Create: `work/tickets/FLR-0104-runtime-debug-tools.md`
- Create: `work/logs/2026-09-12-flr0104.md`
- Create: `work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: the fixed Mini image and its existing BitBake metadata.
- Produces: a ticket-scoped baseline listing actual rootfs tool paths, Yocto providers, and selected debug packages.

- [ ] **Step 1: Verify the canonical repository and current ticket state**

Run:

```sh
bash scripts/assert-canonical-repository.sh
git status --short --branch
```

Expected: the canonical check passes and no unrelated source change is overwritten.

- [ ] **Step 2: Query effective image metadata and rootfs paths on `$BUILD_HOST`**

Run the existing fixed build environment and record the effective `IMAGE_FEATURES`, `IMAGE_INSTALL`, `MACHINE`, `TMPDIR`, and the exact presence/absence of `/usr/bin/gdb`, `/usr/bin/coredumpctl`, `/usr/bin/llvm-symbolizer`, `/usr/bin/strace`, `/usr/bin/perf`, and `/usr/bin/eu-stack`.

Expected: the current image has the ordinary debug tools and lacks `llvm-symbolizer`; `clang` owns `/usr/bin/llvm-symbolizer` in the locked metadata.

- [ ] **Step 3: Add the package provider and evidence to the ticket**

Record the two explanations that were compared: relying on AGL `tools-debug`/`packagegroup-agl-core-devel`, or explicitly owning a project packagegroup. Select the project packagegroup because the first option already produced an incomplete tool set in the measured image.

- [ ] **Step 4: Commit the ticket setup**

```sh
git add TASKS.md work/tickets/FLR-0104-runtime-debug-tools.md work/logs/2026-09-12-flr0104.md work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md
git commit -m "docs: open FLR-0104 runtime debug tools"
```

### Task 2: Add the project-owned runtime debug packagegroup

**Files:**
- Create: `layers/meta-fluorite-trial/recipes-platform/packagegroups/packagegroup-fluorite-runtime-debug.bb`
- Modify: `layers/meta-fluorite-trial/conf/include/fluorite-common.inc`
- Create: `tests/test_runtime_debug_packagegroup.py`

**Interfaces:**
- Consumes: BitBake package providers `gdb`, `gdbserver`, `strace`, `perf`, `elfutils`, `binutils`, `systemd`, and `clang`.
- Produces: `packagegroup-fluorite-runtime-debug` in the shared image include, plus targeted `-dbg` dependencies for Mesa, Flutter, and Filament.

- [ ] **Step 1: Assert the expected project-owned package list**

Run:

```sh
python3 -m unittest tests.test_runtime_debug_packagegroup -v
```

Expected before implementation: FAIL because the packagegroup and image include entry do not exist.

- [ ] **Step 2: Implement the packagegroup**

Use `inherit packagegroup` and an explicit `RDEPENDS:${PN}` containing `gdb`, `gdbserver`, `strace`, `perf`, `elfutils`, `binutils`, `systemd`, `clang`, `clang-dbg`, `mesa-dbg`, `flutter-auto-dbg`, `flutter-engine-dbg`, and `filament-vk-dbg`. Add only `packagegroup-fluorite-runtime-debug` to `fluorite-common.inc`; do not enable global `dbg-pkgs`.

- [ ] **Step 3: Run the focused test**

```sh
python3 -m unittest tests.test_runtime_debug_packagegroup -v
```

Expected: PASS for image inclusion, required runtime tools, targeted symbols, and the absence of a global debug-symbol expansion.

- [ ] **Step 4: Check the layer diff**

```sh
git diff --check
git diff -- layers/meta-fluorite-trial/conf/include/fluorite-common.inc layers/meta-fluorite-trial/recipes-platform/packagegroups/packagegroup-fluorite-runtime-debug.bb tests/test_runtime_debug_packagegroup.py
```

Expected: only the packagegroup, one shared image include line, and its focused test are changed.

- [ ] **Step 5: Commit the implementation**

```sh
git add layers/meta-fluorite-trial/conf/include/fluorite-common.inc layers/meta-fluorite-trial/recipes-platform/packagegroups/packagegroup-fluorite-runtime-debug.bb tests/test_runtime_debug_packagegroup.py
git commit -m "feat: include Fluorite runtime debug tools"
```

### Task 3: Run the authoritative Mini metadata and image gates

**Files:**
- Modify: `work/logs/2026-09-12-flr0104.md`
- Modify: `work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md`

**Interfaces:**
- Consumes: the exact layer Git bundle at the implementation commit.
- Produces: verified receiver revision, effective image metadata, successful image build, and a new rootfs artifact identity.

- [ ] **Step 1: Bundle and transfer the exact layer revision**

Run the existing `scripts/handoff-fluorite-bundle.sh <base> <tip>` with the fixed role variables. Record the bundle SHA-256 and the Mini receiver exact tip.

- [ ] **Step 2: Check metadata before a long build**

On the existing build directory, run `bitbake -e agl-ivi-image-flutter` and record `IMAGE_INSTALL` containing `packagegroup-fluorite-runtime-debug`, plus `bitbake-layers show-recipes packagegroup-fluorite-runtime-debug`.

Expected: the project packagegroup resolves from `meta-fluorite-trial` and the effective image package list contains it.

- [ ] **Step 3: Build the image using the existing cache/TMPDIR**

Run the existing progressive gates: packagegroup parse/provider resolution, `bitbake -c do_rootfs -f agl-ivi-image-flutter` only if the normal image task requires it, then `bitbake agl-ivi-image-flutter`. Do not clean caches or create another TMPDIR.

Expected: the image completes and produces a new exact rootfs/qemuboot identity.

- [ ] **Step 4: Record the first actionable failure or successful gates**

Update the log and evidence index with task names, exit results, artifact size/SHA-256, and disk-space observations. Keep failures as evidence and do not declare runtime readiness from a metadata-only pass.

### Task 4: Verify the tools inside the new image

**Files:**
- Modify: `work/tickets/FLR-0104-runtime-debug-tools.md`
- Modify: `work/logs/2026-09-12-flr0104.md`
- Modify: `work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md`

**Interfaces:**
- Consumes: the new rootfs and qemuboot from Task 3.
- Produces: guest-side command evidence for tools, symbols, coredump configuration, and clean QMP teardown.

- [ ] **Step 1: Start one QEMU with the new exact image**

Run `qemu-runtime-harness.sh preflight`, `start`, and `guest-ready` using the fixed evidence role and one unused port triplet. Reject SHA mismatch or residual process/socket state.

- [ ] **Step 2: Collect bounded guest tool evidence**

Check `command -v gdb gdbserver coredumpctl llvm-symbolizer strace perf eu-stack addr2line readelf`, `gdb --configuration`, `llvm-symbolizer --version`, `coredumpctl list --boot --no-pager`, `/proc/sys/kernel/core_pattern`, and `ulimit -c` through the existing serial/SSH contract.

Expected: all requested commands resolve; coredumpctl and systemd-coredump are usable; LLVM symbolizer reports its version; core collection configuration is recorded without claiming a core exists.

- [ ] **Step 3: Capture one production diagnostic run only if the tool gate passes**

Run the existing production Example Demo once with neutral trace flags, collect only the focused app log, kernel tail, process maps, and one QMP frame. Use GDB attach or `gdbserver` only during the short reproduction window.

- [ ] **Step 4: Teardown and classify**

Send QMP `quit`, verify `residual_targets=0` and `residual_qmp=0`, then classify each tool and symbol package as PASS/FAIL/UNKNOWN. Do not mark the production 3D goal complete from tooling readiness.

### Task 5: Close the tooling unit and hand off the next 3D diagnosis

**Files:**
- Modify: `TASKS.md`
- Modify: `work/tickets/FLR-0104-runtime-debug-tools.md`
- Modify: `work/logs/2026-09-12-flr0104.md`
- Modify: `work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md`

**Interfaces:**
- Consumes: all prior gate results and QMP teardown evidence.
- Produces: a closed or Waiting FLR-0104 ticket and a precise next ticket for FLR-0103 fault mapping.

- [ ] **Step 1: Update PDCA and the evidence index**

Record Facts, Inferences, Hypotheses, UNKNOWN, the package list, image identity, tool output, QMP frame hash, and teardown result. If any required tool or runtime check is missing, keep the ticket Waiting.

- [ ] **Step 2: Run repository verification**

```sh
make verify
```

Expected: canonical, privacy, shell, Python, MCP, Markdown, file-size, and QEMU harness gates pass.

- [ ] **Step 3: Commit the completed documentation/evidence**

```sh
git add TASKS.md work/tickets/FLR-0104-runtime-debug-tools.md work/logs/2026-09-12-flr0104.md work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md
git commit -m "docs: record FLR-0104 debug tooling validation"
```

- [ ] **Step 4: Transfer the final exact tip to Mini**

Run the fixed bundle helper for the documentation commit and record the remote bundle hash and receiver tip. Do not push to the remote Git repository.
