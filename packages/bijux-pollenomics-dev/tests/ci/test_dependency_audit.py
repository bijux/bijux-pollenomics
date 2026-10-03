"""Exercise locked input preparation and explicit workspace source boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from bijux_pollenomics_dev.ci import dependency_audit as EXPORT

JOB = Path(__file__).resolve().parents[4] / "artifacts/dependency-audit-fixtures"


class ExportCases(unittest.TestCase):
    def fixture(self) -> tempfile.TemporaryDirectory[str]:
        (JOB / "fixtures").mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=JOB / "fixtures")

    def repository(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        (repo / "pyproject.toml").write_text(
            '[tool.bijux_pollenomics]\npackages = ["domain"]\n'
        )
        package = repo / "packages/domain"
        (package / "src/domain").mkdir(parents=True)
        (package / "src/domain/__init__.py").write_text('"""First party source."""\n')
        (package / "pyproject.toml").write_text(
            '[project]\nname="domain"\n[project.optional-dependencies]\ndev=[]\n'
        )
        (repo / "uv.lock").write_text(
            '[[package]]\nname="domain"\nsource={editable="packages/domain"}\n[[package]]\nname="public"\nversion="1.2.3"\nsource={registry="https://pypi.org/simple"}\n'
        )
        uv = root / "owned-uv"
        uv.write_text(
            "#!"
            + sys.executable
            + '\nimport pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index("--output-file")+1]);p.write_text("public==1.2.3 ; python_version >= \'3.11\'\\n")\n'
        )
        uv.chmod(0o755)
        return repo, uv

    def test_actual_bounded_export_preserves_markers_and_source_account(self) -> None:
        with self.fixture() as directory:
            repo, uv = self.repository(Path(directory))
            output, account = (
                repo / "artifacts/security/requirements.txt",
                repo / "artifacts/security/workspace-account.json",
            )
            receipt = EXPORT.prepare(repo, "domain", ["dev"], output, account, str(uv))
            self.assertEqual(
                output.read_text(), "public==1.2.3 ; python_version >= '3.11'\n"
            )
            self.assertEqual(
                receipt["requirements_sha256"],
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )
            self.assertFalse(receipt["vulnerability_assessment_performed"])
            self.assertEqual(
                receipt["workspace_distributions"], {"domain": "packages/domain"}
            )
            self.assertIn(
                "packages/domain/src/domain/__init__.py", receipt["source_sha256"]
            )
            self.assertEqual(json.loads(account.read_bytes()), receipt)
            self.assertIn("--locked", receipt["argv"])
            self.assertIn("--offline", receipt["argv"])
            self.assertEqual(
                receipt["argv"][receipt["argv"].index("--python") + 1],
                sys.executable,
            )
            self.assertNotIn("--prune", receipt["argv"])
            self.assertEqual(
                EXPORT.prepare(repo, "domain", ["dev"], output, account, str(uv))[
                    "requirements_sha256"
                ],
                receipt["requirements_sha256"],
            )

    def test_unpinned_unknown_first_party_or_url_never_become_public_pins(self) -> None:
        for text in [
            "public>=1\n",
            "public==9\n",
            "domain==1.2.3\n",
            "public @ https://invalid.example/a.whl\n",
            "public==1.2.3 ; \n",
            "",
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                EXPORT.validate_export(
                    text, {("public", "1.2.3")}, {"domain": "packages/domain"}
                )

    def test_missing_first_party_and_nonpublic_registry_are_refused(self) -> None:
        for packages in [
            [
                {
                    "name": "public",
                    "version": "1",
                    "source": {"registry": "https://pypi.org/simple"},
                }
            ],
            [{"name": "domain", "source": {"editable": "elsewhere"}}],
            [
                {
                    "name": "private",
                    "version": "1",
                    "source": {"registry": "https://private.invalid"},
                }
            ],
        ]:
            with self.subTest(packages=packages), self.assertRaises(ValueError):
                EXPORT.registry_identities(
                    {"package": packages}, {"domain": "packages/domain"}
                )

    def test_invalid_extra_and_external_or_symbolic_publication_refuse(self) -> None:
        with self.fixture() as directory:
            repo, uv = self.repository(Path(directory))
            output, account = (
                repo / "artifacts/requirements.txt",
                repo / "artifacts/account.json",
            )
            with self.assertRaisesRegex(ValueError, "extras"):
                EXPORT.prepare(repo, "domain", ["missing"], output, account, str(uv))
            with self.assertRaisesRegex(ValueError, "owned root"):
                EXPORT.prepare(
                    repo, "domain", ["dev"], repo / "source.txt", account, str(uv)
                )
            (repo / "artifacts").mkdir()
            output.symlink_to(repo / "pyproject.toml")
            before = (repo / "pyproject.toml").read_bytes()
            with self.assertRaisesRegex(ValueError, "symbolic"):
                EXPORT.prepare(repo, "domain", ["dev"], output, account, str(uv))
            self.assertEqual((repo / "pyproject.toml").read_bytes(), before)

    def test_source_mutation_before_publish_preserves_existing_outputs(self) -> None:
        with self.fixture() as directory:
            repo, uv = self.repository(Path(directory))
            output, account = (
                repo / "artifacts/requirements.txt",
                repo / "artifacts/account.json",
            )
            output.parent.mkdir()
            output.write_text("existing requirements")
            account.write_text("existing account")
            uv.write_text(
                uv.read_text()
                + '\npathlib.Path("packages/domain/src/domain/__init__.py").write_text("changed")\n'
            )
            with self.assertRaisesRegex(ValueError, "mutated"):
                EXPORT.prepare(repo, "domain", ["dev"], output, account, str(uv))
            self.assertEqual(output.read_text(), "existing requirements")
            self.assertEqual(account.read_text(), "existing account")


if __name__ == "__main__":
    unittest.main()
