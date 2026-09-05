from __future__ import annotations

import unittest

import pytest
import subprocess

from .repository_paths import (
    PACKAGE_ROOT,
    REPO_ROOT,
    WORKFLOW_URL_RE,
)

pytestmark = pytest.mark.generated_artifacts


class RepositoryAutomationTests(unittest.TestCase):
    def test_pyproject_declares_apache_license_and_author(self) -> None:
        root_pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        package_pyproject_text = (PACKAGE_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn('members = ["packages/*"]', root_pyproject_text)
        self.assertIn('docs_package = "bijux-pollenomics-dev"', root_pyproject_text)
        self.assertIn('license = { text = "Apache-2.0" }', package_pyproject_text)
        self.assertIn('"LICENSE",', package_pyproject_text)
        self.assertIn('"NOTICE",', package_pyproject_text)
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
        build_targets_text = (
            REPO_ROOT / "makes" / "bijux-py" / "ci" / "build.mk"
        ).read_text(encoding="utf-8")
        package_make_text = (
            REPO_ROOT / "makes" / "packages" / "bijux-pollenomics.mk"
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
            'ls -l "$$out_dir" || true',
            build_targets_text,
        )
        self.assertIn("BUILD_POST_TARGETS := build-install-smoke", package_make_text)
        self.assertIn("build-install-smoke:", package_make_text)
        self.assertIn(
            "ROOT_ARTIFACTS_DIR ?= $(PROJECT_ARTIFACTS_DIR)/root", root_env_text
        )
        self.assertIn("ROOT_VENV ?= $(ROOT_ARTIFACTS_DIR)/venv", root_env_text)
        self.assertIn(
            "export PYTHONPYCACHEPREFIX := $(abspath $(ROOT_PYCACHE_DIR))",
            root_env_text,
        )


    def test_readme_bootstrap_flow_installs_before_running_the_console_script(
        self,
    ) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        install_index = readme_text.index("make install")
        console_version_index = readme_text.index(
            "artifacts/root/check-venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertIn("make package-verify", readme_text)


    def test_install_workflow_uses_console_script_smoke_after_install(self) -> None:
        workflow_text = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics"
            / "operations"
            / "installation-and-setup.md"
        ).read_text(encoding="utf-8")

        install_index = workflow_text.index("make install")
        console_version_index = workflow_text.index(
            "artifacts/root/check-venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertNotIn(
            "make package-check\nmake package-smoke\nmake package-source-smoke",
            workflow_text,
        )


    def test_command_reference_uses_installed_cli_examples(self) -> None:
        command_reference = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics"
            / "interfaces"
            / "cli-surface.md"
        ).read_text(encoding="utf-8")

        self.assertIn("collect-data <sources...>", command_reference)
        self.assertIn("adna-layout --species <name>", command_reference)
        self.assertIn("adna-runtime-manifest --species <name>", command_reference)
        self.assertIn("adna-artifact-plan --species <name>", command_reference)
        self.assertIn("adna-curation-manifest --species <name>", command_reference)
        self.assertIn("adna-normalization-bundle --species <name>", command_reference)
        self.assertIn("adna-archive-projects", command_reference)
        self.assertIn("adna-domestication-coverage", command_reference)
        self.assertIn("adna-species", command_reference)
        self.assertIn("adna-species-review --species <name>", command_reference)
        self.assertIn("deterministic species rebuild", command_reference)
        self.assertIn("project summaries, study summaries, lineage", command_reference)
        self.assertIn("curated, pending, and rejected projects", command_reference)
        self.assertIn("cross-species curation coverage", command_reference)
        self.assertIn(
            "project-side metadata that still needs to feed sample extraction",
            command_reference,
        )
        self.assertIn("project admission reviews", command_reference)
        self.assertIn("report-country <country>", command_reference)
        self.assertIn("report-multi-country-map <countries...>", command_reference)
        self.assertIn("publish-reports", command_reference)
        self.assertIn(
            "`--output-root` defaults to `data` for collection", command_reference
        )
        self.assertIn("for collection or `docs/report` for", command_reference)
        self.assertNotIn("python -m bijux_pollenomics.cli", command_reference)


    def test_github_workflows_cover_repository_checks_and_docs_deploy(self) -> None:
        ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        release_artifacts_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-artifacts.yml"
        ).read_text(encoding="utf-8")
        release_pypi_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-pypi.yml"
        ).read_text(encoding="utf-8")
        release_ghcr_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-ghcr.yml"
        ).read_text(encoding="utf-8")
        release_github_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-github.yml"
        ).read_text(encoding="utf-8")
        verify_workflow = (
            REPO_ROOT / ".github" / "workflows" / "verify.yml"
        ).read_text(encoding="utf-8")
        deploy_workflow = (
            REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_call:", ci_workflow)
        self.assertIn(
            "tests-${{ inputs.package_slug }}-py${{ matrix.python-version }}",
            ci_workflow,
        )
        self.assertIn(
            "checks-${{ inputs.package_slug }}-${{ matrix.target }}",
            ci_workflow,
        )
        self.assertIn("lint-${{ inputs.package_slug }}", ci_workflow)
        self.assertIn("cache-dependency-glob: uv.lock", ci_workflow)
        self.assertIn('make -f \\"$makefile\\" -C', ci_workflow)
        self.assertIn("name: release-artifacts", release_artifacts_workflow)
        self.assertIn('find "$dist_dir" -type f', release_artifacts_workflow)
        self.assertIn(
            "No publish artifacts found under $dist_dir",
            release_artifacts_workflow,
        )
        self.assertIn(
            "name: release-artifacts-${{ inputs.package_slug }}",
            release_artifacts_workflow,
        )
        self.assertIn("Stage GitHub release assets", release_artifacts_workflow)
        self.assertIn('sbom_dir="${ARTIFACTS_DIR}/sbom"', release_artifacts_workflow)
        self.assertIn("-dist-$(basename", release_artifacts_workflow)
        self.assertIn("-sbom-prod.cdx.json", release_artifacts_workflow)
        self.assertIn("-sbom-dev.cdx.json", release_artifacts_workflow)
        self.assertIn("-sbom-summary.txt", release_artifacts_workflow)
        self.assertIn("name: release-pypi", release_pypi_workflow)
        self.assertIn("pypa/gh-action-pypi-publish@", release_pypi_workflow)
        self.assertIn("publish_auth_default", release_pypi_workflow)
        self.assertIn("PYPI_API_TOKEN", release_pypi_workflow)
        self.assertIn("name: release-ghcr", release_ghcr_workflow)
        self.assertIn("packages: write", release_ghcr_workflow)
        self.assertIn("name: release-github", release_github_workflow)
        self.assertIn("softprops/action-gh-release@", release_github_workflow)
        self.assertIn("overwrite_files: true", release_github_workflow)
        self.assertIn("check-shared-bijux-py", verify_workflow)
        self.assertIn("check-config-layout", verify_workflow)
        self.assertIn("check-make-layout", verify_workflow)
        self.assertIn('"apis/**"', verify_workflow)
        self.assertIn("mkdocs.shared.yml", verify_workflow)
        self.assertIn("tox.ini", verify_workflow)
        self.assertIn(
            "make check-shared-bijux-py check-config-layout check-make-layout help",
            verify_workflow,
        )
        self.assertIn("uses: ./.github/workflows/ci.yml", verify_workflow)
        self.assertIn("bijux-pollenomics-dev", verify_workflow)
        self.assertIn("openapi-drift", verify_workflow)
        self.assertIn("check_targets:", verify_workflow)
        self.assertIn("api_toolchain_targets:", verify_workflow)
        self.assertIn("pull_request:", verify_workflow)
        self.assertIn("astral-sh/setup-uv", verify_workflow)
        self.assertIn("workflow_dispatch:", deploy_workflow)
        self.assertIn("workflow_call:", deploy_workflow)
        self.assertIn("astral-sh/setup-uv", deploy_workflow)
        self.assertIn("pages: write", deploy_workflow)
        self.assertIn("id-token: write", deploy_workflow)
        self.assertIn("actions/configure-pages@", deploy_workflow)
        self.assertIn("actions/upload-pages-artifact@", deploy_workflow)
        self.assertIn("actions/deploy-pages@", deploy_workflow)
        self.assertIn("github.ref == 'refs/heads/main'", deploy_workflow)
        self.assertIn("github.ref == 'refs/heads/master'", deploy_workflow)
        self.assertIn("startsWith(github.ref, 'refs/tags/v')", deploy_workflow)
        self.assertIn("site_dir", deploy_workflow)
        self.assertIn("artifacts/root/docs/build-site", deploy_workflow)
        self.assertIn("mkdocs.shared.yml", deploy_workflow)


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
            {
                "verify.yml",
                "release-pypi.yml",
                "release-ghcr.yml",
                "release-github.yml",
                "deploy-docs.yml",
            }
            <= found_workflows
        )


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



if __name__ == "__main__":
    unittest.main()
