"""Falsify scientific-value coercion and physical-file custody in the controller."""

import copy
from pathlib import Path
import tempfile
import unittest

from observe import exact_typed
from prepare import pin


class ScientificIdentity(unittest.TestCase):
    def test_exact_identity(self):
        value = {"count": 20732, "missing": None, "admitted": False}
        exact_typed(value, copy.deepcopy(value))

    def test_integer_cannot_be_float(self):
        with self.assertRaises(AssertionError):
            exact_typed({"count": 31}, {"count": 31.0})

    def test_false_cannot_be_zero(self):
        with self.assertRaises(AssertionError):
            exact_typed({"admitted": False}, {"admitted": 0})

    def test_null_cannot_be_zero(self):
        with self.assertRaises(AssertionError):
            exact_typed({"missing": None}, {"missing": 0})

    def test_order_cannot_change(self):
        with self.assertRaises(AssertionError):
            exact_typed({"a": 1, "b": 2}, {"b": 2, "a": 1})

    def test_extra_science_cannot_appear(self):
        with self.assertRaises(AssertionError):
            exact_typed({"count": 31}, {"count": 31, "accuracy": True})

    def test_nonfinite_refused(self):
        with self.assertRaises(ValueError):
            exact_typed({"error": float("nan")}, {"error": float("nan")})


class PhysicalIdentity(unittest.TestCase):
    def test_exact_regular_pin(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).absolute().parent) as name:
            path = Path(name) / "source"
            path.write_bytes(b"original")
            original = pin(path)
            self.assertEqual(original["bytes"], 8)
            path.write_bytes(b"changed!")
            self.assertNotEqual(pin(path)["sha256"], original["sha256"])

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).absolute().parent) as name:
            path = Path(name) / "source"
            path.write_bytes(b"original")
            link = path.with_name("link")
            link.symlink_to(path)
            with self.assertRaises(AssertionError):
                pin(link)

    def test_relative_refused(self):
        with self.assertRaises(AssertionError):
            pin(Path("pyproject.toml"))

    def test_directory_refused(self):
        with self.assertRaises(AssertionError):
            pin(Path(__file__).absolute().parent)


if __name__ == "__main__":
    unittest.main()
