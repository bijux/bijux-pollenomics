from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)


class AdnaRecordUnitTests(unittest.TestCase):
    def test_sample_record_exposes_compatibility_properties(self) -> None:
        sample = AdnaSampleRecord(
            identity=AdnaSampleIdentity(
                namespace="homo_sapiens:aadr_genetic_id",
                stable_token="SE1",
                accession_lineage=(
                    "species:Homo sapiens",
                    "source:AADR",
                    "dataset:ho",
                    "genetic_id:SE1",
                ),
            ),
            locality_identity=AdnaLocalityIdentity(
                namespace="homo_sapiens:locality",
                stable_token="homo_sapiens:aadr:sweden:uppsala:59-8586-17-6389",
                locality_text="Uppsala",
                political_entity="Sweden",
                source_anchor_tokens=("AADR", "59.8586", "17.6389"),
            ),
            species_latin_name="Homo sapiens",
            species_common_name="human",
            source_family="AADR",
            source_release="v66",
            record_modality="metadata_only",
            review_strength="curated_release_metadata",
            provenance_quality="release_manifest_pinned",
            master_id="SE1",
            group_id="Sweden_Group",
            locality="Uppsala",
            political_entity="Sweden",
            coordinates=AdnaCoordinate(
                latitude=59.8586,
                longitude=17.6389,
                latitude_text="59.8586",
                longitude_text="17.6389",
                confidence="unknown",
            ),
            publication="PaperA",
            year_first_published="2022",
            full_date="500 BCE",
            chronology=AdnaChronology(
                original_text="500 BCE",
                time_start_bp=2200,
                time_end_bp=2700,
                time_mean_bp=2450,
                dating_basis="bp_mean_and_stddev",
            ),
            data_type="AG",
            molecular_sex="F",
            datasets=("ho",),
        )

        self.assertEqual(sample.genetic_id, "SE1")
        self.assertEqual(sample.sample_namespace, "homo_sapiens:aadr_genetic_id")
        self.assertEqual(sample.locality_namespace, "homo_sapiens:locality")
        self.assertEqual(sample.latitude_text, "59.8586")
        self.assertEqual(sample.time_mean_bp, 2450)
        self.assertEqual(sample.dating_basis, "bp_mean_and_stddev")
        self.assertEqual(sample.record_modality, "metadata_only")
        self.assertEqual(sample.review_strength, "curated_release_metadata")
        self.assertEqual(sample.provenance_quality, "release_manifest_pinned")

    def test_locality_summary_exposes_species_and_time_properties(self) -> None:
        locality = AdnaLocalitySummary(
            identity=AdnaLocalityIdentity(
                namespace="homo_sapiens:locality",
                stable_token="homo_sapiens:aadr:sweden:uppsala:59-8586-17-6389",
                locality_text="Uppsala",
                political_entity="Sweden",
                source_anchor_tokens=("AADR", "59.8586", "17.6389"),
            ),
            species_latin_name="Homo sapiens",
            species_common_name="human",
            source_family="AADR",
            source_releases=("v66",),
            record_modalities=("metadata_only",),
            review_strengths=("curated_release_metadata",),
            provenance_qualities=("release_manifest_pinned",),
            locality="Uppsala",
            coordinates=AdnaCoordinate(
                latitude=59.8586,
                longitude=17.6389,
                latitude_text="59.8586",
                longitude_text="17.6389",
                confidence="unknown",
            ),
            sample_count=2,
            sample_ids=("SE1", "SE2"),
            datasets=("1240k", "ho"),
            chronology=AdnaChronology(
                original_text="2200-2700 BP",
                time_start_bp=2200,
                time_end_bp=2700,
                time_mean_bp=2450,
                dating_basis="bp_window",
            ),
            sample_namespace="homo_sapiens:aadr_genetic_id",
        )

        self.assertEqual(locality.species_latin_name, "Homo sapiens")
        self.assertEqual(locality.locality_namespace, "homo_sapiens:locality")
        self.assertEqual(locality.time_label, "2200-2700 BP")
        self.assertEqual(locality.coordinate_confidence, "unknown")
        self.assertEqual(locality.source_releases, ("v66",))

    def test_nonhuman_records_can_keep_coordinates_and_political_entity_withheld(self) -> None:
        sample = AdnaSampleRecord(
            identity=AdnaSampleIdentity(
                namespace="equus_caballus:normalized_sample",
                stable_token="equus_caballus:project:PRJEB22390",
                accession_lineage=(
                    "species:Equus caballus",
                    "ENA:PRJEB22390",
                ),
            ),
            locality_identity=AdnaLocalityIdentity(
                namespace="equus_caballus:locality",
                stable_token="equus_caballus:withheld:PRJEB22390",
                locality_text="withheld at project-summary level",
                political_entity=None,
                source_anchor_tokens=("PRJEB22390",),
            ),
            species_latin_name="Equus caballus",
            species_common_name="horse",
            source_family="ENA",
            source_release="PRJEB22390",
            record_modality="archive_reads",
            review_strength="primary_paper_pinned",
            provenance_quality="archive_project_catalog",
            master_id="PRJEB22390",
            group_id="PRJEB22390",
            locality=None,
            political_entity=None,
            coordinates=AdnaCoordinate(
                latitude=None,
                longitude=None,
                latitude_text="",
                longitude_text="",
                confidence="withheld",
            ),
            publication="Ancient genomes revisit the ancestry of domestic and Przewalski's horses",
            year_first_published="2018",
            full_date="",
            chronology=AdnaChronology(
                original_text="",
                time_start_bp=None,
                time_end_bp=None,
                time_mean_bp=None,
                dating_basis="unknown",
            ),
            data_type="archive_project_summary",
            molecular_sex="",
            datasets=("PRJEB22390",),
        )

        self.assertIsNone(sample.latitude)
        self.assertIsNone(sample.longitude)
        self.assertIsNone(sample.political_entity)
        self.assertIsNone(sample.locality)
        self.assertEqual(sample.coordinate_confidence, "withheld")


if __name__ == "__main__":
    unittest.main()
