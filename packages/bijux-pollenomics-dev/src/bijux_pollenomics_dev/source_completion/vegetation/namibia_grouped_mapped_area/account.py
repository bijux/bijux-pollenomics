"""Project compact mapped-area development accounts from admitted saved evidence."""

from __future__ import annotations

from typing import Any

from .authority import SOURCE_SHA256


def products(values: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive bounded reader products from the admitted captured source account."""
    model = values["native-report.json"]
    scores = values["scores.json"]
    oracle = values["independent-numerical-review.json"]
    protocol = values["protocol.json"]
    qualification = values["original-account-saved-result-qualification.json"]
    terminal = values["native-terminal.json"]
    report = {
        "schema_version": "namibia-grouped-mapped-area-account.v1",
        "producer_scope": "Replay retained, source-qualified mapped-area development result; no fresh prediction, scoring, Decimal oracle, physical model or acquisition.",
        "original_native_authority": {
            "candidate": terminal["candidate"],
            "plan_sha256": SOURCE_SHA256["study-plan.json"],
            "terminal_sha256": SOURCE_SHA256["native-terminal.json"],
        },
        "original_native_pending_status": terminal["status"],
        "original_report_pending_status": model["status"],
        "population": model["population"],
        "subsequent_qualification": {
            "actual_source_controls": 17,
            "independent_numeric_fields": oracle["total_numeric_fields_compared"],
            "distinct_prediction_cells": oracle["distinct_prediction_fraction_cells"],
            "maximum_absolute_gap_exact_string": oracle["maximum_abs_numerical_gap"],
            "independent_position_pairs": oracle["source_position_pair_count"],
            "maximum_spherical_distance_gap_m": oracle[
                "maximum_independent_distance_gap_m"
            ],
            "same_interpreter_different_implementation": True,
            "numerical_review_sha256": SOURCE_SHA256[
                "independent-numerical-review.json"
            ],
            "source_account_review_sha256": SOURCE_SHA256[
                "independent-account-review.json"
            ],
            "qualified_external_reviews_received": 0,
            "unfamiliar_human_exercises_completed": 0,
        },
        "predictor_interpretation": "Unique conditional CLR least-squares point correction for five listed map quantities, with separate held-out squared Hellinger development scores; no PPE/ERV identification or environmental validity theorem.",
        "untouched_field_vegetation_PPE_ERV_or_historical_reproduction_claim": False,
        "raw_count_or_area_rows_promoted": False,
    }
    comparisons = {
        "schema_version": "namibia-grouped-mapped-area-comparisons.v1",
        "score": protocol["primary_score"],
        "methods": protocol["methods"],
        "all_original_radii_m": protocol["radii_m"],
        "all45_method_radius_means": scores["summaries"],
        "all300_paired_contrasts": scores["all300_paired_contrasts"],
        "all110_poorer_contrasts": model["negative_contrasts_retained"],
        "paired_better_poorer_counts": qualification["per_site_radius_contrast_counts"],
        "all_radius_mean_better_poorer_counts": qualification[
            "all_radius_mean_outcome_counts"
        ],
        "radius_selected": False,
        "same_paired_source_support_all_methods": True,
        "weighting": "Equal ten-site means and equal nine nominal-group means remain distinct; all sites equally weighted within each group.",
        "uncertainty": model["uncertainty"],
        "stronger_baseline_outcome": "Training mapped composition has smaller mean loss at 8/15 equal-site radii and 9/15 equal-group radii; empirical correction is poorer in 90/150 mapped-baseline site/radius contrasts.",
        "field_accuracy_or_independent_cohorts_claim": False,
    }
    assumptions = {
        "schema_version": "namibia-grouped-mapped-area-assumptions.v1",
        "protocol_sha256": SOURCE_SHA256["protocol.json"],
        "estimand": protocol["estimand"],
        "denominators": protocol["denominators"],
        "native_taxon_axes": protocol["taxa"],
        "taxon_transfer_boundary": protocol["source_axis_boundary"],
        "source_observation_rule": "All 50 native integer count cells and all 750 calculated area cells are positive on the five source axes; no pseudocount, missing zero imputation or six-axis fossil input.",
        "nominal_geometry": {
            "maximum_circle_radius_m": 1500,
            "sphere_radius_m": 6371000,
            "intersection_threshold_m": 3000,
            "groups": protocol["expected_groups"],
            "scope": protocol["grouping_scope"],
            "source_precision": protocol["sourceprecision_boundary"],
        },
        "training_rule": protocol["training_rule"],
        "prediction_rule": protocol["prediction_rule"],
        "estimator_objective_proof": protocol["estimator_objective_proof"],
        "prediction_before_scoring_sequence": protocol["sequence"],
        "source_already_exposed": True,
        "unresolved_source_assumptions": protocol["unresolved_source_assumptions"],
        "conditional_limits": protocol["conditional_limits"],
        "source_year_or_BP_conversion": False,
        "PPE_or_ERV_estimation": False,
    }
    source_account = {
        "schema_version": "namibia-grouped-mapped-area-source-account.v1",
        "attribution": protocol["publication_attribution"],
        "sources": ["10.1594/PANGAEA.931033", "10.1594/PANGAEA.931035"],
        "original_source_hashes": protocol["source_hashes"],
        "source_quantities": {
            "native_count_cells": 50,
            "native_calculated_area_cells": 750,
            "site_ring_rows": 150,
            "unique_source_sites": 10,
            "source_five_label_grains_once": 6894,
            "independent_cohorts_authenticated": False,
        },
        "native_license_statements": "Both original deposited tables state CC BY 4.0 with source attribution; no rights over unavailable thesis/supplement/calibration sources inferred.",
        "original_source_retrieval_manifest_sha256": SOURCE_SHA256[
            "original-source-manifest.json"
        ],
        "original_documentary_review_sha256": SOURCE_SHA256[
            "documentary-source-review.json"
        ],
        "original_seven_member_account_inventory_sha256": SOURCE_SHA256[
            "source-account-inventory.json"
        ],
        "later_read_only_source_qualification_sha256": SOURCE_SHA256[
            "original-account-saved-result-qualification.json"
        ],
        "later_agent_account_review_sha256": SOURCE_SHA256[
            "independent-account-review.json"
        ],
        "original_pending_flags_preserved": True,
        "actual_unfamiliar_or_qualified_external_review_admitted": False,
        "native_raw_count_area_or_position_rows_promoted": False,
        "exact_retained_source_sha256": SOURCE_SHA256,
    }
    return {
        "report.json": report,
        "comparisons.json": comparisons,
        "assumptions.json": assumptions,
        "source-account.json": source_account,
    }
