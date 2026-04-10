from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW_URL_RE = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/workflows/"
    r"(?P<workflow>[A-Za-z0-9_.-]+)"
)


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
            REPO_ROOT / "docs" / "bijux-pollenomics" / "quality" / "test-strategy.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", readme_text)
        self.assertIn("make lock-check", readme_text)
        self.assertIn("make package-check", readme_text)
        self.assertIn("make package-source-smoke", readme_text)
        self.assertIn("make test-unit", readme_text)
        self.assertIn("make test-regression", readme_text)
        self.assertIn("make test-e2e", readme_text)
        self.assertIn("`tests/unit/`", docs_text)
        self.assertIn("`tests/regression/`", docs_text)
        self.assertIn("`tests/e2e/`", docs_text)

    def test_docs_home_page_uses_repository_name_for_title_and_h1(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

        self.assertIn("title: Bijux Pollenomics", docs_index)
        self.assertIn("# Bijux Pollenomics", docs_index)
        self.assertNotIn("# Docs Index", docs_index)

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
            REPO_ROOT
            / "docs"
            / "bijux-pollenomics"
            / "operations"
            / "installation-and-setup.md"
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
            REPO_ROOT / "docs" / "bijux-pollenomics" / "interfaces" / "cli-surface.md"
        ).read_text(encoding="utf-8")

        self.assertIn("collect-data <sources...>", command_reference)
        self.assertIn("report-country <country>", command_reference)
        self.assertIn("report-multi-country-map <countries...>", command_reference)
        self.assertIn("publish-reports", command_reference)
        self.assertIn(
            "`--output-root` defaults to `data` for collection", command_reference
        )
        self.assertIn("for collection or `docs/report` for", command_reference)
        self.assertNotIn("python -m bijux_pollenomics.cli", command_reference)

    def test_mkdocs_uses_main_branch_edit_links_and_local_mermaid_bundle(self) -> None:
        mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("https://bijux.io/bijux-pollenomics/", mkdocs_text)
        self.assertIn("edit/main/docs/", mkdocs_text)
        self.assertIn("site_dir: artifacts/root/docs/site", mkdocs_text)
        self.assertIn("custom_dir: docs/overrides", mkdocs_text)
        self.assertIn("hooks:", mkdocs_text)
        self.assertIn("docs/hooks/publish_site_assets.py", mkdocs_text)
        self.assertTrue(
            (
                REPO_ROOT
                / "docs"
                / "assets"
                / "javascripts"
                / "vendor"
                / "mermaid-11.6.0.min.js"
            ).exists()
        )
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
        self.assertTrue(
            (REPO_ROOT / "docs" / "overrides" / "partials" / "header.html").exists()
        )
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
        ci_workflow = (
            REPO_ROOT / ".github" / "workflows" / "ci-package.yml"
        ).read_text(encoding="utf-8")
        publish_workflow = (
            REPO_ROOT / ".github" / "workflows" / "publish.yml"
        ).read_text(encoding="utf-8")
        verify_workflow = (
            REPO_ROOT / ".github" / "workflows" / "verify.yml"
        ).read_text(encoding="utf-8")
        deploy_workflow = (
            REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_call:", ci_workflow)
        self.assertIn("cache-dependency-glob: uv.lock", ci_workflow)
        self.assertIn('make -f "$makefile" -C', ci_workflow)
        self.assertIn("name: publish", publish_workflow)
        self.assertIn("build-release-artifacts.yml", publish_workflow)
        self.assertIn("pypa/gh-action-pypi-publish@release/v1", publish_workflow)
        self.assertIn("check-shared-bijux-py", verify_workflow)
        self.assertIn("check-config-layout", verify_workflow)
        self.assertIn("check-make-layout", verify_workflow)
        self.assertIn(
            "make check-shared-bijux-py check-config-layout check-make-layout help",
            verify_workflow,
        )
        self.assertIn("uses: ./.github/workflows/ci-package.yml", verify_workflow)
        self.assertIn("bijux-pollenomics-dev", verify_workflow)
        self.assertIn("check_targets: '[\"quality\", \"security\", \"api\", \"build\", \"sbom\"]'", verify_workflow)
        self.assertIn("Confirm clean worktree after checks", verify_workflow)
        self.assertIn("git status --short", verify_workflow)
        self.assertIn("pull_request:", verify_workflow)
        self.assertIn("astral-sh/setup-uv", verify_workflow)
        self.assertIn("branches: [main]", deploy_workflow)
        self.assertNotIn('tags:\n      - "v*"', deploy_workflow)
        self.assertIn("astral-sh/setup-uv", deploy_workflow)
        self.assertIn("DOCS_PUBLISH_REPOSITORY: bijux/pollenomics", deploy_workflow)
        self.assertIn(
            "DOCS_SITE_URL: https://bijux.io/bijux-pollenomics/",
            deploy_workflow,
        )
        self.assertIn("POLLENOMICS_PUBLISH_TOKEN", deploy_workflow)
        self.assertIn("DOCS_SITE_DIR: artifacts/root/docs/build-site", deploy_workflow)
        self.assertIn("artifacts/root/docs/site", deploy_workflow)
        self.assertIn(
            'git clone "https://x-access-token:${DOCS_PUBLISH_TOKEN}@github.com/${DOCS_PUBLISH_REPOSITORY}.git"',
            deploy_workflow,
        )
        self.assertIn("custom_dir: docs/overrides", deploy_workflow)
        self.assertIn("docs/hooks/publish_site_assets.py", deploy_workflow)
        self.assertIn("Validate published site root assets", deploy_workflow)

    def test_root_readme_workflow_links_follow_checked_in_workflow_tree(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        workflows_dir = REPO_ROOT / ".github" / "workflows"
        known_workflows = {path.name for path in workflows_dir.glob("*.yml")}
        found_workflows = set()

        for match in WORKFLOW_URL_RE.finditer(readme_text):
            self.assertEqual(match.group("repo"), "bijux/bijux-pollenomics")
            workflow_name = match.group("workflow")
            self.assertIn(workflow_name, known_workflows)
            found_workflows.add(workflow_name)

        self.assertTrue(
            {"verify.yml", "publish.yml", "deploy-docs.yml"} <= found_workflows
        )

    def test_report_docs_describe_final_summary_paths(self) -> None:
        published_artifacts = (
            REPO_ROOT
            / "docs"
            / "bijux-pollenomics-data"
            / "outputs"
            / "published-reports.md"
        ).read_text(encoding="utf-8")
        report_layout = (
            REPO_ROOT
            / "docs"
            / "bijux-pollenomics"
            / "interfaces"
            / "artifact-contracts.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Published report bundles live under `docs/report/<country-slug>/`",
            published_artifacts,
        )
        self.assertIn(
            "country bundles under `docs/report/<country-slug>/`", report_layout
        )
        self.assertIn(
            "the shared atlas under `docs/report/nordic-atlas/`", report_layout
        )

    def test_engineering_docs_describe_clean_verification_and_docs_asset_checks(
        self,
    ) -> None:
        automation_workflows = (
            REPO_ROOT
            / "docs"
            / "bijux-pollenomics-maintain"
            / "gh-workflows"
            / "deploy-docs.md"
        ).read_text(encoding="utf-8")
        testing_and_evidence = (
            REPO_ROOT
            / "docs"
            / "bijux-pollenomics-maintain"
            / "bijux-pollenomics-dev"
            / "documentation-integrity.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`deploy-docs.yml` builds the strict MkDocs site", automation_workflows
        )
        self.assertIn(
            "validates the docs output contract before publication",
            automation_workflows,
        )
        self.assertIn("strict MkDocs builds", testing_and_evidence)
        self.assertIn("site asset support", testing_and_evidence)
        self.assertIn("docs/hooks/publish_site_assets.py", testing_and_evidence)

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
