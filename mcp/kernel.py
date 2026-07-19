"""Cross-cutting kernel: envelopes, privacy, paging, evidence and audit.

Only technical concerns live here.  Each bounded context owns the meaning and
shape of the object placed in ``payload``.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .errors import MCPDomainError

ENVELOPE_SCHEMA = "fluorite.mcp-envelope/v1"
REDACTION_POLICY = "fluorite.privacy-redaction/v1"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_RESPONSE_BYTES = 128 * 1024
_LOCATOR_KEYS = frozenset(
    {
        "location",
        "relative_path",
        "root",
        "path",
        "start_line",
        "end_line",
        "next_start_line",
        "total_lines",
        "next_cursor",
        "run_id",
        "plan_id",
        "status",
        "file_bytes",
        "scanned_tail_bytes",
    }
)

_SECRET_KEYS = re.compile(
    r"(?:pass(?:word)?|secret|token|credential|authorization|api[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+")
_URL_CREDENTIAL = re.compile(r"(https?://)[^/@\s:]+:[^/@\s]+@", re.IGNORECASE)
_ACCOUNT_HOST = re.compile(
    r"(?<![A-Za-z0-9._/-])(?:ssh://)?[A-Za-z0-9._-]+@(?:[A-Za-z0-9._-]+|\[[^]]+\])",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?im)\b([A-Za-z0-9_-]*(?:pass(?:word)?|secret|token|credential|authorization|api[_-]?key|"
    r"private[_-]?key)[A-Za-z0-9_-]*)\s*[:=]\s*(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s,;}]+)"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----",
    re.DOTALL,
)
_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_IPV6_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9:.\[])(?=[A-Fa-f0-9:.]*:)[A-Fa-f0-9:.]{2,}(?![A-Za-z0-9:.\]])"
)
_IPV6_BRACKETED = re.compile(
    r"(?<![A-Za-z0-9_])\[(?=[A-Fa-f0-9:.]*:)[A-Fa-f0-9:.]{2,}\](?![A-Za-z0-9_])"
)
_PRIVATE_HOSTNAME = re.compile(
    r"(?<![A-Za-z0-9_/@$.-])"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"(?:internal|local|lan|corp|private|localdomain)"
    r"(?![A-Za-z0-9_.-])",
    re.IGNORECASE,
)
_FQDN = re.compile(
    r"(?<![A-Za-z0-9_/@$.-])"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"(?:com|net|org|io|dev|ai|app|cloud|co|jp|us|uk|de|fr|test)"
    r"(?![A-Za-z0-9_.-])",
    re.IGNORECASE,
)
_HOST_ASSIGNMENT = re.compile(
    r"(?im)\b(host(?:name)?|node(?:name)?|machine)\s*[:=]\s*"
    r"(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s,;}]+)"
)
_USER_HOME = re.compile(r"/(?:Users|home)/[^/\s]+")


def observed_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _redact_ipv6_candidate(match: re.Match[str]) -> str:
    candidate = match.group(0)
    try:
        ipaddress.IPv6Address(candidate)
    except ValueError:
        return candidate
    return "$IP"


def _redact_bracketed_ipv6(match: re.Match[str]) -> str:
    candidate = match.group(0)[1:-1]
    try:
        ipaddress.IPv6Address(candidate)
    except ValueError:
        return match.group(0)
    return "$IP"


def _redact_text(value: str) -> str:
    value = _PRIVATE_KEY.sub("[REDACTED_PRIVATE_KEY]", value)
    value = _BEARER.sub(lambda match: f"{match.group(1)} [REDACTED]", value)
    value = _URL_CREDENTIAL.sub(r"\1[REDACTED]@", value)
    value = _ACCOUNT_HOST.sub("[REDACTED_ACCOUNT_HOST]", value)
    value = _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    value = _HOST_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED_HOST]", value)
    value = _PRIVATE_HOSTNAME.sub("$HOST", value)
    value = _FQDN.sub("$HOST", value)
    value = _USER_HOME.sub("$HOME", value)
    value = _IPV4.sub("$IP", value)
    value = _IPV6_BRACKETED.sub(_redact_bracketed_ipv6, value)
    value = _IPV6_CANDIDATE.sub(_redact_ipv6_candidate, value)

    home = str(Path.home())
    if home and home != "/":
        value = value.replace(home, "$HOME")
    for key in ("USER", "LOGNAME", "HOSTNAME"):
        candidate = os.environ.get(key, "")
        if candidate and len(candidate) >= 3:
            value = value.replace(candidate, f"${key}")
    return value


def redact(value: Any, *, key: str = "") -> Any:
    """Recursively remove credentials, host identity and personal locations."""

    if _SECRET_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


def bounded_text(value: str, limit: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value, False
    marker = b"\n[OUTPUT TRUNCATED]\n"
    keep = max(0, limit - len(marker))
    result = encoded[:keep].decode("utf-8", errors="replace") + marker.decode()
    return result, True


def _payload_locators(value: Any, *, limit: int = 4) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def visit(item: Any) -> None:
        if len(records) >= limit:
            return
        if isinstance(item, Mapping):
            locator: dict[str, Any] = {}
            for key in _LOCATOR_KEYS:
                candidate = item.get(key)
                if candidate is None or not isinstance(candidate, (str, int, bool)):
                    continue
                if isinstance(candidate, str):
                    candidate, _ = bounded_text(candidate, 256)
                locator[key] = candidate
            if locator:
                records.append(locator)
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)
    return records


def encode_cursor(offset: int) -> str:
    raw = f"v1:{offset}".encode("ascii")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded).decode("ascii")
        version, offset = raw.split(":", 1)
        if version != "v1" or not offset.isdigit():
            raise ValueError
        return int(offset)
    except (ValueError, UnicodeError) as exc:
        raise MCPDomainError("cursor is invalid", code="invalid_cursor") from exc


@dataclass(frozen=True)
class Page:
    items: list[Any]
    next_cursor: str | None
    truncated: bool


def paginate(
    values: Sequence[Any], cursor: str | None = None, limit: int = DEFAULT_PAGE_SIZE
) -> Page:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_PAGE_SIZE:
        raise MCPDomainError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
    offset = decode_cursor(cursor)
    if offset > len(values):
        raise MCPDomainError("cursor is outside the result set", code="invalid_cursor")
    end = min(len(values), offset + limit)
    return Page(
        items=list(values[offset:end]),
        next_cursor=encode_cursor(end) if end < len(values) else None,
        truncated=end < len(values),
    )


class EvidenceStore:
    """Creates stable, privacy-safe evidence handles for observations.

    The store deliberately retains only redacted summaries in memory.  Source
    content remains in its bounded context and is never written by default.
    """

    def __init__(self, max_records: int = 512) -> None:
        self._max_records = max_records
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record(self, domain: str, operation: str, value: Any) -> str:
        safe = redact(value)
        canonical = json.dumps(safe, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(
            f"{domain}\0{operation}\0{canonical}".encode("utf-8")
        ).hexdigest()[:20]
        evidence_id = f"ev-{domain.replace('_', '-')}-{digest}"
        with self._lock:
            if evidence_id not in self._records and len(self._records) >= self._max_records:
                oldest = next(iter(self._records))
                del self._records[oldest]
            self._records[evidence_id] = {
                "domain": domain,
                "operation": operation,
                "summary_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            }
        return evidence_id


AuditSink = Callable[[dict[str, Any]], None]


class AuditHook:
    """Best-effort audit fan-out.  Audit failure never leaks into tool output."""

    def __init__(self, path: Path | None = None, sinks: Iterable[AuditSink] = ()) -> None:
        self._path = path
        self._sinks = tuple(sinks)
        self._lock = threading.Lock()

    def emit(self, event: Mapping[str, Any]) -> list[str]:
        safe_event = redact(dict(event))
        warnings: list[str] = []
        for sink in self._sinks:
            try:
                sink(safe_event)
            except Exception:  # audit extensions must not break the protocol
                warnings.append("an audit sink failed")
        if self._path is not None:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                line = json.dumps(safe_event, sort_keys=True, ensure_ascii=False) + "\n"
                with self._lock, self._path.open("a", encoding="utf-8") as handle:
                    handle.write(line)
            except OSError:
                warnings.append("the audit file could not be written")
        return warnings


@dataclass
class Kernel:
    domain: str
    subject_id: str = "repository"
    revision_or_image_id: str | None = None
    evidence: EvidenceStore = field(default_factory=EvidenceStore)
    audit: AuditHook = field(default_factory=AuditHook)
    max_response_bytes: int = MAX_RESPONSE_BYTES

    def envelope(
        self,
        operation: str,
        payload: Mapping[str, Any],
        *,
        unknowns: Iterable[str] = (),
        warnings: Iterable[str] = (),
        truncated: bool = False,
        next_queries: Iterable[str] = (),
    ) -> dict[str, Any]:
        safe_payload = redact(dict(payload))
        identity_status = (
            "sufficient" if self.revision_or_image_id is not None else "insufficient"
        )
        safe_unknowns = list(unknowns)
        if identity_status == "insufficient":
            identity_unknown = (
                "revision_or_image_id is not configured; evidence identity is insufficient"
            )
            if identity_unknown not in safe_unknowns:
                safe_unknowns.append(identity_unknown)
        evidence_id = self.evidence.record(
            self.domain,
            operation,
            {
                "subject_id": self.subject_id,
                "revision_or_image_id": self.revision_or_image_id,
                "payload": safe_payload,
            },
        )
        result: dict[str, Any] = {
            "schema": ENVELOPE_SCHEMA,
            "bounded_context": self.domain,
            "operation": operation,
            "subject_id": self.subject_id,
            "revision_or_image_id": self.revision_or_image_id,
            "identity_status": identity_status,
            "observed_at": observed_at(),
            "payload": safe_payload,
            "unknowns": safe_unknowns,
            "evidence_ids": [evidence_id],
            "truncated": bool(truncated),
            "warnings": list(warnings),
            "next_queries": list(next_queries),
            "redaction_policy": REDACTION_POLICY,
            "explainability": {
                "classification": "bounded_observation",
                "basis_evidence_ids": [evidence_id],
                "causal_claims": [],
                "limitations": safe_unknowns + list(warnings),
                "next_actions": list(next_queries),
            },
        }
        serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > self.max_response_bytes:
            locators = _payload_locators(safe_payload)
            result["payload"] = {
                "output_cap": self.max_response_bytes,
                "summary": "payload omitted because the bounded response cap was exceeded",
                "payload_keys": sorted(str(key) for key in safe_payload),
                "resume_locators": locators,
            }
            result["truncated"] = True
            result["warnings"].append("response payload exceeded the configured cap")
            result["explainability"]["limitations"] = safe_unknowns + result["warnings"]
            serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            if len(serialized.encode("utf-8")) > self.max_response_bytes:
                result["payload"]["resume_locators"] = locators[:1]
        return result

    def audit_call(
        self,
        operation: str,
        arguments: Mapping[str, Any],
        *,
        status: str,
        evidence_ids: Iterable[str] = (),
        error_code: str | None = None,
    ) -> list[str]:
        event = {
            "schema": "fluorite.mcp-audit/v1",
            "observed_at": observed_at(),
            "bounded_context": self.domain,
            "operation": operation,
            "arguments": arguments,
            "status": status,
            "evidence_ids": list(evidence_ids),
        }
        if error_code:
            event["error_code"] = error_code
        return self.audit.emit(event)
