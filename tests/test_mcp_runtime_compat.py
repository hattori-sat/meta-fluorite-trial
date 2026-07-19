from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

from mcp.cli import runtime_supported


REPOSITORY = Path(__file__).resolve().parents[1]
RUNTIME = REPOSITORY / "mcp"


class PythonRuntimeCompatibilityTests(unittest.TestCase):
    def test_every_runtime_module_parses_with_python_310_grammar(self) -> None:
        modules = sorted(RUNTIME.rglob("*.py"))
        self.assertGreater(len(modules), 0)
        for path in modules:
            with self.subTest(module=path.relative_to(REPOSITORY)):
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                    feature_version=(3, 10),
                )

    def test_runtime_has_no_third_party_imports(self) -> None:
        external: set[str] = set()
        for path in RUNTIME.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".", 1)[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module.split(".", 1)[0]]
                else:
                    continue
                external.update(
                    name
                    for name in names
                    if name != "mcp" and name not in sys.stdlib_module_names
                )
        self.assertEqual(set(), external)

    def test_deployed_floor_is_310_but_development_gates_remain_311(self) -> None:
        self.assertTrue(runtime_supported((3, 10, 0)))
        self.assertTrue(runtime_supported((3, 11, 0)))
        self.assertFalse(runtime_supported((3, 9, 99)))

        runtime_wrapper = (REPOSITORY / "scripts/run-mcp.sh").read_text(encoding="utf-8")
        self.assertIn("python3.10", runtime_wrapper)
        self.assertIn("(3, 10)", runtime_wrapper)

        for relative in ("scripts/check-python-unittest.sh", "scripts/check-mcp-smoke.sh"):
            with self.subTest(gate=relative):
                gate = (REPOSITORY / relative).read_text(encoding="utf-8")
                self.assertIn("(3, 11)", gate)


if __name__ == "__main__":
    unittest.main()
