from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from mcp.config import MCPConfig
from mcp.domains import factories

REPOSITORY = Path(__file__).resolve().parents[1]

SMOKE_CALLS = {
    "agl": ("get_manifest_catalog", {}),
    "yocto": ("list_layer_metadata", {}),
    "fluorite": ("catalog_scene_assets", {}),
    "flutter_runtime": ("catalog_embedder_surfaces", {}),
    "filament": ("catalog_render_assets", {}),
    "graphics": ("catalog_graphics_configuration", {}),
    "target_validation": ("list_validation_bundles", {}),
    "command_runner": ("list_runbooks", {}),
}

PAYLOAD_KEYS = {
    "agl": "manifest_catalog",
    "yocto": "layers",
    "fluorite": "scene_catalog",
    "flutter_runtime": "surface_contract_candidates",
    "filament": "render_catalog",
    "graphics": "graphics_configuration_candidates",
    "target_validation": "validation_artifacts",
    "command_runner": "runbooks",
}


class ProtocolSmokeTests(unittest.TestCase):
    maxDiff = None

    def _exchange(self, server: str) -> list[dict[str, object]]:
        tool, arguments = SMOKE_CALLS[server]
        messages = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "protocol-test", "version": "1"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            },
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(REPOSITORY)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            [sys.executable, "-m", "mcp", server],
            cwd=REPOSITORY,
            env=environment,
            input="".join(json.dumps(message) + "\n" for message in messages),
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        return [json.loads(line) for line in process.stdout.splitlines() if line.strip()]

    def test_all_bounded_context_servers_initialize_list_and_call(self) -> None:
        for server in SMOKE_CALLS:
            with self.subTest(server=server):
                responses = self._exchange(server)
                self.assertEqual([1, 2, 3], [response["id"] for response in responses])
                initialized = responses[0]["result"]
                self.assertEqual("2025-06-18", initialized["protocolVersion"])
                self.assertEqual(f"fluorite-{server}-mcp", initialized["serverInfo"]["name"])

                tools = responses[1]["result"]["tools"]
                self.assertGreater(len(tools), 0)
                for descriptor in tools:
                    self.assertIn("annotations", descriptor)
                    self.assertIn("readOnlyHint", descriptor["annotations"])
                    self.assertFalse(descriptor["annotations"]["openWorldHint"])

                called = responses[2]["result"]
                self.assertFalse(called["isError"], called)
                envelope = called["structuredContent"]
                self.assertEqual("fluorite.mcp-envelope/v1", envelope["schema"])
                self.assertEqual(server, envelope["bounded_context"])
                self.assertEqual(f"{server}:repository", envelope["subject_id"])
                self.assertIsNone(envelope["revision_or_image_id"])
                self.assertEqual("insufficient", envelope["identity_status"])
                self.assertTrue(
                    any("identity is insufficient" in item for item in envelope["unknowns"])
                )
                self.assertEqual(
                    "fluorite.privacy-redaction/v1", envelope["redaction_policy"]
                )
                self.assertEqual(1, len(envelope["evidence_ids"]))
                self.assertIn(PAYLOAD_KEYS[server], envelope["payload"])

    def test_domain_tool_names_and_payload_vocabulary_are_separate(self) -> None:
        built = {name: factory(MCPConfig(data={})) for name, factory in factories().items()}
        read_contexts = [name for name in built if name != "command_runner"]
        for index, left in enumerate(read_contexts):
            for right in read_contexts[index + 1 :]:
                self.assertTrue(set(built[left].tool_names).isdisjoint(built[right].tool_names))
        self.assertEqual(len(PAYLOAD_KEYS), len(set(PAYLOAD_KEYS.values())))

    def test_tool_schemas_expose_safe_configured_root_aliases(self) -> None:
        config = MCPConfig(
            data={
                "domains": {
                    "agl": {"roots": {"meta_agl": str(REPOSITORY)}}
                }
            }
        )
        server = factories()["agl"](config)
        for descriptor in server._tools_list({})["tools"]:
            root_schema = descriptor["inputSchema"]["properties"].get("root")
            if root_schema is not None:
                self.assertEqual(["meta_agl", "repository"], root_schema["enum"])

    def test_only_command_runner_exposes_state_changing_annotations(self) -> None:
        for name, factory in factories().items():
            descriptors = factory(MCPConfig(data={}))._tools_list({})["tools"]
            state_changing = [
                descriptor
                for descriptor in descriptors
                if not descriptor["annotations"]["readOnlyHint"]
            ]
            if name == "command_runner":
                self.assertEqual(
                    {"cancel_run", "execute_runbook", "start_runbook"},
                    {descriptor["name"] for descriptor in state_changing},
                )
                self.assertTrue(all(item["annotations"]["destructiveHint"] for item in state_changing))
            else:
                self.assertEqual([], state_changing)

    def test_command_runner_has_no_arbitrary_command_parameter(self) -> None:
        server = factories()["command_runner"](MCPConfig(data={}))
        for descriptor in server._tools_list({})["tools"]:
            properties = descriptor["inputSchema"].get("properties", {})
            self.assertNotIn("command", properties)
            self.assertNotIn("argv", properties)
            self.assertNotIn("path", properties)

        rejected = server._tools_call(
            {
                "name": "list_runbooks",
                "arguments": {"command": "unexpected"},
            }
        )
        self.assertTrue(rejected["isError"])
        self.assertEqual(
            "invalid_arguments", rejected["structuredContent"]["error"]["code"]
        )


if __name__ == "__main__":
    unittest.main()
