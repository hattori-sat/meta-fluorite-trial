from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RECIPE = (
    REPOSITORY_ROOT
    / "layers/meta-fluorite-trial/recipes-graphics/flutter-apps/"
    / "toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo_git.bb"
)


class FlutterPubCacheLockTests(unittest.TestCase):
    def test_recipe_installs_lock_before_meta_flutter_archive(self) -> None:
        recipe = RECIPE.read_text(encoding="utf-8")
        self.assertIn("python do_patch:append()", recipe)
        self.assertIn('os.path.join(workdir, "pubspec.lock")', recipe)
        self.assertIn('os.path.join(app_root, "pubspec.lock")', recipe)
        self.assertIn("shutil.copyfile", recipe)
        self.assertIn("PUB_CACHE_ARCHIVE", recipe)
        self.assertIn(".fluorite-pub-cache-archive-refresh", recipe)
        self.assertNotIn("do_configure:prepend()", recipe)


if __name__ == "__main__":
    unittest.main()
