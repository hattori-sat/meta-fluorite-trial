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
from typing import Any, Callable, Mapping

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
    "yocto-metadata-gate.json",
    "yocto-demo-compile.json",
    "yocto-image-build.json",
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
_YOCTO_METADATA_ARGV = ("bitbake", "-e", "agl-ivi-image-flutter")
_YOCTO_DEMO_COMPILE_ARGV = (
    "bitbake",
    "toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo",
    "-c",
    "compile",
)
_YOCTO_IMAGE_ARGV = ("bitbake", "agl-ivi-image-flutter")


def _command_is_allowlisted(argv: tuple[str, ...]) -> bool:
    if argv in (
        _QEMU_X86_64_ARGV,
        _YOCTO_METADATA_ARGV,
        _YOCTO_DEMO_COMPILE_ARGV,
        _YOCTO_IMAGE_ARGV,
    ):
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
    inactivity_timeout_seconds: int | None
    activity_root: str | None


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
            if set(step) - {
                "id", "argv", "root", "environment_profile", "timeout_seconds",
                "inactivity_timeout_seconds",
                "activity_root",
            }:
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
            if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 21600:
                raise ConfigurationError(f"{filename}.steps[{index}].timeout_seconds is invalid")
            inactivity_timeout = step.get("inactivity_timeout_seconds")
            if inactivity_timeout is not None and (
                isinstance(inactivity_timeout, bool)
                or not isinstance(inactivity_timeout, int)
                or not 30 <= inactivity_timeout <= timeout
            ):
                raise ConfigurationError(
                    f"{filename}.steps[{index}].inactivity_timeout_seconds is invalid"
                )
            activity_root = step.get("activity_root")
            if activity_root is not None and (
                not isinstance(activity_root, str) or not _SAFE_PROFILE.fullmatch(activity_root)
            ):
                raise ConfigurationError(f"{filename}.steps[{index}].activity_root is invalid")
            steps.append(
                Step(
                    _string(step.get("id"), f"{filename}.steps[{index}].id"),
                    argv,
                    _string(step.get("root", "repository"), f"{filename}.steps[{index}].root"),
                    profile,
                    timeout,
                    inactivity_timeout,
                    activity_root,
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
                    "inactivity_timeout_seconds": step.inactivity_timeout_seconds,
                    "activity_root_role": step.activity_root,
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
            if step.activity_root is not None:
                self._resolve_root(step.activity_root)
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
                    "inactivity_timeout_seconds": step.inactivity_timeout_seconds,
                    "activity_root_role": step.activity_root,
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
    def _process_group_snapshot(pgid: int) -> list[dict[str, Any]]:
        proc = Path("/proc")
        if not proc.is_dir():
            return []
        members: list[dict[str, Any]] = []
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                stat = (entry / "stat").read_text(encoding="utf-8")
                close = stat.rfind(")")
                fields = stat[close + 2 :].split()
                member_pgid = int(fields[2])
                if member_pgid != pgid:
                    continue
                command = stat[stat.find("(") + 1 : close]
                members.append(
                    {"pid": int(entry.name), "pgid": member_pgid, "command": command[:80]}
                )
            except (OSError, ValueError, IndexError):
                continue
        return sorted(members, key=lambda item: item["pid"])

    @staticmethod
    def _task_activity_marker(root: Path | None) -> tuple[int, int, str] | None:
        if root is None:
            return None
        newest: tuple[int, int, str] | None = None
        try:
            entries = root.iterdir()
            for path in entries:
                if not path.name.startswith(("log.do_", "run.do_")) or not path.is_file():
                    continue
                stat = path.stat()
                marker = (stat.st_mtime_ns, stat.st_size, path.name)
                if newest is None or marker > newest:
                    newest = marker
        except OSError:
            return None
        return newest

    @staticmethod
    def _capture(
        command: list[str],
        cwd: Path,
        environment: Mapping[str, str],
        timeout: int,
        inactivity_timeout: int | None = None,
        cancellation: threading.Event | None = None,
        progress: Callable[[Mapping[str, Any]], None] | None = None,
        activity_root: Path | None = None,
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
        process_pid = process.pid
        process_pgid = os.getpgid(process.pid)
        output_tail = bytearray()
        output_digest = hashlib.sha256()
        total = 0
        cap = 64 * 1024
        output_lock = threading.Lock()
        last_activity = started
        last_activity_source = "process_start"
        observed_members: dict[int, dict[str, Any]] = {}
        next_process_scan = started
        next_activity_scan = started
        activity_marker = CommandRunner._task_activity_marker(activity_root)

        def drain() -> None:
            nonlocal total, last_activity, last_activity_source
            assert process.stdout is not None
            while True:
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    return
                with output_lock:
                    total += len(chunk)
                    last_activity = time.monotonic()
                    last_activity_source = "combined_stdout"
                    output_digest.update(chunk)
                    output_tail.extend(chunk)
                    if len(output_tail) > cap:
                        del output_tail[: len(output_tail) - cap]

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        timed_out = False
        timeout_kind: str | None = None
        cancelled = False
        next_progress = started

        def progress_snapshot() -> None:
            if progress is None:
                return
            with output_lock:
                current_output = bytes(output_tail).decode("utf-8", errors="replace")
                current_total = total
                current_digest = output_digest.copy().hexdigest()
                current_activity = last_activity
                current_activity_source = last_activity_source
            progress(
                {
                    "pid": process_pid,
                    "pgid": process_pgid,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "output": redact(current_output),
                    "output_bytes": current_total,
                    "output_sha256": current_digest,
                    "truncated": current_total > len(output_tail),
                    "observed_processes": list(observed_members.values())[:128],
                    "last_activity_age_seconds": round(
                        max(0.0, time.monotonic() - current_activity), 3
                    ),
                    "activity_source": current_activity_source,
                }
            )

        def terminate_group(sig: int) -> None:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                return

        while process.poll() is None:
            now = time.monotonic()
            if now >= next_process_scan:
                for member in CommandRunner._process_group_snapshot(process_pgid):
                    observed_members[member["pid"]] = member
                next_process_scan = now + 1.0
            if now >= next_activity_scan:
                current_marker = CommandRunner._task_activity_marker(activity_root)
                if current_marker is not None and current_marker != activity_marker:
                    with output_lock:
                        last_activity = now
                        last_activity_source = "task_log"
                    activity_marker = current_marker
                next_activity_scan = now + 0.25
            if now >= next_progress:
                progress_snapshot()
                next_progress = now + 2.0
            if cancellation is not None and cancellation.is_set():
                cancelled = True
                terminate_group(signal.SIGTERM)
                break
            if now - started >= timeout:
                timed_out = True
                timeout_kind = "wall_clock"
                terminate_group(signal.SIGTERM)
                break
            with output_lock:
                inactivity_age = now - last_activity
            if inactivity_timeout is not None and inactivity_age >= inactivity_timeout:
                timed_out = True
                timeout_kind = "task_inactivity"
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
        progress_snapshot()
        with output_lock:
            output = bytes(output_tail).decode("utf-8", errors="replace")
            final_total = total
            final_digest = output_digest.hexdigest()
        output, text_truncated = bounded_text(output, cap)
        return {
            "return_code": return_code,
            "pid": process_pid,
            "pgid": process_pgid,
            "timed_out": timed_out,
            "timeout_kind": timeout_kind,
            "cancelled": cancelled,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output": redact(output),
            "output_bytes": final_total,
            "output_sha256": final_digest,
            "truncated": text_truncated or final_total > len(output_tail),
            "observed_processes": list(observed_members.values())[:128],
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
            "evidence_id": run_id,
            "steps": [],
        }
        with self._lock:
            if len(self._runs) >= 128:
                completed = next(
                    (
                        key
                        for key, value in self._runs.items()
                        if value["status"] in ("completed", "failed", "timed_out", "cancelled", "unknown")
                    ),
                    None,
                )
                if completed is None:
                    raise MCPDomainError("run registry is full", code="runner_busy")
                self._runs.pop(completed, None)
                self._cancellations.pop(completed, None)
            self._runs[run_id] = record
        self._persist_record(record)
        return record

    def _persist_record(self, record: Mapping[str, Any]) -> None:
        audit_path = self.config.audit_path()
        if audit_path is None:
            return
        root = audit_path.parent / "run-records"
        steps = []
        for step in record.get("steps", []):
            steps.append(
                {
                    key: step.get(key)
                    for key in (
                        "id", "return_code", "pid", "pgid", "timed_out", "timeout_kind",
                        "cancelled", "duration_seconds", "output_bytes", "output_sha256",
                        "truncated", "working_root_role", "timeout_seconds",
                        "inactivity_timeout_seconds", "observed_processes",
                        "activity_root_role", "activity_source", "last_activity_age_seconds",
                    )
                }
            )
        payload = redact(
            {
                "schema": "fluorite.run-status/v1",
                "evidence_id": record["evidence_id"],
                "run_id": record["run_id"],
                "ticket_id": record["ticket_id"],
                "runbook_id": record["runbook_id"],
                "risk": record["risk"],
                "plan_id": record["plan_id"],
                "plan_digest": record["plan_digest"],
                "status": record["status"],
                "created_at": record["created_at"],
                "started_at": record.get("started_at"),
                "finished_at": record.get("finished_at"),
                "steps": steps,
            }
        )
        try:
            root.mkdir(parents=True, exist_ok=True)
            destination = root / f"{record['run_id']}.json"
            temporary = root / f".{record['run_id']}.{uuid.uuid4().hex}.tmp"
            temporary.write_text(
                json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, destination)
        except OSError:
            record.setdefault("audit_warnings", []).append(
                "the durable run status could not be written"
            )

    def _perform(
        self,
        record: dict[str, Any],
        runbook: Runbook,
        plan: Mapping[str, Any],
        cancellation: threading.Event | None = None,
    ) -> None:
        record["status"] = "running"
        record["started_at"] = observed_at()
        self._persist_record(record)
        for step in runbook.steps:
            if cancellation is not None and cancellation.is_set():
                record["status"] = "cancelled"
                break
            command, environment = self._command(step, plan["parameters"])
            active_step: dict[str, Any] = {
                "id": step.step_id,
                "argv": redact(self._render_argv(step, plan["parameters"])),
                "working_root_role": step.root,
                "timeout_seconds": step.timeout_seconds,
                "inactivity_timeout_seconds": step.inactivity_timeout_seconds,
                "activity_root_role": step.activity_root,
                "return_code": None,
                "timed_out": False,
                "timeout_kind": None,
                "cancelled": False,
                "duration_seconds": 0.0,
                "output": "",
                "output_bytes": 0,
                "output_sha256": hashlib.sha256(b"").hexdigest(),
                "truncated": False,
                "pid": None,
                "pgid": None,
                "observed_processes": [],
                "activity_source": "process_start",
                "last_activity_age_seconds": 0.0,
            }
            record["steps"].append(active_step)
            self._persist_record(record)

            def update_progress(snapshot: Mapping[str, Any]) -> None:
                active_step.update(snapshot)
                self._persist_record(record)

            outcome = self._capture(
                command,
                self._resolve_root(step.root),
                environment,
                step.timeout_seconds,
                step.inactivity_timeout_seconds,
                cancellation,
                update_progress,
                self._resolve_root(step.activity_root) if step.activity_root else None,
            )
            active_step.update(outcome)
            self._persist_record(record)
            if active_step["cancelled"]:
                record["status"] = "cancelled"
                break
            if active_step["timed_out"]:
                record["status"] = "timed_out"
                break
            if active_step["return_code"] != 0:
                record["status"] = "failed"
                break
        else:
            record["status"] = "completed"
        record["finished_at"] = observed_at()
        self._persist_record(record)
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
                        "inactivity_timeout_seconds": step["inactivity_timeout_seconds"],
                        "return_code": step["return_code"],
                        "timed_out": step["timed_out"],
                        "timeout_kind": step["timeout_kind"],
                        "cancelled": step["cancelled"],
                        "duration_seconds": step["duration_seconds"],
                        "output_bytes": step["output_bytes"],
                        "output_sha256": step["output_sha256"],
                        "truncated": step["truncated"],
                        "pid": step["pid"],
                        "pgid": step["pgid"],
                        "observed_processes": step["observed_processes"],
                        "activity_root_role": step["activity_root_role"],
                        "activity_source": step["activity_source"],
                        "last_activity_age_seconds": step["last_activity_age_seconds"],
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
                record["status"] = "unknown"
                record["finished_at"] = observed_at()
                self._persist_record(record)

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
                    "timeout_kind": step["timeout_kind"],
                    "cancelled": step["cancelled"],
                    "duration_seconds": step["duration_seconds"],
                    "output_bytes": step["output_bytes"],
                    "output_sha256": step["output_sha256"],
                    "truncated": step["truncated"],
                    "pid": step.get("pid"),
                    "pgid": step.get("pgid"),
                    "observed_processes": step.get("observed_processes", []),
                    "activity_source": step.get("activity_source"),
                    "last_activity_age_seconds": step.get("last_activity_age_seconds"),
                    "working_root_role": step["working_root_role"],
                    "timeout_seconds": step["timeout_seconds"],
                    "inactivity_timeout_seconds": step["inactivity_timeout_seconds"],
                    "activity_root_role": step.get("activity_root_role"),
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

    def load_completion(self, run_id: str) -> dict[str, Any]:
        path = self.config.audit_path()
        if path is None:
            raise MCPDomainError("completion record is unavailable", code="unknown_run")
        durable = path.parent / "run-records" / f"{run_id}.json"
        if durable.is_file():
            try:
                record = json.loads(durable.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise MCPDomainError("completion record is unavailable", code="unknown_run") from exc
            if record.get("status") in ("queued", "running"):
                record["status"] = "unknown"
                record["recovery_note"] = (
                    "supervisor restart interrupted final-state observation"
                )
            return record
        if not path.is_file():
            raise MCPDomainError("completion record is unavailable", code="unknown_run")
        found = None
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("schema") == "fluorite.run-lifecycle/v1" and event.get("run_id") == run_id:
                    found = event
        except OSError as exc:
            raise MCPDomainError("completion record is unavailable", code="unknown_run") from exc
        if found is None:
            raise MCPDomainError("unknown run id", code="unknown_run")
        return found
