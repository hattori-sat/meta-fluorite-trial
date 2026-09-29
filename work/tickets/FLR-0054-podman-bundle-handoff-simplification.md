# FLR-0054 — Podman mount and bundle handoff simplification

- Status: Done
- Priority: High
- Owner: container + repository + build-host roles
- Created: 2026-09-09
- Depends on: FLR-0052, FLR-0053
- Working log: `work/logs/2026-09-09-flr0054.md`

## Work unit

Make the repeatable Mac-side workflow use the canonical `meta-fluorite-trial`
directory as the mounted source and reduce the committed-clean → bundle → Mini
PC receiver handoff to one guarded entry point.

## Success criteria

- [x] Podman wrapper checks project read/write, AGL read-only, and persistent
  state mounts before Devtool execution.
- [x] The wrapper never creates a source copy, ticket-specific build directory,
  TMPDIR, QEMU, or Podman machine.
- [x] One bundle handoff helper verifies canonical clean state, explicit base/tip,
  bundle integrity/hash, remote hash, and fixed receiver exact tip.
- [x] SSH/SCP values remain local role configuration; no address, hostname,
  account, credential, or personal path enters Git.
- [x] Static tests, privacy, shell, Markdown, and baseline checks pass.
- [x] The helper fails closed when Podman machine/socket or build-host role
  configuration is unavailable.

## Facts / inferences / hypotheses

### Facts

- The existing Podman wrapper already bind-mounts the canonical project root at
  `/workspace/project:rw` and AGL at `/workspace/agl:ro`.
- The existing receiver helper already refuses dirty receivers and active
  BitBake processes, then checks out an exact tip.
- Podman has no machine/socket on the current Mac and the host has low free
  storage, so runtime Podman execution is not yet available.

### Inferences

- The safest simplification is composition around the existing fixed roles,
  not a new provider, volume migration, or per-ticket state tree.

### Hypotheses

1. A mount permission check inside the persistent container will catch source
   and AGL sharing errors before Devtool mutates state.
2. A single bundle helper can preserve the existing receiver safety gates while
   removing repeated manual `git bundle`, `scp`, and remote hash commands.

## Verification plan

1. Run the new contract test before implementation and retain its failure.
2. Add mount permission checks and the one-command bundle handoff helper.
3. Run the same contract test plus repository gates.
4. Exercise only local dry/validation paths unless Podman and build-host role
   readiness are independently PASS.

## UNKNOWN

- Podman machine provisioning and runtime container status remain UNKNOWN.
- Mini PC transfer and authoritative BitBake remain UNKNOWN until the helper is
  run with local role configuration and a committed tip.

## PDCA

### Do

- Keep all raw bundles outside Git; record only role paths, hashes, and results.

### Check

- The RED→GREEN contract test detected missing mount checks, source-copy
  creation, and unsafe bundle/remote behavior before implementation.
- The configured handoff passed twice at the same tip with identical SHA-256 and
  one fixed receiver/inbox artifact.

### Act

- This unit is committed. Return to FLR-0052 clean receiver verification, then
  resume FLR-0050 runtime evidence.
