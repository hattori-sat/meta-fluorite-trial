# Fluorite development environment contract

This is the short reference for resuming the Fluorite investigation after a
context change. Values that identify a person, host, address, or credential are
local-only and are supplied through environment variables.

## Roles

| Role | Owns | Repository/build rule |
| --- | --- | --- |
| `$MAC_VALIDATION_HOST` | canonical repository, Devtool source editing, local checks, QEMU/QMP evidence | never runs the authoritative full image build |
| `$MAC_DEVTOOL_RUNTIME` | one persistent Docker or Podman Devtool container | reuses one source bind, one build state, and one cache set |
| `$BUILD_HOST` | Mini PC authoritative BitBake and image artifacts | receives a verified Git bundle into an isolated receiver |
| `$TARGET` | QEMU or approved device runtime | produces runtime logs and QMP-only visual evidence |

## Canonical source

- Project: `meta-fluorite-trial`.
- Source-of-truth files: `layers/meta-fluorite-trial`, `TASKS.md`,
  `work/tickets`, `work/logs`, `work/evidence/*.md`, manifests, and docs.
- Raw QMP images/videos, rootfs/deploy files, bundles, and Devtool scratch are
  kept outside Git; their role path, hash, and result belong in the ticket/log.
- Work must pass `bash scripts/assert-canonical-repository.sh` before mutation.

## Evidence and ticket naming

`FLR0026` (also written `FLR-0026`) is a legacy namespace from the first
Fluorite 3D-display experiments. Its tickets, patch history, runtime markers,
and evidence directories are retained for provenance and must be treated as
read-only historical references. New work must not create another directory,
environment variable, runtime marker, or log under that namespace.

Current work uses the active ticket directory or a neutral Fluorite name, for
example `work/logs/2026-09-11-flr0084.md`, `work/evidence/flr0084/`, or
`FLUORITE_*` diagnostic controls. If an old run is cited, record it as legacy
evidence and link to the original ticket; do not copy its identifier into a
new experiment.

The Mini PC's old receiver artifacts were retired from active paths on
2026-09-11. The current handoff uses only the fixed receiver and inbox roles;
historical old-run bundles are recoverable under the neutral
`archive/legacy-runtime-2026-09-05/` archive. Do not create a per-ticket
receiver directory or reuse the retired namespace.

On 2026-09-12, stale Git worktree registrations in the separate legacy
`tcna-packages` clone were pruned after their target temporary directories had
already disappeared. The historical FLR0026 branches remain only as source
provenance; no FLR0026 worktree is an active workspace. New work uses the
canonical `meta-fluorite-trial` checkout and the current ticket/evidence
names.

## Mac container contract

Both providers use the same logical contract:

| Contract item | Container path / role |
| --- | --- |
| canonical project bind | `/workspace/project` read-write |
| AGL/Yocto source bind | `/workspace/agl` read-only |
| Devtool state bind | `/workspace/state` from one fixed host working directory |
| build state | `/workspace/state/build` |
| downloads | `/workspace/state/downloads` |
| sstate | `/workspace/state/sstate-cache` |
| TMPDIR | `/workspace/tmp` as one container-private tmpfs scratch area |
| Devtool user | host `FLUORITE_MAC_DEVTOOL_UID:GID`; container entrypoint may be root only for ownership setup, BitBake runs as host UID/GID |
| allowed operations | `status`, `modify`, `finish`, and recipe-scoped tasks |

Docker uses the existing `compose.mac-devtool.yaml` and
`scripts/run-mac-devtool.sh` contract only as a retained fallback, including
its legacy named state volumes. Podman is the current provider: it uses the
same `tools/yocto-devtool/Dockerfile` and the direct wrapper
`scripts/run-podman-devtool.sh`; it does not require `podman-compose`.
The Podman wrapper mounts the existing host working directory as one
`/workspace/state` bind and never creates a named volume or a second host
working directory. The project/build/download/sstate state remains in that
single bind. Yocto's `TMPDIR` is the one container-private `/workspace/tmp`
tmpfs: it is scratch space for case-sensitive paths, FIFOs, Unix sockets, and
xattrs, not a per-ticket state tree. The wrapper repairs only ownership of the
fixed state bind, then verifies that tmpfs and probes a non-root FIFO plus a
nested `cp --preserve=xattr`; if either fails, it stops before Devtool.
The Podman machine is configured with `selinux=0` for this development VM and
the container uses `label=disable`; this removes only the development-provider
labeling boundary. It does not change the SELinux feature in the target AGL
image or the runtime security policy on the Mini PC.
On container startup it also removes only stale
`self-install/meta-flutter` entries left by the old wrapper, keeping the fixed
`external/meta-flutter` layer selected by AGL. Each wrapper checks that the
project mount is read/write, AGL is read-only, and the state paths used by
Devtool are writable before running.

## Local variables

Set these in an ignored shell file or the current shell; never commit values:

```sh
export FLUORITE_MAC_PROJECT_ROOT="$PWD"
export FLUORITE_MAC_AGL_ROOT="<local AGL checkout>"
export FLUORITE_MAC_DEVTOOL_UID="$(id -u)"
export FLUORITE_MAC_DEVTOOL_GID="$(id -g)"
export FLUORITE_MAC_DEVTOOL_STATE_ROOT="<fixed local Devtool state directory>"
export BUILD_HOST="<local build-host role>"
export BUILD_BUNDLE_INBOX="<fixed build-host bundle inbox>"
export BUILD_RECEIVER="<fixed build-host receiver>"
export BUILD_DIR="<fixed build directory>"
export BUILD_TMPDIR="<fixed TMPDIR>"
export AGL_ROOT="<local build-host AGL checkout>"
```

## Provider selection and recovery

1. Run `make verify` and inspect `TASKS.md`/the current ticket.
2. Docker: do not start Docker Desktop when Podman is available. Its old Mac VM
   may be removed only after explicit operator approval and exact target
   inspection; never remove the Podman machine or fixed state.
3. Podman one-time prerequisite: if no backend is running, the operator may
   create and start exactly one rootful machine outside the wrapper. The
   validated Mac profile is 8 GiB disk, 2 CPUs, 4 GiB memory, 1 GiB swap, and
   user-mode networking. The project wrapper never creates, starts, stops, or
   removes that machine. Keep the backend-owning terminal/session alive on
   hosts that reap detached machine processes.
4. Set `FLUORITE_MAC_DEVTOOL_STATE_ROOT` to one fixed local working directory,
   build the same image once with `podman build -t
   fluorite-yocto-devtool:22.04 tools/yocto-devtool`, then run
   `scripts/run-podman-devtool.sh status` twice. If `podman info` fails, stop
   with UNKNOWN; do not create a second machine, container, or state root.
   The wrapper canonicalizes `/tmp` to the host's real `/private/tmp` path before
   comparing the existing container label, so a spelling difference is not a
   reason to recreate the container.
   The `status` operation is a bounded observational probe: it checks the
   existing container and bind mounts without scanning the persistent downloads
   tree or rewriting BitBake configuration. Ownership repair remains part of
   real Devtool operations only.
5. Verify the container ID, canonical source bind, read-only AGL bind, and the
   single state bind are unchanged. The wrapper also verifies that build,
   downloads, and sstate remain on that host filesystem, repairs stale
   ownership, and performs non-root FIFO/xattr probes in the one
   container-private `/workspace/tmp` tmpfs; a failed probe is a provider error,
   not a reason to create another state tree. Use `modify`/`finish` only through
   the wrapper.
   The first ownership repair creates one marker in the state bind; later calls
   skip the full tree scan unless `FLUORITE_MAC_DEVTOOL_REPAIR_STATE=always` is
   explicitly set. Devtool operations are bounded to 300 seconds by default,
   and a stale `devtool`/`bitbake-server` process causes the next call to fail
   closed with its exact PID list.
6. For every source patch: Devtool source edit → source commit → `devtool finish
   --mode patch` → layer registration → local layer commit → Git bundle → Mini
   PC receiver verification → progressive BitBake → QMP runtime evidence.
7. After the layer commit, use `scripts/handoff-fluorite-bundle.sh <base> <tip>`
   to create one fixed active bundle, send it, verify its remote hash, and update the
   fixed receiver. Do not manually repeat `scp` plus receiver checkout.
8. For the official QEMU loop, use `scripts/qemu-runtime-harness.sh`. Run
   `preflight` before runqemu, then `guest-ready --ssh-port ...` until the
   guest advertises an SSH banner, and use guest SSH for app launch when the
   serial prompt is not available. Run `serial-login` only after the exact
   prompt is available, `summary` for selected markers, and `qmp-quit` for
   negotiated teardown. `serial-login` nudges the getty with one newline
   before waiting for the exact prompt, so a late-attached serial client does
   not silently miss the login banner. For a command whose exit status and
   output are evidence, use `serial-exec` on the Mini host; it keeps one serial
   connection, disables terminal echo before the command, writes the bounded
   output to the run directory, and uses an echo-safe completion marker. The
   serial/QMP `localhost` endpoints belong to the host running QEMU, not the
   Mac controller. Keep the qemuboot file, artifact hashes, ports, and
   QMP socket under the same existing run directory. The harness also records
   the secondary guest serial stream in that run directory from boot onward,
   so a post-QMP guest readiness drop can be classified without starting a
   second QEMU. QMP commands use CRLF framing consistently with the
   pixel-capture client.

Never delete Podman state as recovery. Stop the one container, inspect storage
and process ownership, and record the first actionable error. The operator may
remove an explicitly approved obsolete Docker VM after exact inspection. This
project does not create or remove Podman machines. Never run two QEMU instances
or create a per-ticket TMPDIR.

## TPS-bounded QEMU loop

The harness is fail-closed. It rejects a stale QMP socket, duplicate or
occupied ports, residual `qemu-system-x86_64`/`runqemu`/`flutter-auto`,
unreadable artifacts, and SHA-256 mismatches before invoking runqemu. It records
the exact runqemu command and keeps the QMP framebuffer as the primary visual
evidence. `summary` reads only the last 400 log lines and emits at most 120
selected marker/error lines; raw serial, PPM, and video files remain outside
Git. QMP teardown negotiates `qmp_capabilities`, sends `quit`, then removes only
the exact harness-owned stale socket after all target processes disappear.

The Mini PC runtime evidence root is `/mnt/yocto/evidence`, separate from the
Git receiver and the active BitBake layer. Store raw QMP/serial/app logs under
one ticket-and-run subdirectory there; do not assume `$BUILD_RECEIVER/evidence`
is the runtime evidence root. Commit only the sanitized Markdown manifest and
hashes to the project. Record the evidence directory before starting QEMU and
verify the files still exist before teardown/closeout.

## Current observed state

- Docker Desktop is intentionally stopped because no Mac-side Devtool or
  BitBake process is active. The user-approved obsolete Docker VM file was
  removed; Docker is no longer a provider for this workflow.
- Podman 6.1.1 is installed and the one rootful `fluorite-devtool` machine is
  running with the validated 8 GiB/2 CPU/4 GiB profile. The OCI image build
  passed. FLR-0390 found the fixed-name `fluorite-mac-devtool` container
  mounted a separate older project clone, so the wrapper correctly failed
  closed on its project-root label. The exact idle container was replaced once
  through the Podman wrapper with the current canonical checkout mounted
  read-write at `/workspace/project`; the same image, AGL bind, state bind,
  machine, and container name were reused. Its old project clone was left
  untouched. The prior `/workspace/tmp` contents were archived in the fixed
  state bind, restored, and GNU-tar-compared before the archive was removed.
  Two consecutive wrapper `status` probes and one read-only `devtool-status`
  probe passed. No second machine, container, named volume, state root, or
  TMPDIR was created. Earlier setup repaired stale `self-install/meta-flutter`
  entries in the existing state; status checks defer the large ownership scan
  until a real Devtool operation.
- The active Yocto `TMPDIR` is the single fixed container-private path
  `/workspace/tmp` on a 3 GiB tmpfs. The host bind remains the source/build/
  downloads/sstate state path; the retired host `state/tmp` is not used because
  macOS shared filesystems are case-insensitive and do not support BitBake's
  FIFO and Unix-socket requirements. The old sparsebundle is retained as a
  recovery artifact outside the active contract.
- BitBake's control directory is the single fixed container-local path
  `/tmp/fluorite-bitbake-control`; its `conf` and `workspace` entries point at
  the existing mounted build/config/workspace. This is a control-socket
  workaround, not a second Yocto build or TMPDIR.
- The validated Mini PC bundle inbox is the fixed receiver-side role path
  `/mnt/yocto/flourite-receivers/inbox`, adjacent to the fixed active receiver.
  Do not invent `/mnt/yocto/bundles` or another per-ticket inbox; the handoff
  helper must always send the single active bundle to this existing inbox.
- `scripts/run-mac-devtool.sh` is a retained Docker-only legacy fallback and is
  not part of the active workflow. Do not start Docker Desktop for Fluorite;
  use `scripts/run-podman-devtool.sh` with the current canonical project root.
- Default recipe-scoped extract reached source staging but failed at the
  cross-device move. Official `devtool modify --no-extract` then registered the
  resulting Git tree, and `devtool status` reports `filament-vk` at the fixed
  workspace source path. The wrapper supports this bounded no-extract recovery.
- Mini PC full-build and parent-alpha runtime validation remain separate gates;
  this document does not claim either one passed.
