"""Controlled native rows test joins, partial scope and exact failure retention."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any
import zipfile

import pytest

from bijux_pollenomics_dev.essd_reproduction import pft_crosswalk as source
from bijux_pollenomics_dev.essd_reproduction.pft_covariance import archive


def controlled() -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    taxa = list(source.ISTS_OUTPUT_TAXA + source.TBS_OUTPUT_TAXA)
    taxa.extend(f"unmapped-taxon:{i}" for i in range(22))
    pfts = list(
        source.SOURCE_GROUPS["ET"]
        + source.OBSERVED_MEAN_GROUPS["ST"]
        + source.SOURCE_GROUPS["OL"]
    )
    header = ["LCGRID_ID", "lonDD", "latDD", *taxa, *pfts, "ET", "ST", "OL"]
    mean = dict.fromkeys(header, "0")
    mean.update(LCGRID_ID="grid-a", lonDD="12.5", latDD="50.5")
    for name in source.SOURCE_GROUPS["ET"]:
        mean[name] = "5"
    mean.update(
        IBS="10",
        ISTS="6",
        TBS="12",
        TSD="2",
        LSE="10",
        GL="20",
        AL="10",
        ET="30",
        ST="30",
        OL="40",
    )
    for name in taxa[:9]:
        mean[name] = "2"
    mean[taxa[9]] = "82"
    error = dict.fromkeys(header, "1")
    error.update(LCGRID_ID="grid-a", lonDD="12.50", latDD="50.50")
    return header, [mean], [error]


def analyse(
    means: list[dict[str, str]], errors: list[dict[str, str]], header: list[str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return archive.analyse_window(1, header, means, errors, expected_rows=len(means))


def test_native_partial_tree_is_scoped_and_retains_both_literal_closure_targets() -> (
    None
):
    header, means, errors = controlled()
    summary, diagnostics = analyse(means, errors, header)
    assert not diagnostics
    assert summary["coordinate_rows"] == {"matched_finite": 1}
    assert summary["populations"] == {
        "mean_total_near_hundred": 1,
        "conditional_point_covariance_feasible": 1,
    }
    assert len(summary["ungrouped_taxon_variables"]) == 22
    assert len(summary["minimum_exact_SE_constraint_margins"]) == 6
    assert summary["maximum_absolute_native_mean_identity_residual_exact"] == "0"
    assert summary["native_lct_total_residuals"]["one"] == {
        "rows": 1,
        "minimum_signed_exact": "99",
        "maximum_signed_exact": "99",
        "within_existing_mean_threshold": 0,
    }
    assert (
        summary["native_lct_total_residuals"]["hundred"][
            "within_existing_mean_threshold"
        ]
        == 1
    )


def test_rows_join_by_native_id_even_when_source_order_and_coordinate_spelling_differ() -> (
    None
):
    header, means, errors = controlled()
    second_mean, second_error = deepcopy(means[0]), deepcopy(errors[0])
    second_mean["LCGRID_ID"] = second_error["LCGRID_ID"] = "grid-b"
    second_error["ET"] = "3"
    summary, diagnostics = analyse(
        [means[0], second_mean], [second_error, errors[0]], header
    )
    assert summary["populations"]["conditional_point_covariance_feasible"] == 1
    assert summary["populations"]["conditional_point_covariance_infeasible"] == 1
    assert diagnostics[0]["LCGRID_ID"] == "grid-b"
    assert diagnostics[0]["constraint"] == archive.TOTAL
    assert diagnostics[0]["violation_magnitude_exact"] == "1"
    assert diagnostics[0]["parent_se_literal"] == "0"
    assert '"ET":"3"' in diagnostics[0]["child_se_literals"]


def test_recorded_point_failure_below_old_mean_tolerance_is_still_failure() -> None:
    header, means, errors = controlled()
    errors[0].update(ET="2.000000000000000000000000000001", ST="1", OL="1")
    summary, diagnostics = analyse(means, errors, header)
    assert summary["populations"]["conditional_point_covariance_infeasible"] == 1
    failure = next(d for d in diagnostics if d["constraint"] == archive.TOTAL)
    assert Fraction(failure["violation_magnitude_exact"]) == Fraction(1, 10**30)
    assert "2.000000000000000000000000000001" in failure["child_se_literals"]


@pytest.mark.parametrize("zero", [False, True])
def test_exactly_paired_native_missing_coordinates_preserve_covariance_or_zero_refusal(
    zero: bool,
) -> None:
    header, means, errors = controlled()
    for row in (means[0], errors[0]):
        row.update(lonDD="#N/A", latDD="#N/A")
        if zero:
            for name in header[3:]:
                row[name] = "0"
    summary, diagnostics = analyse(means, errors, header)
    assert summary["coordinate_rows"] == {"matched_missing": 1}
    assert summary["populations"] == (
        {"native_all_zero": 1}
        if zero
        else {"mean_total_near_hundred": 1, "conditional_point_covariance_feasible": 1}
    )
    if zero:
        assert diagnostics[0]["lonDD"] == diagnostics[0]["latDD"] == "#N/A"
    assert means[0]["lonDD"] == errors[0]["lonDD"] == "#N/A"


@pytest.mark.parametrize(
    "left,right",
    [
        ("#N/A", "12.5"),
        ("12.5", "#N/A"),
        ("#N/A", "N/A"),
        ("#N/A", "#N/A "),
        ("", ""),
        ("N/A", "N/A"),
    ],
)
def test_unpaired_unknown_or_differently_spelled_missing_coordinates_refuse(
    left: str, right: str
) -> None:
    header, means, errors = controlled()
    means[0]["lonDD"], errors[0]["lonDD"] = left, right
    with pytest.raises(ValueError):
        analyse(means, errors, header)


@pytest.mark.parametrize(
    "mode,disposition",
    [
        ("all_zero", "native_all_zero"),
        ("means_zero", "mean_total_refused"),
        ("identity", "mean_identity_refused"),
        ("total", "mean_total_refused"),
        ("negative_mean", "negative_native_value"),
        ("negative_se", "negative_native_value"),
        ("missing_mean", "invalid_native_numeric"),
        ("nan_se", "invalid_native_numeric"),
        ("inf_se", "invalid_native_numeric"),
        ("fraction_token", "invalid_native_numeric"),
    ],
)
def test_negative_missing_zero_and_unclosed_populations_are_refused_without_repair(
    mode: str, disposition: str
) -> None:
    header, means, errors = controlled()
    if mode in {"all_zero", "means_zero"}:
        for name in header[3:]:
            means[0][name] = "0"
            if mode == "all_zero":
                errors[0][name] = "0"
    elif mode == "identity":
        means[0]["ET"] = "31"
    elif mode == "total":
        # Preserve every partial identity while changing the total to 200.
        for name in header[3:]:
            means[0][name] = str(2 * Fraction(means[0][name]))
    elif mode == "negative_mean":
        means[0][header[3]] = "-1"
    elif mode == "negative_se":
        errors[0][header[3]] = "-1"
    elif mode == "missing_mean":
        means[0][header[3]] = ""
    else:
        errors[0][header[3]] = {
            "nan_se": "NaN",
            "inf_se": "Infinity",
            "fraction_token": "1/3",
        }[mode]
    original = deepcopy((means, errors))
    summary, diagnostics = analyse(means, errors, header)
    assert summary["populations"] == {disposition: 1}
    assert len(diagnostics) == 1 and diagnostics[0]["disposition"] == disposition
    assert not summary["minimum_exact_SE_constraint_margins"]
    assert (means, errors) == original


def test_common_native_fraction_scale_is_recorded_without_rescaling() -> None:
    header, means, errors = controlled()
    for row in (means[0], errors[0]):
        for name in header[3:]:
            row[name] = str(float(row[name]) / 100)
    summary, diagnostics = analyse(means, errors, header)
    assert not diagnostics
    assert summary["populations"]["mean_total_near_one"] == 1
    assert summary["native_lct_total_residuals"]["one"]["minimum_signed_exact"] == "0"
    assert (
        summary["native_lct_total_residuals"]["hundred"]["minimum_signed_exact"]
        == "-99"
    )
    assert errors[0]["ET"] == "0.01"


def test_existing_mean_threshold_is_separate_from_exact_se_decisions() -> None:
    header, means, errors = controlled()
    means[0]["ET"] = "30.0000000001"
    summary, diagnostics = analyse(means, errors, header)
    assert not diagnostics
    assert (
        summary["maximum_absolute_native_mean_identity_residual_exact"]
        == "1/10000000000"
    )
    means[0]["ET"] = "30.00000001"
    refused, diagnostics = analyse(means, errors, header)
    assert refused["populations"] == {"mean_identity_refused": 1}
    assert diagnostics[0]["reason"]


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate_mean",
        "duplicate_se",
        "missing_mean",
        "extra_se",
        "identity",
        "coordinate",
        "missing_field",
        "pft_header",
        "repeated_header",
    ],
)
def test_structural_axis_and_join_changes_refuse_before_interpretation(
    mode: str,
) -> None:
    header, means, errors = controlled()
    if mode == "duplicate_mean":
        means.append(deepcopy(means[0]))
    elif mode == "duplicate_se":
        errors.append(deepcopy(errors[0]))
    elif mode == "missing_mean":
        means.clear()
    elif mode == "extra_se":
        extra = deepcopy(errors[0])
        extra["LCGRID_ID"] = "other-grid"
        errors.append(extra)
    elif mode == "identity":
        errors[0]["LCGRID_ID"] = "other-grid"
    elif mode == "coordinate":
        errors[0]["lonDD"] = "12.50000001"
    elif mode == "missing_field":
        del means[0]["ET"]
    elif mode == "pft_header":
        header[34] = "unknown-code"
    else:
        header[3] = header[4]
    with pytest.raises(ValueError):
        archive.analyse_window(1, header, means, errors, expected_rows=1)


def test_raw_input_change_during_consumer_refuses_before_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    raw = repository / source.ARCHIVE
    raw.parent.mkdir(parents=True)
    with zipfile.ZipFile(raw, "w"):
        pass
    (repository / "artifacts").mkdir()
    identities = iter(
        (
            [{"path": "raw", "sha256": "original"}],
            [{"path": "raw", "sha256": "changed"}],
        )
    )
    monkeypatch.setattr(
        source, "_verified_sources", lambda _: (b"mapping", next(identities))
    )
    monkeypatch.setattr(source, "_source_mapping", lambda _: None)
    monkeypatch.setattr(
        source,
        "_members",
        lambda _: {kind: dict.fromkeys(range(1, 26), kind) for kind in ("mean", "se")},
    )
    monkeypatch.setattr(source, "_records", lambda *_: (["header"], []))
    monkeypatch.setattr(archive, "_revision", lambda _: "a" * 40)
    monkeypatch.setattr(
        archive,
        "analyse_window",
        lambda *_: (
            {
                "source_grid_rows": 420,
                "populations": {},
                "coordinate_rows": {},
                "ungrouped_taxon_variables": [],
            },
            [],
        ),
    )
    output = repository / "artifacts" / "joint-covariance"
    with pytest.raises(ValueError, match="Raw scientific inputs changed"):
        archive.build(repository, output)
    assert not output.exists()
