"""Score first observed events against independently declared step-change truth."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.propagation.event_estimation import (
    GovernedSample,
    estimate_first_observed,
)
from bijux_pollenomics.analysis.propagation.network import PhenomenonEvent

JsonObject = dict[str, object]
_TRUE_CHANGE_BP = 5500.0
_DENSE_AGES = (5600.0, 5550.0, 5500.0, 5450.0, 5400.0)
_SPARSE_AGES = (5700.0, 5600.0, 5400.0, 5200.0)


def _template() -> PhenomenonEvent:
    return PhenomenonEvent(
        source_family="synthetic-change-time-truth",
        evidence_domain="pollen_context",
        source_snapshot_id="synthetic-step-change",
        source_record_id="template",
        site_id="synthetic-site",
        observation_ids=("template",),
        country_code="SE",
        latitude=60,
        longitude=15,
        coordinate_quality="fabricated_fixture",
        event_type="reported_positive_observation",
        resolution="whole_pollen",
        feature_key="whole:pollen",
        chronology_claim_id="template",
        younger_bp=0,
        older_bp=0,
        comparability_status="comparable",
        threshold_profile_id="reported_positive_v1",
        classification_contract_version=None,
        provenance_record_id="synthetic-fixture",
        input_digest="synthetic-fixture",
        config_digest="synthetic-step-change",
        producer_version="synthetic-change-time.v1",
        build_id="synthetic-step-change",
        measurement_semantics_id="synthetic-count.v1",
        evidence_method_id="synthetic-measurement",
        method_compatibility_key="synthetic-measurement.v1",
    )


def _samples(
    name: str, ages: tuple[float, ...], *, percentage: bool = False
) -> tuple[GovernedSample, ...]:
    return tuple(
        GovernedSample(
            observation_id=f"{name}:{index}",
            source_record_id=f"record:{name}:{index}",
            source_family="synthetic-change-time-truth",
            source_snapshot_id="synthetic-step-change",
            feature_key="whole:pollen",
            site_id="synthetic-site",
            collection_unit_id="synthetic-core",
            sequence_position=index,
            value=5.0 if age <= _TRUE_CHANGE_BP else 0.0,
            measure_kind="percentage" if percentage else "count",
            source_unit="percent_of_declared_synthetic_sum" if percentage else "grains",
            measurement_semantics_id="synthetic-percentage.v1"
            if percentage
            else "synthetic-count.v1",
            chronology_claim_id=f"age:{name}:{index}",
            comparability_status="comparable",
            younger_bp=age,
            older_bp=age,
            percentage_denominator=100.0 if percentage else None,
            source_age_value=age,
            source_age_unit="synthetic_cal_bp_1950",
        )
        for index, age in enumerate(ages)
    )


def build_change_time_challenge(
    *, scoring_change_bp: float = _TRUE_CHANGE_BP
) -> JsonObject:
    """Freeze each estimate before the independent change truth is used to score it."""
    attempts: list[tuple[str, tuple[GovernedSample, ...], str, str, float | None]] = []
    for name, ages, profiles, expected in (
        (
            "dense",
            _DENSE_AGES,
            ("reported_positive_v1", "count_ge_3_v1", "two_consecutive_positive_v1"),
            5500.0,
        ),
        (
            "sparse",
            _SPARSE_AGES,
            ("reported_positive_v1", "two_consecutive_positive_v1"),
            5400.0,
        ),
        ("percentage", _DENSE_AGES, ("percentage_ge_1_v1",), 5500.0),
    ):
        for profile in profiles:
            attempt_name = f"{name}-{profile}"
            attempts.append(
                (
                    attempt_name,
                    _samples(attempt_name, ages, percentage=name == "percentage"),
                    profile,
                    "first_observed_sample_selected",
                    expected,
                )
            )
    base = _samples("controls", _DENSE_AGES)
    transient = tuple(
        replace(row, value=5 if index == 2 else 0) for index, row in enumerate(base)
    )
    lonely = tuple(
        replace(row, value=5 if index == len(base) - 1 else 0)
        for index, row in enumerate(base)
    )
    gap = tuple(
        replace(
            row,
            younger_bp=None,
            older_bp=None,
            comparability_status="unresolved",
            source_age_value=None,
            source_age_unit=None,
        )
        if index == 2
        else row
        for index, row in enumerate(base)
    )
    overlap = tuple(
        replace(row, younger_bp=5480, older_bp=5560) if index == 2 else row
        for index, row in enumerate(base)
    )
    envelopes = tuple(replace(row, subject_granularity="site") for row in base)
    mixed = tuple(
        replace(row, measure_kind="percentage", source_unit="percent")
        if index == 1
        else row
        for index, row in enumerate(base)
    )
    unknown_percentage = tuple(
        replace(row, percentage_denominator=None)
        for row in _samples("unknown-denominator", _DENSE_AGES, percentage=True)
    )
    shuffled = tuple(
        replace(row, value=base[(index + 2) % len(base)].value)
        for index, row in enumerate(base)
    )
    no_change = tuple(replace(row, value=0) for row in base)
    uncalibrated = tuple(
        replace(
            row,
            comparability_status="context_only",
            younger_bp=None,
            older_bp=None,
            source_age_unit="uncalibrated_radiocarbon_bp",
        )
        for row in base
    )
    attempts.extend(
        (
            (
                "isolated-positive",
                transient,
                "two_consecutive_positive_v1",
                "insufficient_persistence",
                None,
            ),
            (
                "terminal-positive",
                lonely,
                "two_consecutive_positive_v1",
                "insufficient_persistence",
                None,
            ),
            (
                "chronology-gap",
                gap,
                "two_consecutive_positive_v1",
                "chronology_unresolved",
                None,
            ),
            (
                "overlapping-ages",
                overlap,
                "reported_positive_v1",
                "chronology_order_indeterminate",
                None,
            ),
            (
                "site-envelopes",
                envelopes,
                "reported_positive_v1",
                "sample_level_sequence_required",
                None,
            ),
            (
                "mixed-native-units",
                mixed,
                "count_ge_3_v1",
                "incompatible_measurement_semantics",
                None,
            ),
            (
                "unknown-percentage-denominator",
                unknown_percentage,
                "percentage_ge_1_v1",
                "percentage_denominator_unknown",
                None,
            ),
            (
                "shuffled-sample-values",
                shuffled,
                "two_consecutive_positive_v1",
                "first_observed_sample_selected",
                5600.0,
            ),
            (
                "no-change-negative-control",
                no_change,
                "reported_positive_v1",
                "threshold_not_met",
                None,
            ),
            (
                "uncalibrated-native-ages",
                uncalibrated,
                "reported_positive_v1",
                "chronology_unresolved",
                None,
            ),
        )
    )
    rows: list[JsonObject] = []
    for name, field, value, reason in (
        (
            "mixed-native-feature",
            "feature_key",
            "taxon:synthetic-other",
            "incompatible_sample_feature",
        ),
        (
            "mixed-source-family",
            "source_family",
            "synthetic-other-source",
            "incompatible_sample_source_family",
        ),
        (
            "stale-source-snapshot",
            "source_snapshot_id",
            "synthetic-stale-snapshot",
            "incompatible_sample_source_snapshot",
        ),
    ):
        changed = tuple(
            replace(
                row,
                feature_key=value if field == "feature_key" else row.feature_key,
                source_family=value if field == "source_family" else row.source_family,
                source_snapshot_id=value
                if field == "source_snapshot_id"
                else row.source_snapshot_id,
            )
            if index == 2
            else row
            for index, row in enumerate(base)
        )
        attempts.append((name, changed, "reported_positive_v1", reason, None))
    for name, samples, profile, expected_reason, expected_age in attempts:
        template = _template()
        if samples[0].measure_kind == "percentage":
            template = replace(
                template, measurement_semantics_id="synthetic-percentage.v1"
            )
        estimate = estimate_first_observed(
            samples, event_template=template, threshold_profile_id=profile
        )
        frozen = estimate.as_dict()
        estimated_age = None if estimate.event is None else estimate.event.younger_bp
        passed = (
            estimate.reason_code == expected_reason and estimated_age == expected_age
        )
        row: JsonObject = {
            "case_id": name,
            "native_samples": [asdict(sample) for sample in samples],
            "event_template": template.as_dict(),
            "threshold_profile_id": profile,
            "prospective_expected_reason_code": expected_reason,
            "prospective_expected_observed_age_bp": expected_age,
            "output": frozen,
            "contract_status": "passed" if passed else "failed",
            "prediction_frozen_before_truth_scoring": True,
            "status": "estimated" if estimate.event is not None else "refused",
            "synthetic_true_change_bp": None
            if name == "no-change-negative-control"
            else scoring_change_bp,
        }
        if estimated_age is not None:
            bias = estimated_age - scoring_change_bp
            row.update(
                signed_age_bias_years=bias,
                absolute_age_error_years=abs(bias),
                observed_detection_delay_years=-bias,
                exact_change_recovered=estimated_age == scoring_change_bp,
                truth_scoring_status="exact" if bias == 0 else "biased",
            )
        else:
            row.update(
                truth_scoring_status="not_scored_refusal",
                signed_age_bias_years=None,
                absolute_age_error_years=None,
                observed_detection_delay_years=None,
                exact_change_recovered=None,
            )
        rows.append(row)
    estimated = [row for row in rows if row["status"] == "estimated"]
    return {
        "schema_version": "pollenomics-synthetic-change-time.v1",
        "source_kind": "independent_piecewise_constant_step_and_fabricated_sample_ages",
        "prospective_contract": {
            "requested_attempts": 19,
            "true_change_bp": _TRUE_CHANGE_BP,
            "native_value_before_change": 0.0,
            "native_value_at_and_after_change": 5.0,
            "dense_ages_bp": _DENSE_AGES,
            "sparse_ages_bp": _SPARSE_AGES,
            "calculation_tolerance_years": 0.0,
            "shuffle": "fixed_two_position_cyclic_value_shift",
            "thresholds_tuned_after_scoring": False,
        },
        "cases": rows,
        "denominators": {
            "requested": 19,
            "attempted": len(rows),
            "estimated": len(estimated),
            "refused": len(rows) - len(estimated),
            "contract_passed": sum(row["contract_status"] == "passed" for row in rows),
            "exact_change_recovered": sum(
                row["exact_change_recovered"] is True for row in rows
            ),
            "biased_change_estimates": sum(
                row["truth_scoring_status"] == "biased" for row in rows
            ),
        },
        "scored_estimate_mean_absolute_error_years": sum(
            cast(float, row["absolute_age_error_years"]) for row in estimated
        )
        / len(estimated),
        "claims": {
            "synthetic_only": True,
            "empirical_threshold_validation": False,
            "real_taxon_or_pollen_sum_admission": False,
            "continuous_presence_established": False,
            "confidence_interval_coverage_established": False,
            "estimand": "first qualifying observed sample, not an interpolated ecological change time",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_change_time_challenge()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    counts = cast(dict[str, int], report["denominators"])
    print(json.dumps({"output": str(args.output), **counts}))
    return 0 if counts["contract_passed"] == counts["requested"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
