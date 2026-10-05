"""Derive per-core support and within-core effects without pooling panels."""

from __future__ import annotations

from .authority import CAPTURE_PINS
from .validation import validate


def products(inputs: dict) -> dict[str, dict]:
    report = inputs["report.json"]
    census = inputs["verification/source-census.json"]
    validated = validate(report, census)
    cases = validated["cases"]
    source_rows = []
    for core, source in sorted(validated["source_by_dataset"].items()):
        core_cases = [
            case for case, _ in cases.values() if case["native_dataset_id"] == core
        ]
        baseline = next(
            case
            for case in core_cases
            if case["static_geometry"]["id"] == "metadata_static_radius"
        )
        rows = baseline["results"]
        source_rows.append(
            {
                "native_dataset_id": core,
                "native_collection_unit_id": baseline["native_collection_unit_id"],
                "native_site_id": baseline["native_site_id"],
                "source_handle": baseline["source_handle"],
                "country": baseline["country"],
                "source_samples": baseline["source_samples"],
                "accepted_point_domain_samples": baseline["accepted_samples"],
                "point_domain_exclusions": baseline["exclusions"],
                "prior_signed_point_or_bounds_refused_samples": source[
                    "prior_nonnegative_BP_point_or_bounds_refusals"
                ],
                "equal_cohort_identity_inferred_from_equal_counts": False,
                "selected_named_calibrated_chronology": baseline[
                    "selected_named_calibrated_chronology"
                ],
                "collection_unit_default_chronology_not_selected": source[
                    "native_default_chronology"
                ],
                "nested_model_default_flags_override_selected_named_id": False,
                "missing_reported_age_bounds_samples": sum(
                    row["source_age_bounds_missing"] for row in rows
                ),
                "signed_reported_age_bounds_retained_samples": sum(
                    row["source_signed_reported_age_bounds_count"] for row in rows
                ),
                "parameter_taxa": baseline["parameter_taxa"],
                "all_selected_labels_explicit_in_each_included_sample": True,
                "missing_label_zero_imputation": False,
                "occupied_windows": baseline["occupied_windows"],
                "represented_case_ids": sorted(case["case_id"] for case in core_cases),
                "mapped_panel_NISP": sum(
                    row["panel_count_denominator"] for row in rows
                ),
                "accepted_all_reported_pollen_NISP": sum(
                    row["reported_all_pollen_NISP_sum"] for row in rows
                ),
                "unparameterized_reported_pollen_NISP": sum(
                    row["unparameterized_reported_NISP_sum"] for row in rows
                ),
                "metadata_locator": source["metadata_locator"],
                "historical_access_marker": source["raw_metadata_fields"][
                    "DataRestricted/NotRestriced"
                ],
                "historical_access_marker_scope": "Historical workbook field; not substituted for current public-source terms or separately restricted author-copy rights.",
                "static_geometry_alternatives": [
                    case["static_geometry"] for case in core_cases
                ],
                "dated_basin_geometry_admitted": False,
                "metadata_core_notes": source["raw_source_metadata"]["collection_unit"][
                    "notes"
                ],
            }
        )
    if sum(row["missing_reported_age_bounds_samples"] for row in source_rows) != 222:
        raise ValueError(
            "Nordic de-duplicated missing chronology-bound population differs"
        )
    comparisons = []
    supplied = {row["case_id"]: row for row in report["within_core_comparisons"]}
    if len(supplied) != 9 or len(report["within_core_comparisons"]) != 9:
        raise ValueError("Nordic saved comparison case axis differs")
    for name, (case, windows) in sorted(cases.items()):
        metadata = cases[f"{case['native_dataset_id']}.metadata_static_radius"]
        if metadata[0]["parameter_taxa"] != case["parameter_taxa"] or set(
            metadata[1]
        ) != set(windows):
            raise ValueError("Nordic within-core comparison support differs")
        recorded = supplied.get(name)
        if recorded is None or recorded["parameter_taxa"] != case["parameter_taxa"]:
            raise ValueError("Nordic saved comparison taxon axis differs")
        actual_windows = []
        maxima = {}
        for window, row in windows.items():
            differences = {
                "physical_corrected_cover_minus_direct_panel_fraction": [
                    right - left
                    for right, left in zip(
                        row["conditional_cover"],
                        row["direct_pollen_panel_fraction"],
                        strict=True,
                    )
                ],
                "static_geometry_cover_minus_metadata_baseline": [
                    right - left
                    for right, left in zip(
                        row["conditional_cover"],
                        metadata[1][window]["conditional_cover"],
                        strict=True,
                    )
                ],
            }
            actual_windows.append({"window_cal_bp": list(window), **differences})
            for comparison, values in differences.items():
                for i, value in enumerate(values):
                    if comparison not in maxima or abs(value) > abs(
                        maxima[comparison]["change_fraction"]
                    ):
                        maxima[comparison] = {
                            "comparison": comparison,
                            "change_fraction": value,
                            "parameter_taxon": case["parameter_taxa"][i],
                            "window_cal_bp": list(window),
                        }
        if actual_windows != recorded["windows"]:
            raise ValueError("Nordic derived comparison differs from saved output")
        comparisons.append(
            {
                "case_id": name,
                "native_dataset_id": case["native_dataset_id"],
                "parameter_taxa": case["parameter_taxa"],
                "occupied_windows": len(windows),
                "maximum_cover_changes": [maxima[key] for key in sorted(maxima)],
                "windows": actual_windows,
            }
        )
    proofs = {
        "original_scientific_report_pending_flag_preserved": report[
            "new_physical_independent_review_complete"
        ]
        is False,
        "independent_scalar_review": inputs[
            "verification/independent-scalar-review.json"
        ],
        "independent_physical_review_sha256": next(
            sha
            for path, sha in CAPTURE_PINS.items()
            if path.endswith("verification/independent-physical-review.json")
        ),
        "independent_physical_tuples": 23,
        "independent_physical_case_target_uses": 29,
        "current_retained_account_equation_check": {
            "case_window_results": validated["rows"],
            "scalar_values_compared": validated["cells"],
            "precision_digits": 50,
            "absolute_tolerance": "2e-12",
            "relative_tolerance": "2e-12",
            "scope": "Saved-input scalar closure/covariance consistency; no maintained physical engine, R, source acquisition or chronology fit.",
        },
    }
    account = {
        "schema_version": "nordic-retained-static-basin-account.v1",
        "source_kind": "Source-bound aggregate replay and scientific account",
        "cases": report["cases"],
        "protocol": report["protocol"],
        "source_sample_population": {
            "distinct_datasets": 4,
            "distinct_collection_units": 4,
            "distinct_sites": len({row["native_site_id"] for row in source_rows}),
            "source_samples": 314,
            "accepted_point_domain_samples": 313,
        },
        "retained_source_sha256": dict(CAPTURE_PINS),
        "scientific_verification": proofs,
        "raw_source_support_promoted": False,
        "fresh_source_acquisition_or_physical_model_run": False,
        "historical_reproduction_claim": False,
        "ecological_accuracy_claim": False,
        "chronology_accuracy_claim": False,
        "full_vegetation_or_cross_country_panel_comparability_claim": False,
    }
    domain = {
        "schema_version": "nordic-static-basin-source-domain.v1",
        "cores": source_rows,
        "source_samples": 314,
        "accepted_point_domain_samples": 313,
        "unknown_reported_age_bounds_samples": 222,
        "geometry_case_count": 9,
        "case_window_results": 182,
        "distinct_sites": len({row["native_site_id"] for row in source_rows}),
        "point_domain_cal_bp": {
            "younger_inclusive": 0,
            "older_exclusive": 11700,
            "epoch": "AD1950",
        },
        "point_vs_bounds_cohort_scope": "Solsø81 retains point7 with younger bound−41 and excludes point12417; equal65sample totals do not establish identity with the earlier nonnegative-bounds cohort. Source point/control/calibration provenance remains distinct; no interpolation/refit/error bounds invented.",
        "comparability_scope": "Panels differ (2/3/2/6 taxa); closed proportions and pollen-count coverage are panel-specific, not whole vegetation/cross-country area estimates. Solsø cores share one lake; geometry alternatives are repeated scenarios, not independent observations.",
        "uncertainty_scope": "Conditional marginal counting and assumed diagonal PPE delta covariance; shared PPE induces dependence across windows/cases, whose joint blocks are not computed. Chronology, basin history, parameter validity and model discrepancy are outside these SEs. Plug-in zero SE does not establish absence.",
    }
    return {
        "account.json": account,
        "source-domain.json": domain,
        "comparisons.json": {
            "schema_version": "nordic-static-basin-within-core-comparisons.v1",
            "cases": comparisons,
            "cross_core_pooling": False,
            "claim": "Within each fixed source panel only; corrections/sensitivities are not measured accuracy.",
        },
    }
