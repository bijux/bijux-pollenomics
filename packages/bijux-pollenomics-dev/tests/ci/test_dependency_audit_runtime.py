"""Exercise actual installed metadata, target markers and publication refusal."""

from __future__ import annotations

import importlib.metadata as metadata
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics_dev.ci import dependency_audit as EXPORT
from bijux_pollenomics_dev.ci import dependency_audit_runtime as RUNTIME

from . import test_dependency_audit as FIXTURES

JOB = (
    Path(__file__).resolve().parents[4] / "artifacts/dependency-audit-runtime-fixtures"
)


class RuntimeCases(unittest.TestCase):
    def fixture(self) -> tempfile.TemporaryDirectory[str]:
        JOB.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=JOB)

    def distribution(self, root: Path, version: str) -> Path:
        directory = root / "public.dist-info"
        directory.mkdir(exist_ok=True)
        path = directory / "METADATA"
        path.write_text(
            "Metadata-Version: 2.1\nName: public\nVersion: " + version + "\n"
        )
        return path

    def test_actual_installed_metadata_and_inactive_marker(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            self.distribution(root, "1.2.3.0")
            with patch.object(sys, "path", [str(root), *sys.path]):
                receipt = RUNTIME.installed_runtime(
                    'public==1.2.3\nnot-installed==9 ; sys_platform == "impossible"\n'
                )
            self.assertEqual(
                receipt["active_locked_public_versions"], {"public": "1.2.3"}
            )
            self.assertEqual(
                receipt["actual_installed_public_versions"], {"public": "1.2.3.0"}
            )
            self.assertEqual(receipt["python_executable"], sys.executable)
            self.assertEqual(receipt["python_prefix"], sys.prefix)
            self.assertIn("python_full_version", receipt["marker_environment"])

    def test_actual_changed_missing_and_conflicting_distribution_refuse(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            self.distribution(root, "2.0")
            with patch.object(sys, "path", [str(root), *sys.path]):
                for text in (
                    "public==1.2.3",
                    "not-installed==9",
                    "public==1.2.3\npublic==2.0",
                ):
                    with self.subTest(text=text), self.assertRaises(ValueError):
                        RUNTIME.installed_runtime(text)

    def test_duplicate_actual_installed_identity_refuses(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            self.distribution(root, "1.2.3")
            duplicate = root / "another-path"
            duplicate.mkdir()
            self.distribution(duplicate, "2.0")
            with (
                patch.object(sys, "path", [str(root), str(duplicate), *sys.path]),
                self.assertRaisesRegex(ValueError, "ambiguous"),
            ):
                RUNTIME.installed_runtime("public==1.2.3")

    def test_inexact_or_nonpublic_runtime_requirements_refuse(self) -> None:
        for text in (
            "",
            "public>=1",
            "public==1.*",
            "public[extra]==1",
            "public @ https://invalid.example/package.whl",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                RUNTIME.installed_runtime(text)

    def test_export_only_is_explicit_and_verified_export_records_runtime(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            repo, uv = FIXTURES.ExportCases().repository(root)
            self.distribution(root, "1.2.3")
            output = repo / "artifacts/requirements.txt"
            account = repo / "artifacts/account.json"
            receipt = EXPORT.prepare(repo, "domain", ["dev"], output, account, str(uv))
            self.assertIsNone(receipt["installed_runtime"])
            original = output.read_bytes()
            with patch.object(sys, "path", [str(root), *sys.path]):
                receipt = EXPORT.prepare(
                    repo,
                    "domain",
                    ["dev"],
                    output,
                    account,
                    str(uv),
                    verify_installed=True,
                )
            self.assertIsNotNone(receipt["installed_runtime"])
            self.assertFalse(receipt["vulnerability_assessment_performed"])
            self.assertEqual(output.read_bytes(), original)

    def test_changed_runtime_before_publication_preserves_output_pair(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            repo, uv = FIXTURES.ExportCases().repository(root)
            output = repo / "artifacts/requirements.txt"
            account = repo / "artifacts/account.json"
            output.parent.mkdir()
            output.write_bytes(b"existing inputs")
            account.write_bytes(b"existing account")
            for versions in (["2.0"], ["1.2.3", "2.0"]):
                with (
                    self.subTest(versions=versions),
                    patch.object(metadata, "version", side_effect=versions),
                    self.assertRaisesRegex(
                        ValueError, "installed public versions differ"
                    ),
                ):
                    EXPORT.prepare(
                        repo,
                        "domain",
                        ["dev"],
                        output,
                        account,
                        str(uv),
                        verify_installed=True,
                    )
                self.assertEqual(output.read_bytes(), b"existing inputs")
                self.assertEqual(account.read_bytes(), b"existing account")


if __name__ == "__main__":
    unittest.main()
