# Fixed command runbooks

These manifests are the complete command surface of `command_runner`. MCP callers
select a runbook ID and enum values; they cannot submit a command, executable,
working directory, setup script or environment variable.

The production registry names each accepted manifest in tracked code and rejects
additional JSON files. Adding a runbook therefore requires changing both the
manifest set and the code allowlist in the same reviewed commit; a local/global
Git exclude cannot extend the catalog.

## Effect classes

| Class | Meaning |
| --- | --- |
| `read_only` | Runs a fixed observer command. The command itself is not expected to write project state. |
| `metadata_write` | May create BitBake cache, cooker logs, locks or generated metadata. `bitbake -n`, `-e` and parsing belong here. |
| `build` | Compiles, packages or assembles an image. |
| `target_mutation` | Changes a QEMU/device process or target state. The installed QEMU profile is snapshot-only and bounded. |

`execute_runbook` is a dry-run unless `dry_run` is explicitly false. Real execution
requires all four gates:

1. local configuration contains `command_runner.allow_execution: true`;
2. process environment contains `FLUORITE_MCP_ALLOW_EXECUTION=1`;
3. request ticket ID matches `FLR-NNNN` and is bound into the plan;
4. `confirmation` exactly matches a fresh `plan_id` for the same ticket, runbook and parameters.

The confirmation challenge makes accidental execution harder; it does not replace
the human approval mechanism of the MCP host.

Synchronous real execution is limited to short `read_only` runbooks. Use
`start_runbook` for every `metadata_write` or `build` operation and follow it with
status/log calls. The catalog exposes fixed qemux86-64 metadata, Fluorite demo
compile and AGL Flutter image-build profiles. They accept no target/task/path
parameters, use independent wall-clock and task-output inactivity limits, own one
new process group, and persist redacted status JSON by run/evidence ID. The catalog
updates active PID/PGID, bounded process membership and the capped output tail while
the step is running; callers do not need to wait for completion to observe progress.
The catalog also exposes one fixed `qemux86-64-fluorite` target profile. It
requires a configured `qemu_artifact` role root, fixed kernel/rootfs basenames,
`-snapshot`, Cocoa display and a 120-second process bound. It does not expose
arbitrary parse, dry-run, effective-environment target or image build. A record
left `queued` or `running` across an MCP restart is returned as `unknown`; the
supervisor never assumes an unobserved completion. Artifact inventory and
lossless allowlisted-variable capture remain separate validation steps.

## Adding a runbook

Keep parameters finite enums and commands as argument arrays. A parameter must be a
whole argument such as `${image}`. The loader rejects interpolation, unknown fields,
unknown commands and path parameters. Add protocol/unit coverage for every new
effect class, then add the reviewed filename to the code allowlist. Never add
clean-cache, recursive deletion or arbitrary shell runbooks.
