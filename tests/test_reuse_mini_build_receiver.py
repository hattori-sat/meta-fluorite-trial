from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
HELPER = REPOSITORY / "scripts/reuse-mini-build-receiver.sh"


class ReuseMiniBuildReceiverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="fluorite-handoff-test-")
        self.root = Path(self.tempdir.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.agl_root = self.root / "agl"
        self.build_dir = self.agl_root / "trout" / "build-test"
        (self.build_dir / "conf").mkdir(parents=True)
        (self.agl_root / "external" / "poky").mkdir(parents=True)
        self.receiver = self.root / "receiver"
        self.source = self.root / "source"
        self.source.mkdir()
        self.ssh_marker = self.root / "ssh-invoked"
        self.expected_tmpdir = self.root / "fixed-tmp"
        self.other_tmpdir = self.root / "other-tmp"
        self.expected_tmpdir.mkdir()
        self.other_tmpdir.mkdir()

        self._write_executable(
            self.bin_dir / "ssh",
            "#!/bin/sh\n"
            "printf 'called\\n' > \"$FLUORITE_TEST_SSH_MARKER\"\n"
            "shift\n"
            "exec \"$@\"\n",
        )
        self._write_executable(self.bin_dir / "pgrep", "#!/bin/sh\nexit 1\n")
        self._write_executable(
            self.bin_dir / "timeout",
            "#!/bin/sh\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "  case \"$1\" in\n"
            "    --*) shift ;;\n"
            "    [0-9]*s) shift; break ;;\n"
            "    *) break ;;\n"
            "  esac\n"
            "done\n"
            "exec \"$@\"\n",
        )
        (self.agl_root / "external" / "poky" / "oe-init-build-env").write_text(
            "#!/usr/bin/env bash\n"
            "test \"${FLUORITE_TEST_OE_INIT_FAIL:-0}\" = 0 || exit 9\n"
            "export TOPDIR=\"$1\"\n"
            "export TMPDIR=\"$FLUORITE_TEST_EFFECTIVE_TMPDIR\"\n",
            encoding="utf-8",
        )
        self._write_executable(
            self.bin_dir / "bitbake",
            "#!/bin/sh\n"
            "test \"$1\" = -e || exit 2\n"
            "test \"${FLUORITE_TEST_BITBAKE_FAIL:-0}\" = 0 || exit 7\n"
            "printf 'TMPDIR=\"%s\"\\nTOPDIR=\"%s\"\\n' \"$TMPDIR\" \"$TOPDIR\"\n",
        )

        self._git(self.source, "init", "--quiet", "--initial-branch=main")
        self._git(self.source, "config", "user.name", "Fluorite Test")
        self._git(self.source, "config", "user.email", "fluorite-test.invalid")
        layer = self.source / "layers" / "meta-fluorite-trial"
        layer.mkdir(parents=True)
        (layer / "layer.conf").write_text("BBPATH .= \":${LAYERDIR}\"\n", encoding="utf-8")
        (self.source / "state.txt").write_text("base\n", encoding="utf-8")
        self._git(self.source, "add", ".")
        self._git(self.source, "commit", "--quiet", "-m", "base")
        self._git(None, "clone", "--quiet", str(self.source), str(self.receiver))
        self._git(self.receiver, "config", "user.name", "Fluorite Test")
        self._git(self.receiver, "config", "user.email", "fluorite-test.invalid")

        (self.source / "state.txt").write_text("tip\n", encoding="utf-8")
        self._git(self.source, "add", "state.txt")
        self._git(self.source, "commit", "--quiet", "-m", "tip")
        self.tip = self._git(self.source, "rev-parse", "HEAD").stdout.strip()
        self.bundle = self.root / "project.bundle"
        self._git(self.source, "bundle", "create", str(self.bundle), "refs/heads/main")

        (self.build_dir / "conf" / "local.conf").write_text("# fixed build\n", encoding="utf-8")
        (self.build_dir / "conf" / "bblayers.conf").write_text(
            f'BBLAYERS += "{self.receiver}/layers/meta-fluorite-trial"\n',
            encoding="utf-8",
        )
        self.fetch_head = self.receiver / ".git" / "FETCH_HEAD"
        self.fetch_head.write_text("sentinel-before-preflight\n", encoding="utf-8")
        self.before_head = self._git(self.receiver, "rev-parse", "HEAD").stdout.strip()
        self.before_tree = self._git(self.receiver, "write-tree").stdout.strip()
        self.before_status = self._git(self.receiver, "status", "--porcelain").stdout

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @staticmethod
    def _write_executable(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    @staticmethod
    def _git(repository: Path | None, *args: str) -> subprocess.CompletedProcess[str]:
        command = ["git"]
        if repository is not None:
            command.extend(["-C", str(repository)])
        command.extend(args)
        return subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            timeout=20,
        )

    def _run_helper(
        self,
        effective_tmpdir: Path,
        expected_tmpdir: Path,
        *,
        query_failure: bool = False,
        oe_init_failure: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "BUILD_HOST": "mini-test-role",
                "BUILD_RECEIVER": str(self.receiver),
                "BUILD_DIR": str(self.build_dir),
                "BUILD_TMPDIR": str(expected_tmpdir),
                "FLUORITE_TEST_EFFECTIVE_TMPDIR": str(effective_tmpdir),
                "FLUORITE_TEST_BITBAKE_FAIL": "1" if query_failure else "0",
                "FLUORITE_TEST_OE_INIT_FAIL": "1" if oe_init_failure else "0",
                "FLUORITE_TEST_SSH_MARKER": str(self.ssh_marker),
                "PATH": f"{self.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin",
            }
        )
        return subprocess.run(
            ["bash", str(HELPER), str(self.bundle), self.tip],
            cwd=REPOSITORY,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_tmpdir_mismatch_rejects_without_receiver_mutation(self) -> None:
        result = self._run_helper(self.other_tmpdir, self.expected_tmpdir)

        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("effective TMPDIR does not match", result.stderr)
        self.assertEqual(self.before_head, self._git(self.receiver, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(self.before_tree, self._git(self.receiver, "write-tree").stdout.strip())
        self.assertEqual(self.before_status, self._git(self.receiver, "status", "--porcelain").stdout)
        self.assertEqual("sentinel-before-preflight\n", self.fetch_head.read_text(encoding="utf-8"))

    def test_metadata_query_failure_rejects_without_receiver_mutation(self) -> None:
        result = self._run_helper(
            self.expected_tmpdir,
            self.expected_tmpdir,
            query_failure=True,
        )

        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("effective BitBake configuration query failed", result.stderr)
        self.assertEqual(self.before_head, self._git(self.receiver, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(self.before_tree, self._git(self.receiver, "write-tree").stdout.strip())
        self.assertEqual(self.before_status, self._git(self.receiver, "status", "--porcelain").stdout)
        self.assertEqual("sentinel-before-preflight\n", self.fetch_head.read_text(encoding="utf-8"))

    def test_oe_initialization_failure_rejects_without_receiver_mutation(self) -> None:
        result = self._run_helper(
            self.expected_tmpdir,
            self.expected_tmpdir,
            oe_init_failure=True,
        )

        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("effective BitBake configuration query failed", result.stderr)
        self.assertEqual(self.before_head, self._git(self.receiver, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(self.before_tree, self._git(self.receiver, "write-tree").stdout.strip())
        self.assertEqual(self.before_status, self._git(self.receiver, "status", "--porcelain").stdout)
        self.assertEqual("sentinel-before-preflight\n", self.fetch_head.read_text(encoding="utf-8"))

    def test_missing_fixed_roles_rejects_before_ssh(self) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "BUILD_HOST": "mini-test-role",
                "FLUORITE_TEST_SSH_MARKER": str(self.ssh_marker),
                "PATH": f"{self.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin",
            }
        )
        for key in ("BUILD_RECEIVER", "BUILD_DIR", "BUILD_TMPDIR"):
            environment.pop(key, None)

        result = subprocess.run(
            ["bash", str(HELPER), str(self.bundle), self.tip],
            cwd=REPOSITORY,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("BUILD_RECEIVER must be set", result.stderr)
        self.assertFalse(self.ssh_marker.exists())
        self.assertEqual(self.before_head, self._git(self.receiver, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(self.before_tree, self._git(self.receiver, "write-tree").stdout.strip())
        self.assertEqual(self.before_status, self._git(self.receiver, "status", "--porcelain").stdout)

    def test_valid_handoff_checks_out_exact_bundle_tip(self) -> None:
        result = self._run_helper(self.expected_tmpdir, self.expected_tmpdir)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.tip, self._git(self.receiver, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual("", self._git(self.receiver, "status", "--porcelain").stdout)
        self.assertIn("effective-tmpdir=PASS", result.stdout)
        self.assertIn("status=ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
