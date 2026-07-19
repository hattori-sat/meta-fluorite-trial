from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "manifests" / "baseline-sources.lock"


def load_lock() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BaselineArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = load_lock()

    def test_fixed_manifest_uses_commit_revisions(self) -> None:
        manifest = ROOT / "manifests" / "agl-trout-fixed.xml"
        root = ET.parse(manifest).getroot()
        projects = root.findall("project")

        self.assertGreaterEqual(len(projects), 1)
        for project in projects:
            revision = project.attrib.get("revision", "")
            self.assertRegex(revision, r"^[0-9a-f]{40}$", project.attrib.get("path"))

        self.assertEqual(
            sha256_file(manifest), self.lock["agl_manifest_sha256"]
        )

    def test_configuration_snapshots_match_lock_and_are_sanitized(self) -> None:
        snapshots = {
            "raspberrypi4_local_conf_sha256": ROOT
            / "conf/raspberrypi4-64/local.conf.template",
            "raspberrypi4_bblayers_conf_sha256": ROOT
            / "conf/raspberrypi4-64/bblayers.conf.template",
            "qemux86_64_local_conf_sha256": ROOT
            / "conf/qemux86-64/local.conf.template",
            "qemux86_64_bblayers_conf_sha256": ROOT
            / "conf/qemux86-64/bblayers.conf.template",
        }

        for key, path in snapshots.items():
            content = path.read_text(encoding="utf-8")
            self.assertEqual(sha256_file(path), self.lock[key], path.name)
            self.assertNotRegex(content, r"/(?:Users|home)/[^/]+/")

        setup_manifests = {
            "raspberrypi4_aglsetup_sanitized_sha256": ROOT
            / "manifests/build-config/raspberrypi4-64.aglsetup.conf",
            "qemux86_64_aglsetup_sanitized_sha256": ROOT
            / "manifests/build-config/qemux86-64.aglsetup.conf",
        }
        for key, path in setup_manifests.items():
            content = path.read_text(encoding="utf-8")
            self.assertEqual(sha256_file(path), self.lock[key], path.name)
            self.assertIn('DIST_DISTRO_NAME="AGL"', content)
            self.assertNotRegex(content, r"/(?:Users|home)/[^/]+/")

        candidates = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout.split(b"\0")
        for path in setup_manifests.values():
            relative = path.relative_to(ROOT).as_posix().encode("utf-8")
            self.assertIn(relative, candidates, path.name)

    def test_project_layer_matches_sanitized_baseline(self) -> None:
        layer = ROOT / "layers/meta-fluorite-trial"
        files = sorted(path for path in layer.rglob("*") if path.is_file())
        self.assertEqual(len(files), int(self.lock["meta_fluorite_trial_file_count"]))
        self.assertTrue((layer / "conf/layer.conf").is_file())

        repository_rows: list[bytes] = []
        normalized_rows: list[bytes] = []
        identity_metadata = re.compile(
            br"^(From|Signed-off-by|Co-authored-by|Tested-by|Reviewed-by|Acked-by): .*?$",
            flags=re.MULTILINE,
        )
        email_address = re.compile(
            br"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        )
        for path in files:
            relative = path.relative_to(ROOT / "layers").as_posix()
            source = path.read_bytes()
            self.assertIsNone(email_address.search(source), relative)
            repository_rows.append(
                relative.encode("utf-8")
                + b" "
                + hashlib.sha256(source).hexdigest().encode("ascii")
                + b"\n"
            )
            content = identity_metadata.sub(
                lambda match: match.group(1) + b": NORMALIZED", source
            )
            normalized_rows.append(
                relative.encode("utf-8")
                + b" "
                + hashlib.sha256(content).hexdigest().encode("ascii")
                + b"\n"
            )

        repository_tree = hashlib.sha256(b"".join(repository_rows)).hexdigest()
        self.assertEqual(
            repository_tree, self.lock["meta_fluorite_trial_repository_tree_sha256"]
        )
        normalized_tree = hashlib.sha256(b"".join(normalized_rows)).hexdigest()
        self.assertEqual(
            normalized_tree,
            self.lock["meta_fluorite_trial_normalized_identity_tree_sha256"],
        )

    def test_target_layer_selection_contains_project_layers(self) -> None:
        for target in ("raspberrypi4-64", "qemux86-64"):
            bblayers = (
                ROOT / "conf" / target / "bblayers.conf.template"
            ).read_text(encoding="utf-8")
            self.assertIn("meta-fluorite-trial", bblayers)
            self.assertIn("meta-vulkan", bblayers)

        raspberry_setup = (
            ROOT / "manifests/build-config/raspberrypi4-64.aglsetup.conf"
        ).read_text(encoding="utf-8")
        raspberry_local = (
            ROOT / "conf/raspberrypi4-64/local.conf.template"
        ).read_text(encoding="utf-8")
        self.assertIn('DIST_MACHINE="raspberrypi4"', raspberry_setup)
        self.assertIn('MACHINE = "raspberrypi4-64"', raspberry_local)

    def test_build_conf_materializer_is_dry_run_then_create_only(self) -> None:
        script = ROOT / "scripts/materialize-build-conf.sh"
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            agl_root = sandbox / "agl"
            output_dir = sandbox / "build"
            (agl_root / "meta-agl").mkdir(parents=True)
            (agl_root / "external/poky").mkdir(parents=True)
            (agl_root / "meta-fluorite-trial/conf").mkdir(parents=True)
            (agl_root / "meta-vulkan/conf").mkdir(parents=True)
            (agl_root / "meta-fluorite-trial/conf/layer.conf").write_text("", encoding="utf-8")
            (agl_root / "meta-vulkan/conf/layer.conf").write_text("", encoding="utf-8")

            arguments = [
                "bash",
                str(script),
                "--target",
                "qemux86-64",
                "--agl-root",
                str(agl_root),
                "--output-dir",
                str(output_dir),
            ]
            dry_run = subprocess.run(arguments, text=True, capture_output=True)
            self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
            self.assertFalse((output_dir / "conf").exists())

            unverified_write = subprocess.run(
                arguments + ["--write"], text=True, capture_output=True
            )
            self.assertNotEqual(unverified_write.returncode, 0)

            write = subprocess.run(
                arguments + ["--write", "--source-identity-verified"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
            for name in ("local.conf", "bblayers.conf"):
                content = (output_dir / "conf" / name).read_text(encoding="utf-8")
                self.assertNotIn("@AGL_ROOT@", content)
                self.assertNotIn("@AGL_BUILD_DIR@", content)

            overwrite = subprocess.run(
                arguments + ["--write", "--source-identity-verified"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(overwrite.returncode, 0)

            atomic_output = sandbox / "atomic-output"
            atomic_arguments = [
                *arguments[:-1],
                str(atomic_output),
                "--write",
                "--source-identity-verified",
            ]
            executable_dir = sandbox / "bin"
            executable_dir.mkdir()
            fake_perl = executable_dir / "perl"
            fake_perl.write_text(
                "#!/usr/bin/env bash\n"
                "if ! test -e \"$FLUORITE_TEST_PERL_COUNTER\"; then\n"
                "  : > \"$FLUORITE_TEST_PERL_COUNTER\"\n"
                "  exec \"$FLUORITE_TEST_REAL_PERL\" \"$@\"\n"
                "fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake_perl.chmod(0o755)
            real_perl = shutil.which("perl")
            self.assertIsNotNone(real_perl)
            failed_environment = {
                **os.environ,
                "PATH": f"{executable_dir}:{os.environ.get('PATH', '')}",
                "FLUORITE_TEST_PERL_COUNTER": str(sandbox / "perl-counter"),
                "FLUORITE_TEST_REAL_PERL": str(real_perl),
            }
            interrupted_render = subprocess.run(
                atomic_arguments,
                text=True,
                capture_output=True,
                env=failed_environment,
            )
            self.assertNotEqual(interrupted_render.returncode, 0)
            self.assertFalse((atomic_output / "conf").exists())
            self.assertEqual([], list(atomic_output.glob(".fluorite-conf.*")))

            raspberry_output = sandbox / "raspberry-build"
            raspberry_arguments = [
                "bash",
                str(script),
                "--target",
                "raspberrypi4-64",
                "--agl-root",
                str(agl_root),
                "--output-dir",
                str(raspberry_output),
            ]
            missing_workspace = subprocess.run(
                raspberry_arguments, text=True, capture_output=True
            )
            self.assertNotEqual(missing_workspace.returncode, 0)
            (raspberry_output / "workspace/conf").mkdir(parents=True)
            (raspberry_output / "workspace/conf/layer.conf").write_text(
                "", encoding="utf-8"
            )
            with_workspace = subprocess.run(
                raspberry_arguments, text=True, capture_output=True
            )
            self.assertEqual(
                with_workspace.returncode,
                0,
                with_workspace.stdout + with_workspace.stderr,
            )


if __name__ == "__main__":
    unittest.main()
