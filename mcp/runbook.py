"""Fixed, allowlisted command plans for the isolated command-runner context."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .config import MCPConfig, repository_root
from .errors import ConfigurationError, MCPDomainError
from .kernel import AuditHook, bounded_text, observed_at, paginate, redact

RISKS = frozenset({"read_only", "metadata_write", "build", "target_mutation"})
_RISK_LEVEL = {"read_only": 0, "metadata_write": 1, "build": 2, "target_mutation": 3}
_PARAMETER = re.compile(r"^\$\{([a-z][a-z0-9_]*)\}$")
_SAFE_PROFILE = re.compile(r"^[a-z][a-z0-9_-]*$")
_TICKET_ID = re.compile(r"^FLR-[0-9]{4}$")
_ALLOWED_PREFIXES = (("git", "status"), ("git", "rev-parse"), ("uname",), ("df",))
_FIXED_RUNBOOK_MANIFESTS = (
    "host-capacity.json",
    "repository-baseline.json",
    "qemux86-64-fluorite.json",
)

_QEMU_X86_64_ARGV = (
    "qemu-system-x86_64", "-machine", "q35", "-accel", "tcg,thread=multi",
    "-m", "2048", "-smp", "4", "-cpu", "qemu64,+ssse3,+sse4.1,+sse4.2,+popcnt",
    "-kernel", "./bzImage", "-append", "root=/dev/sda rw console=ttyS0,115200n8",
    "-drive", "file=./agl-ivi-image-flutter-qemux86-64.rootfs.ext4,format=raw,if=ide",
    "-snapshot", "-display", "cocoa", "-serial", "mon:stdio",
    "-netdev", "user,id=net0", "-device", "virtio-net-pci,netdev=net0",
    "-device", "virtio-vga", "-device", "virtio-rng-pci", "-usb",
    "-device", "usb-tablet", "-device", "usb-kbd",
)


def _command_is_allowlisted(argv: tuple[str, ...]) -> bool:
    if argv == _QEMU_X86_64_ARGV:
        return True
    if any(argv[: len(prefix)] == prefix for prefix in _ALLOWED_PREFIXES):
        return True
    if argv == ("bitbake", "-p"):
        return True
    if len(argv) == 3 and argv[0] == "bitbake" and argv[1] in ("-e", "-n"):
        return bool(_PARAMETER.fullmatch(argv[2]))
    if len(argv) == 2 and argv[0] == "bitbake":
        return bool(_PARAMETER.fullmatch(argv[1]))
    return False


def _minimum_command_risk(argv: tuple[str, ...]) -> str:
    if argv[0] != "bitbake":
        return "read_only"
    if argv == ("bitbake", "-p") or (len(argv) == 3 and argv[1] in ("-e", "-n")):
        return "metadata_write"
    return "build"


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    choices: tuple[str, ...]
    default: str


@dataclass(frozen=True)
class Step:
    step_id: str
    argv: tuple[str, ...]
    root: str
    environment_profile: str | None
    timeout_seconds: int


@dataclass(frozen=True)
class Runbook:
    runbook_id: str
    title: str
    description: str
    risk: str
    parameters: tuple[ParameterSpec, ...]
    steps: tuple[Step, ...]

    def parameter_map(self) -> dict[str, ParameterSpec]:
        return {parameter.name: parameter for parameter in self.parameters}


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f"{label} must be a non-empty string")
    return value


class RunbookRegistry:
    def __init__(self, manifest_dir: Path | None = None) -> None:
        # Production callers do not accept a directory through MCP input.  The
        # optional argument exists for isolated validation tests only.
        self.fixed_catalog = manifest_dir is None
        self.manifest_dir = (manifest_dir or repository_root() / "runbooks").resolve()
        self.runbooks = self._load()

    def _load(self) -> dict[str, Runbook]:
        result: dict[str, Runbook] = {}
        if not self.manifest_dir.is_dir():
            raise ConfigurationError("fixed runbook directory is unavailable")
        if self.fixed_catalog:
            expected = set(_FIXED_RUNBOOK_MANIFESTS)
            actual = {path.name for path in self.manifest_dir.glob("*.json")}
            if actual != expected:
                raise ConfigurationError("fixed runbook directory differs from the code allowlist")
            paths = [self.manifest_dir / name for name in _FIXED_RUNBOOK_MANIFESTS]
        else:
            paths = sorted(self.manifest_dir.glob("*.json"))
        for path in paths:
            if not path.is_file() or path.is_symlink():
                raise ConfigurationError(f"invalid fixed runbook manifest: {path.name}")
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ConfigurationError(f"invalid fixed runbook manifest: {path.name}") from exc
            runbook = self._parse(_mapping(raw, path.name), path.name)
            if runbook.runbook_id in result:
                raise ConfigurationError("duplicate runbook id")
            result[runbook.runbook_id] = runbook
        if not result:
            raise ConfigurationError("no fixed runbooks are installed")
        return result

    def _parse(self, raw: Mapping[str, Any], filename: str) -> Runbook:
        allowed_top = {"schema", "id", "title", "description", "risk", "parameters", "steps"}
        if set(raw) - allowed_top:
            raise ConfigurationError(f"{filename} contains unsupported fields")
        if raw.get("schema") != "fluorite.runbook/v1":
            raise ConfigurationError(f"{filename} has an unsupported schema")
        runbook_id = _string(raw.get("id"), f"{filename}.id")
        if not _SAFE_PROFILE.fullmatch(runbook_id):
            raise ConfigurationError(f"{filename}.id is invalid")
        risk = _string(raw.get("risk"), f"{filename}.risk")
        if risk not in RISKS:
            raise ConfigurationError(f"{filename}.risk is invalid")

        parameter_specs: list[ParameterSpec] = []
        raw_parameters = _mapping(raw.get("parameters", {}), f"{filename}.parameters")
        for name, value in raw_parameters.items():
            if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
                raise ConfigurationError(f"{filename} has an invalid parameter name")
            spec = _mapping(value, f"{filename}.parameters.{name}")
            if set(spec) - {"choices", "default"}:
                raise ConfigurationError(f"{filename}.parameters.{name} has unsupported fields")
            choices_raw = spec.get("choices")
            if not isinstance(choices_raw, list) or not choices_raw or not all(
                isinstance(item, str) and item for item in choices_raw
            ):
                raise ConfigurationError(f"{filename}.parameters.{name}.choices is invalid")
            choices = tuple(choices_raw)
            default = _string(spec.get("default"), f"{filename}.parameters.{name}.default")
            if default not in choices:
                raise ConfigurationError(f"{filename}.parameters.{name}.default is not allowed")
            parameter_specs.append(ParameterSpec(name, choices, default))

        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ConfigurationError(f"{filename}.steps must be a non-empty array")
        steps: list[Step] = []
        known_parameters = {parameter.name for parameter in parameter_specs}
        for index, value in enumerate(raw_steps):
            step = _mapping(value, f"{filename}.steps[{index}]")
            if set(step) - {"id", "argv", "root", "environment_profile", "timeout_seconds"}:
                raise ConfigurationError(f"{filename}.steps[{index}] has unsupported fields")
            argv_raw = step.get("argv")
            if not isinstance(argv_raw, list) or not argv_raw or not all(
                isinstance(item, str) and item and "\x00" not in item for item in argv_raw
            ):
                raise ConfigurationError(f"{filename}.steps[{index}].argv is invalid")
            argv = tuple(argv_raw)
            for token in argv:
                match = _PARAMETER.fullmatch(token)
                if "${" in token and not match:
                    raise ConfigurationError(f"{filename} permits only whole-token parameters")
                if match and match.group(1) not in known_parameters:
                    raise ConfigurationError(f"{filename} references an unknown parameter")
            if not _command_is_allowlisted(argv):
                raise ConfigurationError(f"{filename} contains a non-allowlisted command")
            minimum_risk = _minimum_command_risk(argv)
            if _RISK_LEVEL[risk] < _RISK_LEVEL[minimum_risk]:
                raise ConfigurationError(f"{filename}.risk understates a command effect")
            profile = step.get("environment_profile")
            if profile is not None and (not isinstance(profile, str) or not _SAFE_PROFILE.fullmatch(profile)):
                raise ConfigurationError(f"{filename}.steps[{index}].environment_profile is invalid")
            timeout = step.get("timeout_seconds", 30)
            if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
                raise ConfigurationError(f"{filename}.steps[{index}].timeout_seconds is invalid")
            steps.append(
                Step(
                    _string(step.get("id"), f"{filename}.steps[{index}].id"),
                    argv,
                    _string(step.get("root", "repository"), f"{filename}.steps[{index}].root"),
                    profile,
                    timeout,
                )
            )
        return Runbook(
            runbook_id,
            _string(raw.get("title"), f"{filename}.title"),
            _string(raw.get("description"), f"{filename}.description"),
            risk,
            tuple(parameter_specs),
            tuple(steps),
        )

    def get(self, runbook_id: str) -> Runbook:
        try:
            return self.runbooks[runbook_id]
        except KeyError as exc:
            raise MCPDomainError("unknown runbook id", code="unknown_runbook") from exc


class CommandRunner:
    def __init__(self, config: MCPConfig, registry: RunbookRegistry | None = None) -> None:
        self.config = config
        self.registry = registry or RunbookRegistry()
        self.roots = {alias: path.resolve() for alias, path in config.roots("command_runner").items()}
        self.profiles = _mapping(config.command_runner().get("environment_profiles", {}), "command_runner.environment_profiles")
        self._plans: dict[str, dict[str, Any]] = {}
        self._runs: dict[str, dict[str, Any]] = {}
        self._cancellations: dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self._lifecycle_audit = AuditHook(config.audit_path())
        raw_concurrency = config.command_runner().get("max_concurrent_runs", 1)
        if (
            isinstance(raw_concurrency, bool)
            or not isinstance(raw_concurrency, int)
            or not 1 <= raw_concurrency <= 4
        ):
            raise ConfigurationError("command_runner.max_concurrent_runs must be between 1 and 4")
        self.max_concurrent_runs = raw_concurrency

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": runbook.runbook_id,
                "title": runbook.title,
                "risk": runbook.risk,
                "parameters": {
                    parameter.name: {"choices": list(parameter.choices), "default": parameter.default}
                    for parameter in runbook.parameters
                },
            }
            for runbook in sorted(self.registry.runbooks.values(), key=lambda value: value.runbook_id)
        ]

    def describe(self, runbook_id: str) -> dict[str, Any]:
        runbook = self.registry.get(runbook_id)
        return {
            "id": runbook.runbook_id,
            "title": runbook.title,
            "description": runbook.description,
            "risk": runbook.risk,
            "execution_enabled": self.config.execution_allowed(),
            "steps": [
                {
                    "id": step.step_id,
                    "root_role": step.root,
                    "environment_profile": step.environment_profile,
                    "timeout_seconds": step.timeout_seconds,
                }
                for step in runbook.steps
            ],
            "parameters": {
                parameter.name: {"choices": list(parameter.choices), "default": parameter.default}
                for parameter in runbook.parameters
            },
        }

    def _parameters(self, runbook: Runbook, supplied: Any) -> dict[str, str]:
        if supplied is None:
            supplied = {}
        if not isinstance(supplied, dict):
            raise MCPDomainError("parameters must be an object")
        specs = runbook.parameter_map()
        extras = set(supplied) - set(specs)
        if extras:
            raise MCPDomainError("runbook received unsupported parameters")
        values: dict[str, str] = {}
        for name, spec in specs.items():
            value = supplied.get(name, spec.default)
            if not isinstance(value, str) or value not in spec.choices:
                raise MCPDomainError(f"parameter {name} is outside its allowlist")
            values[name] = value
        return values

    @staticmethod
    def _render_argv(step: Step, parameters: Mapping[str, str]) -> list[str]:
        result: list[str] = []
        for token in step.argv:
            match = _PARAMETER.fullmatch(token)
            result.append(parameters[match.group(1)] if match else token)
        return result

    def _resolve_root(self, alias: str) -> Path:
        try:
            root = self.roots[alias]
        except KeyError as exc:
            raise MCPDomainError(f"runbook root role is not configured: {alias}", code="root_unavailable") from exc
        if not root.is_dir():
            raise MCPDomainError(f"runbook root role is unavailable: {alias}", code="root_unavailable")
        return root

    def _profile(self, name: str | None) -> Mapping[str, Any] | None:
        if name is None:
            return None
        try:
            raw = _mapping(self.profiles[name], f"environment profile {name}")
        except KeyError as exc:
            raise MCPDomainError(f"environment profile is not configured: {name}", code="profile_unavailable") from exc
        allowed = {"setup_script", "source_arguments", "environment"}
        if set(raw) - allowed:
            raise ConfigurationError(f"environment profile {name} contains unsupported fields")
        setup = raw.get("setup_script")
        if not isinstance(setup, str):
            raise ConfigurationError(f"environment profile {name} needs setup_script")
        setup_path = Path(setup).expanduser().resolve()
        if not setup_path.is_file() or setup_path.is_symlink():
            raise MCPDomainError(f"environment profile is unavailable: {name}", code="profile_unavailable")
        source_arguments = raw.get("source_arguments", [])
        if not isinstance(source_arguments, list) or not all(isinstance(item, str) and "\x00" not in item for item in source_arguments):
            raise ConfigurationError(f"environment profile {name}.source_arguments is invalid")
        environment = _mapping(raw.get("environment", {}), f"environment profile {name}.environment")
        for key, value in environment.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not isinstance(value, str):
                raise ConfigurationError(f"environment profile {name}.environment is invalid")
        return {"setup_script": setup_path, "source_arguments": source_arguments, "environment": environment}

    @staticmethod
    def _ticket_id(value: Any) -> str:
        if not isinstance(value, str) or not _TICKET_ID.fullmatch(value):
            raise MCPDomainError("ticket_id must match FLR-NNNN", code="invalid_ticket")
        return value

    def plan(
        self, runbook_id: str, supplied: Any = None, ticket_id: Any = None
    ) -> dict[str, Any]:
        runbook = self.registry.get(runbook_id)
        checked_ticket = self._ticket_id(ticket_id)
        parameters = self._parameters(runbook, supplied)
        steps = []
        for step in runbook.steps:
            self._resolve_root(step.root)
            profile = self._profile(step.environment_profile)
            argv = self._render_argv(step, parameters)
            steps.append(
                {
                    "id": step.step_id,
                    "argv": redact(argv),
                    "working_root_role": step.root,
                    "environment_profile": step.environment_profile,
                    "environment_source": "fixed_profile" if profile else None,
                    "timeout_seconds": step.timeout_seconds,
                }
            )
        canonical = json.dumps(
            {
                "ticket_id": checked_ticket,
                "runbook": runbook.runbook_id,
                "risk": runbook.risk,
                "parameters": parameters,
                "steps": steps,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        plan_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        plan_id = (
            "plan-"
            + plan_digest[:8]
            + "-"
            + uuid.uuid4().hex[:16]
        )
        plan = {
            "plan_id": plan_id,
            "plan_digest": plan_digest,
            "ticket_id": checked_ticket,
            "runbook_id": runbook.runbook_id,
            "risk": runbook.risk,
            "parameters": parameters,
            "steps": steps,
            "execution_enabled": self.config.execution_allowed(),
            "confirmation_required": True,
            "expires_in_seconds": 900,
        }
        with self._lock:
            now = time.monotonic()
            self._plans = {
                key: value for key, value in self._plans.items() if value["expires_at"] > now
            }
            if len(self._plans) >= 128:
                oldest = next(iter(self._plans))
                del self._plans[oldest]
            self._plans[plan_id] = {"plan": plan, "expires_at": now + 900}
        return plan

    def _command(self, step: Step, parameters: Mapping[str, str]) -> tuple[list[str], dict[str, str]]:
        argv = self._render_argv(step, parameters)
        profile = self._profile(step.environment_profile)
        environment = os.environ.copy()
        if argv[0] == "git":
            environment["GIT_OPTIONAL_LOCKS"] = "0"
        if profile is None:
            return argv, environment
        environment.update(profile["environment"])
        source_arguments = list(profile["source_arguments"])
        setup_count = 1 + len(source_arguments)
        command_argv = argv
        assignments = ["mcp_setup=$1"]
        assignments.extend(
            f"mcp_source_{index}=${index + 1}" for index in range(1, len(source_arguments) + 1)
        )
        first_command_position = setup_count + 1
        assignments.extend(
            f"mcp_command_{index}=${first_command_position + index}"
            for index in range(len(command_argv))
        )
        source_values = " ".join(
            ["\"$mcp_setup\""]
            + [f'"$mcp_source_{index}"' for index in range(1, len(source_arguments) + 1)]
        )
        command_values = " ".join(
            f'"$mcp_command_{index}"' for index in range(len(command_argv))
        )
        script = "; ".join(assignments) + f"; . {source_values} && exec {command_values}"
        command = [
            "/bin/sh",
            "-c",
            script,
            "mcp-fixed-environment",
            str(profile["setup_script"]),
            *source_arguments,
            *argv,
        ]
        return command, environment

    @staticmethod
    def _capture(
        command: list[str],
        cwd: Path,
        environment: Mapping[str, str],
        timeout: int,
        cancellation: threading.Event | None = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        chunks: list[bytes] = []
        output_digest = hashlib.sha256()
        retained = 0
        total = 0
        cap = 64 * 1024

        def drain() -> None:
            nonlocal retained, total
            assert process.stdout is not None
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    return
                total += len(chunk)
                output_digest.update(chunk)
                if retained < cap:
                    kept = chunk[: cap - retained]
                    chunks.append(kept)
                    retained += len(kept)

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        timed_out = False
        cancelled = False

        def terminate_group(sig: int) -> None:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                return

        while process.poll() is None:
            if cancellation is not None and cancellation.is_set():
                cancelled = True
                terminate_group(signal.SIGTERM)
                break
            if time.monotonic() - started >= timeout:
                timed_out = True
                terminate_group(signal.SIGTERM)
                break
            time.sleep(0.05)
        if process.poll() is None:
            try:
                return_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                terminate_group(signal.SIGKILL)
                return_code = process.wait(timeout=5)
        else:
            return_code = int(process.returncode)
        reader.join(timeout=2)
        if process.stdout is not None:
            process.stdout.close()
        output = b"".join(chunks).decode("utf-8", errors="replace")
        output, text_truncated = bounded_text(output, cap)
        return {
            "return_code": return_code,
            "timed_out": timed_out,
            "cancelled": cancelled,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output": redact(output),
            "output_bytes": total,
            "output_sha256": output_digest.hexdigest(),
            "truncated": text_truncated or total > retained,
        }

    def _confirmed_plan(
        self, runbook_id: str, supplied: Any, ticket_id: Any, confirmation: Any
    ) -> tuple[Runbook, dict[str, Any]]:
        if not self.config.execution_allowed():
            raise MCPDomainError(
                "execution is disabled; set both command_runner.allow_execution and FLUORITE_MCP_ALLOW_EXECUTION=1",
                code="execution_disabled",
            )
        if not isinstance(confirmation, str):
            raise MCPDomainError("confirmation must match a freshly generated plan_id", code="confirmation_required")
        runbook = self.registry.get(runbook_id)
        checked_ticket = self._ticket_id(ticket_id)
        parameters = self._parameters(runbook, supplied)
        with self._lock:
            stored = self._plans.pop(confirmation, None)
            if stored is None or stored["expires_at"] <= time.monotonic():
                raise MCPDomainError("plan is not available", code="confirmation_required")
        plan = stored["plan"]
        if (
            plan["runbook_id"] != runbook_id
            or plan["parameters"] != parameters
            or plan["ticket_id"] != checked_ticket
        ):
            raise MCPDomainError(
                "confirmation does not match the runbook and parameters", code="confirmation_required"
            )
        return runbook, plan

    def _assert_capacity(self) -> None:
        with self._lock:
            active = sum(
                record["status"] in ("queued", "running") for record in self._runs.values()
            )
        if active >= self.max_concurrent_runs:
            raise MCPDomainError("maximum concurrent runbook count reached", code="runner_busy")

    def _new_record(
        self, runbook: Runbook, status: str, plan: Mapping[str, Any]
    ) -> dict[str, Any]:
        run_id = f"run-{uuid.uuid4().hex[:16]}"
        record: dict[str, Any] = {
            "run_id": run_id,
            "ticket_id": plan["ticket_id"],
            "runbook_id": runbook.runbook_id,
            "risk": runbook.risk,
            "plan_id": plan["plan_id"],
            "plan_digest": plan["plan_digest"],
            "created_at": observed_at(),
            "status": status,
            "steps": [],
        }
        with self._lock:
            if len(self._runs) >= 128:
                completed = next(
                    (
                        key
                        for key, value in self._runs.items()
                        if value["status"] in ("succeeded", "failed", "cancelled")
                    ),
                    None,
                )
                if completed is None:
                    raise MCPDomainError("run registry is full", code="runner_busy")
                self._runs.pop(completed, None)
                self._cancellations.pop(completed, None)
            self._runs[run_id] = record
        return record

    def _perform(
        self,
        record: dict[str, Any],
        runbook: Runbook,
        plan: Mapping[str, Any],
        cancellation: threading.Event | None = None,
    ) -> None:
        record["status"] = "running"
        record["started_at"] = observed_at()
        for step in runbook.steps:
            if cancellation is not None and cancellation.is_set():
                record["status"] = "cancelled"
                break
            command, environment = self._command(step, plan["parameters"])
            outcome = self._capture(
                command,
                self._resolve_root(step.root),
                environment,
                step.timeout_seconds,
                cancellation,
            )
            outcome["id"] = step.step_id
            outcome["argv"] = redact(self._render_argv(step, plan["parameters"]))
            outcome["working_root_role"] = step.root
            outcome["timeout_seconds"] = step.timeout_seconds
            record["steps"].append(outcome)
            if outcome["cancelled"]:
                record["status"] = "cancelled"
                break
            if outcome["timed_out"] or outcome["return_code"] != 0:
                record["status"] = "failed"
                break
        else:
            record["status"] = "succeeded"
        record["finished_at"] = observed_at()
        record["audit_warnings"] = self._lifecycle_audit.emit(
            {
                "schema": "fluorite.run-lifecycle/v1",
                "observed_at": record["finished_at"],
                "run_id": record["run_id"],
                "ticket_id": record["ticket_id"],
                "runbook_id": record["runbook_id"],
                "risk": record["risk"],
                "plan_id": record["plan_id"],
                "plan_digest": record["plan_digest"],
                "status": record["status"],
                "steps": [
                    {
                        "id": step["id"],
                        "working_root_role": step["working_root_role"],
                        "timeout_seconds": step["timeout_seconds"],
                        "return_code": step["return_code"],
                        "timed_out": step["timed_out"],
                        "cancelled": step["cancelled"],
                        "duration_seconds": step["duration_seconds"],
                        "output_bytes": step["output_bytes"],
                        "output_sha256": step["output_sha256"],
                        "truncated": step["truncated"],
                    }
                    for step in record["steps"]
                ],
            }
        )
        with self._lock:
            self._cancellations.pop(record["run_id"], None)

    def execute(
        self, runbook_id: str, supplied: Any, ticket_id: Any, confirmation: Any
    ) -> dict[str, Any]:
        self._assert_capacity()
        runbook, plan = self._confirmed_plan(
            runbook_id, supplied, ticket_id, confirmation
        )
        if runbook.risk != "read_only" or any(
            step.timeout_seconds > 45 for step in runbook.steps
        ):
            raise MCPDomainError(
                "this runbook requires asynchronous start_runbook execution",
                code="asynchronous_required",
            )
        record = self._new_record(runbook, "running", plan)
        self._perform(record, runbook, plan)
        return record

    def start(
        self, runbook_id: str, supplied: Any, ticket_id: Any, confirmation: Any
    ) -> dict[str, Any]:
        self._assert_capacity()
        runbook, plan = self._confirmed_plan(
            runbook_id, supplied, ticket_id, confirmation
        )
        record = self._new_record(runbook, "queued", plan)
        cancellation = threading.Event()
        with self._lock:
            self._cancellations[record["run_id"]] = cancellation

        def run() -> None:
            try:
                self._perform(record, runbook, plan, cancellation)
            except Exception:
                record["status"] = "failed"
                record["finished_at"] = observed_at()

        threading.Thread(
            target=run,
            name=f"fluorite-runbook-{record['run_id']}",
            daemon=True,
        ).start()
        return self.status(record["run_id"])

    def status(self, run_id: str) -> dict[str, Any]:
        try:
            record = self._runs[run_id]
        except KeyError as exc:
            raise MCPDomainError("unknown run id", code="unknown_run") from exc
        return {
            "run_id": run_id,
            "ticket_id": record["ticket_id"],
            "runbook_id": record["runbook_id"],
            "risk": record["risk"],
            "plan_id": record["plan_id"],
            "plan_digest": record["plan_digest"],
            "status": record["status"],
            "created_at": record["created_at"],
            "started_at": record.get("started_at"),
            "finished_at": record.get("finished_at"),
            "audit_warnings": list(record.get("audit_warnings", [])),
            "steps": [
                {
                    "id": step["id"],
                    "return_code": step["return_code"],
                    "timed_out": step["timed_out"],
                    "cancelled": step["cancelled"],
                    "duration_seconds": step["duration_seconds"],
                    "output_bytes": step["output_bytes"],
                    "output_sha256": step["output_sha256"],
                    "truncated": step["truncated"],
                    "working_root_role": step["working_root_role"],
                    "timeout_seconds": step["timeout_seconds"],
                }
                for step in record["steps"]
            ],
        }

    def cancel(self, run_id: str) -> dict[str, Any]:
        status = self.status(run_id)
        if status["status"] not in ("queued", "running"):
            return {"run_id": run_id, "cancellation_requested": False, "status": status["status"]}
        with self._lock:
            cancellation = self._cancellations.get(run_id)
        if cancellation is None:
            return {"run_id": run_id, "cancellation_requested": False, "status": status["status"]}
        cancellation.set()
        return {"run_id": run_id, "cancellation_requested": True, "status": status["status"]}

    def run_log(self, run_id: str, cursor: str | None, limit: int) -> dict[str, Any]:
        try:
            record = self._runs[run_id]
        except KeyError as exc:
            raise MCPDomainError("unknown run id", code="unknown_run") from exc
        lines: list[dict[str, Any]] = []
        for step in record["steps"]:
            for number, line in enumerate(str(step["output"]).splitlines(), start=1):
                lines.append({"step_id": step["id"], "line": number, "text": line})
        page = paginate(lines, cursor, limit)
        return {
            "run_id": run_id,
            "ticket_id": record["ticket_id"],
            "plan_id": record["plan_id"],
            "plan_digest": record["plan_digest"],
            "status": record["status"],
            "log_lines": page.items,
            "next_cursor": page.next_cursor,
            "truncated": page.truncated or any(bool(step["truncated"]) for step in record["steps"]),
        }
