"""Local, role-based MCP configuration."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import ConfigurationError
from .kernel import AuditHook, Kernel


_IDENTITY_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:+-]{0,127}$")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be a JSON object")
    return value


@dataclass(frozen=True)
class MCPConfig:
    data: Mapping[str, Any]
    source: Path | None = None

    @classmethod
    def load(cls, path: str | Path | None = None) -> "MCPConfig":
        selected = path or os.environ.get("FLUORITE_MCP_CONFIG")
        if not selected:
            return cls(data={})
        config_path = Path(selected).expanduser().resolve()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError("FLUORITE_MCP_CONFIG could not be loaded") from exc
        return cls(data=_as_mapping(data, "configuration"), source=config_path)

    def roots(self, domain: str) -> dict[str, Path]:
        roots: dict[str, Path] = {"repository": repository_root()}
        domains = _as_mapping(self.data.get("domains", {}), "domains")
        domain_data = _as_mapping(domains.get(domain, {}), f"domains.{domain}")
        configured = _as_mapping(domain_data.get("roots", {}), f"domains.{domain}.roots")
        for alias, raw_path in configured.items():
            if not isinstance(alias, str) or not alias.replace("_", "").isalnum():
                raise ConfigurationError(f"invalid root alias for {domain}")
            if alias == "repository":
                raise ConfigurationError("repository is a reserved root alias")
            if not isinstance(raw_path, str):
                raise ConfigurationError(f"root {domain}.{alias} must be a string")
            roots[alias] = Path(raw_path).expanduser().resolve()
        return roots

    def identity(self, domain: str) -> tuple[str, str | None]:
        domains = _as_mapping(self.data.get("domains", {}), "domains")
        domain_data = _as_mapping(domains.get(domain, {}), f"domains.{domain}")
        identity = _as_mapping(domain_data.get("identity", {}), f"domains.{domain}.identity")
        unsupported = set(identity) - {"subject_id", "revision_or_image_id"}
        if unsupported:
            raise ConfigurationError(f"identity for {domain} contains an unsupported key")

        subject_id = identity.get("subject_id", f"{domain}:repository")
        revision = identity.get("revision_or_image_id")
        if not isinstance(subject_id, str) or not _IDENTITY_VALUE.fullmatch(subject_id):
            raise ConfigurationError(f"identity subject_id for {domain} is invalid")
        if revision is not None and (
            not isinstance(revision, str) or not _IDENTITY_VALUE.fullmatch(revision)
        ):
            raise ConfigurationError(
                f"identity revision_or_image_id for {domain} is invalid"
            )
        return subject_id, revision

    def command_runner(self) -> Mapping[str, Any]:
        return _as_mapping(self.data.get("command_runner", {}), "command_runner")

    def execution_allowed(self) -> bool:
        configured = self.command_runner().get("allow_execution", False)
        if not isinstance(configured, bool):
            raise ConfigurationError("command_runner.allow_execution must be a boolean")
        environment = os.environ.get("FLUORITE_MCP_ALLOW_EXECUTION", "") == "1"
        return configured and environment

    def audit_path(self) -> Path | None:
        raw = self.data.get("audit_file") or os.environ.get("FLUORITE_MCP_AUDIT_LOG")
        if not raw:
            return None
        if not isinstance(raw, str):
            raise ConfigurationError("audit_file must be a string")
        return Path(raw).expanduser().resolve()

    def kernel(self, domain: str) -> Kernel:
        raw_cap = self.data.get("max_response_bytes", 128 * 1024)
        if isinstance(raw_cap, bool) or not isinstance(raw_cap, int):
            raise ConfigurationError("max_response_bytes must be an integer")
        cap = min(max(raw_cap, 4096), 512 * 1024)
        subject_id, revision = self.identity(domain)
        return Kernel(
            domain=domain,
            subject_id=subject_id,
            revision_or_image_id=revision,
            audit=AuditHook(self.audit_path()),
            max_response_bytes=cap,
        )
