"""Inspect retained model/oracle authority and publish conditional aggregates."""

from __future__ import annotations

import math
from typing import Any, cast

from .authority import CAPTURE_PINS

PRODUCTS = (
    "four-annulus-factors.json",
    "observed-source-closure.json",
    "shared-ppe-counting-covariance.json",
    "signed-forward-roundtrip-and-native-refusals.json",
    "source-case-census.json",
    "source-masks-and-assumptions.json",
    "three-conditional-love-cases.json",
)


def require(value: bool, message: str) -> None:
    """Refuse captured source fields that violate the declared admission invariant."""
    if not value:
        raise ValueError(message)


def integer(value: object) -> int:
    """Require a literal nonnegative integer source count."""
    if type(value) is not int or value < 0:
        raise ValueError("Source count must be a nonnegative integer")
    return value


def close(actual: object, expected: object) -> None:
    """Compare saved finite scalar cells at the declared numerical tolerance."""
    require(
        type(actual) in (int, float) and type(expected) in (int, float),
        "Numerical type differs",
    )
    a, b = float(cast(float, actual)), float(cast(float, expected))
    require(
        math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 2e-9 + 2e-10 * abs(b),
        "Saved numerical comparison differs",
    )


def vector(actual: object, expected: object) -> None:
    """Compare each saved cell on the literal two-taxon vector axis."""
    require(
        isinstance(actual, list)
        and isinstance(expected, list)
        and len(actual) == len(expected) == 2,
        "Literal two-taxon vector differs",
    )
    for a, b in zip(cast(list[Any], actual), cast(list[Any], expected), strict=True):
        close(a, b)


def matrix(actual: object, expected: object) -> None:
    """Compare saved covariance cells on the literal two-taxon matrix axis."""
    require(
        isinstance(actual, list)
        and isinstance(expected, list)
        and len(actual) == len(expected) == 2,
        "Literal two-taxon matrix differs",
    )
    for a, b in zip(cast(list[Any], actual), cast(list[Any], expected), strict=True):
        vector(a, b)


def native_scope(
    model: dict[str, Any],
    model_stages: list[dict[str, Any]],
    oracle: dict[str, Any],
    oracle_stages: list[dict[str, Any]],
) -> None:
    """Preserve original native execution outcomes and their exact custody boundaries."""
    for terminal in (model, oracle):
        require(
            type(terminal.get("native_exit_code")) is int,
            "Native exit must be an integer",
        )
        require(
            terminal.get("custody_after_checked") is True
            and terminal.get("custody_after_unchanged") is True
            and terminal.get("custody_errors") == []
            and terminal.get("owned_survivors") == {}
            and terminal.get("resource_failure") is None,
            "Native custody/resource authority differs",
        )
    require(
        model["status"] == "FAIL" and model["native_exit_code"] == 1,
        "Original overall model-job failure must remain",
    )
    require(
        oracle["status"] == "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"
        and oracle["native_exit_code"] == 0,
        "Independent oracle native acceptance differs",
    )
    require(
        [r.get("stage") for r in model_stages]
        == [
            "source-panel-age-dependency-covariance-contract-guards",
            "actual-three-marginal-lambda-local-annulus-reconstruction",
            "independent-four-annulus-and-shared-delta-covariance-review",
        ],
        "Model stage axis differs",
    )
    require(
        [r.get("stage") for r in oracle_stages]
        == [
            "saved-model-capture-and-stable-complement-guards",
            "independent-four-saved-factors-and-shared-covariance-oracle",
        ],
        "Oracle stage axis differs",
    )
    for stages, exits in ((model_stages, [0, 0, 1]), (oracle_stages, [0, 0])):
        require(
            all(type(r.get("native_exit_code")) is int for r in stages)
            and [r["native_exit_code"] for r in stages] == exits,
            "Scoped model/oracle native stage exit differs",
        )
    for terminal, name in (
        (model, "model-native-stages.json"),
        (oracle, "oracle-native-stages.json"),
    ):
        require(
            terminal["native_files"]["stages.json"]["sha256"] == CAPTURE_PINS[name],
            "Native stages are not bound by original receipt",
        )
    for name in PRODUCTS:
        require(
            model["native_files"]["products/" + name]["sha256"] == CAPTURE_PINS[name],
            "Seven model capture identities differ",
        )
    for name in ("independent-review.json", "capture-reuse-review.json"):
        require(
            oracle["comparison_files"][name]["sha256"] == CAPTURE_PINS[name],
            "Oracle output identity differs",
        )


def source_totals(
    census: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    """Retain observed source support independently of conditional model completeness."""
    rows = census["sources"]
    require(
        [r["dataset_id"] for r in rows] == [54001, 23013, 53999],
        "Native core/source axis differs",
    )
    declared = [protocol["target"], *protocol["regional_training"]]
    public = []
    observed_samples, unknown, total_panel, total_nisp = 0, 0, 0, 0
    ids: set[int] = set()
    for row, decl in zip(rows, declared, strict=True):
        metadata = row["source_metadata"]
        count = len(metadata)
        require(
            count == integer(decl["source_sample_count"]),
            "Source sample denominator differs",
        )
        counts = row["counts"]
        require(
            isinstance(counts, list) and len(counts) == 2, "Literal count axis differs"
        )
        panel = sum(integer(v) for v in counts)
        nisp = integer(row["reported_pollen_NISP"])
        require(
            panel == row["panel_N"] == decl["panel_N"]
            and nisp == decl["reported_pollen_NISP"]
            and panel + integer(row["residual_reported_NISP"]) == nisp,
            "Panel/residual reported NISP does not conserve",
        )
        require(
            row["raw_source_redistribution"] is False,
            "Raw source publication scope differs",
        )
        require(
            len(row["literal_source_present_mask"]) == count
            and all(m == [True, True] for m in row["literal_source_present_mask"]),
            "Literal source presence differs",
        )
        missing = 0
        for sample in metadata:
            sid = integer(sample["sample_id"])
            require(sid not in ids, "Native source sample deduplication differs")
            ids.add(sid)
            point = sample["source_point_age"]
            require(
                type(point) in (int, float)
                and math.isfinite(point)
                and 100 <= point < 350,
                "Source point window differs",
            )
            actual_missing = (
                sample["source_older_age"] is None
                or sample["source_younger_age"] is None
            )
            require(
                sample["bounds_missing"] is actual_missing,
                "Unknown chronology bounds replaced",
            )
            missing += actual_missing
        require(
            missing == row["unknown_age_bounds"] == decl["bounds_missing"],
            "Unknown age-bound denominator differs",
        )
        require(
            all(
                row[k] == decl[k]
                for k in (
                    "dataset_id",
                    "collection_unit_id",
                    "site_id",
                    "chronology_id",
                )
            ),
            "Native core/chronology identity differs",
        )
        public.append(
            {
                "core": decl["core_handle"],
                "dataset_id": row["dataset_id"],
                "collection_unit_id": row["collection_unit_id"],
                "site_id": row["site_id"],
                "chronology_id": row["chronology_id"],
                "source_sample_count": count,
                "unknown_age_bounds": missing,
                "literal_panel_N": panel,
                "reported_pollen_NISP": nisp,
                "residual_reported_NISP": nisp - panel,
            }
        )
        observed_samples += count
        unknown += missing
        total_panel += panel
        total_nisp += nisp
    require(
        [observed_samples, unknown, total_panel, total_nisp] == [29, 20, 7396, 27940]
        and [
            census[k]
            for k in (
                "total_source_samples",
                "unknown_age_bounds",
                "panel_N",
                "reported_pollen_NISP",
            )
        ]
        == [29, 20, 7396, 27940],
        "Complete source denominator closure differs",
    )
    return public


def summarize(inputs: dict[str, Any]) -> dict[str, Any]:
    """Derive bounded reader summaries while preserving the captured scientific scope."""
    require(
        set(inputs) == set(CAPTURE_PINS),
        "Complete14 original-capture membership differs",
    )
    model, oracle = (
        inputs["model-native-terminal.json"],
        inputs["oracle-native-terminal.json"],
    )
    native_scope(
        model,
        inputs["model-native-stages.json"],
        oracle,
        inputs["oracle-native-stages.json"],
    )
    p = inputs["protocol.json"]
    cases = inputs["three-conditional-love-cases.json"]
    review = inputs["independent-review.json"]
    reuse = inputs["capture-reuse-review.json"]
    require(
        cases["protocol_sha256"] == CAPTURE_PINS["protocol.json"]
        and cases["literal_panel"] == p["literal_panel"] == ["Betula", "Poaceae"],
        "Panel/protocol identity differs",
    )
    require(
        p["window"]["younger_cal_bp"] == 100
        and p["window"]["older_cal_bp_exclusive"] == 350,
        "Point-age window contract differs",
    )
    require(
        p["uncertainty"]["required_covariance_assumptions"]
        == {
            "count_ppe_cross_covariance": "assumed_zero",
            "cross_scenario_joint_covariance_computed": False,
            "scenarios_use_same_source_samples_and_ppe": True,
        },
        "Conditional covariance assumptions differ",
    )
    require(
        p["transport"]["receiver_radius_m"] == 80
        and p["transport"]["split_radius_m"] == 1000
        and p["transport"]["regional_outer_radius_m"] == 100000
        and p["transport"]["local_terrestrial_fraction"]
        == p["transport"]["regional_terrestrial_fraction"]
        == 1,
        "Static split/landmask scenario differs",
    )
    require(
        p["rights"]["raw_source_redistribution"] is False
        and p["rights"]["formal_external_review_received"] is False,
        "Source/review rights scope differs",
    )
    require(
        all(v is False for v in cases["claims"].values()),
        "Scientific claim upgraded beyond conditional outputs",
    )
    sources = source_totals(inputs["source-case-census.json"], p)
    folds = inputs["source-case-census.json"]["dependency_excluded_folds"]
    require(
        len(folds) == 2
        and {r["grouping_scenario"] for r in folds}
        == {"primary_publication_relations", "all_returned_publication_relations"},
        "Whole-dependency exclusion grouping axis differs",
    )
    require(
        all(
            r["target_dataset_id"] == 54001
            and r["training_dataset_ids"] == [23013, 53999]
            and 54001 not in r["training_dependency_groups"]
            and r["source_support_eligible"] is True
            for r in folds
        ),
        "Target whole-dependency training exclusion differs",
    )
    require(
        review["passed"] is True
        and review["no_maintained_engine_import"] is True
        and review["physical_tuples_checked"] == 4
        and review["scalar_result_cells_checked"] == 48
        and all(
            review[k] is False
            for k in (
                "source_ecological_accuracy_claim",
                "historical_equivalence_claim",
                "untouched_claim",
            )
        ),
        "Actual independent review scope differs",
    )
    require(
        review["capture_source_sha256"]
        == {
            n: CAPTURE_PINS[n]
            for n in (
                "four-annulus-factors.json",
                "three-conditional-love-cases.json",
                "source-case-census.json",
            )
        },
        "Independent input identity differs",
    )
    admission = reuse["admission"]
    require(
        reuse["passed"] is True
        and reuse["independent_review_sha256"]
        == CAPTURE_PINS["independent-review.json"]
        and admission["original_native_terminal_sha256"]
        == CAPTURE_PINS["model-native-terminal.json"]
        and admission["original_plan_sha256"] == model["plan_sha256"]
        and admission["source_model_stage_native_exit"] == 0
        and admission["original_overall_native_exit"] == 1
        and admission["original_oracle_failed_and_preserved"] is True
        and admission["model_rerun"] is False
        and {n: r["sha256"] for n, r in admission["exact_seven_products"].items()}
        == {n: CAPTURE_PINS[n] for n in PRODUCTS},
        "Saved seven-product reuse authority differs",
    )
    actual = cases["cases"]
    require(
        len(actual) == len(review["cases"]) == 3
        and [r["scenario"]["lambda"] for r in actual] == [0.5, 1.0, 2.0],
        "Complete three-lambda marginal axis differs",
    )
    require(
        inputs["shared-ppe-counting-covariance.json"]["cases"]
        == [{**r["covariance"], "scenario": r["scenario"]} for r in actual],
        "Saved covariance sidecar differs",
    )
    projected = []
    for row, independent, forward in zip(
        actual,
        review["cases"],
        inputs["signed-forward-roundtrip-and-native-refusals.json"]["cases"],
        strict=True,
    ):
        require(
            row["scenario"] == independent["scenario"] == forward["scenario"],
            "Independent scenario identity differs",
        )
        cover = row["cover"]
        cov = row["covariance"]
        require(len(cover) == 2, "Closed panel output shape differs")
        close(sum(cover), 1.0)
        vector(cover, independent["oracle"]["cover"])
        feasible = all(0 <= v <= 1 for v in cover)
        require(
            row["simplex_feasible"] is feasible
            and independent["simplex_feasible"] is feasible
            and forward["simplex_feasible"] is feasible,
            "Signed negative-cover feasibility changed",
        )
        negative = [
            taxon
            for taxon, v in zip(cases["literal_panel"], cover, strict=True)
            if v < 0
        ]
        excess = [
            taxon
            for taxon, v in zip(cases["literal_panel"], cover, strict=True)
            if v > 1
        ]
        require(
            row["negative_taxon_labels"]
            == independent["negative_taxon_labels"]
            == negative
            and row["greater_than_one_taxon_labels"]
            == independent["greater_than_one_taxon_labels"]
            == excess,
            "Negative/out-of-simplex diagnostic differs",
        )
        require(
            row["maintained_forward"] == forward["maintained_forward"]
            and row["roundtrip_prediction_accuracy_claim"] is False,
            "Forward consequence or accuracy scope differs",
        )
        require(
            row["maintained_forward"]["status"]
            == ("accepted" if feasible else "refused"),
            "Maintained simplex refusal must remain",
        )
        for name in (
            "counting_covariance",
            "shared_ppe_covariance",
            "total_covariance",
        ):
            matrix(cov[name], independent["oracle"][name])
        vector(cov["conditional_SE"], independent["oracle"]["conditional_SE"])
        for i in range(2):
            for k in range(2):
                close(
                    cov["total_covariance"][i][k],
                    cov["counting_covariance"][i][k]
                    + cov["shared_ppe_covariance"][i][k],
                )
            close(cov["conditional_SE"][i] ** 2, cov["total_covariance"][i][i])
        require(
            cov["empirical_interval_coverage_claim"] is False,
            "Conditional SE is not interval coverage",
        )
        projected.append(
            {
                "scenario": row["scenario"],
                "signed_conditional_local_panel_cover": cover,
                "conditional_SE": cov["conditional_SE"],
                "counting_covariance": cov["counting_covariance"],
                "once_shared_ppe_covariance": cov["shared_ppe_covariance"],
                "total_conditional_covariance": cov["total_covariance"],
                "simplex_feasible": feasible,
                "negative_taxon_labels": negative,
                "greater_than_one_taxon_labels": excess,
                "maintained_forward_status": row["maintained_forward"]["status"],
                "maintained_forward_refusal": row["maintained_forward"].get("cause"),
                "inverse_forward_roundtrip_is_prediction_accuracy": False,
            }
        )
    require(
        [r["simplex_feasible"] for r in projected] == [True, False, False],
        "Both retained negative outcomes required",
    )
    physical = inputs["four-annulus-factors.json"]["new_tuples"]
    require(
        len(physical) == len(review["physical"]) == 4,
        "Four new physical request axis differs",
    )
    factors = []
    for row, independent in zip(physical, review["physical"], strict=True):
        require(
            row["arguments"] == independent["arguments"]
            and row["taxon"] == independent["taxon"]
            and row["region"] == independent["region"],
            "Physical tuple source binding differs",
        )
        close(row["factor"], independent["maintained_factor"])
        factors.append(
            {
                "region": row["region"],
                "taxon": row["taxon"],
                "arguments": row["arguments"],
                "maintained_factor": row["factor"],
                "independent_factor": independent["independent_factor"],
                "absolute_difference": independent["absolute_difference"],
                "nonrigorous_estimates": True,
            }
        )
    return {
        "schema_version": "swedish-conditional-love-account.v1",
        "actual_scientific_candidate": model["candidate"],
        "actual_scientific_plan_sha256": model["plan_sha256"],
        "original_model_job_status": model["status"],
        "original_model_stage_native_exit": 0,
        "original_independent_stage_native_exit": 1,
        "oracle_only_plan_sha256": oracle["plan_sha256"],
        "oracle_only_native_exit": 0,
        "literal_panel": cases["literal_panel"],
        "source_window": {
            "younger_cal_bp_inclusive": 100,
            "older_cal_bp_exclusive": 350,
            "point_membership_only": True,
            "epoch": "AD1950 convention for exact named calibrated BP fields; no historical chronology identity",
        },
        "source_denominators": {
            "source_samples": 29,
            "unknown_age_bounds": 20,
            "literal_panel_N": 7396,
            "reported_pollen_NISP": 27940,
            "residual_reported_NISP": 20544,
        },
        "source_cores": sources,
        "all_three_same_source_marginal_scenarios": projected,
        "four_source_bound_response_factors": factors,
        "independent_qualification": {
            "physical_tuples": 4,
            "scalar_cover_covariance_SE_cells": 48,
            "independent_review_sha256": CAPTURE_PINS["independent-review.json"],
            "geometry_estimates_nonrigorous": True,
        },
        "assumptions": {
            "static_receiving_radius_m": 80,
            "unestimated_split_radius_m": 1000,
            "regional_outer_radius_m": 100000,
            "all_terrestrial_without_landmask": True,
            "regional_proxy_contains80m_basin": True,
            "lambda_is_unestimated_panel_mass_ratio": True,
            "count_ppe_cross_covariance_assumed_zero": True,
            "same_source_lambda_covariances_are_marginal_not_joint": True,
            "chronology_bounds_not_repaired": True,
        },
        "unresolved_geometry_context": {
            "core": "KRAGMJNY",
            "workbook_static_radius_m": 837,
            "CAA2007_area_ha": 186,
            "CAA_document_url": "https://proceedings.caaconference.org/files/2007/125_Sugita_et_al_CAA2007.pdf",
            "printed_page": 388,
            "authority": "Browser parsed-text documentary review; no native PDF digest or historical geometry admission",
            "interpretation": "Unresolved cross-source area/radius provenance; neither replaces the frozen scientific scenario",
        },
        "raw_source_or_sample_rows_redistributed": False,
        "historical_vegetation_untouched_intervalcoverage_rights_review_admission": False,
    }
