from __future__ import annotations

import unittest

from bijux_pollenomics.adna.project_localities import (
    build_species_project_locality_leads,
    resolve_project_locality_leads,
)


class AdnaProjectLocalityUnitTests(unittest.TestCase):
    def test_resolve_project_locality_leads_returns_curated_botai_anchor(self) -> None:
        rows = resolve_project_locality_leads("PRJEB22390")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].locality_text, "Botai culture steppe context")
        self.assertEqual(rows[0].political_entity, "Kazakhstan")
        self.assertEqual((rows[0].time_start_bp, rows[0].time_end_bp), (5400, 5600))

    def test_build_species_project_locality_leads_keeps_requested_accession_order(self) -> None:
        rows = build_species_project_locality_leads(
            ("PRJEB59481", "PRJEB60484", "unknown")
        )

        self.assertEqual(
            [row.project_accession for row in rows],
            ["PRJEB59481", "PRJEB60484"],
        )


if __name__ == "__main__":
    unittest.main()
