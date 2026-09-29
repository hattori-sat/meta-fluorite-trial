from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGEGROUP = (
    REPOSITORY_ROOT
    / "layers/meta-fluorite-trial/recipes-platform/packagegroups/"
    / "packagegroup-fluorite-runtime-debug.bb"
)
COMMON_INCLUDE = (
    REPOSITORY_ROOT / "layers/meta-fluorite-trial/conf/include/fluorite-common.inc"
)


class RuntimeDebugPackagegroupTests(unittest.TestCase):
    def test_image_uses_project_owned_runtime_debug_packagegroup(self) -> None:
        common = COMMON_INCLUDE.read_text(encoding="utf-8")
        self.assertIn("packagegroup-fluorite-runtime-debug", common)

    def test_packagegroup_contains_runtime_tools_and_target_symbols(self) -> None:
        recipe = PACKAGEGROUP.read_text(encoding="utf-8")
        required_packages = (
            "gdb",
            "gdbserver",
            "strace",
            "perf",
            "elfutils",
            "binutils",
            "systemd",
            "clang",
            "clang-dbg",
            "mesa-dbg",
            "flutter-auto-dbg",
            "flutter-engine-dbg",
            "filament-vk-dbg",
        )
        for package in required_packages:
            with self.subTest(package=package):
                self.assertIn(f"    {package} \\", recipe)

    def test_packagegroup_does_not_enable_global_debug_symbols(self) -> None:
        recipe = PACKAGEGROUP.read_text(encoding="utf-8")
        self.assertNotIn("dbg-pkgs", recipe)


if __name__ == "__main__":
    unittest.main()
