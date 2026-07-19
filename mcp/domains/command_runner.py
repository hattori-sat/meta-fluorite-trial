"""Command-runner bounded context; the only state-changing MCP server."""

from __future__ import annotations

from typing import Any, Mapping

from ..config import MCPConfig
from ..domain_support import int_arg, page_args, string_arg
from ..protocol import CURSOR_PROPERTY, LIMIT_PROPERTY, MCPServer, Tool, object_schema
from ..runbook import CommandRunner


def create_server(config: MCPConfig) -> MCPServer:
    kernel = config.kernel("command_runner")
    runner = CommandRunner(config)

    def list_runbooks(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        cursor, limit = page_args(arguments)
        from ..kernel import paginate

        page = paginate(runner.catalog(), cursor, limit)
        return kernel.envelope(
            "list_runbooks",
            {"runbooks": page.items, "next_cursor": page.next_cursor},
            truncated=page.truncated,
            next_queries=("describe_runbook", "plan_runbook") if page.items else (),
        )

    def describe(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        description = runner.describe(string_arg(arguments, "runbook_id", required=True))
        return kernel.envelope("describe_runbook", {"runbook": description}, next_queries=("plan_runbook",))

    def plan(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        result = runner.plan(
            string_arg(arguments, "runbook_id", required=True),
            arguments.get("parameters", {}),
            string_arg(arguments, "ticket_id", required=True),
        )
        return kernel.envelope(
            "plan_runbook",
            {"execution_plan": result},
            next_queries=("start_runbook", "execute_runbook"),
            warnings=("plan_id is a confirmation challenge, not proof of external operator approval",),
        )

    def execute(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        dry_run = arguments.get("dry_run", True)
        if not isinstance(dry_run, bool):
            from ..errors import MCPDomainError

            raise MCPDomainError("dry_run must be a boolean")
        runbook_id = string_arg(arguments, "runbook_id", required=True)
        ticket_id = string_arg(arguments, "ticket_id", required=True)
        parameters = arguments.get("parameters", {})
        if dry_run:
            result = runner.plan(runbook_id, parameters, ticket_id)
            return kernel.envelope(
                "execute_runbook",
                {"dry_run": True, "execution_plan": result},
                warnings=("no command was executed",),
            )
        result = runner.execute(
            runbook_id, parameters, ticket_id, arguments.get("confirmation")
        )
        truncated = any(bool(step.get("truncated")) for step in result["steps"])
        return kernel.envelope(
            "execute_runbook",
            {"dry_run": False, "run_result": result},
            truncated=truncated,
            next_queries=("read_run_log",),
        )

    def start(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        result = runner.start(
            string_arg(arguments, "runbook_id", required=True),
            arguments.get("parameters", {}),
            string_arg(arguments, "ticket_id", required=True),
            arguments.get("confirmation"),
        )
        return kernel.envelope(
            "start_runbook",
            {"run_status": result},
            next_queries=("get_run_status", "read_run_log", "cancel_run"),
        )

    def status(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        result = runner.status(string_arg(arguments, "run_id", required=True))
        return kernel.envelope(
            "get_run_status",
            {"run_status": result},
            next_queries=("read_run_log",) if result["steps"] else (),
        )

    def cancel(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        result = runner.cancel(string_arg(arguments, "run_id", required=True))
        return kernel.envelope("cancel_run", {"cancellation": result})

    def read_log(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        cursor, limit = page_args(arguments)
        result = runner.run_log(string_arg(arguments, "run_id", required=True), cursor, limit)
        return kernel.envelope("read_run_log", {"run_log": result}, truncated=bool(result["truncated"]))

    runbook_id = {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"}
    ticket_id = {"type": "string", "pattern": "^FLR-[0-9]{4}$"}
    parameters = {
        "type": "object",
        "description": "Only manifest-defined enum parameters are accepted.",
        "additionalProperties": {"type": "string"},
    }
    execution_schema = object_schema(
        {
            "runbook_id": runbook_id,
            "ticket_id": ticket_id,
            "parameters": parameters,
            "confirmation": {"type": "string", "description": "Fresh plan_id returned by plan_runbook."},
        },
        required=("runbook_id", "ticket_id", "confirmation"),
    )
    return MCPServer(
        "command_runner",
        kernel,
        [
            Tool("list_runbooks", "List fixed, Git-managed runbooks and their effect classes.", object_schema({"cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}), list_runbooks),
            Tool("describe_runbook", "Describe a fixed runbook without resolving or executing a command.", object_schema({"runbook_id": runbook_id}, required=("runbook_id",)), describe),
            Tool(
                "plan_runbook",
                "Resolve allowlisted enum parameters, roots and fixed environment profiles without execution.",
                object_schema(
                    {
                        "runbook_id": runbook_id,
                        "ticket_id": ticket_id,
                        "parameters": parameters,
                    },
                    required=("runbook_id", "ticket_id"),
                ),
                plan,
            ),
            Tool(
                "execute_runbook",
                "Dry-run by default. Real execution needs dual local enablement and a fresh plan_id confirmation.",
                object_schema(
                    {
                        "runbook_id": runbook_id,
                        "ticket_id": ticket_id,
                        "parameters": parameters,
                        "dry_run": {"type": "boolean", "default": True},
                        "confirmation": {"type": "string", "description": "Fresh plan_id returned by plan_runbook."},
                    },
                    required=("runbook_id", "ticket_id"),
                ),
                execute,
                read_only=False,
                destructive=True,
                idempotent=False,
            ),
            Tool(
                "start_runbook",
                "Start an allowlisted runbook asynchronously after all execution gates pass.",
                execution_schema,
                start,
                read_only=False,
                destructive=True,
                idempotent=False,
            ),
            Tool(
                "get_run_status",
                "Read bounded status for a process owned by this server instance.",
                object_schema({"run_id": {"type": "string"}}, required=("run_id",)),
                status,
            ),
            Tool(
                "read_run_log",
                "Read a bounded, privacy-redacted log page retained for this server process.",
                object_schema({"run_id": {"type": "string"}, "cursor": CURSOR_PROPERTY, "limit": LIMIT_PROPERTY}, required=("run_id",)),
                read_log,
            ),
            Tool(
                "cancel_run",
                "Request termination of a process owned by this server instance; unrelated processes are inaccessible.",
                object_schema({"run_id": {"type": "string"}}, required=("run_id",)),
                cancel,
                read_only=False,
                destructive=True,
                idempotent=True,
            ),
        ],
    )
