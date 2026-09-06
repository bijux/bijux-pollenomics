from __future__ import annotations

import unittest

from bijux_pollenomics.adna.projects.registry.localities import (
    build_species_project_locality_leads,
    resolve_project_locality_leads,
)


class AdnaProjectLocalityUnitTests(unittest.TestCase):
    def test_resolve_project_locality_leads_expand_botai_into_sample_owned_sites(
        self,
    ) -> None:
        rows = resolve_project_locality_leads("PRJEB22390")

        self.assertEqual(len(rows), 27)
        botai = next(row for row in rows if row.locality_text == "Botai")
        self.assertEqual(botai.political_entity, "")
        self.assertEqual(botai.coordinate_basis, "")
        self.assertEqual(botai.chronology_text, "5500 BP")

    def test_resolve_project_locality_leads_maps_source_reported_sites(
        self,
    ) -> None:
        rows = resolve_project_locality_leads("PRJEB59481")

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {row.locality_text for row in rows}, {"Kastelholm", "Stora Förvar"}
        )
        self.assertTrue(
            all(row.coordinate_basis == "archive_coordinates" for row in rows)
        )
        self.assertEqual(
            {(row.latitude_text, row.longitude_text) for row in rows},
            {("60.23", "20.08"), ("57.29", "17.97")},
        )
        self.assertEqual({row.political_entity for row in rows}, {"Finland", "Sweden"})
        self.assertTrue(all(row.time_start_bp is None for row in rows))
        self.assertTrue(all(row.time_end_bp is None for row in rows))
        self.assertTrue(all(row.chronology_text == "" for row in rows))

    def test_resolve_project_locality_leads_keep_direct_horse_coordinate_sites(
        self,
    ) -> None:
        rows = resolve_project_locality_leads("PRJEB31613")

        uppsala = next(row for row in rows if row.locality_text == "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")

    def test_build_species_project_locality_leads_keeps_requested_accession_order(
        self,
    ) -> None:
        rows = build_species_project_locality_leads(
            ("PRJEB59481", "PRJEB60484", "unknown")
        )

        self.assertEqual(
            [row.project_accession for row in rows],
            ["PRJEB59481", "PRJEB59481", "PRJEB60484"],
        )


if __name__ == "__main__":
    unittest.main()
