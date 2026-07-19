# FLR-0020 — Self-contained build workspace bootstrap

Status: In Progress (Plan)

## Outcome

Make `meta-fluorite-trial` the sole project control point for reproducing the AGL/Yocto build workspace on the Linux build role, without depending on the pre-existing `/AGL/trout` checkout. Reuse role-local downloads/sstate caches, but materialize source and build configuration from the tracked fixed revisions.

## Facts

- The repository tracks the fixed AGL manifest, external-layer lock, sanitized build templates, and Fluorite `meta-local` layer.
- `scripts/materialize-build-conf.sh` requires an already populated `$AGL_ROOT` containing `meta-agl`, `external/poky`, `meta-local`, and `meta-vulkan`.
- `scripts/setup-build-host.sh` is check-only and also requires an existing `$AGL_ROOT`; it does not run `repo init`, `repo sync`, or fetch external layers.
- The build configuration templates contain `$AGL_ROOT`-derived paths, so the repository alone cannot currently start BitBake.
- Existing Mini PC builds use a separate AGL checkout with dirty layer state; its provenance is therefore not a canonical reproduction of this repository.
- The qemux86-64 template sets `DL_DIR`, `SSTATE_DIR`, and `TMPDIR` to the role cache roots under `/mnt/yocto/flourite-qemux86-64`; the Raspberry Pi template uses `/mnt/yocto/flourite`.
- The templates set `MACHINE=qemux86-64` or `raspberrypi4-64` and `DISTRO=poky-agl`.
- The tracked baseline identifies Yocto Scarthgap / BitBake 2.8.1, and the fixed Poky revision is pinned in `manifests/agl-trout-fixed.xml`.
- AGL's current Trout documentation describes downloading the AGL software, running `aglsetup.sh`, creating `local.conf`/`bblayers.conf`, and then invoking BitBake; it also documents `SSTATE_DIR` and shared-state mirrors as build configuration inputs.

## Inferences

- The current repository is a source/configuration overlay and evidence system, not yet a self-contained build-workspace bootstrapper.
- A bounded Bash entry point is the smallest useful control surface; MCP should observe/authorize that entry point rather than embed source-fetch logic in domain servers.

## Hypotheses

1. A project-owned bootstrap script can materialize fixed AGL and external layers into a role-local workspace while leaving downloads/sstate in configured cache roots.
2. A full vendoring of all AGL layers into this Git repository is unnecessary and would create excessive storage/integration risk.

## Unknowns

- Whether the fixed manifest is sufficient for the exact active AGL `trout` source tree, including generated workspace layers and local changes.
- Which `repo` version and network credentials are available on the build role.
- Whether the tracked `meta-local` patches apply cleanly to a fresh fixed-revision checkout.

## Evidence IDs

- `ev-flr0020-repo-source-overlay-audit-20260719`
- `ev-flr0020-cache-version-template-audit-20260719`
- `web-agl-trout-build-environment-20260719`
- `web-yocto-scarthgap-bitbake-2.8-20260719`

## Smallest next action

Design a dry-run-first `scripts/bootstrap-build-workspace.sh` contract with explicit source root, build root, cache roots, target, and fixed-revision verification. Do not run source sync or BitBake until the script contract and ticket acceptance criteria are reviewed.

## Acceptance criteria

- A fresh role-local workspace can be created from tracked manifest/locks plus the tracked `meta-local` layer.
- Existing downloads/sstate caches are reused by configuration and are never deleted.
- Dry-run reports all required source/layer/revision inputs without network or filesystem mutation.
- Materialization is explicit, bounded, and refuses unverified or dirty source identities.
- The QEMU iteration script/MCP can invoke the resulting workspace without referencing `/AGL/trout`.
