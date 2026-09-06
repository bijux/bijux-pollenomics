from __future__ import annotations

import unittest

import pytest
import yaml

from .mkdocs_loading import MkDocsLoader

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class MkDocsConfigurationTests(unittest.TestCase):
    def test_root_mkdocs_redirect_targets_exist(self) -> None:
        config = yaml.load(
            (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"),
            Loader=MkDocsLoader,
        )
        redirect_maps = config["plugins"][2]["redirects"]["redirect_maps"]

        missing_targets = [
            target
            for target in redirect_maps.values()
            if not (REPO_ROOT / "docs" / target).is_file()
        ]

        self.assertEqual(missing_targets, [])


    def test_public_mkdocs_nav_uses_directory_sections_before_leaf_pages(self) -> None:
        config = yaml.load(
            (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"),
            Loader=MkDocsLoader,
        )
        nav = config["nav"]

        def nav_entry(label: str) -> list[object]:
            for item in nav:
                if label in item:
                    return item[label]
            raise AssertionError(f"Missing nav section: {label}")

        pollenomics = nav_entry("Pollenomics")
        self.assertEqual(pollenomics[0], {"Overview": "public/pollenomics/index.md"})
        self.assertEqual(
            [next(iter(item.keys())) for item in pollenomics[1:]],
            ["Foundation", "Architecture", "Interfaces", "Operations", "Quality"],
        )

        pollenomics_data = nav_entry("Data")
        self.assertEqual(
            [next(iter(item.keys())) for item in pollenomics_data[1:]],
            [
                "System",
                "Database",
                "Sources",
                "Curation",
                "Evidence",
                "Publications",
            ],
        )

        fieldwork = nav_entry("Fieldwork")
        self.assertEqual(fieldwork[0], {"Overview": "public/fieldwork/index.md"})
        self.assertEqual(
            fieldwork[1],
            {
                "Lyngsjön Lake Fieldwork": "public/fieldwork/lyngsjon-lake-fieldwork/index.md"
            },
        )

        nordic_atlas = nav_entry("Nordic Atlas")
        self.assertEqual(nordic_atlas[0], {"Overview": "public/nordic-atlas/index.md"})
        self.assertEqual(
            nordic_atlas[1],
            {"Chronology Playback": "public/nordic-atlas/chronology-playback/index.md"},
        )
        self.assertEqual(
            nordic_atlas[2],
            {
                "Sweden Lake Priorities": "public/nordic-atlas/sweden-lake-priorities/index.md"
            },
        )


    def test_shared_mkdocs_excludes_badge_template_from_public_docs_graph(self) -> None:
        config = yaml.unsafe_load(
            (REPO_ROOT / "mkdocs.shared.yml").read_text(encoding="utf-8")
        )

        self.assertEqual(config["exclude_docs"].strip(), "badges.md\ninternal/**")


    def test_shared_mkdocs_keeps_generic_shell_defaults(self) -> None:
        config = yaml.unsafe_load(
            (REPO_ROOT / "mkdocs.shared.yml").read_text(encoding="utf-8")
        )
        bijux = config["extra"]["bijux"]

        self.assertEqual(bijux["repository"], "bijux")
        self.assertEqual(bijux["nav_mode"], "default")
        self.assertEqual(bijux["theme_key"], "bijux:theme")
        self.assertNotIn("docs_package", bijux)
        self.assertIn("hub_links", bijux)
        self.assertTrue(
            any(
                link["url"] == "https://bijux.io/bijux-core/"
                for link in bijux["hub_links"]
            )
        )


    def test_mkdocs_uses_main_branch_edit_links_and_local_mermaid_bundle(self) -> None:
        mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        shared_mkdocs_text = (REPO_ROOT / "mkdocs.shared.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("https://bijux.io/bijux-pollenomics/", mkdocs_text)
        self.assertIn("edit/main/docs/", mkdocs_text)
        self.assertIn("INHERIT: mkdocs.shared.yml", mkdocs_text)
        self.assertIn("https://bijux.io/bijux-core/", shared_mkdocs_text)
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
        self.assertFalse((REPO_ROOT / "docs" / "publications" / "gallery").exists())


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


    def test_shared_nav_hides_scoped_sidebar_on_section_overview_homepages(
        self,
    ) -> None:
        nav_override = (
            REPO_ROOT / "docs" / "overrides" / "partials" / "nav.html"
        ).read_text(encoding="utf-8")
        shared_nav = (
            REPO_ROOT / ".bijux" / "shared" / "bijux-docs" / "partials" / "nav.html"
        ).read_text(encoding="utf-8")
        root_make = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")
        docs_make = (REPO_ROOT / "makes" / "bijux-docs.mk").read_text(encoding="utf-8")

        self.assertFalse((REPO_ROOT / "configs" / "docs-shell").exists())
        self.assertIn("current_page.parent.children", nav_override)
        self.assertIn("landing_home_page", nav_override)
        self.assertEqual(nav_override, shared_nav)
        self.assertNotIn("bijux-docs-apply-repo-overrides", root_make)
        self.assertNotIn("bijux-docs-apply-repo-overrides", docs_make)



if __name__ == "__main__":
    unittest.main()
