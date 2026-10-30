"""Analytical panel factorization, missingness and actual consumer boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    cohort,
    counting,
)
from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    measured_panels as panels,
)
from bijux_pollenomics_lra.models.errors import ValidationError

RESPONSES = [[2.0, 1.0], [1.0, 1.0]]


def group(r: float = 0.5, fraxinus: int = 6) -> dict[str, Any]:
    counts = [[2, fraxinus, 1], [4, 4]]
    probabilities = [[2 * r / (1 + r), (1 - r) / (1 + r)], [r, 1 - r]]
    projected = [[2, 1], [4, 4]]
    nll = -math.fsum(
        n * math.log(p)
        for row, probs in zip(projected, probabilities, strict=True)
        for n, p in zip(row, probs, strict=True)
    )
    saturated = -math.fsum(n * math.log(n / sum(row)) for row in projected for n in row)
    return {
        "window_cal_bp": [0, 100],
        "status": "computed",
        "solver": {"converged": True},
        "common_cover_fit": {
            "cover": [r, 1 - r],
            "negative_log_likelihood_without_combinatorial_constant": nll,
            "multinomial_deviance": 2 * (nll - saturated),
        },
        "sites": [
            {
                "core": name,
                "original_axis": axis,
                "original_counts": row,
                "original_panel_N": sum(row),
                "projected_counts": projection,
                "projected_panel_N": sum(projection),
                "Fraxinus_original_panel_count": fraxinus if name == "BOKE" else None,
                "taxon_measured": [True, True],
            }
            for name, axis, row, projection in zip(
                ["BOKE", "BUS"],
                [panels.AXIS, ["Betula", "Ulmus"]],
                counts,
                projected,
                strict=True,
            )
        ],
    }


def test_known_three_taxon_completion_keeps_missing_bus_cell_and_effort() -> None:
    result = panels.complete_panel(group(), RESPONSES, 3.0)
    assert result["common_relative_cover"] == [0.25, 0.5, 0.25]
    assert result["BOKE_predicted_measured_panel"] == [2 / 9, 6 / 9, 1 / 9]
    assert result["BUS_predicted_measured_panel_on_common_axis"] == [0.5, None, 0.5]
    assert result["taxon_measured_on_common_axis"] == [
        [True, True, True],
        [True, False, True],
    ]
    assert result["full_measured_grains"] == 17
    assert result["original_projected_grains"] == 11
    assert result["retained_Fraxinus_grains"] == 6
    assert (
        result["mean_negative_log_likelihood_per_full_measured_grain"]
        == result["negative_log_likelihood_without_combinatorial_constant"] / 17
    )


@pytest.mark.parametrize("first", [False, True])
def test_original_single_active_bu_taxon_retains_exact_boundary(first: bool) -> None:
    source = group()
    source["common_cover_fit"].update(
        cover=[1.0, 0.0] if first else [0.0, 1.0],
        negative_log_likelihood_without_combinatorial_constant=0.0,
        multinomial_deviance=0.0,
    )
    for site in source["sites"]:
        measured = [3, 0] if first else [0, 3]
        site.update(projected_counts=measured, projected_panel_N=3)
        if site["core"] == "BOKE":
            site.update(
                original_counts=[measured[0], 6, measured[1]], original_panel_N=9
            )
        else:
            site.update(original_counts=measured, original_panel_N=3)
    result = panels.complete_panel(source, RESPONSES, 3.0)
    assert result["common_relative_cover"][2 if first else 0] == 0.0
    assert result["multinomial_deviance"] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("r", [0.2, 0.5, 0.8])
@pytest.mark.parametrize("nf", [0, 1, 100])
def test_full_profile_changes_only_the_saturated_fraxinus_factor(
    r: float, nf: int
) -> None:
    source = group(r, nf)
    before = deepcopy(source)
    result = panels.complete_panel(source, RESPONSES, 3.0)
    assert source == before
    assert result["multinomial_deviance"] == pytest.approx(
        source["common_cover_fit"]["multinomial_deviance"], abs=1e-12
    )
    assert result[
        "negative_log_likelihood_without_combinatorial_constant"
    ] == pytest.approx(
        result["original_projected_negative_log_likelihood"]
        + result["profiled_Fraxinus_binomial_negative_log_likelihood"],
        abs=1e-12,
    )
    cover = result["common_relative_cover"]
    assert cover[0] / (cover[0] + cover[2]) == pytest.approx(r, abs=1e-15)
    if nf == 0:
        assert cover[1] == 0
        assert result["BOKE_predicted_measured_panel"][1] == 0
        assert result["profiled_Fraxinus_binomial_negative_log_likelihood"] == 0


@pytest.mark.parametrize(
    "defect",
    [
        "nonconverged",
        "missing_panel",
        "mask_bool",
        "counts_missing",
        "counts_bool",
        "fractional",
        "no_bu",
        "axis",
        "conservation",
        "fit_nll",
        "fit_deviance",
        "cover",
        "bus_f_measured",
    ],
)
def test_source_and_numerical_domain_defects_refuse(defect: str) -> None:
    source = group()
    boke, bus = source["sites"]
    if defect == "nonconverged":
        source["solver"]["converged"] = False
    elif defect == "missing_panel":
        bus["taxon_measured"][0] = False
    elif defect == "mask_bool":
        bus["taxon_measured"][0] = 1
    elif defect == "counts_missing":
        boke["original_counts"][1] = None
    elif defect == "counts_bool":
        boke["original_counts"][1] = True
    elif defect == "fractional":
        boke["original_counts"][1] = 1.5
    elif defect == "no_bu":
        boke["original_counts"] = [0, 6, 0]
    elif defect == "axis":
        boke["original_axis"] = ["Betula", "Ulmus", "Fraxinus"]
    elif defect == "conservation":
        boke["projected_panel_N"] += 1
    elif defect == "fit_nll":
        source["common_cover_fit"][
            "negative_log_likelihood_without_combinatorial_constant"
        ] += 1
    elif defect == "fit_deviance":
        source["common_cover_fit"]["multinomial_deviance"] += 1
    elif defect == "cover":
        source["common_cover_fit"]["cover"] = [True, 0.0]
    else:
        bus["Fraxinus_original_panel_count"] = 0
    with pytest.raises(ValidationError):
        panels.complete_panel(source, RESPONSES, 3.0)


@pytest.mark.parametrize(
    "response", [0.0, -1.0, float("nan"), float("inf"), None, True, 10**1000]
)
def test_invalid_fraxinus_response_refuses(response: Any) -> None:
    with pytest.raises(ValidationError):
        panels.complete_panel(group(), RESPONSES, response)


def source_fixture(tmp_path: Path) -> dict[str, Any]:
    saved = {
        "cores": [
            {
                "metadata_code": "BOKE",
                "parameter_taxa": panels.AXIS,
                "ppe": [2.0, 3.0, 1.0],
                "ppe_standard_deviation": [0.1, 0.2, 0.3],
                "fall_speed_m_s": [0.02, 0.03, 0.04],
                "quadrature": [
                    {
                        "profile": "metadata_radius_wind_3",
                        "factors": [[1.0, 1.0, 1.0]],
                        "rigorous_error_bound": False,
                    }
                ],
            }
        ]
    }
    csv = b"Plant taxa/Pollen-morphological types,PPE (SD),FSP (m/s)\nFraxinus,3.0 (0.2),0.03\n"
    pins = []
    for relative, raw in [
        (panels.SWEDISH_REPORT, json.dumps(saved).encode()),
        (cohort.PARAMETERS, csv),
    ]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        pins.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )
    return {
        "cores": [
            {
                "core": "BOKE",
                "ppe": [2.0, 1.0],
                "saved_K": [1.0, 1.0],
                "response_PPE_times_K": RESPONSES[0],
            },
            {"core": "BUS", "response_PPE_times_K": RESPONSES[1]},
        ],
        "scientific_inputs": pins,
        "groups": [
            {**group(), "window_cal_bp": [i * 100, (i + 1) * 100]} for i in range(13)
        ],
        "age_unit": "calibrated years BP, AD1950 reference",
        "original_source_epochs": {"swedish": "saved-original"},
        "unmatched": [{"core": "BUS"} for _ in range(6)],
        "limits": ["Original rights and chronology limits"],
    }


@pytest.mark.parametrize(
    "defect",
    [None, "raw", "literal_parameter", "duplicate_pin", "axis", "projected_response"],
)
def test_original_parameter_binding_has_no_new_source_identity(
    tmp_path: Path, defect: str | None
) -> None:
    point = source_fixture(tmp_path)
    if defect == "raw":
        (tmp_path / panels.SWEDISH_REPORT).write_bytes(b"changed")
    elif defect == "literal_parameter":
        path = tmp_path / cohort.PARAMETERS
        raw = path.read_bytes().replace(b"3.0 (0.2)", b"4.0 (0.2)")
        path.write_bytes(raw)
        point["scientific_inputs"][1].update(
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
        )
    elif defect == "duplicate_pin":
        point["scientific_inputs"].append(point["scientific_inputs"][0])
    elif defect == "axis":
        path = tmp_path / panels.SWEDISH_REPORT
        value = json.loads(path.read_bytes())
        value["cores"][0]["parameter_taxa"].reverse()
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        point["scientific_inputs"][0].update(
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
        )
    elif defect == "projected_response":
        point["cores"][0]["saved_K"][0] = 0.5
    if defect:
        with pytest.raises(ValueError):
            panels.read_response(tmp_path, point)
    else:
        response = panels.read_response(tmp_path, point)
        assert response["response_PPE_times_K"] == [2.0, 3.0, 1.0]
        assert response["source_report"] == panels.SWEDISH_REPORT
        assert response["saved_quadrature"]["rigorous_error_bound"] is False


@pytest.mark.parametrize(
    "change", [None, "raw", "point_epoch", "consumer_epoch", "refusal"]
)
def test_actual_main_preserves_epochs_raw_integrity_and_terminal_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str | None
) -> None:
    point = source_fixture(tmp_path)
    if change == "refusal":
        point["groups"][1]["solver"]["converged"] = False
    identity = {
        "path": counting.POINT_REPORT,
        "publication_commit": "1" * 40,
        "point_source_commit": "2" * 40,
    }
    count = 0

    def read_point(repository: Path) -> tuple[dict[str, Any], dict[str, str]]:
        nonlocal count
        assert repository == tmp_path
        count += 1
        return point, (
            {**identity, "publication_commit": "4" * 40}
            if change == "point_epoch" and count > 1
            else identity
        )

    monkeypatch.setattr(counting, "read_point_report", read_point)
    admissions = []

    def authenticate(repository: Path, observed: dict[str, Any]) -> None:
        assert repository == tmp_path and observed is point
        admissions.append(True)

    monkeypatch.setattr(counting, "authenticate_inputs", authenticate)
    revisions = iter(["3" * 40, "4" * 40 if change == "consumer_epoch" else "3" * 40])
    monkeypatch.setattr(panels, "_revision", lambda repository: next(revisions))
    original = panels.read_response

    def response(repository: Path, observed: dict[str, Any]) -> dict[str, Any]:
        result = original(repository, observed)
        if change == "raw":
            (tmp_path / cohort.PARAMETERS).write_bytes(b"changed")
        return result

    monkeypatch.setattr(panels, "read_response", response)
    output = tmp_path / "artifacts" / "measured-panels.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["measured-panels", "--repository", str(tmp_path), "--output", str(output)],
    )
    if change in {"raw", "point_epoch", "consumer_epoch"}:
        with pytest.raises(ValueError):
            panels.main()
        assert not output.exists()
    else:
        with pytest.raises(SystemExit) as terminal:
            panels.main()
        assert terminal.value.code == 0
        report = json.loads(output.read_bytes())
        assert report["source_commit"] == "3" * 40
        assert report["point_report"] == identity
        assert (
            report["new_optimizer_runs"]
            == report["new_kernel_evaluations"]
            == report["new_count_tail_evaluations"]
            == 0
        )
        assert report["three_taxon_uncertainty_evaluated"] is False
        assert (
            report["reused_B_U_point_fits"]
            == report["analytic_profile_completions"]
            == (12 if change == "refusal" else 13)
        )
        assert (
            report["groups"][0]["BUS_predicted_measured_panel_on_common_axis"][1]
            is None
        )
        assert report["original_point_limits"] == point["limits"]
        assert report["status_counts"] == (
            {"computed": 12, "refused": 1} if change == "refusal" else {"computed": 13}
        )
        assert len(report["unmatched"]) == 6
        assert output.stat().st_size <= 1024**2
    assert admissions == [True]


def test_consumed_source_alias_refuses(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside canonical source"):
        panels._revision(tmp_path)
