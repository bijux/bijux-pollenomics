from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    AdnaEnaQuery,
    build_archive_project_catalog,
    build_ena_filereport_url,
    build_species_archive_projects,
    classify_archive_project_evidence,
    parse_ena_filereport_tsv,
)


class AdnaEnaUnitTests(unittest.TestCase):
    def test_build_ena_filereport_url_uses_expected_read_run_fields(self) -> None:
        url = build_ena_filereport_url("PRJEB22390", "read_run")

        self.assertIn("accession=PRJEB22390", url)
        self.assertIn("result=read_run", url)
        self.assertIn("study_accession", url)
        self.assertIn("run_accession", url)
        self.assertNotIn("analysis_accession", url)

    def test_parse_ena_filereport_tsv_filters_by_sample(self) -> None:
        query = AdnaEnaQuery(
            projects=("PRJEB22390",),
            samples=("SAMEA1",),
            extra_accessions=(),
        )
        tsv = (
            "study_accession\tsample_accession\texperiment_accession\trun_accession\t"
            "tax_id\tscientific_name\tlibrary_layout\tlibrary_source\tlibrary_strategy\t"
            "instrument_model\tbase_count\tread_count\tfastq_bytes\tfastq_ftp\t"
            "submitted_ftp\tsra_ftp\n"
            "PRJEB22390\tSAMEA1\tERX1\tERR1\t9796\tEquus caballus\tPAIRED\tGENOMIC\tWGS\t"
            "NovaSeq\t100\t10\t42;43\tftp.sra.ebi.ac.uk/a_1.fastq.gz;ftp.sra.ebi.ac.uk/a_2.fastq.gz\t"
            "ftp.sra.ebi.ac.uk/a.submitted\tftp.sra.ebi.ac.uk/a.sra\n"
            "PRJEB22390\tSAMEA2\tERX2\tERR2\t9796\tEquus caballus\tPAIRED\tGENOMIC\tWGS\t"
            "NovaSeq\t100\t10\t42;43\tftp.sra.ebi.ac.uk/b_1.fastq.gz;ftp.sra.ebi.ac.uk/b_2.fastq.gz\t"
            "ftp.sra.ebi.ac.uk/b.submitted\tftp.sra.ebi.ac.uk/b.sra\n"
        )

        rows = parse_ena_filereport_tsv(tsv=tsv, query=query)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].run_accession, "ERR1")
        self.assertEqual(rows[0].scientific_name, "Equus caballus")
        self.assertEqual(len(rows[0].fastq_ftp), 2)

    def test_parse_ena_filereport_tsv_rejects_missing_required_columns(self) -> None:
        query = AdnaEnaQuery(projects=("PRJEB22390",), samples=(), extra_accessions=())
        with self.assertRaisesRegex(ValueError, "missing required columns: sample_accession"):
            parse_ena_filereport_tsv(
                "study_accession\trun_accession\nPRJEB22390\tERR1\n",
                query=query,
            )

    def test_archive_project_catalog_includes_paper_pinned_and_rejected_projects(self) -> None:
        catalog = build_archive_project_catalog()

        horse = [row for row in catalog if row.species_latin_name == "Equus caballus"]
        goat = [row for row in catalog if row.species_latin_name == "Capra hircus"]
        donkey = [row for row in catalog if row.species_latin_name == "Equus asinus"]
        pig = [row for row in catalog if row.species_latin_name == "Sus scrofa domesticus"]

        self.assertGreaterEqual(len(horse), 8)
        self.assertTrue(any(row.project_accession == "PRJEB90141" for row in goat))
        self.assertTrue(
            any(
                row.project_accession == "PRJEB55549"
                and row.archive_status == "reject_or_out_of_scope"
                for row in donkey
            )
        )
        self.assertTrue(any(row.project_accession == "PRJNA421430" for row in pig))

    def test_species_archive_projects_resolve_via_registered_alias(self) -> None:
        projects = build_species_archive_projects("horse")

        self.assertEqual(projects[0].species_latin_name, "Equus caballus")
        self.assertTrue(
            all(project.metadata_url.startswith("https://www.ebi.ac.uk/ena/portal/api/filereport?")
                for project in projects)
        )

    def test_archive_project_catalog_records_primary_paper_linkage_and_scientific_metadata(
        self,
    ) -> None:
        projects = build_species_archive_projects("horse")

        botai = next(row for row in projects if row.project_accession == "PRJEB22390")

        self.assertEqual(classify_archive_project_evidence(botai), "primary_paper_pinned")
        self.assertEqual(botai.archive_status, "paper_pinned_core")
        self.assertEqual(botai.ancient_status, "ancient_confirmed")
        self.assertEqual(botai.sequencing_target, "shotgun_genome")
        self.assertEqual(botai.material_basis, "individual_bone_or_tooth")
        self.assertEqual(botai.dating_basis, "mixed_radiocarbon_and_archaeological_context")
        self.assertEqual(botai.geographic_basis, "site_level_localities")
        self.assertEqual(botai.paper_linkage.doi, "10.1126/science.aao3297")
        self.assertIn("PRJEB22390", botai.paper_linkage.pinning_evidence)

    def test_archive_project_catalog_preserves_archive_only_status_when_paper_pin_is_missing(
        self,
    ) -> None:
        projects = build_species_archive_projects("pig")

        chinese = next(row for row in projects if row.project_accession == "PRJNA788987")

        self.assertEqual(classify_archive_project_evidence(chinese), "archive_only")
        self.assertEqual(chinese.archive_status, "archive_verified_needs_paper_pinning")
        self.assertEqual(chinese.ancient_status, "ancient_confirmed")
        self.assertIsNone(chinese.paper_linkage)


if __name__ == "__main__":
    unittest.main()
