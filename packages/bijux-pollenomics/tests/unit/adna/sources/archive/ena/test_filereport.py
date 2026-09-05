from __future__ import annotations

import unittest

from bijux_pollenomics.adna.sources.archive.ena import (
    AdnaEnaQuery,
    build_ena_filereport_url,
    parse_ena_filereport_tsv,
)


class EnaFileReportTests(unittest.TestCase):
    def test_url_uses_expected_read_run_fields(self) -> None:
        url = build_ena_filereport_url("PRJEB22390", "read_run")

        self.assertIn("accession=PRJEB22390", url)
        self.assertIn("result=read_run", url)
        self.assertIn("study_accession", url)
        self.assertIn("run_accession", url)
        self.assertNotIn("analysis_accession", url)

    def test_url_rejects_invalid_accession(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid ENA selector"):
            build_ena_filereport_url("PRJEB22390&format=json")

    def test_parser_filters_by_sample(self) -> None:
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

    def test_parser_rejects_missing_required_columns(self) -> None:
        query = AdnaEnaQuery(projects=("PRJEB22390",), samples=(), extra_accessions=())
        with self.assertRaisesRegex(
            ValueError, "missing required columns: sample_accession"
        ):
            parse_ena_filereport_tsv(
                "study_accession\trun_accession\nPRJEB22390\tERR1\n",
                query=query,
            )

    def test_parser_rejects_duplicate_or_blank_required_columns(self) -> None:
        query = AdnaEnaQuery(projects=("PRJEB22390",), samples=(), extra_accessions=())
        with self.assertRaisesRegex(ValueError, "duplicate columns: run_accession"):
            parse_ena_filereport_tsv(
                "study_accession\tsample_accession\texperiment_accession\t"
                "run_accession\trun_accession\nPRJEB22390\tSAMEA1\tERX1\tERR1\tERR1\n",
                query=query,
            )
        with self.assertRaisesRegex(ValueError, "blank required values: run_accession"):
            parse_ena_filereport_tsv(
                "study_accession\tsample_accession\texperiment_accession\t"
                "run_accession\nPRJEB22390\tSAMEA1\tERX1\t\n",
                query=query,
            )

    def test_parser_rejects_negative_counts_and_fastq_cardinality_mismatch(
        self,
    ) -> None:
        query = AdnaEnaQuery(projects=("PRJEB22390",), samples=(), extra_accessions=())
        header = (
            "study_accession\tsample_accession\texperiment_accession\trun_accession\t"
            "base_count\tfastq_bytes\tfastq_ftp\n"
        )
        with self.assertRaisesRegex(ValueError, "negative base_count value -1"):
            parse_ena_filereport_tsv(
                header + "PRJEB22390\tSAMEA1\tERX1\tERR1\t-1\t42\ta.fastq.gz\n",
                query=query,
            )
        with self.assertRaisesRegex(ValueError, "2 fastq byte values for 1 FASTQ"):
            parse_ena_filereport_tsv(
                header + "PRJEB22390\tSAMEA1\tERX1\tERR1\t1\t42;43\ta.fastq.gz\n",
                query=query,
            )

    def test_parser_excludes_rows_outside_project_and_sample_selectors(self) -> None:
        query = AdnaEnaQuery(
            projects=("PRJEB22390",),
            samples=("SAMEA1",),
            extra_accessions=(),
        )
        header = (
            "study_accession\tsample_accession\texperiment_accession\trun_accession\n"
        )
        rows = parse_ena_filereport_tsv(
            header
            + "PRJEB99999\tSAMEA1\tERX1\tERR1\n"
            + "PRJEB22390\tSAMEA2\tERX2\tERR2\n"
            + "PRJEB22390\tSAMEA1\tERX3\tERR3\n",
            query=query,
        )

        self.assertEqual([row.run_accession for row in rows], ["ERR3"])


if __name__ == "__main__":
    unittest.main()
