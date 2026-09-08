from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    resolve_accession_lineage,
    resolve_accession_reference,
)


class AdnaAccessionUnitTests(unittest.TestCase):
    def test_resolve_accession_reference_keeps_ena_projects_separate_from_bioprojects(
        self,
    ) -> None:
        ena = resolve_accession_reference("ENA:PRJEB22390")
        bioproject = resolve_accession_reference("BioProject:PRJNA788987")

        self.assertEqual(ena.family, "ena_project")
        self.assertEqual(ena.accession, "PRJEB22390")
        self.assertEqual(bioproject.family, "bioproject")
        self.assertEqual(bioproject.accession, "PRJNA788987")

    def test_resolve_accession_reference_supports_sra_samples_and_genbank_ranges(
        self,
    ) -> None:
        sample = resolve_accession_reference("SAMEA104746767")
        accession_range = resolve_accession_reference("GenBank:AY123456-AY123460")

        self.assertEqual(sample.family, "sra_sample")
        self.assertEqual(accession_range.family, "genbank_range")
        self.assertEqual(accession_range.range_end, "AY123460")

    def test_resolve_accession_lineage_ignores_non_accession_tokens(self) -> None:
        references = resolve_accession_lineage(
            (
                "species:Homo sapiens",
                "source:AADR",
                "ENA:PRJEB22390",
                "SAMEA104746767",
            )
        )

        self.assertEqual(
            [item.family for item in references], ["ena_project", "sra_sample"]
        )


if __name__ == "__main__":
    unittest.main()
