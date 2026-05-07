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
MERMAID_RESERVED_IDS = {
    "class",
    "classdef",
    "click",
    "default",
    "end",
    "graph",
    "linkstyle",
    "style",
    "subgraph",
}


class RepositoryContractRegressionTests(unittest.TestCase):
    def test_generated_data_readme_targets_existing_docs_pages(self) -> None:
        readme_text = (REPO_ROOT / "data" / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\]\((\.\./docs/[^\)]+)\)", readme_text)

        self.assertIn("adna/homo_sapiens", readme_text)
        self.assertIn("adna/equus_caballus", readme_text)
        self.assertIn("adna/bos_taurus", readme_text)
        self.assertIn("adna/canis_lupus_familiaris", readme_text)
        self.assertIn("adna/camelus_dromedarius", readme_text)
        self.assertIn("adna/rangifer_tarandus", readme_text)
        self.assertIn("adna/equus_asinus", readme_text)
        self.assertIn("domesticated-animal curation program", readme_text)
        self.assertIn("aadr -> ../../../aadr", readme_text)
        self.assertGreaterEqual(len(targets), 2)
        for target in targets:
            resolved = (REPO_ROOT / "data" / target).resolve()
            self.assertTrue(
                resolved.exists(),
                f"data/README.md points at a missing docs page: {target}",
            )

    def test_tracked_adna_root_ships_cross_species_audit_artifacts(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"

        self.assertTrue((adna_root / "cross_species_bibliography.json").is_file())
        self.assertTrue((adna_root / "cross_species_bibliography.csv").is_file())
        self.assertTrue((adna_root / "cross_species_archive_inventory.json").is_file())
        self.assertTrue((adna_root / "cross_species_archive_inventory.csv").is_file())
        self.assertTrue((adna_root / "cross_species_freshness.json").is_file())
        self.assertTrue((adna_root / "cross_species_freshness.csv").is_file())
        self.assertTrue((adna_root / "cross_species_coverage_dashboard.json").is_file())
        self.assertTrue((adna_root / "cross_species_coverage_dashboard.csv").is_file())
        self.assertTrue((adna_root / "cross_species_map_readiness.json").is_file())
        self.assertTrue((adna_root / "cross_species_map_readiness.csv").is_file())
        self.assertTrue((adna_root / "unresolved_site_ledger.json").is_file())
        self.assertTrue((adna_root / "unresolved_site_ledger.csv").is_file())
        self.assertTrue((adna_root / "overbroad_site_ledger.json").is_file())
        self.assertTrue((adna_root / "overbroad_site_ledger.csv").is_file())
        self.assertTrue((adna_root / "coordinate_caveat_surface.json").is_file())
        self.assertTrue((adna_root / "coordinate_caveat_surface.md").is_file())
        self.assertTrue((adna_root / "coordinate_confidence_scale.md").is_file())
        self.assertTrue((adna_root / "shipped_product_audit.json").is_file())
        self.assertTrue((adna_root / "source_library" / "project_registry.json").is_file())
        self.assertTrue((adna_root / "source_library" / "paper_registry.json").is_file())
        self.assertTrue((adna_root / "source_library" / "supplement_registry.json").is_file())
        self.assertTrue((adna_root / "source_library" / "source_audit.json").is_file())
        self.assertTrue((adna_root / "source_library" / "source_blockers.json").is_file())
        self.assertTrue(
            (
                adna_root
                / "source_library"
                / "projects"
                / "PRJEB22390"
                / "bundle_manifest.json"
            ).is_file()
        )

    def test_public_report_root_ships_animal_output_audit(self) -> None:
        report_root = REPO_ROOT / "docs" / "report"
        audit_json = report_root / "animal_output_audit.json"
        audit_markdown = report_root / "animal_output_audit.md"

        self.assertTrue(audit_json.is_file())
        self.assertTrue(audit_markdown.is_file())
        self.assertIn("Animal output audit", audit_markdown.read_text(encoding="utf-8"))

    @staticmethod
    def _declared_mermaid_node_ids(block: str) -> set[str]:
        ids: set[str] = set()
        for line in block.splitlines():
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*\[", line)
            if match:
                ids.add(match.group(1).lower())
        return ids

    def test_docs_mermaid_diagrams_avoid_reserved_node_ids(self) -> None:
        failures: list[str] = []

        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"```mermaid\n([\s\S]*?)\n```", text):
                reserved_ids = sorted(
                    MERMAID_RESERVED_IDS.intersection(
                        self._declared_mermaid_node_ids(match.group(1))
                    )
                )
                if reserved_ids:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: reserved Mermaid ids "
                        + ", ".join(reserved_ids)
                    )

        self.assertFalse(
            failures,
            "Mermaid diagrams use reserved node ids:\n" + "\n".join(failures),
        )

    def test_pyproject_declares_apache_license_and_author(self) -> None:
        root_pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        package_pyproject_text = (PACKAGE_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn('members = ["packages/*"]', root_pyproject_text)
        self.assertIn('docs_package = "bijux-pollenomics-dev"', root_pyproject_text)
        self.assertIn('license = { text = "Apache-2.0" }', package_pyproject_text)
        self.assertIn(
            'force-include = { "LICENSE" = "LICENSE", "NOTICE" = "NOTICE" }',
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
            "export PYTHONPYCACHEPREFIX ?= $(ROOT_PYCACHE_DIR)", root_env_text
        )

    def test_readme_and_docs_describe_license_and_test_suites(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docs_text = (
            REPO_ROOT / "docs" / "01-bijux-pollenomics" / "quality" / "test-strategy.md"
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
            "artifacts/root/check-venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertIn("make package-verify", readme_text)

    def test_install_workflow_uses_console_script_smoke_after_install(self) -> None:
        workflow_text = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
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
            / "01-bijux-pollenomics"
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
        self.assertIn("project-level scientific metadata", command_reference)
        self.assertIn("project-level admission reviews", command_reference)
        self.assertIn("report-country <country>", command_reference)
        self.assertIn("report-multi-country-map <countries...>", command_reference)
        self.assertIn("publish-reports", command_reference)
        self.assertIn(
            "`--output-root` defaults to `data` for collection", command_reference
        )
        self.assertIn("for collection or `docs/report` for", command_reference)
        self.assertNotIn("python -m bijux_pollenomics.cli", command_reference)

    def test_module_map_mentions_adna_runtime_boundary(self) -> None:
        module_map = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
            / "architecture"
            / "module-map.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`adna/` owns species-aware ancient-DNA contracts",
            module_map,
        )
        self.assertIn("Homo sapiens runtime manifests", module_map)
        self.assertIn("metadata-only analysis boundaries", module_map)
        self.assertIn("accession-family resolution", module_map)
        self.assertIn("archive-integrity", module_map)
        self.assertIn("curated ENA archive intake metadata", module_map)
        self.assertIn("species curation", module_map)
        self.assertIn("project-level paper", module_map)
        self.assertIn("linkage and scientific metadata", module_map)
        self.assertIn("scientist-facing species review packets", module_map)
        self.assertIn("manifest diff outputs", module_map)
        self.assertIn("cross-species domestication coverage reporting", module_map)
        self.assertIn("non-human normalization", module_map)
        self.assertIn("deterministic artifact plans", module_map)
        self.assertIn("`reporting/adna/`", module_map)
        self.assertIn("`src/bijux_pollenomics/adna/`", module_map)

    def test_directory_layout_docs_mentions_curated_species_roots(self) -> None:
        directory_layout = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "foundation"
            / "directory-layout.md"
        ).read_text(encoding="utf-8")

        self.assertIn("species-owned ancient-DNA surface", directory_layout)
        self.assertIn("domesticated-animal curation roots", directory_layout)
        self.assertIn("`data/adna/equus_caballus/`", directory_layout)
        self.assertIn("`data/adna/bos_taurus/`", directory_layout)
        self.assertIn("`data/adna/canis_lupus_familiaris/`", directory_layout)
        self.assertIn("`data/adna/camelus_dromedarius/`", directory_layout)
        self.assertIn("`data/adna/rangifer_tarandus/`", directory_layout)
        self.assertIn("`data/adna/equus_asinus/`", directory_layout)
        self.assertIn("`data/adna/felis_catus/`", directory_layout)

    def test_homo_sapiens_adna_layout_exists_in_tracked_data_tree(self) -> None:
        species_root = REPO_ROOT / "data" / "adna" / "homo_sapiens"

        self.assertTrue((species_root / "README.md").exists())
        self.assertTrue((species_root / "normalized").is_dir())
        self.assertTrue((species_root / "manifests").is_dir())
        self.assertTrue((species_root / "reports").is_dir())
        self.assertTrue((species_root / "review").is_dir())
        raw_aadr = species_root / "raw" / "aadr"
        self.assertTrue(raw_aadr.is_symlink())
        self.assertEqual(raw_aadr.readlink().as_posix(), "../../../aadr")

    def test_tracked_nonhuman_adna_roots_ship_real_reviewable_files(self) -> None:
        tracked_roots = (
            "equus_caballus",
            "sus_scrofa_domesticus",
            "ovis_aries",
            "bos_taurus",
            "capra_hircus",
            "canis_lupus_familiaris",
            "felis_catus",
            "camelus_dromedarius",
            "rangifer_tarandus",
            "equus_asinus",
        )

        for slug in tracked_roots:
            species_root = REPO_ROOT / "data" / "adna" / slug
            self.assertTrue((species_root / "README.md").is_file(), slug)
            self.assertTrue((species_root / "raw" / "archive_inventory.json").is_file(), slug)
            self.assertTrue((species_root / "raw" / "archive_inventory.csv").is_file(), slug)
            self.assertTrue((species_root / "raw" / "source_snapshot.json").is_file(), slug)
            self.assertTrue((species_root / "raw" / "source_snapshot.csv").is_file(), slug)
            self.assertTrue(
                (species_root / "normalized" / "sample_records.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "sample_records.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "coordinate_provenance.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "coordinate_provenance.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "site_evidence.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "site_evidence.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "project_summaries.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "project_summaries.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "locality_summaries.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "locality_summaries.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "species_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "curation_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "project_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "runtime_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "normalization_bundle.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "citation_manifest.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "support_summary.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "support_summary.md").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "review" / "species_review.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "review" / "archive_integrity.json").is_file(),
                slug,
            )

    def test_mkdocs_uses_main_branch_edit_links_and_local_mermaid_bundle(self) -> None:
        mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("https://bijux.io/bijux-pollenomics/", mkdocs_text)
        self.assertIn("edit/main/docs/", mkdocs_text)
        self.assertIn("https://bijux.io/bijux-core/", mkdocs_text)
        self.assertNotIn("bijux-genomics", mkdocs_text)
        self.assertIn("site_dir: artifacts/root/docs/site", mkdocs_text)
        self.assertIn("custom_dir: docs/overrides", mkdocs_text)
        self.assertIn(
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/docs",
            mkdocs_text,
        )
        self.assertNotIn(
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev\n",
            mkdocs_text,
        )
        self.assertNotIn("docs/hooks/publish_site_assets.py", mkdocs_text)
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

    def test_docs_header_uses_repository_label_for_repository_handbook(self) -> None:
        header_text = (
            REPO_ROOT / "docs" / "overrides" / "partials" / "header.html"
        ).read_text(encoding="utf-8")

        self.assertIn('title == "Repository Handbook"', header_text)
        self.assertIn("Repository", header_text)
        self.assertNotIn("\n    Home\n", header_text)

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
        self.assertFalse((REPO_ROOT / "docs" / "favicon.ico").exists())
        self.assertFalse((REPO_ROOT / "docs" / "apple-touch-icon.png").exists())
        self.assertFalse(
            (REPO_ROOT / "docs" / "apple-touch-icon-precomposed.png").exists()
        )
        self.assertFalse((REPO_ROOT / "docs" / "outputs" / "gallery").exists())

    def test_navigation_sync_bootstraps_shared_navigation_shell(self) -> None:
        script_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "navigation-sync.js"
        ).read_text(encoding="utf-8")
        nav_state_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "nav-state.js"
        ).read_text(encoding="utf-8")
        detail_tabs_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "detail-tabs.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "window.bijuxShell?.bootstrap?.ensureBound",
            script_text,
        )
        self.assertIn(
            "[data-bijux-site-path][aria-current='page']",
            nav_state_text,
        )
        self.assertIn(
            "[data-bijux-detail-path][aria-current='page']",
            detail_tabs_text,
        )

    def test_fieldwork_page_embeds_video_from_site_root_gallery(self) -> None:
        fieldwork_text = (
            REPO_ROOT / "docs" / "04-fieldwork" / "lyngsjon-lake-fieldwork" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '<source src="../../gallery/2026-02-26-data-collection.mp4"',
            fieldwork_text,
        )
        self.assertIn(
            '<a href="../../gallery/2026-02-26-data-collection.mp4">',
            fieldwork_text,
        )

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

    def test_report_docs_describe_final_summary_paths(self) -> None:
        published_artifacts = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "published-reports.md"
        ).read_text(encoding="utf-8")
        report_layout = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
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
            / "03-bijux-pollenomics-maintain"
            / "gh-workflows"
            / "deploy-docs.md"
        ).read_text(encoding="utf-8")
        testing_and_evidence = (
            REPO_ROOT
            / "docs"
            / "03-bijux-pollenomics-maintain"
            / "bijux-pollenomics-dev"
            / "documentation-integrity.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`deploy-docs.yml` builds the strict MkDocs site", automation_workflows
        )
        self.assertIn(
            "workflow follows the shared Bijux docs contract",
            automation_workflows,
        )
        self.assertIn("`mkdocs.shared.yml`", automation_workflows)
        self.assertIn("strict MkDocs builds", testing_and_evidence)
        self.assertIn("`docs/assets/site-icons/`", testing_and_evidence)
        self.assertIn("shared Bijux docs theme contract", testing_and_evidence)

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
