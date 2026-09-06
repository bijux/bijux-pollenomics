from __future__ import annotations

from collections import Counter
import unittest

from bijux_pollenomics.adna.sources.archive import (
    build_archive_project_catalog,
    build_species_archive_projects,
    classify_archive_project_evidence,
)
from bijux_pollenomics.adna.sources.snapshots import resolve_archive_source_snapshot


class ArchiveCatalogTests(unittest.TestCase):
    def test_catalog_has_unique_accessions_and_expected_species_counts(self) -> None:
        catalog = build_archive_project_catalog()
        accessions = [row.project_accession for row in catalog]

        self.assertEqual(len(catalog), 40)
        self.assertEqual(len(accessions), len(set(accessions)))
        self.assertEqual(
            Counter(row.species_latin_name for row in catalog),
            {
                "Equus caballus": 8,
                "Ovis aries": 6,
                "Sus scrofa domesticus": 4,
                "Bos taurus": 3,
                "Capra hircus": 3,
                "Felis catus": 2,
                "Canis lupus familiaris": 3,
                "Camelus dromedarius": 2,
                "Equus asinus": 5,
                "Rangifer tarandus": 4,
            },
        )
        for project in catalog:
            self.assertEqual(
                resolve_archive_source_snapshot(project).project_accession,
                project.project_accession,
            )

    def test_catalog_includes_paper_pinned_and_rejected_projects(self) -> None:
        catalog = build_archive_project_catalog()
        projects_by_species = {
            species: [row for row in catalog if row.species_latin_name == species]
            for species in (
                "Equus caballus",
                "Capra hircus",
                "Canis lupus familiaris",
                "Camelus dromedarius",
                "Rangifer tarandus",
                "Equus asinus",
                "Sus scrofa domesticus",
            )
        }

        self.assertGreaterEqual(len(projects_by_species["Equus caballus"]), 8)
        self.assertTrue(
            any(
                row.project_accession == "PRJEB90141"
                for row in projects_by_species["Capra hircus"]
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "SRS1407451"
                for row in projects_by_species["Canis lupus familiaris"]
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "SRP073444"
                for row in projects_by_species["Camelus dromedarius"]
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJEB60484"
                for row in projects_by_species["Rangifer tarandus"]
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJEB55549"
                and row.archive_status == "reject_or_out_of_scope"
                for row in projects_by_species["Equus asinus"]
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJNA421430"
                for row in projects_by_species["Sus scrofa domesticus"]
            )
        )

    def test_species_projects_resolve_via_registered_alias(self) -> None:
        projects = build_species_archive_projects("horse")

        self.assertEqual(projects[0].species_latin_name, "Equus caballus")
        self.assertTrue(
            all(
                project.metadata_url.startswith(
                    "https://www.ebi.ac.uk/ena/portal/api/filereport?"
                )
                for project in projects
            )
        )

        dog_projects = build_species_archive_projects("dog")
        self.assertEqual(dog_projects[0].source_family, "SRA")
        self.assertEqual(dog_projects[0].accession_scope, "sample")
        self.assertTrue(
            dog_projects[0].metadata_url.startswith(
                "https://www.ncbi.nlm.nih.gov/sra?term="
            )
        )

    def test_primary_paper_linkage_retains_scientific_metadata(self) -> None:
        projects = build_species_archive_projects("horse")
        botai = next(row for row in projects if row.project_accession == "PRJEB22390")

        self.assertEqual(
            classify_archive_project_evidence(botai), "primary_paper_pinned"
        )
        self.assertEqual(botai.archive_status, "paper_pinned_core")
        self.assertEqual(botai.ancient_status, "ancient_confirmed")
        self.assertEqual(botai.sequencing_target, "shotgun_genome")
        self.assertEqual(botai.material_basis, "individual_bone_or_tooth")
        self.assertEqual(
            botai.dating_basis, "mixed_radiocarbon_and_archaeological_context"
        )
        self.assertEqual(botai.geographic_basis, "site_level_localities")
        self.assertIsNotNone(botai.paper_linkage)
        assert botai.paper_linkage is not None
        self.assertEqual(botai.paper_linkage.doi, "10.1126/science.aao3297")
        self.assertIn("PRJEB22390", botai.paper_linkage.pinning_evidence)

    def test_archive_only_project_remains_explicit(self) -> None:
        chinese = next(
            row
            for row in build_species_archive_projects("pig")
            if row.project_accession == "PRJNA788987"
        )

        self.assertEqual(classify_archive_project_evidence(chinese), "archive_only")
        self.assertEqual(chinese.archive_status, "archive_verified_needs_paper_pinning")
        self.assertEqual(chinese.ancient_status, "ancient_confirmed")
        self.assertIsNone(chinese.paper_linkage)

    def test_comparator_and_genbank_scope_remain_explicit(self) -> None:
        reindeer = next(
            row
            for row in build_species_archive_projects("reindeer")
            if row.project_accession == "PRJEB60484"
        )
        camel = next(
            row
            for row in build_species_archive_projects("camel")
            if row.project_accession == "KU605068-KU605080"
        )

        self.assertEqual(reindeer.archive_status, "comparator_only")
        self.assertEqual(reindeer.domestication_scope, "ancient_comparator")
        self.assertEqual(camel.source_family, "GenBank")
        self.assertEqual(camel.accession_scope, "accession_range")
        self.assertIsNotNone(camel.paper_linkage)
        assert camel.paper_linkage is not None
        self.assertEqual(camel.paper_linkage.doi, "10.1111/1755-0998.12551")


if __name__ == "__main__":
    unittest.main()
