from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    AdnaArchiveProject,
    AdnaEnaRecord,
    build_archive_integrity_report,
)


class AdnaIntegrityUnitTests(unittest.TestCase):
    def test_archive_integrity_report_detects_duplicate_project_accessions(self) -> None:
        report = build_archive_integrity_report(
            projects=(
                AdnaArchiveProject(
                    species_latin_name="Equus caballus",
                    project_accession="PRJEB22390",
                    result_kind="read_run",
                    metadata_url="https://example.org/1",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="curated_candidate",
                    notes="horse",
                ),
                AdnaArchiveProject(
                    species_latin_name="Equus asinus",
                    project_accession="PRJEB22390",
                    result_kind="read_run",
                    metadata_url="https://example.org/2",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="curated_candidate",
                    notes="donkey",
                ),
            )
        )

        self.assertEqual(len(report.duplicates), 1)
        self.assertEqual(report.duplicates[0].accession, "PRJEB22390")

    def test_archive_integrity_report_detects_species_mismatch_from_archive_metadata(
        self,
    ) -> None:
        report = build_archive_integrity_report(
            species_name="horse",
            projects=(
                AdnaArchiveProject(
                    species_latin_name="Equus caballus",
                    project_accession="PRJEB22390",
                    result_kind="read_run",
                    metadata_url="https://example.org/1",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="curated_candidate",
                    notes="horse",
                ),
            ),
            records=(
                AdnaEnaRecord(
                    study_accession="PRJEB22390",
                    sample_accession="SAMEA1",
                    experiment_accession="ERX1",
                    run_accession="ERR1",
                    analysis_accession=None,
                    analysis_type=None,
                    tax_id="9796",
                    scientific_name="Equus asinus",
                    library_layout="PAIRED",
                    library_source="GENOMIC",
                    library_strategy="WGS",
                    instrument_model="NovaSeq",
                    base_count=100,
                    read_count=10,
                    fastq_bytes=(42, 43),
                    fastq_ftp=("ftp://a_1.fastq.gz", "ftp://a_2.fastq.gz"),
                    submitted_ftp=(),
                    sra_ftp=(),
                    bam_ftp=(),
                ),
            ),
            paper_species_name="Equus caballus",
        )

        self.assertEqual(len(report.species_mismatches), 1)
        self.assertEqual(
            report.species_mismatches[0].mismatch_fields,
            ("archive_scientific_name",),
        )

    def test_archive_integrity_report_surfaces_access_and_domestication_findings(
        self,
    ) -> None:
        report = build_archive_integrity_report(
            projects=(
                AdnaArchiveProject(
                    species_latin_name="Bos taurus",
                    project_accession="PRJEB75467",
                    result_kind="read_run",
                    metadata_url="https://example.org/cattle",
                    source_family="ENA",
                    accession_scope="project",
                    archive_status="paper_pinned_core",
                    notes="aurochs context",
                    ancient_status="ancient_confirmed",
                    access_policy="restricted_access",
                    domestication_scope="wild_or_progenitor_context",
                ),
            )
        )

        self.assertEqual(report.schema_version, "adna-archive-integrity-report.v1")
        self.assertEqual(report.access_findings[0].blocking_reason, "archive_not_publicly_usable")
        self.assertEqual(
            report.domestication_scope_mismatches[0].domestication_scope,
            "wild_or_progenitor_context",
        )


if __name__ == "__main__":
    unittest.main()
