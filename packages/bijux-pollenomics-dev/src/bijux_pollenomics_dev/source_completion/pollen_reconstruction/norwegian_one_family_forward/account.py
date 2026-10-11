"""Expose conditional forward results without republishing native sample rows."""

from __future__ import annotations

from typing import Any

from .authority import SOURCE_SHA256


def products(values: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive bounded reader products from the admitted captured source account."""
    model = values["model-report.json"]
    protocol = values["protocol.json"]
    scalar = values["independent-scalar-review.json"]
    physical = values["independent-physical-review.json"]
    windows = []
    outcomes = {r["window_index"]: r for r in values["outcome-ledger.json"]}
    for row in values["prediction-ledger.json"]:
        index = row["window_index"]
        windows.append(
            {
                "window_index": index,
                "window_cal_bp": row["window_cal_bp"],
                "predictions": row["predictions"],
                "target_outcome_present": outcomes[index]["target_counts"] is not None,
                "conditional_training_cover": row["physical_training_cover"],
                "conditional_training_counting_covariance": row[
                    "conditional_training_counting_covariance"
                ],
                "conditional_training_shared_PPE_covariance": row[
                    "conditional_training_shared_PPE_covariance"
                ],
                "conditional_training_total_covariance": row[
                    "conditional_training_total_covariance"
                ],
                "conditional_training_standard_error": row[
                    "conditional_training_standard_error"
                ],
                "forward_predictive_uncertainty_emitted": False,
            }
        )
    losses = {
        baseline: [
            r["window_index"]
            for r in model["paired_contrasts"]
            if r["baseline"] == baseline
            and any(v > 0 for v in r["physical_minus_baseline"].values())
        ]
        for baseline in protocol["methods"][1:]
    }
    report = {
        "schema_version": "norwegian-one-family-forward-account.v1",
        "producer_scope": "Replay exact retained source-bound numerical account; no fresh model, physical integration or source acquisition.",
        "original_native_authority": {
            "candidate": values["native-terminal.json"]["candidate"],
            "plan_sha256": SOURCE_SHA256["study-plan.json"],
            "terminal_sha256": SOURCE_SHA256["native-terminal.json"],
        },
        "population": {
            "training_physical_cores": 2,
            "training_publication_dependency_families": 1,
            "predicted_windows": 20,
            "method_vectors": 60,
            "paired_target_windows": 18,
            "scored_method_rows": 54,
            "missing_target_method_rows": 6,
            "unique_paired_target_panel_N": 17935,
            "core_sample_populations": model["core_sample_populations"],
        },
        "qualification": {
            "original_model_report_pending_flag": model[
                "new252physical_and_independent_scalar_qualification_pending"
            ],
            "later_native_exit_code": 0,
            "source_controls": 15,
            "independent_Decimal50_cells": scalar["actual_scalar_cell_comparisons"],
            "maximum_scalar_absolute_difference": scalar["maximum_absolute_difference"],
            "new_physical_tuples": physical["actual_new_tuples"],
            "new_physical_window_taxon_uses": physical["actual_window_taxon_uses"],
            "scalar_review_sha256": SOURCE_SHA256["independent-scalar-review.json"],
            "physical_review_sha256": SOURCE_SHA256["independent-physical-review.json"],
            "numerical_error_estimates_rigorous": False,
        },
        "windows": windows,
        "shared_PPE_identified_by_pollen_predictions": False,
        "untouched_target_or_vegetation_accuracy_claim": False,
        "rights_or_external_review_admitted": False,
    }
    comparisons = {
        "schema_version": "norwegian-one-family-forward-comparisons.v1",
        "same_support_context": [1486, 1436],
        "support_distance_radius_m": 100000,
        "methods": protocol["methods"],
        "summaries": model["summaries"],
        "paired_contrasts": model["paired_contrasts"],
        "physical_poorer_than_baseline_window_indices": losses,
        "score_rows": values["score-ledger.json"],
        "negative_outcomes_removed": False,
        "scope": "Development-exposed two-taxon direct-pollen scores; source families, chronological correlations and physical assumptions remain conditional. Smaller scores do not establish vegetation truth.",
    }
    assumptions = {
        "schema_version": "norwegian-one-family-forward-assumptions.v1",
        "original_protocol_sha256": SOURCE_SHA256["protocol.json"],
        "age_windows_cal_bp": protocol["age_window_edges_cal_bp"],
        "epoch": protocol["epoch"],
        "point_age_policy": protocol["point_age_policy"],
        "spatial_assumption": protocol["spatial_assumption"],
        "physical": protocol["physical"],
        "panel": protocol["panel"],
        "grouping": protocol["grouping"],
        "measurement_policy": protocol["measurement_policy"],
        "covariance_scope": protocol["ppe_scope"],
        "scoring_protocol": protocol["scoring"],
        "shared_PPE_cancellation": "U_i=sum_s n_si/(K_si p_i); c_i=U_i/sum_j U_j. close(K_target,i p_i c_i)=close(K_target,i sum_s n_si/K_si). Positive shared PPE therefore cancels from this pollen prediction, which cannot identify PPE or validate vegetation cover.",
        "remaining_acceptance": protocol["remaining_acceptance"],
    }
    source_account = {
        "schema_version": "norwegian-one-family-forward-source-account.v1",
        "cores": protocol["cores"],
        "native_target_point": protocol["target_native_point"],
        "original_input_hashes": protocol["source_sha256"],
        "training_primary_publication": {
            "publication_id": 1096,
            "citation": values["mukk-publications.json"]["data"][0]["publication"][
                "citation"
            ],
        },
        "training_secondary_reference_ids": [1149],
        "target_primary_reference_id": 9495,
        "source_age_bounds": "All72 target bounds are missing. Mukk and Rattu native bounds remain private; most accepted bounds cross their point-assigned window. No interval-allocation probability or chronology accuracy claim.",
        "source_access_or_rights_claim": False,
        "private_sample_rows_promoted": False,
        "exact_retained_source_sha256": SOURCE_SHA256,
    }
    return {
        "report.json": report,
        "comparisons.json": comparisons,
        "assumptions.json": assumptions,
        "source-account.json": source_account,
    }
