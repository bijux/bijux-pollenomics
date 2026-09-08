from __future__ import annotations

import unittest

import pytest

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class SpeciesPublicationTests(unittest.TestCase):
    def test_tracked_species_readmes_start_from_counted_sample_and_map_posture(
        self,
    ) -> None:
        readme_text = (
            REPO_ROOT / "data" / "adna" / "species" / "ovis_aries" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("- Curated sample rows:", readme_text)
        self.assertIn("- Curated projects:", readme_text)
        self.assertIn("- Curated site rows:", readme_text)
        self.assertIn("- Direct-coordinate rows:", readme_text)
        self.assertIn("- Geocoded rows:", readme_text)
        self.assertIn("- Unresolved sample rows:", readme_text)
        self.assertIn("- Mapped Nordic rows:", readme_text)
        self.assertIn("- Tracked intake projects:", readme_text)
        self.assertIn("## Interpret The Posture", readme_text)
        self.assertIn("## Inspect The Evidence", readme_text)
        self.assertIn("## Directory Contract", readme_text)
        self.assertIn("## Evidence Boundary", readme_text)
        self.assertIn("```mermaid", readme_text)

    def test_public_data_docs_keep_the_evidence_chain_directly_linked(self) -> None:
        inventory_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "sources"
            / "animal-source-intake.md"
        )

        self.assertTrue(inventory_page.is_file())
        inventory_text = inventory_page.read_text(encoding="utf-8")
        self.assertIn("tracked_project_and_paper_inventory.json", inventory_text)
        self.assertIn("paper_registry.json", inventory_text)
        self.assertIn("supplement_acquisition_checklist.json", inventory_text)
        self.assertIn("supplement_file_family_audit.json", inventory_text)
        self.assertIn("Animal Source Intake", inventory_text)
        self.assertIn("source_intake_audit.json", inventory_text)
        self.assertIn("project_sample_master_completeness.json", inventory_text)
        self.assertIn("sample_master.json", inventory_text)
        self.assertIn("project_sample_site_review.json", inventory_text)
        self.assertIn("sample_sites.json", inventory_text)
        self.assertIn("locality_worksheet.json", inventory_text)
        self.assertIn("sample_locality_evidence.json", inventory_text)
        self.assertIn("sample_locality_conflict_ledger.json", inventory_text)
        self.assertIn("site_name_normalization_dictionary.json", inventory_text)
        self.assertIn("project_sample_chronology_review.json", inventory_text)
        self.assertIn("sample_chronology.json", inventory_text)

    def test_project_sample_master_completeness_keeps_traceable_expected_counts(
        self,
    ) -> None:
        import json

        payload = json.loads(
            (
                REPO_ROOT
                / "data"
                / "adna"
                / "governance"
                / "source_library"
                / "project_sample_master_completeness.json"
            ).read_text(encoding="utf-8")
        )
        rows = payload["rows"]

        self.assertTrue(rows)
        for row in rows:
            if row["expected_sample_count"] is None:
                continue
            self.assertTrue(
                str(row["expected_sample_count_provenance"]).strip(),
                f"Expected sample count for {row['project_accession']} lacks provenance.",
            )
            self.assertTrue(
                str(row["expected_sample_count_artifact_path"]).strip(),
                f"Expected sample count for {row['project_accession']} lacks an artifact path.",
            )

    def test_sample_master_rows_do_not_claim_final_status_with_unresolved_ambiguity(
        self,
    ) -> None:
        import json

        project_root = (
            REPO_ROOT / "data" / "adna" / "governance" / "source_library" / "projects"
        )
        for path in project_root.glob("*/sample_master.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rows"]:
                if row["sample_identity_resolution"] != "final":
                    continue
                self.assertFalse(
                    str(row["sample_ambiguity_note"]).strip(),
                    f"{path.relative_to(REPO_ROOT)} publishes a final sample row with an ambiguity note.",
                )

    def test_homo_sapiens_adna_layout_exists_in_tracked_data_tree(self) -> None:
        species_root = REPO_ROOT / "data" / "adna" / "species" / "homo_sapiens"

        self.assertTrue((species_root / "README.md").exists())
        self.assertTrue((species_root / "normalized").is_dir())
        self.assertTrue((species_root / "manifests").is_dir())
        self.assertTrue((species_root / "reports").is_dir())
        self.assertTrue((species_root / "review").is_dir())
        raw_aadr = species_root / "raw" / "aadr"
        self.assertTrue(raw_aadr.is_symlink())
        self.assertEqual(raw_aadr.readlink().as_posix(), "../../../../aadr")

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
            species_root = REPO_ROOT / "data" / "adna" / "species" / slug
            self.assertTrue((species_root / "README.md").is_file(), slug)
            self.assertTrue(
                (species_root / "raw" / "archive_inventory.json").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "archive_inventory.csv").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "source_snapshot.json").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "source_snapshot.csv").is_file(), slug
            )
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
                (species_root / "reports" / "project_recovery_deficits.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "project_recovery_deficits.md").is_file(),
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


if __name__ == "__main__":
    unittest.main()
