from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"


def run_script(
    script_name: str,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_environment = os.environ.copy()
    process_environment.update(environment or {})
    return subprocess.run(
        ["bash", str(SCRIPTS / script_name), *arguments],
        cwd=REPOSITORY_ROOT,
        env=process_environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


class SetupScriptTests(unittest.TestCase):
    def test_setup_scripts_document_check_only_help(self) -> None:
        for script in sorted(SCRIPTS.glob("setup-*.sh")):
            with self.subTest(script=script.name):
                result = run_script(script.name, "--help")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("does not", result.stdout)

    def test_setup_scripts_do_not_invoke_mutating_package_commands(self) -> None:
        forbidden_invocation = re.compile(
            r"^\s*(?:sudo\s+)?(?:apt(?:-get)?|brew|dnf|yum|pacman|port|"
            r"curl|wget|rm|repo\s+sync|bitbake)\b",
            re.MULTILINE,
        )
        for script in sorted(SCRIPTS.glob("setup-*.sh")):
            with self.subTest(script=script.name):
                source = script.read_text(encoding="utf-8")
                self.assertIsNone(forbidden_invocation.search(source))

    def test_project_setup_succeeds_in_canonical_checkout(self) -> None:
        result = run_script("setup-project.sh", str(REPOSITORY_ROOT))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("project setup: PASS", result.stdout)


class RepositoryCheckTests(unittest.TestCase):
    def test_markdown_link_checker_accepts_and_rejects_internal_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("# Setup section\n", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("[guide](guide.md#setup-section)\n", encoding="utf-8")

            passing = run_script("check-markdown-links.sh", str(root))
            self.assertEqual(passing.returncode, 0, passing.stdout)

            readme.write_text("[missing](absent.md)\n", encoding="utf-8")
            failing = run_script("check-markdown-links.sh", str(root))
            self.assertEqual(failing.returncode, 1, failing.stdout)
            self.assertIn("missing target", failing.stdout)

    def test_file_size_checker_uses_configured_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(root)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            candidate = root / "candidate.txt"
            candidate.write_bytes(b"small")

            passing = run_script(
                "check-file-sizes.sh",
                str(root),
                environment={"MAX_FILE_BYTES": "8"},
            )
            self.assertEqual(passing.returncode, 0, passing.stdout)

            candidate.write_bytes(b"too-large")
            failing = run_script(
                "check-file-sizes.sh",
                str(root),
                environment={"MAX_FILE_BYTES": "8"},
            )
            self.assertEqual(failing.returncode, 1, failing.stdout)
            self.assertIn("too large", failing.stdout)

    def test_privacy_checker_covers_project_config_and_project_layers(self) -> None:
        sensitive_value = ".".join(("203", "0", "113", "7"))
        covered_suffixes = (".template", ".conf", ".xml", ".lock", ".patch")

        for suffix in covered_suffixes:
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                candidate = root / f"candidate{suffix}"
                candidate.write_text("SANITIZED_VALUE\n", encoding="utf-8")
                passing = run_script("check-repository-privacy.sh", str(root))
                self.assertEqual(passing.returncode, 0, passing.stdout)

                candidate.write_text(f"endpoint={sensitive_value}\n", encoding="utf-8")
                failing = run_script("check-repository-privacy.sh", str(root))
                self.assertEqual(failing.returncode, 1, failing.stdout)
                self.assertNotIn(sensitive_value, failing.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layers = root / "layers"
            layers.mkdir()
            (layers / "upstream.patch").write_text(
                f"upstream-metadata={sensitive_value}\n", encoding="utf-8"
            )
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(sensitive_value, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "identity.patch"
            sensitive_email = "@".join(("local-role", "example.invalid"))
            candidate.write_text(
                f"From: Project Role <{sensitive_email}>\n", encoding="utf-8"
            )
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(sensitive_email, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "credential.patch"
            private_key_marker = "-----" + "BEGIN PRIVATE KEY" + "-----"
            candidate.write_text(private_key_marker + "\n", encoding="utf-8")
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(private_key_marker, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "network.conf"
            ipv6_value = ":".join(
                ("2001", "0db8", "0000", "0000", "0000", "0000", "0000", "0042")
            )
            candidate.write_text(f"endpoint={ipv6_value}\n", encoding="utf-8")
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(ipv6_value, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "compressed-network.conf"
            compressed_ipv6 = "2001" + ":db8:" + ":42"
            candidate.write_text(f"endpoint={compressed_ipv6}\n", encoding="utf-8")
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(compressed_ipv6, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "hostname.conf"
            private_hostname = "build-role" + ".internal"
            candidate.write_text(f"endpoint={private_hostname}\n", encoding="utf-8")
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn(private_hostname, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "slice.py"
            candidate.write_text("items = values[1::2]\n", encoding="utf-8")
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 0, result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(root)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            (root / ".gitignore").write_text(".fluorite-mcp/\n", encoding="utf-8")
            private = root / ".fluorite-mcp"
            private.mkdir()
            ignored_value = ".".join(("203", "0", "113", "9"))
            (private / "config.json").write_text(
                f'{{"endpoint": "{ignored_value}"}}\n', encoding="utf-8"
            )
            result = run_script("check-repository-privacy.sh", str(root))
            self.assertEqual(result.returncode, 0, result.stdout)


class CiWorkflowTests(unittest.TestCase):
    def test_ci_uses_read_only_official_actions_without_secrets(self) -> None:
        workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("Run lightweight repository gates", workflow)
        self.assertIn("check-canonical check-privacy check-shell check-markdown check-file-sizes", workflow)
        self.assertNotIn("actions/setup-python", workflow)
        self.assertNotIn("secrets.", workflow)

        action_references = re.findall(r"uses:\s+([^@\s]+)@([^\s]+)", workflow)
        self.assertTrue(action_references)
        for action, version in action_references:
            with self.subTest(action=action):
                self.assertTrue(action.startswith("actions/"))
                self.assertRegex(version, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
