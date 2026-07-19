from __future__ import annotations

import json
import subprocess
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_IDS = {
    "agl",
    "yocto",
    "fluorite",
    "flutter_runtime",
    "filament",
    "graphics",
    "target_validation",
    "command_runner",
}


class AgentConfigurationTests(unittest.TestCase):
    def test_project_defines_disabled_domain_transports(self) -> None:
        with (ROOT / ".codex/config.toml").open("rb") as stream:
            config = tomllib.load(stream)

        servers = config["mcp_servers"]
        self.assertEqual(set(servers), SERVER_IDS)
        for server_id, server in servers.items():
            self.assertFalse(server["enabled"], server_id)
            self.assertEqual(server["command"], "bash")
            wrapper = (
                "scripts/run-remote-mcp.sh"
                if server_id in {"agl", "yocto", "command_runner"}
                else "scripts/run-mcp.sh"
            )
            self.assertEqual(
                server["args"], [wrapper, server_id], server_id
            )
            self.assertEqual(server["cwd"], "..", server_id)
            resolved_cwd = ((ROOT / ".codex") / server["cwd"]).resolve()
            self.assertEqual(resolved_cwd, ROOT, server_id)
            self.assertTrue(server["enabled_tools"], server_id)

    def test_each_agent_enables_at_most_one_declared_server(self) -> None:
        with (ROOT / ".codex/config.toml").open("rb") as stream:
            project = tomllib.load(stream)
        project_servers = project["mcp_servers"]

        agent_files = sorted((ROOT / ".codex/agents").glob("*.toml"))
        self.assertGreaterEqual(len(agent_files), 1)
        for path in agent_files:
            with self.subTest(agent=path.name), path.open("rb") as stream:
                agent = tomllib.load(stream)
                self.assertEqual(agent.get("sandbox_mode"), "read-only")
                configured = agent.get("mcp_servers", {})
                self.assertEqual(set(configured), SERVER_IDS)
                enabled = [
                    server_id
                    for server_id, settings in configured.items()
                    if settings.get("enabled", False)
                ]
                self.assertLessEqual(len(enabled), 1)
                for server_id in enabled:
                    self.assertTrue(
                        set(configured[server_id].get("enabled_tools", []))
                        <= set(project_servers[server_id]["enabled_tools"])
                    )

        pdca_path = ROOT / ".codex/agents/pdca-checker.toml"
        with pdca_path.open("rb") as stream:
            pdca = tomllib.load(stream)
        self.assertFalse(
            any(
                settings.get("enabled", False)
                for settings in pdca["mcp_servers"].values()
            )
        )

    def test_project_mcp_wrapper_negotiates_stdio(self) -> None:
        requests = "\n".join(
            (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18"},
                    }
                ),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    }
                ),
                "",
            )
        )
        with (ROOT / ".codex/config.toml").open("rb") as stream:
            config = tomllib.load(stream)
        server = config["mcp_servers"]["fluorite"]
        resolved_cwd = ((ROOT / ".codex") / server["cwd"]).resolve()
        result = subprocess.run(
            [server["command"], *server["args"]],
            cwd=resolved_cwd,
            input=requests,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertTrue(responses[1]["result"]["tools"])


if __name__ == "__main__":
    unittest.main()
