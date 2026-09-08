from __future__ import annotations

import hashlib
import json
import unittest

from bijux_pollenomics.adna.sources import archive
from bijux_pollenomics.adna.sources import ena as legacy_archive
from bijux_pollenomics.adna.sources.archive import ena


class ArchiveCompatibilityTests(unittest.TestCase):
    def test_legacy_surface_reexports_canonical_archive_objects(self) -> None:
        self.assertIs(legacy_archive.AdnaArchiveProject, archive.AdnaArchiveProject)
        self.assertIs(legacy_archive.AdnaPaperLinkage, archive.AdnaPaperLinkage)
        self.assertIs(legacy_archive.AdnaEnaQuery, ena.AdnaEnaQuery)
        self.assertIs(legacy_archive.AdnaEnaRecord, ena.AdnaEnaRecord)
        self.assertIs(
            legacy_archive.build_archive_project_catalog,
            archive.build_archive_project_catalog,
        )
        self.assertIs(
            legacy_archive.build_ena_filereport_url,
            ena.build_ena_filereport_url,
        )

    def test_legacy_surface_and_catalog_bytes_are_pinned(self) -> None:
        self.assertEqual(
            legacy_archive.__all__,
            [
                "ADNA_ACCESSION_SCOPES",
                "ADNA_ACCESS_POLICIES",
                "ADNA_DOMESTICATION_SCOPES",
                "ADNA_ENA_RESULT_KINDS",
                "ADNA_PROJECT_EVIDENCE_STRENGTHS",
                "AdnaArchiveProject",
                "AdnaEnaQuery",
                "AdnaEnaRecord",
                "AdnaPaperLinkage",
                "build_archive_project_catalog",
                "build_ena_filereport_url",
                "build_species_archive_projects",
                "classify_archive_project_evidence",
                "parse_ena_filereport_tsv",
            ],
        )
        payload = [row.as_dict() for row in archive.build_archive_project_catalog()]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

        self.assertEqual(len(canonical), 46_489)
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            "fe2d370f55c904a74f907763a1ea712eaac3e513aebc1def411fdf3860a0ee49",
        )


if __name__ == "__main__":
    unittest.main()
