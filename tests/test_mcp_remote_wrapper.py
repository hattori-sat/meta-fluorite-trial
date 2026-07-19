from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
WRAPPER = REPOSITORY / "scripts/run-remote-mcp.sh"
LOCAL_WRAPPER = REPOSITORY / "scripts/run-mcp.sh"


class RemoteMCPWrapperTests(unittest.TestCase):
    def _run_remote(
        self, directory: Path, server_id: str, role_config: str
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        config = directory / "remote-role.conf"
        config.write_text(role_config, encoding="utf-8")
        capture = directory / "ssh-arguments"
        executable_dir = directory / "bin"
        executable_dir.mkdir()
        ssh = executable_dir / "ssh"
        ssh.write_text(
            "#!/usr/bin/env bash\n"
            "printf '%s\\0' \"$@\" > \"$MCP_TEST_SSH_CAPTURE\"\n",
            encoding="utf-8",
        )
        ssh.chmod(0o755)
        environment = os.environ.copy()
        environment.update(
            {
                "FLUORITE_MCP_REMOTE_ROLE_CONFIG": str(config),
                "MCP_TEST_SSH_CAPTURE": str(capture),
                "PATH": f"{executable_dir}:/usr/bin:/bin",
            }
        )
        result = subprocess.run(
            ["bash", str(WRAPPER), server_id],
            cwd=REPOSITORY,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result, capture

    @staticmethod
    def _arguments(capture: Path) -> list[str]:
        return [
            item.decode("utf-8")
            for item in capture.read_bytes().split(b"\0")
            if item
        ]

    def test_only_build_context_servers_get_fixed_ssh_transport(self) -> None:
        role_config = (
            "ssh_alias=build-role\n"
            "remote_repository=/role/canonical/repository\n"
            "expected_project_revision=0123456789abcdef0123456789abcdef01234567\n"
            "allow_command_execution=1\n"
        )
        for server_id in ("agl", "yocto", "command_runner"):
            with self.subTest(server=server_id), tempfile.TemporaryDirectory() as directory:
                result, capture = self._run_remote(Path(directory), server_id, role_config)
                self.assertEqual(0, result.returncode, result.stderr)
                arguments = self._arguments(capture)
                self.assertEqual(
                    [
                        "-T",
                        "-o",
                        "BatchMode=yes",
                        "-o",
                        "ClearAllForwardings=yes",
                        "-o",
                        "PermitLocalCommand=no",
                        "-o",
                        "StrictHostKeyChecking=yes",
                        "--",
                        "build-role",
                    ],
                    arguments[:-1],
                )
                command = arguments[-1]
                self.assertIn("bash scripts/assert-canonical-repository.sh >&2", command)
                self.assertIn(
                    "0123456789abcdef0123456789abcdef01234567", command
                )
                self.assertIn("project revision mismatch", command)
                self.assertIn("git diff --quiet -- .", command)
                self.assertIn("git diff --cached --quiet -- .", command)
                self.assertIn("git ls-files --others --exclude-standard", command)
                self.assertIn("git ls-files --others --ignored --exclude-standard", command)
                self.assertIn("ignored runtime surface is not clean", command)
                self.assertIn("project worktree is not clean", command)
                self.assertIn("BASH_ENV=/dev/null ENV=/dev/null PYTHON=", command)
                self.assertIn(f"exec bash scripts/run-mcp.sh {server_id}", command)
                self.assertIn(".fluorite-mcp/config.json", command)
                expected_gate = "1" if server_id == "command_runner" else "0"
                self.assertIn(f"FLUORITE_MCP_ALLOW_EXECUTION={expected_gate}", command)

    def test_adjacent_context_and_injection_inputs_are_rejected_before_ssh(self) -> None:
        passing_shape = (
            "ssh_alias=build-role\n"
            "remote_repository=/role/canonical/repository\n"
            "expected_project_revision=0123456789abcdef0123456789abcdef01234567\n"
            "allow_command_execution=0\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            result, capture = self._run_remote(Path(directory), "graphics", passing_shape)
            self.assertEqual(2, result.returncode)
            self.assertFalse(capture.exists())

        malicious_shapes = (
            "ssh_alias=build-role;unexpected\nremote_repository=/role/repository\nexpected_project_revision=0123456789abcdef0123456789abcdef01234567\n",
            "ssh_alias=build-role\nremote_repository=/role/repository/../unexpected\nexpected_project_revision=0123456789abcdef0123456789abcdef01234567\n",
            "ssh_alias=build-role\nremote_repository=/role/repository\nexpected_project_revision=unexpected\n",
            "ssh_alias=build-role\nremote_repository=/role/repository\nexpected_project_revision=0123456789abcdef0123456789abcdef01234567\nremote_command=unexpected\n",
        )
        for content in malicious_shapes:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                result, capture = self._run_remote(Path(directory), "yocto", content)
                self.assertEqual(1, result.returncode)
                self.assertFalse(capture.exists())

    def test_role_config_is_parsed_as_data_not_sourced(self) -> None:
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertNotIn("source $role_config", source)
        self.assertNotIn(". $role_config", source)
        self.assertNotIn("eval ", source)

    def test_local_runtime_wrapper_accepts_a_310_interpreter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable_dir = Path(directory)
            python = executable_dir / "python3.10"
            python.write_text(
                "#!/usr/bin/env bash\n"
                "for argument in \"$@\"; do\n"
                "    if test \"$argument\" = -c; then exit 0; fi\n"
                "done\n"
                "printf '%s\\n' \"$*\"\n",
                encoding="utf-8",
            )
            python.chmod(0o755)
            environment = os.environ.copy()
            environment.update({"PATH": f"{executable_dir}:/usr/bin:/bin", "PYTHON": ""})
            result = subprocess.run(
                ["bash", str(LOCAL_WRAPPER), "agl"],
                cwd=REPOSITORY,
                env=environment,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("-E -S -B -m mcp agl", result.stdout.strip())

    def test_local_runtime_ignores_inherited_python_customization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "startup-marker"
            (root / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('unexpected', encoding='utf-8')\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHON": sys.executable,
                    "PYTHONPATH": str(root),
                    "PYTHONHOME": "",
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )
            result = subprocess.run(
                ["bash", str(LOCAL_WRAPPER), "agl"],
                cwd=REPOSITORY,
                env=environment,
                input="",
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
