"""Independent small-panel arithmetic and native denominator admission."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import cohort, producer
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import Cell, Core
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    fit_multisite_likelihood,
)


def group(counts: list[list[int]] | None = None) -> dict[str, Any]:
    values = counts if counts is not None else [[80, 20], [50, 50]]
    return {
        "window_cal_bp": [0, 100],
        "sites": [
            {"core": name, "projected_counts": row, "taxon_measured": [True, True]}
            for name, row in zip(cohort.CORES, values, strict=True)
        ],
    }


def test_likelihood_and_correct_then_pool_have_distinct_same_input_estimands() -> None:
    result = producer.compare_group(group(), [[9, 1], [1, 1]])
    assert result["status"] == "computed"
    fitted = result["common_cover_fit"]
    expected = (4 + math.sqrt(4176)) / 160
    assert fitted["cover"] == pytest.approx([expected, 1 - expected], abs=2e-11)
    baseline = result["geometry_correct_then_pool"]
    assert baseline["cover"] == pytest.approx([53 / 116, 63 / 116])
    old_equal_place_inverse = 21 / 52
    assert abs(expected - old_equal_place_inverse) > 0.01
    assert abs(expected - baseline["cover"][0]) > 0.01
    nll = -sum(
        n * math.log(p)
        for counts, probabilities in zip(
            [[80, 20], [50, 50]], fitted["predicted_pollen_fraction"], strict=True
        )
        for n, p in zip(counts, probabilities, strict=True)
    )
    saturated = -sum(n * math.log(n / 100) for row in [[80, 20], [50, 50]] for n in row)
    assert fitted[
        "negative_log_likelihood_without_combinatorial_constant"
    ] == pytest.approx(nll)
    assert fitted["mean_negative_log_likelihood"] == pytest.approx(nll / 200)
    assert fitted["multinomial_deviance"] == pytest.approx(2 * (nll - saturated))
    assert result["baseline_minus_fitted_negative_log_likelihood"] > 0


def test_common_response_reduces_to_effort_weighted_counts_not_equal_place_mean() -> (
    None
):
    result = producer.compare_group(group([[9, 1], [10, 90]]), [[2, 1], [2, 1]])
    expected = (19 / 2) / (19 / 2 + 91)
    assert result["common_cover_fit"]["cover"][0] == pytest.approx(expected)
    assert result["geometry_correct_then_pool"]["cover"][0] == pytest.approx(expected)
    assert abs(expected - 0.5 * ((9 / 2) / (9 / 2 + 1) + 5 / 95)) > 0.1


def test_global_zero_taxon_remains_boundary_and_zero_likelihood_terms_are_defined() -> (
    None
):
    result = producer.compare_group(group([[3, 0], [5, 0]]), [[2, 1], [7, 2]])
    assert result["common_cover_fit"]["cover"] == [1, 0]
    assert result["common_cover_fit"]["multinomial_deviance"] == 0


def test_nonconverged_cover_and_any_improvement_claim_are_withheld() -> None:
    def limited(*args: Any, **kwargs: Any) -> Any:
        kwargs["max_steps"] = 0
        return fit_multisite_likelihood(*args, **kwargs)

    result = producer.compare_group(group(), [[9, 1], [1, 1]], limited)
    assert result["status"] == "nonconverged"
    assert result["solver"]["converged"] is False
    assert result["common_cover_fit"] is None
    assert result["baseline_minus_fitted_negative_log_likelihood"] is None
    assert result["geometry_correct_then_pool"]["cover"] is not None
    assert "cover" not in result["solver"]


def test_saturated_information_refusal_also_withholds_apparently_stationary_cover() -> (
    None
):
    result = producer.compare_group(
        group([[2, 0], [0, 1]]), [[1e100, 1e-100], [1e-100, 1e100]]
    )
    assert result["status"] == "nonconverged"
    assert result["solver"]["stop_reason"] == "floating_information_unresolved"
    assert result["common_cover_fit"] is None
    assert result["baseline_minus_fitted_negative_log_likelihood"] is None


@pytest.mark.parametrize("defect", ["missing", "fractional", "bool", "response"])
def test_unmeasured_and_invalid_counts_or_responses_refuse(defect: str) -> None:
    value = group()
    responses = [[9.0, 1.0], [1.0, 1.0]]
    if defect == "missing":
        value["sites"][0]["taxon_measured"][0] = False
    elif defect == "fractional":
        value["sites"][0]["projected_counts"][0] = 0.5
    elif defect == "bool":
        value["sites"][0]["projected_counts"][0] = True
    else:
        responses[0][0] = 0
    with pytest.raises(ValidationError):
        producer.compare_group(value, responses)


def test_refused_fatal_and_not_run_populations_are_retained() -> None:
    loaded = {
        "cores": [{"response_PPE_times_K": r} for r in [[9, 1], [1, 1]]],
        "groups": [group() for _ in range(4)],
    }
    calls = 0

    def mixed(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValidationError("Unresolved measured cells")
        if calls == 3:
            raise RuntimeError("Unexpected execution failure")
        return fit_multisite_likelihood(*args, **kwargs)

    rows = producer.evaluate(loaded, mixed)
    assert [r["status"] for r in rows] == ["computed", "refused", "fatal", "not_run"]
    assert all(r["common_cover_fit"] is None for r in rows[1:])


def checksum(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def native_fixture(
    *, include_fraxinus: bool = True
) -> tuple[dict[str, Any], dict[str, Any], Core]:
    axis = ("Betula", "Fraxinus", "Ulmus") if include_fraxinus else ("Betula", "Ulmus")
    name = "BOKE" if include_fraxinus else "BUS"
    model = {
        "modelagetype": "Calibrated radiocarbon years BP",
        "notes": "Synthetic dated source",
    }
    samples = []
    counts = (
        [[2, 3, 1], [4, 0, 2], [7, 3, 1]]
        if include_fraxinus
        else [[2, 1], [4, 2], [7, 1]]
    )
    for index, (age, values) in enumerate(zip([10, 100, -5], counts, strict=True)):
        samples.append(
            {
                "sampleid": index + 1,
                "analysisunitid": index + 100,
                "depth": index,
                "ages": [
                    {
                        "chronologyid": 42,
                        "agetype": "Calibrated radiocarbon years BP",
                        "age": age,
                        "ageolder": None,
                        "ageyounger": None,
                    }
                ],
                "datum": [
                    {
                        "element": "pollen",
                        "elementtype": "pollen",
                        "units": "NISP",
                        "variablename": name,
                        "taxonid": taxon,
                        "value": value,
                    }
                    for taxon, (name, value) in enumerate(
                        zip([*axis, "Pinus"], [*values, 7], strict=True)
                    )
                ],
            }
        )
    native = {
        "site": {
            "siteid": 1,
            "collectionunit": {
                "collectionunitid": 2,
                "handle": name,
                "defaultchronology": 42,
                "chronologies": [
                    {
                        "chronology": {
                            "chronologyid": 42,
                            "chronology": model,
                            "chroncontrols": [],
                        }
                    }
                ],
                "dataset": {"datasetid": 3, "samples": samples},
            },
        }
    }
    results, cells = [], []
    for index, bounds in enumerate([(0.0, 100.0), (100.0, 350.0)]):
        sample = samples[index]
        support = [
            {
                "sample_id": index + 1,
                "analysis_unit_id": index + 100,
                "depth": index,
                "ages": sample["ages"],
                "datum_rows": [
                    {"ordinal": i, "taxon_id": i, "name": name, "count": value}
                    for i, (name, value) in enumerate(
                        zip([*axis, "Pinus"], [*counts[index], 7], strict=True)
                    )
                ],
            }
        ]
        identity = checksum(support)
        cells.append(Cell(bounds, tuple(counts[index]), identity))
        results.append(
            {
                "profile": "metadata_radius_wind_3",
                "younger_cal_bp": bounds[0],
                "older_cal_bp_exclusive": bounds[1],
                "native_sample_count": 1,
                "raw_age_bounds_missing": 1,
                "reported_all_pollen_NISP_sum": sum(counts[index]) + 7,
            }
        )
    saved = {
        "chronology_id": 42,
        "selected_chronology": {
            "model": model,
            "raw_control_count": 0,
            "raw_control_sha256": checksum([]),
        },
        "source_default_chronology": 42,
        "source_dataset": {"datasetid": 3},
        "native_sample_count": 3,
        "included_sample_count": 2,
        "occupied_window_count": 2,
        "exclusions_by_reason": {"point_age_outside_declared_windows": 1},
        "local_native_exclusions_sha256": checksum(
            [{"sample_id": 3, "reason": "point_age_outside_declared_windows"}]
        ),
        "results": results,
    }
    core = Core(
        name,
        "SE",
        1,
        3,
        2,
        axis,
        tuple(float(i + 2) for i in range(len(axis))),
        (0.1,) * len(axis),
        (0.5,) * len(axis),
        tuple(cells),
    )
    return native, saved, core


def test_native_projection_conserves_original_and_all_pollen_denominators() -> None:
    native, saved, core = native_fixture()
    rows = cohort.project_core(native, saved, core, [0, 100, 350])
    assert rows[0]["original_counts"] == [2, 3, 1]
    assert rows[0]["projected_counts"] == [2, 1]
    assert rows[0]["original_panel_N"] == 6
    assert rows[0]["projected_panel_N"] == 3
    assert rows[0]["Fraxinus_original_panel_count"] == 3
    assert rows[0]["reported_all_pollen_NISP_N"] == 13
    assert rows[0]["outside_original_panel_N"] == 7
    assert rows[0]["outside_projected_panel_N"] == 10
    assert rows[1]["sample_ids"] == [
        2
    ]  # Point exactly100 enters the second half-open window.
    assert rows[1]["Fraxinus_original_panel_count"] == 0
    assert rows[0]["raw_age_bounds_missing"] == 1


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "units",
        "fractional",
        "chronology",
        "support",
        "duplicate",
        "denominator",
        "bounds",
        "site",
    ],
)
def test_native_projection_refuses_changed_source_meaning(defect: str) -> None:
    native, saved, core = native_fixture()
    samples = native["site"]["collectionunit"]["dataset"]["samples"]
    if defect == "missing":
        samples[0]["datum"].pop(2)
    elif defect == "units":
        samples[0]["datum"][0]["units"] = "percent"
    elif defect == "fractional":
        samples[0]["datum"][0]["value"] = 0.5
    elif defect == "chronology":
        samples[0]["ages"][0]["chronologyid"] = 43
    elif defect == "support":
        core = replace(
            core,
            cells=(
                replace(core.cells[0], source_support_sha256="0" * 64),
                core.cells[1],
            ),
        )
    elif defect == "duplicate":
        samples[1]["sampleid"] = 1
    elif defect == "denominator":
        saved["results"][0]["reported_all_pollen_NISP_sum"] += 1
    elif defect == "bounds":
        samples[0]["ages"][0]["ageolder"] = 20
    else:
        native["site"]["siteid"] = 7
    with pytest.raises(ValueError):
        cohort.project_core(native, saved, core, [0, 100, 350])


def test_taxon_outside_original_panel_is_null_instead_of_zero() -> None:
    native, saved, core = native_fixture(include_fraxinus=False)
    rows = cohort.project_core(native, saved, core, [0, 100, 350])
    assert rows[0]["original_axis"] == ["Betula", "Ulmus"]
    assert rows[0]["original_panel_N"] == rows[0]["projected_panel_N"] == 3
    assert rows[0]["Fraxinus_original_panel_count"] is None
    assert rows[0]["discarded_original_panel_counts"] == {}
    assert rows[0]["outside_projected_panel_N"] == 7
