from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_DIR = ROOT / "work/commands"
RUN_ID = "fluorite-0408-0001"
PROFILE = {
    "FLR0026_NATIVE_MODEL_MATCH=sequoia",
    "FLR0026_NATIVE_MODEL_LIMIT=2",
    "FLR0026_NATIVE_SKIP_SKYBOX=1",
    "FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1",
    "FLR0027_NATIVE_SKIP_SHAPES=1",
    "FLR0027_NATIVE_SKIP_LIGHTS=1",
    "FLR0026_MODEL_STAGE_TRACE=1",
}


class FLR0408ProfileTests(unittest.TestCase):
    def test_guest_commands_are_single_line_posix_shell(self):
        paths = sorted(COMMAND_DIR.glob("FLR-0408-guest-*.cmd"))
        self.assertEqual(6, len(paths))
        for path in paths:
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertTrue(source.endswith("\n"))
                self.assertEqual(1, len(source.splitlines()))
                result = subprocess.run(
                    ["/bin/sh", "-n", "-c", source.strip()],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertLessEqual(len(source.strip().encode("utf-8")), 4096)

    def test_launch_reuses_only_the_recorded_model_only_profile(self):
        launch = (COMMAND_DIR / "FLR-0408-guest-launch.cmd").read_text(
            encoding="utf-8"
        )
        for setting in PROFILE:
            with self.subTest(setting=setting):
                self.assertEqual(1, launch.count(setting))
        self.assertIn("env -i HOME=$home PATH=/usr/bin:/bin", launch)
        self.assertIn("XDG_RUNTIME_DIR=/run/user/1001", launch)
        self.assertIn("WAYLAND_DISPLAY=wayland-0", launch)
        self.assertIn("/usr/bin/flutter-auto -b", launch)
        self.assertNotIn("FLR0026_NATIVE_SKIP_ENVIRONMENT", launch)
        self.assertNotIn("FLR0026_NATIVE_READBACK_PROBE", launch)
        self.assertNotIn("FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE", launch)
        self.assertNotIn("FLR0305_PRODUCTION_SCENE_LIGHT", launch)
        self.assertNotIn("CAMERA_", launch)
        self.assertNotIn("WAYLAND_BELOW_PARENT", launch)

    def test_every_guest_path_uses_the_new_fluorite_run_namespace(self):
        for path in COMMAND_DIR.glob("FLR-0408-guest-*.cmd"):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIn(RUN_ID, source)
                self.assertNotIn("/run/user/1001/flr0408-", source)
                self.assertNotIn("/run/user/1001/flr0026-", source)

    def test_scene_gate_is_bounded_and_requires_secondary_scene_add(self):
        gate = (COMMAND_DIR / "FLR-0408-guest-scene-gate.cmd").read_text(
            encoding="utf-8"
        )
        self.assertIn("-lt 90", gate)
        self.assertIn("+ 50", gate)
        self.assertIn("FLR0026_MODEL_STAGE_SCENE_ADD_DONE", gate)
        self.assertIn("FLUORITE0408_SCENE_GATE status=$status", gate)
        self.assertIn("KERNEL_FAULT", gate)
        self.assertIn("IDENTITY_CHANGED", gate)


if __name__ == "__main__":
    unittest.main()
