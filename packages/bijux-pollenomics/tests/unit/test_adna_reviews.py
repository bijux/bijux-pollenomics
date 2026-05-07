from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    AdnaSpeciesProjectManifest,
    AdnaSpeciesProjectRow,
    build_species_manifest_diff,
    build_species_review_packet,
)


class AdnaReviewPacketUnitTests(unittest.TestCase):
    def test_species_review_packet_exposes_scientific_manifest_and_release_blockers(
        self,
    ) -> None:
        packet = build_species_review_packet("horse")

        self.assertEqual(packet.species_manifest.species.latin_name, "Equus caballus")
        self.assertEqual(packet.dataset_review.dataset_bucket, "archive_verified_needs_paper_pinning")
        self.assertIn("missing_archive_paper_pinning_rationale", packet.release_blockers)
        self.assertTrue(
            any(
                review.project_accession == "PRJEB56293"
                and not review.admissible_for_curated_support
                for review in packet.project_reviews
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJEB56293"
                and row.support_class == "ancient_but_too_weak"
                for row in packet.too_weak_projects
            )
        )
        botai = next(
            row
            for row in packet.project_manifest.projects
            if row.project_accession == "PRJEB22390"
        )
        self.assertEqual(botai.paper_doi, "10.1126/science.aao3297")
        self.assertEqual(botai.sequencing_target, "shotgun_genome")
        self.assertEqual(botai.nordic_relevance, "non_nordic")

    def test_species_manifest_diff_reports_added_removed_and_changed_projects(self) -> None:
        previous = AdnaSpeciesProjectManifest(
            schema_version="adna-species-project-manifest.v1",
            species_latin_name="Equus caballus",
            projects=(
                AdnaSpeciesProjectRow(
                    project_accession="PRJEB22390",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="archive_verified_needs_paper_pinning",
                    evidence_strength="archive_only",
                    ancient_status="ancient_confirmed",
                    paper_title=None,
                    paper_doi=None,
                    sequencing_target="unknown_or_mixed",
                    material_basis="not_yet_curated",
                    dating_basis="not_yet_curated",
                    geographic_basis="not_yet_curated",
                    access_policy="public_downloadable",
                    public_release_date=None,
                    domestication_scope="domesticated_core",
                    notes="pending paper pin",
                    nordic_relevance="non_nordic",
                    nordic_relevance_reason="not yet tagged as Nordic-relevant in tracked archive context.",
                    last_checked_on="2026-05-07",
                ),
                AdnaSpeciesProjectRow(
                    project_accession="PRJEB56293",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="archive_verified_needs_paper_pinning",
                    evidence_strength="archive_only",
                    ancient_status="ancient_confirmed",
                    paper_title=None,
                    paper_doi=None,
                    sequencing_target="shotgun_genome",
                    material_basis="individual_bone_or_tooth",
                    dating_basis="mixed_radiocarbon_and_archaeological_context",
                    geographic_basis="site_level_localities",
                    access_policy="public_downloadable",
                    public_release_date=None,
                    domestication_scope="domesticated_core",
                    notes="pending paper pin",
                    nordic_relevance="non_nordic",
                    nordic_relevance_reason="not yet tagged as Nordic-relevant in tracked archive context.",
                    last_checked_on="2026-05-07",
                ),
            ),
        )
        current = AdnaSpeciesProjectManifest(
            schema_version="adna-species-project-manifest.v1",
            species_latin_name="Equus caballus",
            projects=(
                AdnaSpeciesProjectRow(
                    project_accession="PRJEB22390",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="paper_pinned_core",
                    evidence_strength="primary_paper_pinned",
                    ancient_status="ancient_confirmed",
                    paper_title="Ancient genomes revisit the ancestry of domestic and Przewalski's horses",
                    paper_doi="10.1126/science.aao3297",
                    sequencing_target="shotgun_genome",
                    material_basis="individual_bone_or_tooth",
                    dating_basis="mixed_radiocarbon_and_archaeological_context",
                    geographic_basis="site_level_localities",
                    access_policy="public_downloadable",
                    public_release_date=None,
                    domestication_scope="domesticated_core",
                    notes="Botai and Przewalski/domestic ancestry anchor.",
                    nordic_relevance="non_nordic",
                    nordic_relevance_reason="not yet tagged as Nordic-relevant in tracked archive context.",
                    last_checked_on="2026-05-07",
                ),
                AdnaSpeciesProjectRow(
                    project_accession="PRJEB44430",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="paper_pinned_core",
                    evidence_strength="primary_paper_pinned",
                    ancient_status="ancient_confirmed",
                    paper_title="The origins and spread of domestic horses from the Western Eurasian steppes",
                    paper_doi="10.1038/s41586-021-04018-9",
                    sequencing_target="shotgun_genome",
                    material_basis="individual_bone_or_tooth",
                    dating_basis="mixed_radiocarbon_and_archaeological_context",
                    geographic_basis="site_level_localities",
                    access_policy="public_downloadable",
                    public_release_date=None,
                    domestication_scope="domesticated_core",
                    notes="Major horse domestication-and-dispersal anchor.",
                    nordic_relevance="non_nordic",
                    nordic_relevance_reason="not yet tagged as Nordic-relevant in tracked archive context.",
                    last_checked_on="2026-05-07",
                ),
            ),
        )

        diff = build_species_manifest_diff(previous, current)

        self.assertEqual(diff.species_latin_name, "Equus caballus")
        self.assertEqual([row.project_accession for row in diff.added_projects], ["PRJEB44430"])
        self.assertEqual([row.project_accession for row in diff.removed_projects], ["PRJEB56293"])
        self.assertEqual(len(diff.changed_projects), 1)
        self.assertEqual(diff.changed_projects[0].project_accession, "PRJEB22390")
        self.assertIn("archive_status", diff.changed_projects[0].changed_fields)
        self.assertIn("paper_doi", diff.changed_projects[0].changed_fields)

    def test_species_review_packet_surfaces_rejected_and_nordic_lead_tables(self) -> None:
        packet = build_species_review_packet("reindeer")

        self.assertTrue(
            any(
                row.project_accession == "PRJEB57293"
                and row.support_class == "rejected"
                for row in packet.rejected_projects
            )
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJEB60484"
                and row.nordic_relevance == "nordic_relevant_unmapped"
                for row in packet.nordic_unmapped_leads
            )
        )


if __name__ == "__main__":
    unittest.main()
