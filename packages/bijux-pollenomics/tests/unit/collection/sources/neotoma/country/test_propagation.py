from __future__ import annotations

import copy
import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import (
    country_decisions,
    download_row,
    set_row_identity,
)


class NeotomaCountryPropagationTests(unittest.TestCase):
    def test_source_country_conflict_retains_membership_but_blocks_propagation(
        self,
    ) -> None:
        row = download_row()
        row["site"]["geopolitical"] = [{"country": "Norway"}]
        decisions = country_decisions([row])

        payload = build_neotoma_relational_snapshot(
            [row],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=decisions,
        )

        site = payload["sites"][0]
        self.assertEqual(site["raw_country"], "Norway")
        self.assertEqual(site["derived_country"], "Sweden")
        self.assertEqual(site["country_code"], "UNASSIGNED")
        self.assertEqual(site["country_decision_status"], "review")
        self.assertEqual(site["source_vs_derived_comparison"], "conflicts")
        self.assertEqual(site["country_ambiguity_reason"], "raw_country_conflict")
        self.assertFalse(site["country_propagation_eligible"])
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
                all(
                    child["country_code"] == "UNASSIGNED"
                    for child in payload[table_name]
                ),
                table_name,
            )
        counts = payload["reconciliation"]["country_attribution_counts"]
        self.assertEqual(counts["derived_country_codes"], {"SE": 1})
        self.assertEqual(counts["final_country_codes"], {"UNASSIGNED": 1})
        self.assertEqual(counts["source_vs_derived_comparisons"], {"conflicts": 1})
        self.assertEqual(counts["propagation_eligibility"], {"blocked": 1})

    def test_near_border_site_is_reviewed_without_prior_proximity_snap(self) -> None:
        row = download_row()
        row["site"]["geography"] = '{"type":"Point","coordinates":[13.05,61.5]}'
        row["site"]["geopolitical"] = [{"country": "Norway"}]
        boundaries = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 60.0],
                                    [13.0, 60.0],
                                    [13.0, 63.0],
                                    [10.0, 63.0],
                                    [10.0, 60.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }
        decisions = country_decisions([row], boundaries)

        payload = build_neotoma_relational_snapshot(
            [row],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=decisions,
        )

        site = payload["sites"][0]
        self.assertIsNone(site["derived_country"])
        self.assertEqual(site["country_code"], "UNASSIGNED")
        self.assertEqual(site["country_decision_status"], "review")
        self.assertEqual(site["country_decision_method"], "boundary_proximity")
        self.assertEqual(site["country_candidates"], ["Norway"])
        self.assertEqual(
            site["country_ambiguity_reason"], "near_boundary_without_containment"
        )
        self.assertEqual(len(payload["observations"]), 2)

    def test_missing_and_invalid_geometry_are_refused_without_dropping_rows(
        self,
    ) -> None:
        missing = download_row()
        invalid = copy.deepcopy(missing)
        set_row_identity(invalid, 21)
        missing["site"].pop("geography")
        invalid["site"]["geography"] = "not-json"
        decisions = country_decisions([missing, invalid])

        payload = build_neotoma_relational_snapshot(
            [missing, invalid],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=decisions,
        )

        self.assertEqual(len(payload["sites"]), 2)
        self.assertEqual(len(payload["datasets"]), 2)
        self.assertEqual(len(payload["samples"]), 2)
        self.assertEqual(len(payload["observations"]), 4)
        self.assertEqual(
            {site["country_refusal_reason"] for site in payload["sites"]},
            {"missing_site_geometry", "invalid_site_geometry"},
        )
        self.assertTrue(
            all(site["country_code"] == "UNASSIGNED" for site in payload["sites"])
        )
        self.assertEqual(
            payload["reconciliation"]["country_counts"]["UNASSIGNED"]["refused_sites"],
            2,
        )

    def test_country_accounting_is_deterministic_across_source_order(self) -> None:
        sweden = download_row()
        norway = copy.deepcopy(sweden)
        set_row_identity(norway, 21)
        norway["site"]["geography"] = '{"type":"Point","coordinates":[4.0,1.0]}'
        norway["site"]["geopolitical"] = [{"country": "Norway"}]
        decisions = country_decisions([sweden, norway])

        forward = build_neotoma_relational_snapshot(
            [sweden, norway],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=decisions,
        )
        reverse = build_neotoma_relational_snapshot(
            [copy.deepcopy(norway), copy.deepcopy(sweden)],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=dict(reversed(tuple(decisions.items()))),
        )

        self.assertEqual(forward, reverse)
        counts = forward["reconciliation"]["country_attribution_counts"]
        self.assertEqual(counts["raw_country_codes"], {"NO": 1, "SE": 1})
        self.assertEqual(counts["derived_country_codes"], {"NO": 1, "SE": 1})
        self.assertEqual(counts["final_country_codes"], {"NO": 1, "SE": 1})
        self.assertEqual(counts["decision_statuses"], {"assigned": 2})
        self.assertEqual(counts["propagation_eligibility"], {"eligible": 2})

    def test_legacy_country_string_is_retained_only_as_unproven_review(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id={20: "Sweden"},
        )

        site = payload["sites"][0]
        self.assertEqual(site["derived_country"], "Sweden")
        self.assertEqual(site["country_code"], "UNASSIGNED")
        self.assertEqual(site["country_decision_status"], "review")
        self.assertEqual(
            site["country_decision_method"], "legacy_unproven_country_string"
        )
        self.assertIsNone(site["boundary_artifact_digest"])
        self.assertFalse(site["country_propagation_eligible"])
