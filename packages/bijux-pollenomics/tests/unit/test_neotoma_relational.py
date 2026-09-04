from __future__ import annotations

import copy
import unittest

from bijux_pollenomics.data_downloader.sources.neotoma.normalization import (
    build_neotoma_site_country_decisions,
    build_neotoma_site_rows_from_downloads,
)
from bijux_pollenomics.data_downloader.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.data_downloader.spatial import CountryAttributionDecision


def _download_row(dataset_id: int = 201) -> dict[str, object]:
    chronologies = [
        {
            "chronology": {
                "chronologyid": 7001,
                "chronology": {
                    "chronologyname": "Selected model",
                    "modelagetype": "Calibrated radiocarbon years BP",
                    "isdefault": True,
                },
                "chroncontrols": [
                    {
                        "chroncontrolid": 8001,
                        "depth": 10,
                        "chroncontrolage": 1200,
                        "agelimityounger": 1150,
                        "agelimitolder": 1250,
                    }
                ],
            }
        },
        {
            "chronology": {
                "chronologyid": 7002,
                "chronology": {
                    "chronologyname": "Alternate model",
                    "modelagetype": "Radiocarbon years BP",
                    "isdefault": True,
                },
                "chroncontrols": [],
            }
        },
    ]
    return {
        "site": {
            "siteid": 20,
            "sitename": "Ageröds Mosse",
            "geography": '{"type":"Point","coordinates":[1.0,1.0]}',
            "geopolitical": [{"country": "Sweden"}],
            "dataset": {"datasetid": dataset_id, "datasettype": "pollen"},
            "collectionunit": {
                "collectionunitid": 301,
                "collectionunit": "Core A",
                "defaultchronology": 7001,
                "chronologies": chronologies,
                "dataset": {
                    "datasetid": dataset_id,
                    "datasettype": "pollen",
                    "database": "European Pollen Database",
                    "samples": [
                        {
                            "sampleid": 9001 + dataset_id,
                            "analysisunitid": 9101 + dataset_id,
                            "analysisunitname": "10 cm",
                            "depth": 10,
                            "thickness": 1,
                            "sampleanalyst": [{"contactid": 42}],
                            "ages": [
                                {
                                    "age": 1200,
                                    "ageyounger": 1150,
                                    "ageolder": 1250,
                                    "agetype": ("Calibrated radiocarbon years BP"),
                                    "chronologyid": 7001,
                                    "chronologyname": "Selected model",
                                },
                                {
                                    "age": 1100,
                                    "ageyounger": None,
                                    "ageolder": None,
                                    "agetype": "Radiocarbon years BP",
                                    "chronologyid": 7002,
                                    "chronologyname": "Alternate model",
                                },
                            ],
                            "datum": [
                                {
                                    "taxonid": 1947,
                                    "variablename": "Poaceae (Cerealia-type)",
                                    "taxongroup": "Vascular plants",
                                    "ecologicalgroup": "UPHE",
                                    "element": "pollen",
                                    "elementtype": "pollen",
                                    "units": "NISP",
                                    "value": 0,
                                    "context": None,
                                    "symmetry": None,
                                },
                                {
                                    "taxonid": 8000,
                                    "variablename": "Pollen concentration",
                                    "taxongroup": "Laboratory",
                                    "ecologicalgroup": "LABO",
                                    "element": "measurement",
                                    "elementtype": "concentration",
                                    "units": "grains/cm3",
                                    "value": 12.5,
                                    "context": "calculated",
                                    "symmetry": None,
                                },
                            ],
                        }
                    ],
                },
            },
        }
    }


def _country_boundaries() -> dict[str, dict[str, object]]:
    return {
        "Sweden": {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [0.0, 0.0],
                                [2.0, 0.0],
                                [2.0, 2.0],
                                [0.0, 2.0],
                                [0.0, 0.0],
                            ]
                        ],
                    }
                }
            ]
        },
        "Norway": {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [3.0, 0.0],
                                [5.0, 0.0],
                                [5.0, 2.0],
                                [3.0, 2.0],
                                [3.0, 0.0],
                            ]
                        ],
                    }
                }
            ]
        },
    }


def _country_decisions(
    rows: list[dict[str, object]],
    boundaries: dict[str, dict[str, object]] | None = None,
) -> dict[str, CountryAttributionDecision]:
    return build_neotoma_site_country_decisions(
        rows,
        boundaries or _country_boundaries(),
        boundary_artifact_digest="sha256:boundary-fixture",
        boundary_version="boundary-fixture-v1",
    )


def _set_row_identity(row: dict[str, object], identifier: int) -> None:
    site = row["site"]
    site["siteid"] = identifier
    unit = site["collectionunit"]
    unit["collectionunitid"] = identifier + 1000
    dataset = unit["dataset"]
    dataset["datasetid"] = identifier + 2000
    site["dataset"]["datasetid"] = identifier + 2000
    sample = dataset["samples"][0]
    sample["sampleid"] = identifier + 3000
    sample["analysisunitid"] = identifier + 4000


class NeotomaRelationalTests(unittest.TestCase):
    def test_site_rows_retain_collection_unit_owned_chronologies(self) -> None:
        rows = build_neotoma_site_rows_from_downloads([_download_row()])

        dataset = rows[0]["collectionunits"][0]["datasets"][0]
        self.assertEqual(dataset["defaultchronology"], 7001)
        self.assertEqual(len(dataset["chronologies"]), 2)
        self.assertEqual(rows[0]["chronology_count"], 2)

    def test_preserves_joined_entities_alternate_ages_units_and_zero(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [_download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=_country_decisions([_download_row()]),
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

    def test_explicit_default_governs_and_source_assertion_conflict_is_visible(
        self,
    ) -> None:
        payload = build_neotoma_relational_snapshot(
            [_download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        selected = {
            chronology["source_chronology_id"]: chronology[
                "selected_by_collection_unit_reference"
            ]
            for chronology in payload["chronologies"]
        }
        source_assertions = {
            chronology["source_chronology_id"]: chronology[
                "source_is_default_assertion"
            ]
            for chronology in payload["chronologies"]
        }
        self.assertEqual(selected, {7001: True, 7002: False})
        self.assertEqual(source_assertions, {7001: True, 7002: True})
        default_conflicts = [
            conflict
            for conflict in payload["conflicts"]
            if conflict["conflict_kind"] == "default_chronology_assertions_conflict"
        ]
        self.assertEqual(len(default_conflicts), 1)
        self.assertEqual(
            default_conflicts[0]["detail"]["governing_selection"],
            "collection_unit.defaultchronology",
        )
        self.assertEqual(
            default_conflicts[0]["detail"]["explicit_default_chronology_id"],
            "neotoma:chronology:301:7001",
        )
        self.assertEqual(
            default_conflicts[0]["detail"]["source_flagged_default_chronology_ids"],
            ["neotoma:chronology:301:7001", "neotoma:chronology:301:7002"],
        )
        chronology_ids = {
            chronology["chronology_id"] for chronology in payload["chronologies"]
        }
        self.assertIn(
            default_conflicts[0]["detail"]["explicit_default_chronology_id"],
            chronology_ids,
        )
        self.assertTrue(
            set(
                default_conflicts[0]["detail"]["source_flagged_default_chronology_ids"]
            ).issubset(chronology_ids)
        )

    def test_refuses_negative_bp_without_turning_missing_age_into_zero(self) -> None:
        row = _download_row()
        sample = row["site"]["collectionunit"]["dataset"]["samples"][0]
        sample["ages"] = [
            {
                "age": -2,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
            {
                "age": None,
                "ageyounger": None,
                "ageolder": None,
                "agetype": None,
                "chronologyid": None,
            },
            {
                "age": 0,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
        ]

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )
        by_status = payload["reconciliation"]["age_comparability_counts"]
        self.assertEqual(by_status, {"comparable": 1, "refused": 1, "unresolved": 1})
        zero = next(
            claim for claim in payload["age_claims"] if claim["source_age_value"] == 0
        )
        missing = next(
            claim
            for claim in payload["age_claims"]
            if claim["source_age_value"] is None
        )
        self.assertEqual((zero["younger_bp"], zero["older_bp"]), (0, 0))
        self.assertIsNone(missing["younger_bp"])
        self.assertIsNone(missing["older_bp"])

    def test_identical_source_rows_preserve_multiplicity_with_stable_ids(self) -> None:
        row = _download_row()
        sample = row["site"]["collectionunit"]["dataset"]["samples"][0]
        sample["ages"].append(copy.deepcopy(sample["ages"][0]))
        sample["datum"].append(copy.deepcopy(sample["datum"][0]))

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(payload["age_claims"]), 3)
        self.assertEqual(len(payload["observations"]), 3)
        self.assertEqual(
            len({claim["chronology_claim_id"] for claim in payload["age_claims"]}),
            3,
        )
        self.assertEqual(
            len(
                {
                    observation["observation_id"]
                    for observation in payload["observations"]
                }
            ),
            3,
        )

    def test_missing_chronology_identifiers_are_preserved_and_reported(self) -> None:
        row = _download_row()
        chronology = row["site"]["collectionunit"]["chronologies"][0]["chronology"]
        chronology["chronologyid"] = None
        chronology["chroncontrols"][0]["chroncontrolid"] = None
        row["site"]["collectionunit"]["defaultchronology"] = 7002

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(payload["chronologies"]), 2)
        self.assertEqual(len(payload["chronology_controls"]), 1)
        self.assertEqual(payload["reconciliation"]["orphan_count"], 3)
        self.assertEqual(
            {orphan["entity_type"] for orphan in payload["orphans"]},
            {"chronology", "chronology_control", "age_claim"},
        )

    def test_every_emitted_relational_reference_targets_its_table(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [_download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=_country_decisions([_download_row()]),
        )
        site_ids = {row["site_id"] for row in payload["sites"]}
        unit_ids = {row["collection_unit_id"] for row in payload["collection_units"]}
        dataset_ids = {row["dataset_id"] for row in payload["datasets"]}
        chronology_ids = {row["chronology_id"] for row in payload["chronologies"]}
        sample_ids = {row["sample_id"] for row in payload["samples"]}
        variable_ids = {row["variable_id"] for row in payload["variables"]}

        self.assertTrue(
            all(row["site_id"] in site_ids for row in payload["collection_units"])
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in payload["datasets"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in payload["chronologies"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["chronology_id"] in chronology_ids
                for row in payload["chronology_controls"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                for row in payload["samples"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                and row["subject_type"] == "sample"
                and row["subject_id"] in sample_ids
                and (
                    row["chronology_id"] is None
                    or row["chronology_id"] in chronology_ids
                )
                for row in payload["age_claims"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                and row["sample_id"] in sample_ids
                and row["variable_id"] in variable_ids
                for row in payload["observations"]
            )
        )

    def test_source_country_conflict_retains_membership_but_blocks_propagation(
        self,
    ) -> None:
        row = _download_row()
        row["site"]["geopolitical"] = [{"country": "Norway"}]
        decisions = _country_decisions([row])

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
        row = _download_row()
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
        decisions = _country_decisions([row], boundaries)

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
        missing = _download_row()
        invalid = copy.deepcopy(missing)
        _set_row_identity(invalid, 21)
        missing["site"].pop("geography")
        invalid["site"]["geography"] = "not-json"
        decisions = _country_decisions([missing, invalid])

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
        sweden = _download_row()
        norway = copy.deepcopy(sweden)
        _set_row_identity(norway, 21)
        norway["site"]["geography"] = '{"type":"Point","coordinates":[4.0,1.0]}'
        norway["site"]["geopolitical"] = [{"country": "Norway"}]
        decisions = _country_decisions([sweden, norway])

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
            [_download_row()],
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

    def test_output_is_invariant_to_download_row_order(self) -> None:
        first = _download_row(201)
        second = _download_row(202)
        second["site"]["collectionunit"]["dataset"]["samples"][0]["sampleid"] = 9999
        second["site"]["collectionunit"]["dataset"]["samples"][0]["analysisunitid"] = (
            9302
        )

        forward = build_neotoma_relational_snapshot(
            [first, second],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )
        reverse = build_neotoma_relational_snapshot(
            [copy.deepcopy(second), copy.deepcopy(first)],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
