from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]


class RepositoryContractRegressionTests(unittest.TestCase):
    def test_pyproject_declares_apache_license_and_author(self) -> None:
        root_pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        package_pyproject_text = (PACKAGE_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn('members = ["packages/*"]', root_pyproject_text)
        self.assertIn('docs_package = "bijux-pollenomics-dev"', root_pyproject_text)
        self.assertIn('license = { text = "Apache-2.0" }', package_pyproject_text)
        self.assertIn(
            'force-include = { "../../LICENSE" = "LICENSE", "../../NOTICE" = "NOTICE" }',
            package_pyproject_text,
        )
        self.assertIn(
            '{ name = "Bijan Mousavi", email = "bijan@bijux.io" }',
            package_pyproject_text,
        )

    def test_makefile_exposes_named_test_suites(self) -> None:
        makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        root_make_text = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")
        root_env_text = (
            REPO_ROOT / "makes" / "bijux-py" / "root" / "env.mk"
        ).read_text(encoding="utf-8")
        test_targets_text = (
            REPO_ROOT / "makes" / "bijux-py" / "ci" / "test.mk"
        ).read_text(encoding="utf-8")

        self.assertIn("include makes/root.mk", makefile_text)
        self.assertIn("lock", root_make_text)
        self.assertIn("lock-check", root_make_text)
        self.assertIn("package-verify", root_make_text)
        self.assertIn("package-check", root_make_text)
        self.assertIn("package-smoke", root_make_text)
        self.assertIn("package-source-smoke", root_make_text)
        self.assertIn("test-unit:", test_targets_text)
        self.assertIn("test-regression:", test_targets_text)
        self.assertIn("test-e2e:", test_targets_text)
        self.assertIn(
            "ROOT_ARTIFACTS_DIR ?= $(PROJECT_ARTIFACTS_DIR)/root", root_env_text
        )
        self.assertIn("ROOT_VENV ?= $(ROOT_ARTIFACTS_DIR)/venv", root_env_text)
        self.assertIn(
            "export PYTHONPYCACHEPREFIX ?= $(ROOT_PYCACHE_DIR)", root_env_text
        )

    def test_readme_and_docs_describe_license_and_test_suites(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docs_text = (
            REPO_ROOT / "docs" / "engineering" / "testing-and-evidence.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", readme_text)
        self.assertIn("make lock-check", readme_text)
        self.assertIn("make package-check", readme_text)
        self.assertIn("make package-source-smoke", readme_text)
        self.assertIn("make test-unit", readme_text)
        self.assertIn("make test-regression", readme_text)
        self.assertIn("make test-e2e", readme_text)
        self.assertIn("packages/bijux-pollenomics/tests/unit/", docs_text)
        self.assertIn("packages/bijux-pollenomics/tests/regression/", docs_text)
        self.assertIn("packages/bijux-pollenomics/tests/e2e/", docs_text)

    def test_readme_bootstrap_flow_installs_before_running_the_console_script(
        self,
    ) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        install_index = readme_text.index("make install")
        console_version_index = readme_text.index(
            "artifacts/.venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertIn("make package-verify", readme_text)

    def test_install_workflow_uses_console_script_smoke_after_install(self) -> None:
        workflow_text = (
            REPO_ROOT / "docs" / "workflows" / "install-and-verify.md"
        ).read_text(encoding="utf-8")

        install_index = workflow_text.index("make install")
        console_version_index = workflow_text.index(
            "artifacts/.venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertNotIn(
            "make package-check\nmake package-smoke\nmake package-source-smoke",
            workflow_text,
        )

    def test_command_reference_uses_installed_cli_examples(self) -> None:
        command_reference = (
            REPO_ROOT / "docs" / "reference" / "command-reference.md"
        ).read_text(encoding="utf-8")

        bootstrap_section = command_reference.split(
            "## Data Collection Commands", maxsplit=1
        )[0]

        self.assertIn(
            "artifacts/.venv/bin/bijux-pollenomics collect-data all", command_reference
        )
        self.assertLess(
            bootstrap_section.index("make install"),
            bootstrap_section.index("artifacts/.venv/bin/bijux-pollenomics --version"),
        )
        self.assertIn("make package-check", command_reference)
        self.assertIn("make package-smoke", command_reference)
        self.assertIn("make package-source-smoke", command_reference)
        self.assertIn("## Make Targets That Change Tracked State", command_reference)
        self.assertIn("normalized case-insensitively", command_reference)
        self.assertNotIn("python -m bijux_pollenomics.cli", command_reference)

    def test_mkdocs_uses_main_branch_edit_links_and_local_mermaid_bundle(self) -> None:
        mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("https://bijux.io/pollenomics/", mkdocs_text)
        self.assertIn("edit/main/docs/", mkdocs_text)
        self.assertIn("site_dir: artifacts/root/docs/site", mkdocs_text)
        self.assertIn("assets/javascripts/vendor/mermaid-11.6.0.min.js", mkdocs_text)
        self.assertIn("custom_dir: docs/overrides", mkdocs_text)
        self.assertIn("favicon: assets/site-icons/favicon.ico", mkdocs_text)
        self.assertIn("hooks:", mkdocs_text)
        self.assertIn("docs/hooks/publish_site_assets.py", mkdocs_text)
        self.assertNotIn("cdn.jsdelivr.net/npm/mermaid", mkdocs_text)

    def test_docs_keep_browser_icon_sources_under_assets(self) -> None:
        self.assertTrue(
            (REPO_ROOT / "docs" / "assets" / "site-icons" / "favicon.ico").exists()
        )
        self.assertTrue(
            (
                REPO_ROOT / "docs" / "assets" / "site-icons" / "apple-touch-icon.png"
            ).exists()
        )
        self.assertTrue(
            (
                REPO_ROOT
                / "docs"
                / "assets"
                / "site-icons"
                / "apple-touch-icon-precomposed.png"
            ).exists()
        )
        self.assertTrue((REPO_ROOT / "docs" / "overrides" / "main.html").exists())
        self.assertTrue(
            (REPO_ROOT / "docs" / "hooks" / "publish_site_assets.py").exists()
        )
        self.assertFalse((REPO_ROOT / "docs" / "favicon.ico").exists())
        self.assertFalse((REPO_ROOT / "docs" / "apple-touch-icon.png").exists())
        self.assertFalse(
            (REPO_ROOT / "docs" / "apple-touch-icon-precomposed.png").exists()
        )
        self.assertFalse((REPO_ROOT / "docs" / "outputs" / "gallery").exists())

    def test_github_workflows_cover_repository_checks_and_docs_deploy(self) -> None:
        verify_workflow = (
            REPO_ROOT / ".github" / "workflows" / "verify.yml"
        ).read_text(encoding="utf-8")
        deploy_workflow = (
            REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("make check PYTHON=python", verify_workflow)
        self.assertIn("Confirm clean worktree after checks", verify_workflow)
        self.assertIn("git status --short", verify_workflow)
        self.assertIn("pull_request:", verify_workflow)
        self.assertIn("astral-sh/setup-uv", verify_workflow)
        self.assertIn("branches:\n      - main", deploy_workflow)
        self.assertNotIn('tags:\n      - "v*"', deploy_workflow)
        self.assertIn("astral-sh/setup-uv", deploy_workflow)
        self.assertIn("DOCS_PUBLISH_REPOSITORY: bijux/pollenomics", deploy_workflow)
        self.assertIn("DOCS_SITE_URL: https://bijux.io/pollenomics/", deploy_workflow)
        self.assertIn("POLLENOMICS_PUBLISH_TOKEN", deploy_workflow)
        self.assertIn("artifacts/root/docs/site", deploy_workflow)
        self.assertIn(
            'git clone "https://x-access-token:${DOCS_PUBLISH_TOKEN}@github.com/${DOCS_PUBLISH_REPOSITORY}.git"',
            deploy_workflow,
        )
        self.assertIn("custom_dir: docs/overrides", deploy_workflow)
        self.assertIn("docs/hooks/publish_site_assets.py", deploy_workflow)
        self.assertIn("Validate published site root assets", deploy_workflow)

    def test_report_docs_describe_final_summary_paths(self) -> None:
        published_artifacts = (
            REPO_ROOT / "docs" / "outputs" / "published-artifacts.md"
        ).read_text(encoding="utf-8")
        report_layout = (
            REPO_ROOT / "docs" / "reference" / "report-layout.md"
        ).read_text(encoding="utf-8")

        self.assertIn("final `docs/report/...` output paths", published_artifacts)
        self.assertIn("final `docs/report/...` bundle locations", report_layout)

    def test_engineering_docs_describe_clean_verification_and_docs_asset_checks(
        self,
    ) -> None:
        automation_workflows = (
            REPO_ROOT / "docs" / "engineering" / "automation-workflows.md"
        ).read_text(encoding="utf-8")
        testing_and_evidence = (
            REPO_ROOT / "docs" / "engineering" / "testing-and-evidence.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "fails if `make check` leaves tracked or untracked repository drift behind",
            automation_workflows,
        )
        self.assertIn(
            "published the browser-probed root icons into the site root",
            automation_workflows,
        )
        self.assertIn(
            "dedicated `bijux/pollenomics` Pages repository", automation_workflows
        )
        self.assertIn("clean repository tree after verification", testing_and_evidence)

    def test_notice_file_keeps_copyright_holder(self) -> None:
        notice_text = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")

        self.assertIn("Bijan Mousavi <bijan@bijux.io>", notice_text)

    def test_repository_does_not_track_generated_cache_files(self) -> None:
        tracked_files = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()

        generated_cache_files = [
            path
            for path in tracked_files
            if "/__pycache__/" in f"/{path}"
            or path.endswith((".pyc", ".pyo", ".DS_Store"))
        ]

        self.assertEqual(generated_cache_files, [])
