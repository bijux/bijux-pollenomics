from __future__ import annotations

import re
import tomllib
import unittest

from tests.support.repository import REPOSITORY_ROOT


class CommandLineUnitTests(unittest.TestCase):
    def test_package_version_matches_pyproject(self) -> None:
        package_root = REPOSITORY_ROOT / "packages" / "bijux-pollenomics"
        pyproject_text = package_root.joinpath("pyproject.toml").read_text(
            encoding="utf-8"
        )
        pyproject = tomllib.loads(pyproject_text)
        module_text = package_root.joinpath(
            "src/bijux_pollenomics/__init__.py"
        ).read_text(encoding="utf-8")
        pyproject_fallback = re.search(
            r'fallback-version\s*=\s*"(?P<version>[^"]+)"', pyproject_text
        )
        module_fallback = re.search(
            r'__version__\s*=\s*"(?P<version>[^"]+)"', module_text
        )

        self.assertIn('dynamic = ["version"]', pyproject_text)
        self.assertEqual(pyproject["project"]["requires-python"], ">=3.11,<4")
        self.assertIn("[tool.hatch.version]", pyproject_text)
        self.assertIn('source = "vcs"', pyproject_text)
        if pyproject_fallback is None:
            self.fail("Missing fallback-version in package pyproject.toml")
        if module_fallback is None:
            self.fail("Missing fallback __version__ in package module")
        self.assertEqual(
            pyproject_fallback.group("version"), module_fallback.group("version")
        )
