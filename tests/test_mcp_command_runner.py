from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp.config import MCPConfig
from mcp.errors import ConfigurationError, MCPDomainError
from mcp.runbook import CommandRunner, RunbookRegistry


class RunbookRegistryTests(unittest.TestCase):
    def test_installed_manifests_load_and_have_finite_parameters(self) -> None:
        registry = RunbookRegistry()
        self.assertIn("repository-baseline", registry.runbooks)
        self.assertEqual(
            {
                "host-capacity", "repository-baseline", "qemux86-64-fluorite",
                "yocto-metadata-gate", "yocto-demo-compile", "yocto-image-build",
            },
            set(registry.runbooks),
        )
        self.assertNotIn("yocto-parse", registry.runbooks)
        self.assertNotIn("yocto-dry-run", registry.runbooks)
        self.assertIn("yocto-image-build", registry.runbooks)
        self.assertNotIn("yocto-effective-environment", registry.runbooks)
        qemu = registry.get("qemux86-64-fluorite")
        self.assertEqual("target_mutation", qemu.risk)
        self.assertEqual("qemu_artifact", qemu.steps[0].root)
        self.assertEqual(120, qemu.steps[0].timeout_seconds)
        self.assertIn("-snapshot", qemu.steps[0].argv)
        for runbook in registry.runbooks.values():
            for parameter in runbook.parameters:
                self.assertGreater(len(parameter.choices), 0)
                self.assertIn(parameter.default, parameter.choices)

    def test_arbitrary_shell_and_destructive_bitbake_are_rejected(self) -> None:
        examples = [
            ["sh", "-c", "echo unsafe"],
            ["bitbake", "-c", "cleanall", "agl-ivi-image-flutter"],
        ]
        for argv in examples:
            with self.subTest(argv=argv), tempfile.TemporaryDirectory() as directory:
                manifest = {
                    "schema": "fluorite.runbook/v1",
                    "id": "unsafe",
                    "title": "Unsafe",
                    "description": "Must fail",
                    "risk": "metadata_write",
                    "parameters": {},
                    "steps": [{"id": "unsafe", "argv": argv, "root": "repository"}],
                }
                Path(directory, "unsafe.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(ConfigurationError):
                    RunbookRegistry(Path(directory))

    def test_production_catalog_rejects_additional_json_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / "runbooks"
            manifests.mkdir()
            source = Path(__file__).resolve().parents[1] / "runbooks"
            for name in (
                "host-capacity.json",
                "repository-baseline.json",
                "yocto-metadata-gate.json",
                "yocto-demo-compile.json",
                "yocto-image-build.json",
                "qemux86-64-fluorite.json",
            ):
                (manifests / name).write_text(
                    (source / name).read_text(encoding="utf-8"), encoding="utf-8"
                )
            (manifests / "locally-excluded.json").write_text(
                (source / "host-capacity.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with patch("mcp.runbook.repository_root", return_value=root):
                with self.assertRaises(ConfigurationError):
                    RunbookRegistry()

    def test_qemu_variants_without_snapshot_are_rejected(self) -> None:
        source = Path(__file__).resolve().parents[1] / "runbooks" / "qemux86-64-fluorite.json"
        manifest = json.loads(source.read_text(encoding="utf-8"))
        manifest["steps"][0]["argv"].remove("-snapshot")
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "unsafe.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                RunbookRegistry(Path(directory))


class CommandRunnerTests(unittest.TestCase):
    @staticmethod
    def _metadata_runner(root: Path, setup_source: str) -> CommandRunner:
        setup = root / "setup.sh"
        setup.write_text(setup_source, encoding="utf-8")
        manifests = root / "runbooks"
        manifests.mkdir()
        manifest = {
            "schema": "fluorite.runbook/v1",
            "id": "yocto-parse",
            "title": "Test metadata parse",
            "description": "Test-only metadata operation",
            "risk": "metadata_write",
            "parameters": {},
            "steps": [
                {
                    "id": "parse",
                    "argv": ["bitbake", "-p"],
                    "root": "yocto_build",
                    "environment_profile": "yocto",
                    "timeout_seconds": 60,
                }
            ],
        }
        (manifests / "yocto-parse.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        config = MCPConfig(
            data={
                "domains": {
                    "command_runner": {"roots": {"yocto_build": str(root)}}
                },
                "command_runner": {
                    "allow_execution": True,
                    "environment_profiles": {
                        "yocto": {
                            "setup_script": str(setup),
                            "source_arguments": [],
                            "environment": {},
                        }
                    },
                },
            }
        )
        return CommandRunner(config, RunbookRegistry(manifests))

    def test_plan_is_fresh_and_execution_is_disabled_by_default(self) -> None:
        runner = CommandRunner(MCPConfig(data={}))
        first = runner.plan("repository-baseline", ticket_id="FLR-0001")
        second = runner.plan("repository-baseline", ticket_id="FLR-0001")
        self.assertNotEqual(first["plan_id"], second["plan_id"])
        self.assertFalse(first["execution_enabled"])
        with self.assertRaises(MCPDomainError) as caught:
            runner.execute("repository-baseline", {}, "FLR-0001", first["plan_id"])
        self.assertEqual("execution_disabled", caught.exception.code)

    def test_dual_gate_confirmation_executes_fixed_read_only_runbook(self) -> None:
        config = MCPConfig(data={"command_runner": {"allow_execution": True}})
        runner = CommandRunner(config)
        with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
            plan = runner.plan("repository-baseline", ticket_id="FLR-0001")
            result = runner.execute(
                "repository-baseline", {}, "FLR-0001", plan["plan_id"]
            )
        self.assertEqual("completed", result["status"])
        self.assertEqual(plan["plan_id"], result["plan_id"])
        self.assertEqual(plan["plan_digest"], result["plan_digest"])
        self.assertEqual(2, len(result["steps"]))
        self.assertTrue(all(step["return_code"] == 0 for step in result["steps"]))
        self.assertTrue(all(step["working_root_role"] == "repository" for step in result["steps"]))
        self.assertTrue(all(step["timeout_seconds"] == 10 for step in result["steps"]))
        self.assertTrue(all(len(step["output_sha256"]) == 64 for step in result["steps"]))
        log = runner.run_log(result["run_id"], None, 1)
        self.assertEqual(result["run_id"], log["run_id"])
        self.assertLessEqual(len(log["log_lines"]), 1)

        with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
            with self.assertRaises(MCPDomainError) as reused:
                runner.execute(
                    "repository-baseline", {}, "FLR-0001", plan["plan_id"]
                )
        self.assertEqual("confirmation_required", reused.exception.code)

    def test_completion_lifecycle_audit_records_plan_and_outcome_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit_file = Path(directory) / "run-audit.jsonl"
            config = MCPConfig(
                data={
                    "audit_file": str(audit_file),
                    "command_runner": {"allow_execution": True},
                }
            )
            runner = CommandRunner(config)
            with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
                plan = runner.plan("host-capacity", ticket_id="FLR-0001")
                result = runner.execute(
                    "host-capacity", {}, "FLR-0001", plan["plan_id"]
                )

            events = [
                json.loads(line)
                for line in audit_file.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(1, len(events))
            event = events[0]
            self.assertEqual("fluorite.run-lifecycle/v1", event["schema"])
            self.assertEqual("completed", event["status"])
            self.assertEqual(plan["plan_digest"], event["plan_digest"])
            self.assertEqual(result["run_id"], event["run_id"])
            self.assertTrue(all(len(step["output_sha256"]) == 64 for step in event["steps"]))
            restarted = CommandRunner(config)
            durable = restarted.load_completion(result["run_id"])
            self.assertEqual("completed", durable["status"])
            self.assertEqual(result["run_id"], durable["evidence_id"])

    def test_asynchronous_run_has_bounded_status_and_log(self) -> None:
        config = MCPConfig(data={"command_runner": {"allow_execution": True}})
        runner = CommandRunner(config)
        with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
            plan = runner.plan("host-capacity", ticket_id="FLR-0001")
            started = runner.start(
                "host-capacity", {}, "FLR-0001", plan["plan_id"]
            )
            deadline = time.monotonic() + 10
            status = started
            while status["status"] in ("queued", "running") and time.monotonic() < deadline:
                time.sleep(0.05)
                status = runner.status(started["run_id"])
        self.assertEqual("completed", status["status"])
        self.assertTrue(all("output" not in step for step in status["steps"]))
        log = runner.run_log(started["run_id"], None, 100)
        self.assertGreater(len(log["log_lines"]), 0)
        cancellation = runner.cancel(started["run_id"])
        self.assertFalse(cancellation["cancellation_requested"])

    def test_ticket_is_bound_and_metadata_runbooks_require_async_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = self._metadata_runner(root, "return 0\n")
            with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
                mismatched = runner.plan("yocto-parse", ticket_id="FLR-0001")
                with self.assertRaises(MCPDomainError) as wrong_ticket:
                    runner.start(
                        "yocto-parse", {}, "FLR-0002", mismatched["plan_id"]
                    )
                self.assertEqual("confirmation_required", wrong_ticket.exception.code)

                synchronous = runner.plan("yocto-parse", ticket_id="FLR-0001")
                with self.assertRaises(MCPDomainError) as asynchronous:
                    runner.execute(
                        "yocto-parse", {}, "FLR-0001", synchronous["plan_id"]
                    )
                self.assertEqual("asynchronous_required", asynchronous.exception.code)

    def test_failed_environment_setup_does_not_execute_the_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = self._metadata_runner(
                root, "echo setup-stopped; return 7\n"
            )
            with patch.dict(os.environ, {"FLUORITE_MCP_ALLOW_EXECUTION": "1"}):
                plan = runner.plan("yocto-parse", ticket_id="FLR-0001")
                started = runner.start(
                    "yocto-parse", {}, "FLR-0001", plan["plan_id"]
                )
                deadline = time.monotonic() + 10
                status = started
                while status["status"] in ("queued", "running") and time.monotonic() < deadline:
                    time.sleep(0.05)
                    status = runner.status(started["run_id"])
            self.assertEqual("failed", status["status"])
            self.assertEqual(7, status["steps"][0]["return_code"])
            log = runner.run_log(started["run_id"], None, 20)
            self.assertTrue(any("setup-stopped" in line["text"] for line in log["log_lines"]))

    def test_cancellation_terminates_the_owned_process_group(self) -> None:
        cancellation = threading.Event()
        timer = threading.Timer(0.2, cancellation.set)
        timer.start()
        child_script = (
            "trap 'echo child-terminated; exit 0' TERM; "
            "echo child-ready; while :; do sleep 1; done"
        )
        try:
            result = CommandRunner._capture(
                ["/bin/sh", "-c", '/bin/sh -c "$1" & wait', "mcp-test", child_script],
                Path.cwd(),
                os.environ,
                10,
                cancellation=cancellation,
            )
        finally:
            timer.cancel()
        self.assertTrue(result["cancelled"])
        self.assertFalse(result["timed_out"])
        self.assertIn("child-ready", result["output"])
        self.assertIn("child-terminated", result["output"])

    def test_task_inactivity_timeout_is_distinct_from_wall_clock(self) -> None:
        result = CommandRunner._capture(
            ["/bin/sh", "-c", "sleep 2"],
            Path.cwd(),
            os.environ,
            5,
            inactivity_timeout=1,
        )
        self.assertTrue(result["timed_out"])
        self.assertEqual("task_inactivity", result["timeout_kind"])

    def test_capture_reports_live_bounded_tail_and_process_identity(self) -> None:
        snapshots: list[dict[str, object]] = []
        result = CommandRunner._capture(
            ["/bin/sh", "-c", "printf first; sleep 3; printf last"],
            Path.cwd(),
            os.environ,
            5,
            progress=lambda item: snapshots.append(dict(item)),
        )
        self.assertEqual(0, result["return_code"])
        self.assertGreaterEqual(len(snapshots), 1)
        self.assertTrue(all(item["pid"] == result["pid"] for item in snapshots))
        self.assertTrue(
            any("first" in item["output"] and "last" not in item["output"] for item in snapshots)
        )
        self.assertIn("last", snapshots[-1]["output"])


if __name__ == "__main__":
    unittest.main()
