from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mcp.config import MCPConfig
from mcp.domains.target_validation import create_server


class TargetValidationSignalTests(unittest.TestCase):
    def _call(self, log: str, tool: str, revision: str | None) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session.log").write_text(log, encoding="utf-8")
            config = MCPConfig(
                data={
                    "domains": {
                        "target_validation": {
                            "identity": {"subject_id": "test-session", "revision_or_image_id": revision},
                            "roots": {"target_evidence": str(root)},
                        }
                    }
                }
            )
            server = create_server(config)
            server._initialize({"protocolVersion": "2025-06-18"})
            response = server._tools_call({"name": tool, "arguments": {"root": "target_evidence", "path": "session.log"}})
            self.assertFalse(response["isError"])
            return response["structuredContent"]

    def test_ready_then_sigsegv_is_fail_with_identity(self) -> None:
        result = self._call("Native is ready\nFEngine::loop segfault in libLLVM.so.18.1\n", "summarize_render_case", "image-1")
        evidence = result["payload"]["render_case_evidence"]
        self.assertEqual("FAIL", evidence["verdict"])

    def test_identity_missing_forces_unknown(self) -> None:
        result = self._call("Native is ready\n", "summarize_app_launch", None)
        evidence = result["payload"]["app_launch_evidence"]
        self.assertEqual("UNKNOWN", evidence["verdict"])

    def test_llvmpipe_capability_signal_is_not_failure_alone(self) -> None:
        result = self._call("Vulkan device driver: llvmpipe Mesa\n", "summarize_render_case", "image-1")
        evidence = result["payload"]["render_case_evidence"]
        self.assertEqual("PASS", evidence["verdict"])


if __name__ == "__main__":
    unittest.main()
