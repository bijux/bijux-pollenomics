from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_COORDINATE_PROVENANCE_CLASSES,
    ADNA_MAPPING_POSTURES,
    build_species_coordinate_provenance_rows,
    resolve_project_coordinate_provenance,
)


class AdnaCoordinateProvenanceUnitTests(unittest.TestCase):
    def test_resolve_project_coordinate_provenance_returns_point_ready_horse_anchor(
        self,
    ) -> None:
        rows = resolve_project_coordinate_provenance("PRJEB22390")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.coordinate_basis, "named_site_geocoding")
        self.assertEqual(row.mapping_posture, "mappable_point")
        self.assertEqual(row.coordinate_confidence, "approximate")
        self.assertIn("Botai", row.resolved_place_text)
        self.assertEqual(row.latitude_text, "52.99")
        self.assertEqual(row.longitude_text, "69.15")

    def test_resolve_project_coordinate_provenance_refuses_region_only_pig_point_mapping(
        self,
    ) -> None:
        rows = resolve_project_coordinate_provenance("PRJEB30282")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.coordinate_basis, "region_centroid_fallback")
        self.assertEqual(row.mapping_posture, "refused_region_only")
        self.assertEqual(row.coordinate_confidence, "withheld")
        self.assertEqual(row.latitude_text, "")
        self.assertEqual(row.longitude_text, "")

    def test_resolve_project_coordinate_provenance_keeps_named_place_geocoding_details(
        self,
    ) -> None:
        rows = resolve_project_coordinate_provenance("SRP073444")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.site_label, "Site 1040 near Wadi Halfa dromedary context")
        self.assertEqual(row.original_place_text, "Site 1040 near Wadi Halfa")
        self.assertEqual(row.resolved_place_text, "Wadi Halfa")
        self.assertEqual(row.geocoding_method, "manual_named_place_resolution")
        self.assertIn("Wadi Halfa", row.geocoder_or_gazetteer)

    def test_build_species_coordinate_provenance_rows_preserves_requested_accession_order(
        self,
    ) -> None:
        rows = build_species_coordinate_provenance_rows(
            ("PRJEB59481", "PRJEB22390", "unknown")
        )

        self.assertEqual(
            [row.project_accession for row in rows],
            ["PRJEB59481", "PRJEB22390"],
        )

    def test_coordinate_provenance_constants_expose_supported_classes(self) -> None:
        self.assertIn("named_site_geocoding", ADNA_COORDINATE_PROVENANCE_CLASSES)
        self.assertIn("region_centroid_fallback", ADNA_COORDINATE_PROVENANCE_CLASSES)
        self.assertIn("mappable_point", ADNA_MAPPING_POSTURES)
        self.assertIn("refused_region_only", ADNA_MAPPING_POSTURES)


if __name__ == "__main__":
    unittest.main()
