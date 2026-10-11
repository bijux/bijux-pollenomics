"""Exercise declared tooling closures and direct repository-file execution."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import packaging

from bijux_pollenomics_dev.ci import dependency_audit as EXPORT

from . import test_dependency_audit as FIXTURES


class ScopeCases(unittest.TestCase):
    def test_additional_workspace_owner_is_explicit_in_export_and_account(self) -> None:
        cases = FIXTURES.ExportCases()
        with cases.fixture() as directory:
            root = Path(directory)
            repo, uv = cases.repository(root)
            (repo / "pyproject.toml").write_text(
                '[tool.bijux_pollenomics]\npackages=["domain","tooling"]\n'
            )
            tool = repo / "packages/tooling"
            (tool / "src/tooling").mkdir(parents=True)
            (tool / "src/tooling/__init__.py").write_text('"""Tool source."""\n')
            (tool / "pyproject.toml").write_text('[project]\nname="tooling"\n')
            lock = repo / "uv.lock"
            lock.write_text(
                lock.read_text()
                + '\n[[package]]\nname="tooling"\nsource={editable="packages/tooling"}\n'
            )
            receipt = EXPORT.prepare(
                repo,
                "domain",
                ["dev"],
                repo / "artifacts/requirements.txt",
                repo / "artifacts/account.json",
                str(uv),
                additional_distributions=["tooling"],
            )
            self.assertEqual(receipt["additional_workspace_distributions"], ["tooling"])
            self.assertEqual(receipt["argv"].count("--package"), 2)
            self.assertIn(
                "packages/tooling/src/tooling/__init__.py", receipt["source_sha256"]
            )

    def test_undeclared_or_duplicate_workspace_owner_refuses_before_export(
        self,
    ) -> None:
        cases = FIXTURES.ExportCases()
        with cases.fixture() as directory:
            repo, uv = cases.repository(Path(directory))
            for additional in (["unknown"], ["domain"], ["unknown", "unknown"]):
                with (
                    self.subTest(additional=additional),
                    self.assertRaisesRegex(ValueError, "additional"),
                ):
                    EXPORT.prepare(
                        repo,
                        "domain",
                        ["dev"],
                        repo / "artifacts/requirements.txt",
                        repo / "artifacts/account.json",
                        str(uv),
                        additional_distributions=additional,
                    )
            self.assertFalse((repo / "artifacts/requirements.txt").exists())

    def test_direct_file_guard_without_installed_dev_distribution(self) -> None:
        cases = FIXTURES.ExportCases()
        with cases.fixture() as directory:
            root = Path(directory)
            repo, uv = cases.repository(root)
            source = root / "producer-src"
            owned = source / "bijux_pollenomics_dev/ci"
            owned.mkdir(parents=True)
            (owned.parent / "__init__.py").write_text('"""Owned tooling source."""\n')
            (owned / "__init__.py").write_text('"""Owned CI source."""\n')
            original = Path(EXPORT.__file__).parent
            for name in ("dependency_audit.py", "dependency_audit_runtime.py"):
                shutil.copyfile(original / name, owned / name)
            shutil.copytree(
                Path(packaging.__file__).parent,
                source / "packaging",
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            public = owned / "public.dist-info"
            public.mkdir()
            (public / "METADATA").write_text(
                "Metadata-Version: 2.1\nName: public\nVersion: 1.2.3\n"
            )
            script = owned / "dependency_audit.py"
            output, account = (
                repo / "artifacts/requirements.txt",
                repo / "artifacts/account.json",
            )
            child = (
                "import importlib.metadata as m,runpy,sys;"
                "sys.path.insert(0,sys.argv[1]);"
                "assert not list(m.distributions(name='bijux-pollenomics-dev'));"
                "sys.argv=sys.argv[2:];runpy.run_path(sys.argv[0],run_name='__main__')"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-c",
                    child,
                    str(owned),
                    str(script),
                    "--repository",
                    str(repo),
                    "--distribution",
                    "domain",
                    "--extra",
                    "dev",
                    "--output",
                    str(output),
                    "--account",
                    str(account),
                    "--uv",
                    str(uv),
                    "--verify-installed",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=125,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(account.read_text())
            self.assertEqual(
                receipt["installed_runtime"]["actual_installed_public_versions"],
                {"public": "1.2.3"},
            )
            self.assertFalse(receipt["vulnerability_assessment_performed"])
            self.assertEqual(
                output.read_text(), "public==1.2.3 ; python_version >= '3.11'\n"
            )


if __name__ == "__main__":
    unittest.main()
