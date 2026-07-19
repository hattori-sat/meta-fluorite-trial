"""Small MCP stdio transport supporting the tools capability."""

from __future__ import annotations

import copy
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, TextIO

from . import __version__
from .errors import MCPDomainError
from .kernel import Kernel, redact

SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")

ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def _validate_schema(value: Any, schema: Mapping[str, Any], path: str = "arguments") -> None:
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise MCPDomainError(f"{path} must be an object", code="invalid_arguments")
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise MCPDomainError("tool schema is invalid", code="internal_error")
        required = schema.get("required", ())
        for name in required if isinstance(required, list) else ():
            if name not in value:
                raise MCPDomainError(
                    f"{path}.{name} is required", code="invalid_arguments"
                )
        additional = schema.get("additionalProperties", True)
        for name, item in value.items():
            child_schema = properties.get(name)
            if child_schema is None:
                if additional is False:
                    raise MCPDomainError(
                        f"{path} contains unsupported field {name}",
                        code="invalid_arguments",
                    )
                if isinstance(additional, Mapping):
                    _validate_schema(item, additional, f"{path}.{name}")
                continue
            if isinstance(child_schema, Mapping):
                _validate_schema(item, child_schema, f"{path}.{name}")
        return
    if expected == "string":
        if not isinstance(value, str):
            raise MCPDomainError(f"{path} must be a string", code="invalid_arguments")
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise MCPDomainError(f"{path} is too short", code="invalid_arguments")
        if isinstance(maximum, int) and len(value) > maximum:
            raise MCPDomainError(f"{path} is too long", code="invalid_arguments")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            raise MCPDomainError(f"{path} has an invalid format", code="invalid_arguments")
    elif expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise MCPDomainError(f"{path} must be an integer", code="invalid_arguments")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, int) and value < minimum:
            raise MCPDomainError(f"{path} is below its minimum", code="invalid_arguments")
        if isinstance(maximum, int) and value > maximum:
            raise MCPDomainError(f"{path} is above its maximum", code="invalid_arguments")
    elif expected == "boolean":
        if not isinstance(value, bool):
            raise MCPDomainError(f"{path} must be a boolean", code="invalid_arguments")

    choices = schema.get("enum")
    if isinstance(choices, list) and value not in choices:
        raise MCPDomainError(f"{path} is outside the allowed values", code="invalid_arguments")


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    handler: ToolHandler
    read_only: bool = True
    destructive: bool = False
    idempotent: bool = True
    open_world: bool = False

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": dict(self.input_schema),
            "annotations": {
                "readOnlyHint": self.read_only,
                "destructiveHint": self.destructive,
                "idempotentHint": self.idempotent,
                "openWorldHint": self.open_world,
            },
        }


class MCPServer:
    def __init__(
        self,
        name: str,
        kernel: Kernel,
        tools: list[Tool],
        *,
        root_aliases: tuple[str, ...] | list[str] = (),
    ) -> None:
        self.name = name
        self.kernel = kernel
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("tool names must be unique")
        self._initialized = False
        self._protocol = SUPPORTED_PROTOCOLS[0]
        self._root_aliases = tuple(sorted(root_aliases))

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def _initialize(self, params: Mapping[str, Any]) -> dict[str, Any]:
        requested = params.get("protocolVersion", SUPPORTED_PROTOCOLS[0])
        self._protocol = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
        self._initialized = True
        return {
            "protocolVersion": self._protocol,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": f"fluorite-{self.name}-mcp", "version": __version__},
            "instructions": (
                f"Bounded context: {self.name}. Tool output is capped, redacted and evidence-linked. "
                "Do not interpret observations as causal conclusions."
            ),
        }

    def _tools_list(self, params: Mapping[str, Any]) -> dict[str, Any]:
        if params.get("cursor") not in (None, ""):
            return {"tools": []}
        descriptors = []
        for name in sorted(self._tools):
            descriptor = copy.deepcopy(self._tools[name].descriptor())
            root_schema = descriptor["inputSchema"].get("properties", {}).get("root")
            if self._root_aliases and isinstance(root_schema, dict):
                root_schema["enum"] = list(self._root_aliases)
            descriptors.append(descriptor)
        return {"tools": descriptors}

    def _tools_call(self, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or name not in self._tools:
            return self._tool_error(name or "unknown", {}, "unknown tool", "unknown_tool")
        if not isinstance(arguments, dict):
            return self._tool_error(name, {}, "arguments must be an object", "invalid_arguments")
        try:
            tool = self._tools[name]
            _validate_schema(arguments, tool.input_schema)
            result = dict(tool.handler(arguments))
            evidence = result.get("evidence_ids", [])
            audit_warnings = self.kernel.audit_call(
                name, arguments, status="ok", evidence_ids=evidence if isinstance(evidence, list) else ()
            )
            if audit_warnings:
                result.setdefault("warnings", []).extend(audit_warnings)
            text = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            return {
                "content": [{"type": "text", "text": text}],
                "structuredContent": result,
                "isError": False,
            }
        except MCPDomainError as exc:
            return self._tool_error(name, arguments, str(exc), exc.code)
        except Exception:
            return self._tool_error(
                name, arguments, "internal tool failure; inspect the local audit sink", "internal_error"
            )

    def _tool_error(
        self, name: str, arguments: Mapping[str, Any], message: str, code: str
    ) -> dict[str, Any]:
        self.kernel.audit_call(name, arguments, status="error", error_code=code)
        safe = redact({"error": {"code": code, "message": message}})
        return {
            "content": [{"type": "text", "text": json.dumps(safe, ensure_ascii=False)}],
            "structuredContent": safe,
            "isError": True,
        }

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        is_notification = "id" not in request
        if request.get("jsonrpc") != "2.0" or not isinstance(method, str):
            if is_notification:
                return None
            return self._error(request_id, -32600, "Invalid Request")
        params = request.get("params", {})
        if not isinstance(params, dict):
            if is_notification:
                return None
            return self._error(request_id, -32602, "Invalid params")
        if method in ("notifications/initialized", "notifications/cancelled"):
            return None
        if is_notification:
            return None
        if method == "initialize":
            result = self._initialize(params)
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = self._tools_list(params)
        elif method == "tools/call":
            result = self._tools_call(params)
        else:
            return self._error(request_id, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def serve(self, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
        for raw_line in stdin:
            if not raw_line.strip():
                continue
            try:
                message = json.loads(raw_line)
                if not isinstance(message, dict):
                    response = self._error(None, -32600, "Invalid Request")
                else:
                    response = self.dispatch(message)
            except json.JSONDecodeError:
                response = self._error(None, -32700, "Parse error")
            if response is not None:
                stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                stdout.flush()


def object_schema(
    properties: Mapping[str, Any], *, required: tuple[str, ...] = (), additional: bool = False
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required),
        "additionalProperties": additional,
    }


ROOT_PROPERTY = {
    "type": "string",
    "description": "Configured root alias; use a value exposed by the server configuration.",
    "default": "repository",
    "maxLength": 128,
}
CURSOR_PROPERTY = {
    "type": "string",
    "description": "Opaque cursor returned by the prior call.",
    "maxLength": 256,
}
LIMIT_PROPERTY = {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
PATH_PROPERTY = {
    "type": "string",
    "description": "Relative path inside the selected root.",
    "minLength": 1,
    "maxLength": 1024,
}
