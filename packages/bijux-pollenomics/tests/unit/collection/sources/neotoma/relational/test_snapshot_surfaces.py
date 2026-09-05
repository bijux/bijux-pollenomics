from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import country_decisions, download_row


class NeotomaRelationalTests(unittest.TestCase):
    def test_preserves_joined_entities_alternate_ages_units_and_zero(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=country_decisions([download_row()]),
        )

        self.assertEqual(
            payload["reconciliation"]["normalized_row_counts"],
            {
                "sites": 1,
                "collection_units": 1,
                "datasets": 1,
                "chronologies": 2,
                "chronology_controls": 1,
                "samples": 1,
                "age_claims": 2,
                "variables": 2,
                "observations": 2,
            },
        )
        self.assertEqual(payload["schema_version"], "neotoma-relational-snapshot.v2")
        site = payload["sites"][0]
        self.assertEqual(site["raw_country"], "Sweden")
        self.assertEqual(site["derived_country"], "Sweden")
        self.assertEqual(site["country_code"], "SE")
        self.assertEqual(site["country_decision_status"], "assigned")
        self.assertEqual(site["country_decision_method"], "strict_boundary_containment")
        self.assertEqual(site["country_candidates"], ["Sweden"])
        self.assertIsNone(site["country_ambiguity_reason"])
        self.assertIsNone(site["country_refusal_reason"])
        self.assertEqual(site["boundary_artifact_digest"], "sha256:boundary-fixture")
        self.assertEqual(site["boundary_version"], "boundary-fixture-v1")
        self.assertEqual(site["source_vs_derived_comparison"], "agrees")
        self.assertTrue(site["country_propagation_eligible"])
        for table_name in (
            "collection_units",
            "datasets",
            "chronologies",
            "chronology_controls",
            "samples",
            "age_claims",
            "observations",
        ):
            self.assertTrue(
                all(row["country_code"] == "SE" for row in payload[table_name]),
                table_name,
            )
        claims_by_type = {
            claim["source_age_type"]: claim for claim in payload["age_claims"]
        }
        alternate = claims_by_type["Radiocarbon years BP"]
        selected = claims_by_type["Calibrated radiocarbon years BP"]
        self.assertEqual(alternate["comparability_status"], "context_only")
        self.assertIsNone(alternate["younger_bp"])
        self.assertIsNone(alternate["refusal_reason"])
        self.assertEqual(selected["comparability_status"], "comparable")
        self.assertEqual((selected["younger_bp"], selected["older_bp"]), (1150, 1250))
        self.assertTrue(selected["is_default_chronology"])
        observations = payload["observations"]
        self.assertEqual(
            {observation["source_value"] for observation in observations}, {0, 12.5}
        )
        self.assertEqual(
            {observation["aggregation_key"] for observation in observations},
            {"neotoma:exact-unit:NISP", "neotoma:exact-unit:grains/cm3"},
        )
        self.assertTrue(
            all(
                observation["denominator_status"] == "not_provided_by_source"
                for observation in observations
            )
        )
        self.assertEqual(payload["reconciliation"]["orphan_count"], 0)
        self.assertEqual(
            payload["reconciliation"]["country_counts"]["SE"]["variables"], 2
        )
        self.assertEqual(
            payload["reconciliation"]["country_counts"]["DK"]["age_claim_rows"],
            0,
        )
