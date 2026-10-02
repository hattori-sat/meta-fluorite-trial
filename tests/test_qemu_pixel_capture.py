import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "qemu-pixel-capture.py"
SPEC = importlib.util.spec_from_file_location("qemu_pixel_capture", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_ppm(path: Path, width: int, height: int, pixels: bytes) -> None:
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + pixels)


class QemuPixelCaptureTests(unittest.TestCase):
    def test_analyze_full_region_uses_ppm_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "small.ppm"
            write_ppm(image, 4, 3, bytes([0, 0, 0] * 12))
            result = MODULE.analyze(image, "full", None, "0,0,0", 8)
            self.assertEqual(result["width"], 4)
            self.assertEqual(result["height"], 3)

    def test_analyze_reports_changed_bbox_against_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.ppm"
            sample = root / "sample.ppm"
            baseline = bytes([0, 0, 0] * 16)
            changed = bytearray(baseline)
            changed[(1 * 4 + 2) * 3 : (1 * 4 + 3) * 3] = bytes([0, 0, 255])
            write_ppm(reference, 4, 4, baseline)
            write_ppm(sample, 4, 4, bytes(changed))
            result = MODULE.analyze(sample, "0,0,4,4", reference, "0,0,0", 8)
            self.assertEqual(result["changed_pixels"], 1)
            self.assertEqual(result["bounding_box"], [2, 1, 1, 1])
            self.assertEqual(result["comparison"], "reference")

    def test_analyze_rejects_out_of_bounds_region(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.ppm"
            write_ppm(image, 2, 2, bytes([0, 0, 0] * 4))
            with self.assertRaises(ValueError):
                MODULE.analyze(image, "1,1,2,2", None, "0,0,0", 8)

    def test_ppm_reader_accepts_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.ppm"
            image.write_bytes(b"P6\n# qemu\n2 1\n255\n" + bytes([1, 2, 3, 4, 5, 6]))
            self.assertEqual(MODULE._read_ppm(image), (2, 1, bytes([1, 2, 3, 4, 5, 6])))

    def test_analyze_reports_chromatic_geometry_indicator(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "red-accent.ppm"
            pixels = bytearray([0, 0, 0] * 16)
            pixels[(1 * 4 + 2) * 3 : (1 * 4 + 3) * 3] = bytes([180, 0, 0])
            write_ppm(image, 4, 4, bytes(pixels))
            result = MODULE.analyze(image, "0,0,4,4", None, "0,0,0", 8)
            self.assertEqual(result["chromatic_pixels"], 1)
            self.assertEqual(result["chromatic_bounding_box"], [2, 1, 1, 1])
            self.assertEqual(result["classification_hint"], "geometry-indicators-present")

    def test_analyze_reports_local_edges_for_black_on_white_control(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "black-object.ppm"
            pixels = bytearray([255, 255, 255] * 25)
            for row in (1, 2, 3):
                for column in (1, 2, 3):
                    pixels[(row * 5 + column) * 3 : (row * 5 + column + 1) * 3] = bytes([0, 0, 0])
            write_ppm(image, 5, 5, bytes(pixels))
            result = MODULE.analyze(image, "0,0,5,5", None, "255,255,255", 8)
            self.assertGreater(result["edge_pixels"], 0)
            self.assertEqual(result["edge_bounding_box"], [0, 0, 5, 5])
            self.assertEqual(result["chromatic_pixels"], 0)

    def test_analyze_marks_uniform_black_as_undetectable(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "uniform-black.ppm"
            write_ppm(image, 3, 3, bytes([0, 0, 0] * 9))
            result = MODULE.analyze(image, "0,0,3,3", None, "0,0,0", 8)
            self.assertEqual(result["changed_pixels"], 0)
            self.assertEqual(result["edge_pixels"], 0)
            self.assertEqual(result["chromatic_pixels"], 0)
            self.assertEqual(result["classification_hint"], "uniform-or-undetectable")


if __name__ == "__main__":
    unittest.main()
