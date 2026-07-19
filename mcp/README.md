# Fluorite bounded-context MCP runtime

This directory contains eight dependency-free Python 3.10+ MCP servers. They
share a small technical kernel, but not a domain model. AGL and Yocto are
separate because an automotive Linux distribution and its build system give
different meanings to manifests, features, recipes, tasks and runtime evidence.

The implementation uses newline-delimited JSON-RPC over stdio and implements
`initialize`, `ping`, `tools/list`, `tools/call` and initialization/cancellation
notifications. It has no package-install step and performs no network fetch.
The [runtime compatibility audit](python-compatibility.md) records the Python 3.10
boundary and the still-required remote acceptance check.
Tool calls are validated against the advertised object schema. Unsupported fields,
including a caller-supplied `command`, fail closed instead of being ignored.

## Bounded contexts

| Server ID | Owned meaning | Tools |
| --- | --- | --- |
| `agl` | AGL manifests, image/features, packagegroups, compositor and service integration | `get_manifest_catalog`, `search_integration_points`, `read_integration_evidence` |
| `yocto` | layers, recipes/appends/classes, configuration and existing task logs | `list_layer_metadata`, `find_recipe_candidates`, `search_metadata`, `read_metadata`, `list_task_logs`, `tail_task_log` |
| `fluorite` | Dart scene, assets, interaction, startup and platform contracts | `catalog_scene_assets`, `search_scene_contract`, `read_scene_source` |
| `flutter_runtime` | Flutter Engine/embedder, IVI launcher, threads and surfaces | `catalog_embedder_surfaces`, `search_embedder_contract`, `read_runtime_source` |
| `filament` | Dart/native bridge, Filament engine, materials and render assets | `catalog_render_assets`, `search_render_bridge`, `read_render_source` |
| `graphics` | Wayland, Vulkan, Mesa, DRM, GPU and presentation path | `catalog_graphics_configuration`, `search_graphics_path`, `read_graphics_evidence` |
| `target_validation` | existing boot, service, graphics, input and screen evidence | `list_validation_bundles`, `summarize_boot_evidence`, `summarize_graphics_evidence`, `read_target_evidence` |
| `command_runner` | fixed runbook planning, execution ownership and bounded logs | `list_runbooks`, `describe_runbook`, `plan_runbook`, `execute_runbook`, `start_runbook`, `get_run_status`, `read_run_log`, `cancel_run` |

The first seven servers are read-only. They do not run SSH, BitBake or target
commands. `command_runner` is isolated and is the only server with tools marked
state-changing/destructive in MCP annotations.

## Shared kernel, separate payloads

Only this response envelope is shared:

```json
{
  "schema": "fluorite.mcp-envelope/v1",
  "bounded_context": "yocto",
  "operation": "find_recipe_candidates",
  "subject_id": "yocto-build-snapshot",
  "revision_or_image_id": "sha256:combined-input-digest",
  "identity_status": "sufficient",
  "observed_at": "UTC timestamp",
  "payload": {"domain_owned_shape": "..."},
  "unknowns": [],
  "evidence_ids": ["ev-yocto-..."],
  "truncated": false,
  "warnings": [],
  "next_queries": [],
  "redaction_policy": "fluorite.privacy-redaction/v1",
  "explainability": {
    "classification": "bounded_observation",
    "basis_evidence_ids": ["ev-yocto-..."],
    "causal_claims": [],
    "limitations": [],
    "next_actions": []
  }
}
```

Each server owns the vocabulary inside `payload`. The shared kernel provides
opaque pagination, byte/line caps, privacy redaction, evidence identifiers and
audit hooks. It does not infer causes. A source occurrence is a fact; its role in
a failure remains a ticket-level hypothesis until verified. Missing
`revision_or_image_id` produces `identity_status=insufficient` and an explicit
UNKNOWN; identity-less evidence cannot establish a baseline.
If the final envelope exceeds its configured byte cap, the domain payload is
replaced by a bounded summary that retains available path/cursor/line resume
locators. The response remains `truncated=true` and cannot support an absence claim.

Evidence IDs correlate an in-process response with its audit event; they are not
durable content-addressed objects and cannot be dereferenced alone after restart.
A durable handoff must retain subject/revision identity, tool name and the
repository-safe root/path/range or search parameters needed to repeat the bounded
query. Configure `audit_file` when a persistent local call record is required.

The `explainability` block is transport metadata, not domain vocabulary. It
states what kind of result was returned, which evidence IDs support it, that the
bounded read made no causal claim, what remains limited or unknown, and the next
bounded actions. Agents must still separate facts, inferences and hypotheses in
their handoff; this block does not turn an observation into a diagnosis.

## Start a server

Run the version-selecting project wrapper from the repository root:

```sh
bash scripts/run-mcp.sh agl
bash scripts/run-mcp.sh yocto
bash scripts/run-mcp.sh command_runner
```

Use direct invocation with `--list-tools` for a local installation check:

```sh
python3.12 -m mcp graphics --list-tools
```

The wrapper selects Python 3.13, 3.12, 3.11 or 3.10 and rejects older runtimes.
Both its version probe and server process ignore inherited Python environment
paths, skip `site` customization and disable bytecode writes. `PYTHON` remains a
trusted local-development interpreter override; the remote wrapper clears it.
Direct invocation may use any available Python 3.10+ executable. Project
development and CI intentionally remain on Python 3.11+; the 3.10 floor exists
for the deployed MCP runtime on the AGL/Yocto build role only.

Every server has the same wrapper shape, so an MCP host only changes the last
argument. Use the repository root as the process working directory. The checked-in
[project MCP configuration](../.codex/config.toml) defines all eight transports and
their tool allowlists. Domain servers remain disabled for the primary role and are
enabled selectively by custom agent instructions.

Example host entry (adapt field names to the MCP host version):

```toml
[mcp_servers.yocto]
command = "bash"
args = ["scripts/run-mcp.sh", "yocto"]
cwd = ".." # relative to .codex/config.toml
```

Agent policy should enable only the server for that agent's bounded context. A
build-runner can additionally receive `command_runner`; a PDCA checker should
receive summaries/evidence and no execution tool.

## Mac-to-build-host transport

Codex and QEMU run on the Mac role. AGL metadata, Yocto state and build commands
belong to the Linux build role. Only `agl`, `yocto` and `command_runner` may cross
that SSH boundary; Fluorite, Flutter runtime, Filament, graphics source and Mac
target validation remain local.

Copy `mcp/remote-role.example.conf` to the Git-ignored path
`.fluorite-mcp/remote-role.conf` on the Mac. Put the real hostname/account in the
user's SSH config and store only its role alias in this file. On the Linux build
role, place the runtime JSON at the fixed Git-ignored path
`.fluorite-mcp/config.json` inside its canonical clone.

Set `expected_project_revision` to the full pushed commit checked out by the
Linux role. The wrapper refuses to start if remote HEAD differs. This guards the
MCP runtime revision; the domain `revision_or_image_id` separately identifies the
AGL manifest/source set, Yocto build snapshot, or target image/session.
The wrapper also rejects modified/staged tracked files, non-ignored untracked
files, and ignored files on the Python/script/runbook runtime surface before
loading the runtime or runbook catalog. Git-ignored role config and audit data
remain local, but cannot replace the commit-bound command surface.

```sh
bash scripts/run-remote-mcp.sh agl
bash scripts/run-remote-mcp.sh yocto
bash scripts/run-remote-mcp.sh command_runner
```

The remote wrapper is not a generic SSH command runner. It rejects every other
server ID, does not source the role config, accepts only three fixed keys, rejects
account/address syntax and shell metacharacters, requires the canonical-repository
guard, and launches only `scripts/run-mcp.sh <allowlisted-id>`. SSH uses batch mode
so an authentication prompt cannot consume MCP JSON from stdin. Its stdout remains
the remote MCP stdio stream; diagnostics and the canonical guard go to stderr.

Real command execution has independent gates on both hosts. The Mac role config
must set `allow_command_execution=1`, the Linux JSON must set Boolean
`command_runner.allow_execution: true`, a fresh one-time plan ID must match, and
the MCP host must approve the destructive-annotated tool.

## Local roots and configuration

Without configuration every context exposes the role alias `repository`, resolved
from the installed package location. This makes the repository's `manifests/`,
`conf/` and `layers/meta-local/` available without embedding a user, host or IP.

Additional source/build roots are local machine data. Copy
`mcp/config.example.json` outside Git, replace role paths and point the process to
it:

```sh
FLUORITE_MCP_CONFIG=/local/private/mcp-config.json bash scripts/run-mcp.sh yocto
```

Responses use locations such as `$YOCTO_METADATA_ROOT/path/to/recipe.bb`; configured
absolute paths are not returned. Root resolution rejects absolute input,
`..`, escape through symlinks, unsupported extensions and oversized files.
Each tool schema exposes configured root alias names as an enum without exposing
their absolute values.
The Git-ignored `.fluorite-mcp` role-config directory is a sensitive boundary:
walks skip it, direct relative reads reject it, and it cannot be configured as a
domain root. The built-in `repository` alias is reserved and cannot be replaced
by role-local configuration.

Each domain config also declares one repository-safe `identity.subject_id` and an
optional `identity.revision_or_image_id`. For a context with multiple roots, use a
manifest or combined digest covering every root. The runtime validates the value
shape and scopes evidence IDs with it, but does not claim to verify configured
identity against each root's Git HEAD/content. Keep the example's `null` until a
real fixed identity is available; responses then remain explicitly insufficient.

A scan stops after 4,000 eligible files or 32 MiB of text. Pagination divides the
results already collected before that stop; it cannot continue beyond the scan
cap. Therefore a large AGL checkout or Yocto build must be configured as narrow,
allowlisted roots per repository or evidence subtree, for example `meta_agl`,
`project_metadata` and `task_logs`. A response with `truncated=true` is incomplete;
repeat the query against a narrower root instead of treating an empty/missing item
as proof of absence. The combined identity must cover every configured subroot.
Directory traversal, stat or file-read errors also set `truncated=true`; an empty
result is negative evidence only when identity is sufficient and `truncated=false`.
Yocto task-log discovery deliberately traverses a configured root's `tmp` subtree,
while downloads, sstate, deploy and cache directories remain pruned. Point the
`task_logs` alias at the narrowest useful `tmp/work` subtree to bound traversal.
Catalog file caps are applied after suffix/name filtering. `tail_task_log` reads
only a bounded end window for logs over the normal 2 MiB source-read limit and
returns unknown line numbers plus `truncated=true`; it never loads the whole log.

To record privacy-redacted JSONL audit events, set `audit_file` in local config or
set `FLUORITE_MCP_AUDIT_LOG`. Audit is best effort: a sink failure is reported as a
warning and does not corrupt the stdio protocol.

## Fixed command execution

The API never accepts `command`, `argv`, a working path, setup-script path or free
text parameter. Production loads only the manifest filenames fixed in the code
allowlist and rejects any additional `runbooks/*.json`, including files hidden by
local/global Git excludes. It rejects unknown fields/executables and accepts only
finite enum parameters. Clean-cache,
recursive deletion and arbitrary shell commands are absent and rejected by the
loader.

`plan_runbook` resolves the fixed root and environment profile, binds an
`FLR-NNNN` ticket ID, and returns a `plan_id`. `execute_runbook` remains a dry-run
unless `dry_run` is explicitly false.
For real synchronous or asynchronous execution all gates must pass:

1. local configuration has `command_runner.allow_execution` set to Boolean `true`;
2. the MCP process has `FLUORITE_MCP_ALLOW_EXECUTION=1`;
3. the request supplies the same ticket ID and fresh matching `plan_id` as `confirmation`;
4. the MCP host/operator approval policy permits the destructive-annotated tool.

Use `start_runbook` for long-running work, then `get_run_status`, `read_run_log` and
`cancel_run`. A server can cancel only processes it started. Run status/logs are
process-local and disappear when the server restarts. This initial runtime has no
resume or distributed process ownership; that remains explicitly UNKNOWN until a
persistent supervisor is selected.

Real metadata-write operations are async-only; synchronous execution is limited
to short read-only runbooks so MCP host timeouts cannot orphan a long call. A
non-zero environment setup result stops before the command is executed. The
initial catalog deliberately exposes only short read-only repository/capacity
observations. Parse, dry-run, image build and full `bitbake -e` remain absent:
graceful/abrupt MCP shutdown ownership or a persistent supervisor, build
preflight/artifact inventory and lossless allowlisted variable capture are not yet
implemented. Those are acceptance work for the build tickets, not capabilities to
simulate with truncated output.

Environment setup is also fixed. A runbook names a profile such as `yocto`; local
configuration supplies that profile's setup script and finite source arguments.
The wrapper sources it in a child shell and directly executes the manifest command.
No sourced environment is applied to the MCP server process.

See [runbook policy](../runbooks/README.md) for effect classes. `bitbake -p`, `-e`
and `-n` are classified as `metadata_write`, because they may write cache, cooker
logs or locks despite appearing observational.

## Verification

Run all unit and protocol smoke tests with Python 3.11 or newer:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s tests -p 'test_mcp*.py' -v
```

The smoke suite starts every stdio server as a subprocess, negotiates MCP,
inspects tool annotations and calls one bounded tool. Unit coverage checks path
escape, pagination, privacy redaction, stable evidence IDs, runbook rejection,
dual execution gates, asynchronous status and bounded logs.
