# Mac Devtool Container Reuse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse one persistent Mac-side Docker container and one isolated mini-PC receiver/build state across Fluorite validation runs so repeated ticket validation does not create duplicate containers, receivers, or Yocto state trees.

**Architecture:** Docker Compose owns one deterministic Mac-side container and four deterministic named volumes. The first invocation creates the container with the complete mount and environment contract; later invocations start the stopped container and execute the requested Devtool operation inside it. The mini PC uses one fixed receiver and build directory, updates the receiver to the exact bundle revision, and keeps one TMPDIR while preserving shared caches. Both workflows refuse unsafe path or contract mismatches.

**Tech Stack:** Bash, Docker Compose, Dockerfile, Ubuntu 22.04 Yocto/devtool image, Docker named volumes, Yocto BitBake, shell syntax/privacy checks.

**Spec:** `docs/mac-devtool-bundle-workflow.md`

## Global Constraints

- Mac is used for source editing and Devtool-generated patches; mini PC remains the authoritative image-build host.
- The project layer and AGL source are separate mounts; the AGL source is read-only.
- `build`, `downloads`, `sstate-cache`, and `tmp` use fixed Mac-only named volumes.
- The Mac wrapper rejects image recipes and never invokes `cleanall` or unapproved `cleansstate`.
- Existing source changes are preserved; no mini-PC paths, credentials, hostnames, IP addresses, large logs, or deploy artifacts enter Git.
- Container reuse must not silently reuse a container with a different project, AGL source, image, UID/GID, or volume contract.
- Mini-PC reuse must not modify the canonical checkout and must not move or delete a TMPDIR while a build is active.

---

### Task 1: Define the persistent-container contract

**Files:**
- Create: `scripts/run-mac-devtool.sh`
- Create: `compose.mac-devtool.yaml`
- Create: `tools/yocto-devtool/Dockerfile`
- Create: `tools/yocto-devtool/entrypoint.sh`
- Create: `tools/yocto-devtool/run-devtool.sh`
- Create: `tools/yocto-devtool/run-recipe-task.sh`
- Create: `tools/yocto-devtool/.dockerignore`

**Interfaces:**
- Consumes: `FLUORITE_MAC_PROJECT_ROOT`, `FLUORITE_MAC_AGL_ROOT`, optional image/container/volume variables, and `modify`, `finish`, or `status` arguments.
- Produces: a reusable container named from `FLUORITE_MAC_DOCKER_CONTAINER` and fixed volumes named from `FLUORITE_MAC_DOCKER_VOLUME_PREFIX`; the command runs through `docker exec` after the container is started.

- [ ] **Step 1: Add the Compose file with deterministic defaults.** Define the fixed service/container name `fluorite-mac-devtool`, image `fluorite-yocto-devtool:22.04`, the project and read-only AGL mounts, and the four `fluorite-mac-devtool-*` volumes. Keep image-build commands out of the service command.
- [ ] **Step 2: Add the host wrapper with deterministic defaults.** Define the fixed Compose project, validate absolute source paths, numeric UID/GID, supported Docker names, and forbidden mini-PC paths.
- [ ] **Step 3: Implement first-run creation and later reuse.** Use `docker compose up -d` only when the fixed service is absent, then `docker compose start` for a stopped service and `docker compose exec` for operations. Refuse a contract mismatch instead of creating a second service/container.
- [ ] **Step 4: Add the container-side command allowlist.** Permit only the Devtool operations and recipe-scoped tasks required by the workflow, reject image recipes, source the pinned environment, and keep Yocto state rooted in the named volumes.
- [ ] **Step 5: Run static checks.** Run `bash -n scripts/run-mac-devtool.sh tools/yocto-devtool/*.sh` and the repository shell/privacy checks. Expected result: no syntax errors and no secret/path findings.

### Task 2: Document lifecycle and disk policy

**Files:**
- Modify: `docs/mac-devtool-bundle-workflow.md`
- Modify: `tools/yocto-devtool/README.md`
- Modify: `compose.mac-devtool.yaml`

**Interfaces:**
- Consumes: the persistent-container behavior from Task 1.
- Produces: operator instructions that distinguish `docker stop` from destructive volume deletion and prevent per-ticket container/volume creation.

- [ ] **Step 1: Document first run versus subsequent runs.** Show `docker build` once, the wrapper’s first-run creation, and subsequent `docker start`/`docker exec` reuse.
- [ ] **Step 2: Document inspection commands.** Add read-only commands using `docker inspect`, `docker volume inspect`, and `docker system df -v` to verify reuse and identify reclaimable state before cleanup.
- [ ] **Step 3: Document retention.** Keep the fixed Devtool volumes across tickets; stop the container after work, and delete a volume only after explicit approval and evidence that no active source operation depends on it.
- [ ] **Step 4: Document QEMU artifact retention.** Keep only the current run and required evidence; do not leave each trial’s rootfs/VMDK under `/private/tmp` without an evidence index.
- [ ] **Step 5: Run Markdown link and privacy checks.** Expected result: all links resolve and no personal host/path/IP/credential is recorded.

### Task 3: Reuse the mini-PC receiver and build state

**Files:**
- Create: `scripts/reuse-mini-build-receiver.sh`
- Modify: `docs/mac-devtool-bundle-workflow.md`
- Modify: `work/tickets/FLR-0022-devtool-docker-bundle.md`

**Interfaces:**
- Consumes: `$BUILD_HOST`, `$AGL_ROOT`, `$RECEIVER`, `$BUILD_DIR`, `$TMPDIR`, and a verified Git bundle path supplied by the operator.
- Produces: one receiver checkout at the fixed path, one fixed build directory and TMPDIR, and an exact bundle revision ready for `bitbake`.

- [ ] **Step 1: Add a read-only preflight mode.** Show receiver revision, worktree status, active BitBake processes, filesystem free space, and configured `DL_DIR`, `SSTATE_DIR`, and `TMPDIR` before any update.
- [ ] **Step 2: Add exact bundle update behavior.** Fetch the verified bundle into the fixed receiver, check out the requested tip, and refuse to proceed if the receiver is dirty or a build is active. Never touch the canonical checkout.
- [ ] **Step 3: Reuse the fixed build configuration.** Keep one build directory and one TMPDIR; update only the receiver layer path and exact source revision. Do not create commit-suffixed TMPDIRs for ordinary retries.
- [ ] **Step 4: Add duplicate detection.** List other matching receiver/build/TMPDIR candidates and stop with a report; do not delete them automatically. A separate explicitly approved cleanup command may remove only archived, inactive candidates.
- [ ] **Step 5: Document retention and cleanup.** Retain the current receiver, build state, required evidence, shared downloads, and sstate-cache; archive or remove old candidates only after process and evidence checks.

### Task 4: Verify reuse without building an image

**Files:**
- Modify: `work/logs/2026-08-31-flr0026.md` or the current ticket log selected at execution time

**Interfaces:**
- Consumes: the wrapper and documentation from Tasks 1–2.
- Produces: redacted evidence showing one container ID and unchanged volume names across two wrapper invocations.

- [ ] **Step 1: Run `status` twice.** Record the container ID, status, image, labels, and mounted volume names after each run. Expected result: the ID and volume names are identical.
- [ ] **Step 2: Stop and run `status` again.** Expected result: the same container is started and reused, not replaced.
- [ ] **Step 3: Confirm image recipes are rejected.** Run the wrapper with `agl-ivi-image-flutter`; expected result: rejection before Docker execution.
- [ ] **Step 4: Confirm no image build occurred.** Inspect the command output and container process list; expected result: only the requested Devtool/status command ran.
- [ ] **Step 5: Record Facts, Inferences, Hypotheses, and UNKNOWN separately.** Do not record personal IP addresses, hostnames, absolute personal paths, credentials, or large artifacts.

### Task 5: Commit the workflow improvement

**Files:**
- Modify: all files from Tasks 1–3 that pass validation

- [ ] **Step 1: Run `git diff --check` and repository privacy/shell/Markdown checks.** Expected result: all checks pass.
- [ ] **Step 2: Review the diff for unrelated changes and forbidden artifacts.** Expected result: only the persistent-container workflow, documentation, and redacted evidence are staged.
- [ ] **Step 3: Create a local feature commit.** Use a message explaining that the persistent container and named volumes prevent per-ticket duplication. Do not push or create a PR.
- [ ] **Step 4: Verify the worktree and commit identity.** Expected result: clean worktree, commit hash recorded in the working log, and no deploy artifacts tracked.
