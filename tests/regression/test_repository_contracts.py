from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RepositoryContractRegressionTests(unittest.TestCase):
    def test_pyproject_declares_apache_license_and_author(self) -> None:
        pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('license = "Apache-2.0"', pyproject_text)
        self.assertIn('license-files = ["LICENSE"]', pyproject_text)
        self.assertIn('{ name = "Bijan Mousavi", email = "bijan@bijux.io" }', pyproject_text)

    def test_makefile_exposes_named_test_suites(self) -> None:
        makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn(".PHONY:", makefile_text)
        self.assertIn("lock", makefile_text)
        self.assertIn("lock-check", makefile_text)
        self.assertIn("test-unit: install", makefile_text)
        self.assertIn("test-regression: install", makefile_text)
        self.assertIn("test-e2e: install", makefile_text)

    def test_readme_and_docs_describe_license_and_test_suites(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docs_text = (REPO_ROOT / "docs" / "engineering" / "testing-and-evidence.md").read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", readme_text)
        self.assertIn("make lock-check", readme_text)
        self.assertIn("make test-unit", readme_text)
        self.assertIn("make test-regression", readme_text)
        self.assertIn("make test-e2e", readme_text)
        self.assertIn("tests/unit/", docs_text)
        self.assertIn("tests/regression/", docs_text)
        self.assertIn("tests/e2e/", docs_text)

    def test_notice_file_keeps_copyright_holder(self) -> None:
        notice_text = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")

        self.assertIn("Bijan Mousavi <bijan@bijux.io>", notice_text)
