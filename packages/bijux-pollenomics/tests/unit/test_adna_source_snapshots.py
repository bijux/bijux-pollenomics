from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    build_species_archive_projects,
    build_species_source_snapshots,
    resolve_archive_source_snapshot,
)


class AdnaSourceSnapshotUnitTests(unittest.TestCase):
    def test_species_source_snapshots_preserve_live_ena_study_wording(self) -> None:
        horse_snapshots = build_species_source_snapshots("horse")
        botai = next(
            snapshot
            for snapshot in horse_snapshots
            if snapshot.project_accession == "PRJEB22390"
        )

        self.assertEqual(botai.title_basis, "ena-study-search")
        self.assertIn("domestic and Przewalski's horses", botai.source_title)
        self.assertIn("Botai culture", botai.source_description)

    def test_source_snapshot_uses_honest_fallback_for_sample_level_sra_accessions(
        self,
    ) -> None:
        sample_project = next(
            project
            for project in build_species_archive_projects("dog")
            if project.project_accession == "SRS1407451"
        )

        snapshot = resolve_archive_source_snapshot(sample_project)

        self.assertEqual(
            snapshot.title_basis,
            "primary_paper_sample_accession_fallback",
        )
        self.assertEqual(
            snapshot.description_basis,
            "curated_scope_note_fallback",
        )
        self.assertIn("Ancient European dog genomes", snapshot.source_title)
        self.assertIn("CTC sample", snapshot.source_description)

    def test_species_source_snapshots_cover_non_ena_secondary_accessions(self) -> None:
        camel_snapshots = build_species_source_snapshots("camel")
        camel_anchor = next(
            snapshot
            for snapshot in camel_snapshots
            if snapshot.project_accession == "SRP073444"
        )

        self.assertEqual(camel_anchor.title_basis, "ena-secondary-study-search")
        self.assertIn("Camelus dromedarius Raw sequence reads", camel_anchor.source_title)
        self.assertIn("ancient domestic and wild dromedary camel", camel_anchor.source_description)


if __name__ == "__main__":
    unittest.main()
