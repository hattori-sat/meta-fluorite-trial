# Python runtime compatibility

## Decision

The deployed MCP runtime supports CPython 3.10 and newer. Repository development,
unit tests and CI continue to require Python 3.11 or newer.

This split is intentional. The Linux AGL/Yocto build role currently provides
Python 3.10, while the Mac Codex/QEMU role and GitHub workflow provide a newer
development interpreter. Test code may use development-only standard-library
modules; files under `mcp/` may not use syntax or APIs introduced after 3.10.

## Audit evidence

- Every `mcp/**/*.py` file parses with `ast.parse(feature_version=(3, 10))`.
- Runtime imports are checked against Python's standard-library module catalog;
  no third-party dependency is present.
- Runtime annotations use postponed evaluation where annotations are non-trivial.
- The newest relevant APIs used by the runtime are already available in 3.10:
  built-in generic types and union syntax, `dataclasses`, `pathlib` bounded reads,
  `subprocess.Popen(start_new_session=True)`, `os.killpg`, `threading.Event`, and
  `sys.stdlib`-independent JSON-RPC processing.
- `scripts/run-mcp.sh` accepts 3.10+; `scripts/check-python-unittest.sh` and
  `scripts/check-mcp-smoke.sh` retain their 3.11+ gate.
- A fake 3.10 executable selection test proves the wrapper does not accidentally
  skip the remote interpreter floor.

These checks are in `tests/test_mcp_runtime_compat.py` and run under the normal
3.11+ development suite.

## Deployment acceptance

An actual Python 3.10 interpreter was not available in the Mac workspace, and no
Git-ignored SSH role configuration was present. Therefore an end-to-end 3.10 stdio
handshake on the Linux role remains **UNKNOWN**, not silently assumed.

Before enabling a remote server in an agent, perform these checks without starting
a build:

1. Install the local and remote Git-ignored role configuration described in
   `mcp/README.md`.
2. Start `agl`, send `initialize` and `tools/list`, and verify that stdout contains
   only JSON-RPC responses.
3. Repeat for `yocto` and `command_runner`; call only `list_runbooks` on the latter.
4. Confirm the audit sink contains redacted role names and no connection details.
5. Keep command execution disabled until a separate approved plan is ready.

Failure of any handshake is a deployment blocker. Do not fall back to sending a
generic SSH or shell command through MCP.
