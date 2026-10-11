"""Verify exact, bounded ESSD published-estimate comparisons."""

from __future__ import annotations

from decimal import Decimal, localcontext
import re

import pytest

from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    LandClimPublishedEstimate,
    LandClimPublishedEstimateInventory,
    LandClimPublishedEstimateRow,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    contracts as published_contracts,
)
from bijux_pollenomics_dev.essd_reproduction.comparison import (
    PublishedEstimateCandidate,
    PublishedEstimateComparisonError,
    PublishedEstimateKey,
    PublishedEstimateValue,
    compare_published_estimates,
)


def _value(
    grid: str,
    window: str,
    feature: str,
    mean: str | None,
    standard_error: str | None,
) -> PublishedEstimateValue:
    return PublishedEstimateValue(
        key=PublishedEstimateKey(grid, window, feature),
        mean=None if mean is None else Decimal(mean),
        standard_error=(None if standard_error is None else Decimal(standard_error)),
    )


def _inventory(
    rows: tuple[tuple[str, str, tuple[tuple[str, str, str], ...]], ...],
) -> LandClimPublishedEstimateInventory:
    records: list[LandClimPublishedEstimateRow] = []
    variables: list[str] = []
    windows: list[str] = []
    for window, grid, estimates in rows:
        if window not in windows:
            windows.append(window)
        for feature, _, _ in estimates:
            if feature not in variables:
                variables.append(feature)
        records.append(
            LandClimPublishedEstimateRow(
                time_window=window,
                cell_id=grid,
                mean_cell_id_token=grid,
                standard_error_cell_id_token=grid,
                mean_source_locator=f"mean/{window}.csv",
                standard_error_source_locator=f"se/{window}.csv",
                mean_longitude_token="10",
                mean_latitude_token="60",
                standard_error_longitude_token="10",
                standard_error_latitude_token="60",
                longitude=Decimal("10"),
                latitude=Decimal("60"),
                coordinate_status="available",
                coordinate_refusal_reason=None,
                estimates=tuple(
                    LandClimPublishedEstimate(
                        variable=feature,
                        mean_token=mean,
                        mean=Decimal(mean),
                        standard_error_token=standard_error,
                        standard_error=Decimal(standard_error),
                    )
                    for feature, mean, standard_error in estimates
                ),
            )
        )
    return published_contracts._mint_inventory(
        receipt_sha256="1" * 64,
        archive_sha256="2" * 64,
        dataset_doi="10.1594/PANGAEA.937075",
        time_windows=tuple(windows),
        variables=tuple(variables),
        records=tuple(records),
        coordinate_available_record_count=len(records),
        coordinate_refused_record_count=0,
        mean_zero_value_count=sum(
            Decimal(mean).is_finite() and Decimal(mean).is_zero()
            for _, _, estimates in rows
            for _, mean, _ in estimates
        ),
        mean_above_one_value_count=sum(
            Decimal(mean).is_finite() and Decimal(mean) > 1
            for _, _, estimates in rows
            for _, mean, _ in estimates
        ),
        mean_negative_value_count=sum(
            Decimal(mean).is_finite() and Decimal(mean) < 0
            for _, _, estimates in rows
            for _, mean, _ in estimates
        ),
        mean_negative_record_count=sum(
            any(
                Decimal(mean).is_finite() and Decimal(mean) < 0
                for _, mean, _ in estimates
            )
            for _, _, estimates in rows
        ),
    )


def _reference() -> LandClimPublishedEstimateInventory:
    return _inventory(
        (
            ("TW01", "grid-a", (("forest", "10", "1.5"),)),
            ("TW02", "grid-b", (("open", "0", "0"),)),
        )
    )


def _candidate(
    rows: tuple[PublishedEstimateValue, ...],
    *,
    unit: str = "percentage_cover",
) -> PublishedEstimateCandidate:
    return PublishedEstimateCandidate(
        candidate_id="native-publication-profile:test-build",
        value_unit=unit,
        rows=rows,
    )


def test_full_join_preserves_exact_zero_and_reports_residuals_and_hashes() -> None:
    reference = _reference()
    candidate = _candidate(
        (
            _value("grid-a", "TW01", "forest", "12.25", "1.25"),
            _value("grid-b", "TW02", "open", "0", "0"),
        )
    )

    result = compare_published_estimates(reference, candidate)

    assert result.denominators.payload() == {
        "reference_keys": 2,
        "candidate_keys": 2,
        "union_keys": 2,
        "shared_keys": 2,
        "reference_only_keys": 0,
        "candidate_only_keys": 0,
        "mean": {
            "numeric_pairs": 2,
            "both_null": 0,
            "null_disagreements": 0,
        },
        "standard_error": {
            "numeric_pairs": 2,
            "both_null": 0,
            "null_disagreements": 0,
        },
    }
    forest, exact_zero = result.rows
    assert (forest.mean_residual, forest.standard_error_residual) == (
        Decimal("2.25"),
        Decimal("-0.25"),
    )
    assert (
        exact_zero.reference_mean,
        exact_zero.candidate_mean,
        exact_zero.mean_residual,
    ) == (Decimal("0"), Decimal("0"), Decimal("0"))
    assert result.reference_input_sha256 == reference.sha256
    assert result.candidate_input_sha256 == candidate.sha256
    assert re.fullmatch(r"[0-9a-f]{64}", result.sha256)
    payload = result.payload()
    assert payload["residual_definition"] == "candidate_minus_reference"
    assert payload["claims"] == {
        "historical_raw_inputs_recovered": False,
        "original_r_execution": False,
        "whole_paper_reproduction_certified": False,
        "independent_measured_vegetation_accuracy": False,
        "scientifically_accepted": False,
        "scientific_acceptance": "not_evaluated",
    }


def test_outer_join_exposes_missing_key_denominators() -> None:
    candidate = _candidate(
        (
            _value("grid-a", "TW01", "forest", "10", "1.5"),
            _value("grid-c", "TW03", "crop", "4", "0.5"),
        )
    )

    result = compare_published_estimates(_reference(), candidate)

    assert result.denominators.shared_keys == 1
    assert result.denominators.reference_only_keys == 1
    assert result.denominators.candidate_only_keys == 1
    assert [row.membership for row in result.rows] == [
        "shared",
        "reference_only",
        "candidate_only",
    ]
    assert result.rows[1].candidate_mean is None
    assert result.rows[2].reference_mean is None
    assert result.rows[1].mean_null_disagreement is False
    assert result.rows[2].mean_null_disagreement is False


def test_present_null_is_not_zero_or_an_absent_key() -> None:
    candidate = _candidate(
        (
            _value("grid-a", "TW01", "forest", None, "1.5"),
            _value("grid-b", "TW02", "open", "0", None),
        )
    )

    result = compare_published_estimates(_reference(), candidate)

    assert result.denominators.mean.payload() == {
        "numeric_pairs": 1,
        "both_null": 0,
        "null_disagreements": 1,
    }
    assert result.denominators.standard_error.payload() == {
        "numeric_pairs": 1,
        "both_null": 0,
        "null_disagreements": 1,
    }
    forest, exact_zero = result.rows
    assert forest.membership == "shared"
    assert forest.candidate_mean is None
    assert forest.mean_residual is None
    assert forest.mean_null_disagreement is True
    assert exact_zero.candidate_mean == Decimal("0")
    assert exact_zero.mean_residual == Decimal("0")
    assert exact_zero.standard_error_null_disagreement is True


def test_duplicate_keys_are_refused_on_either_side() -> None:
    duplicate = _value("grid-a", "TW01", "forest", "10", "1.5")
    with pytest.raises(PublishedEstimateComparisonError, match="duplicate candidate"):
        _candidate((duplicate, duplicate))

    reference = _inventory(
        (
            (
                "TW01",
                "grid-a",
                (("forest", "10", "1.5"), ("forest", "11", "1.6")),
            ),
        )
    )
    with pytest.raises(PublishedEstimateComparisonError, match="duplicate reference"):
        compare_published_estimates(reference, _candidate((duplicate,)))


@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_candidate_values_are_refused(invalid: str) -> None:
    with pytest.raises(PublishedEstimateComparisonError, match="finite Decimal"):
        _value("grid-a", "TW01", "forest", invalid, "1")
    with pytest.raises(PublishedEstimateComparisonError, match="finite Decimal"):
        _value("grid-a", "TW01", "forest", "1", invalid)


def test_nonfinite_reference_values_are_refused() -> None:
    reference = _inventory((("TW01", "grid-a", (("forest", "NaN", "1"),)),))
    candidate = _candidate((_value("grid-a", "TW01", "forest", "1", "1"),))
    with pytest.raises(PublishedEstimateComparisonError, match="finite Decimal"):
        compare_published_estimates(reference, candidate)


def test_mismatched_units_are_refused_without_conversion() -> None:
    candidate = _candidate(
        (_value("grid-a", "TW01", "forest", "0.1", "0.01"),),
        unit="proportion",
    )
    with pytest.raises(PublishedEstimateComparisonError, match="implicit conversion"):
        compare_published_estimates(_reference(), candidate)


def test_candidate_order_is_canonical_but_content_changes_hashes() -> None:
    first = _value("grid-a", "TW01", "forest", "10", "1.5")
    second = _value("grid-b", "TW02", "open", "0", "0")
    forward = _candidate((first, second))
    reverse = _candidate((second, first))

    forward_result = compare_published_estimates(_reference(), forward)
    reverse_result = compare_published_estimates(_reference(), reverse)

    assert forward.sha256 == reverse.sha256
    assert forward_result == reverse_result
    changed = _candidate((first, _value("grid-b", "TW02", "open", "1", "0")))
    changed_result = compare_published_estimates(_reference(), changed)
    assert changed.sha256 != forward.sha256
    assert (
        changed_result.candidate_input_sha256 != forward_result.candidate_input_sha256
    )
    changed_reference = _inventory(
        (
            ("TW01", "grid-a", (("forest", "11", "1.5"),)),
            ("TW02", "grid-b", (("open", "0", "0"),)),
        )
    )
    assert (
        compare_published_estimates(changed_reference, forward).reference_input_sha256
        != forward_result.reference_input_sha256
    )


def test_residuals_do_not_depend_on_callers_decimal_precision() -> None:
    reference = _inventory((("TW01", "grid-a", (("forest", "1.000001", "0.000001"),)),))
    candidate = _candidate(
        (
            _value(
                "grid-a",
                "TW01",
                "forest",
                "123456789.123456",
                "0.123456789",
            ),
        )
    )

    with localcontext() as context:
        context.prec = 3
        row = compare_published_estimates(reference, candidate).rows[0]

    assert row.mean_residual == Decimal("123456788.123455")
    assert row.standard_error_residual == Decimal("0.123455789")
