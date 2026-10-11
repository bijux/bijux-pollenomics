"""Derive bounded reader summaries from saved aggregate numerical output."""

from __future__ import annotations

from collections.abc import Mapping
import math
from typing import TypedDict


class ChronologyTotals(TypedDict):
    """Keep mapped and residual pollen denominators independently visible."""

    mapped_pollen_NISP: int
    residual_pollen_NISP: int
    reported_pollen_NISP: int
    accepted_samples: int
    occupied_windows: int


class ParameterSummary(TypedDict):
    """Describe the derived maximal change and conserved chronology totals."""

    parameter_profile: str
    parameter_taxa: list[str]
    chronology_totals: dict[str, ChronologyTotals]
    changed_count_windows: int
    occupied_window_union: int
    largest_absolute_cover_change: float
    signed_cover_change: float
    taxon_at_maximum: str
    window_at_maximum_cal_bp: list[float]


def _record(value: object) -> dict[str, object]:
    """Require a captured object while retaining every original comparison field."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("captured source record must be an object")
    return value


def _records(value: object) -> list[dict[str, object]]:
    """Admit captured records independently without discarding extra source fields."""
    if not isinstance(value, list):
        raise ValueError("captured source record population must be an array")
    return [_record(row) for row in value]


def _token(value: object) -> str:
    """Keep source profile identifiers and taxon labels literal."""
    if not isinstance(value, str):
        raise ValueError("captured source profile or taxon token differs")
    return value


def _tokens(value: object) -> list[str]:
    """Admit the captured literal taxon axis before using it as an index."""
    if not isinstance(value, list):
        raise ValueError("captured case axis differs")
    return [_token(token) for token in value]


def _integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("captured count must be a nonnegative integer")
    return value


def _vector(value: object, size: int) -> list[float]:
    if not isinstance(value, list) or len(value) != size:
        raise ValueError("captured flat taxon axis differs")
    admitted: list[float] = []
    for cell in value:
        if (
            not isinstance(cell, (int, float))
            or type(cell) not in (int, float)
            or not math.isfinite(cell)
        ):
            raise ValueError("captured numerical axis is not finite")
        admitted.append(cell)
    return admitted


def _window(row: Mapping[str, object], size: int) -> tuple[float, float]:
    lower = row["younger_cal_bp"]
    upper = row["older_cal_bp_exclusive"]
    if (
        not isinstance(lower, (int, float))
        or not isinstance(upper, (int, float))
        or type(lower) not in (int, float)
        or type(upper) not in (int, float)
    ):
        raise ValueError("captured window axis is not numerical")
    if not math.isfinite(lower) or not math.isfinite(upper) or not 0 <= lower < upper:
        raise ValueError("captured window bounds differ")
    count_rows = row["hypothesized_panel_counts"]
    if not isinstance(count_rows, list) or len(count_rows) != 1:
        raise ValueError("captured single-core count matrix shape differs")
    counts = _vector(count_rows[0], size)
    if sum(_integer(count) for count in counts) != _integer(row["panel_NISP_sum"]):
        raise ValueError("captured panel denominator differs")
    if not row["panel_NISP_sum"]:
        raise ValueError("captured occupied window has zero panel mass")
    if _integer(row["panel_NISP_sum"]) + _integer(
        row["unparameterized_reported_NISP_sum"]
    ) != _integer(row["reported_all_pollen_NISP_sum"]):
        raise ValueError("captured mapped and residual counts do not conserve NISP")
    samples = _integer(row["native_sample_count"])
    if not samples or _integer(row["source_age_bounds_missing"]) != samples:
        raise ValueError("captured missing age-bound population differs")
    for key in (
        "actual_explicit_zero_rows",
        "assumed_zero_parameter_cells",
        "assumed_zero_source_cells",
    ):
        _integer(row[key])
    presence = _vector(row["actual_source_target_presence_counts"], size)
    if any(_integer(cell) > samples for cell in presence):
        raise ValueError("captured source-presence population differs")
    cover = _vector(row["conditional_cover"], size)
    errors = _vector(row["conditional_standard_error"], size)
    if any(cell < 0 or cell > 1 for cell in cover) or abs(math.fsum(cover) - 1) > 1e-12:
        raise ValueError("captured conditional cover does not close")
    if any(cell < 0 for cell in errors):
        raise ValueError("captured conditional error is negative")
    matrices = {}
    for key, matrix in (
        ("counting_covariance", row["counting_covariance"]),
        ("assumed_ppe_covariance", row["assumed_ppe_covariance"]),
        ("total_conditional_covariance", row["total_conditional_covariance"]),
    ):
        if not isinstance(matrix, list) or len(matrix) != size:
            raise ValueError("captured covariance shape differs")
        matrices[key] = [_vector(axis, size) for axis in matrix]
    for i in range(size):
        for j in range(size):
            total = matrices["total_conditional_covariance"][i][j]
            if not math.isclose(
                total,
                matrices["counting_covariance"][i][j]
                + matrices["assumed_ppe_covariance"][i][j],
                abs_tol=1e-12,
                rel_tol=1e-12,
            ):
                raise ValueError("captured covariance components differ")
            if not math.isclose(
                total,
                matrices["total_conditional_covariance"][j][i],
                abs_tol=1e-12,
                rel_tol=1e-12,
            ):
                raise ValueError("captured covariance symmetry differs")
        if not math.isclose(
            errors[i] ** 2,
            matrices["total_conditional_covariance"][i][i],
            abs_tol=1e-12,
            rel_tol=1e-12,
        ):
            raise ValueError("captured standard error and variance differ")
    return lower, upper


def summarize(
    report: Mapping[str, object], diagnostic: Mapping[str, object]
) -> dict[str, object]:
    """Inspect saved structure and derive changes; execute no physical model."""
    profiles = ("native_default_calibrated_points", "published_TP_depth_matched_points")
    if (
        report["native_sample_population"] != 45
        or report["exact_native_baseline_windows_verified"] != 92
    ):
        raise ValueError("captured baseline population differs")
    cases = {}
    for case in _records(report["cases"]):
        key = _token(case["parameter_profile"]), _token(case["chronology_profile"])
        taxa = _tokens(case["parameter_taxa"])
        if (
            key in cases
            or key[1] not in profiles
            or not isinstance(taxa, list)
            or not taxa
            or len(set(taxa)) != len(taxa)
        ):
            raise ValueError("captured case axis differs")
        if (
            case["accepted_samples"] != 45
            or case["excluded_samples"] != {}
            or case["occupied_windows"] != 23
        ):
            raise ValueError("captured sample and occupied-window population differs")
        if (
            case["source_measurement_complete_claimed"]
            or case["point_boundaries_known"]
            or not case["conditional_panel_N_not_total_NISP"]
        ):
            raise ValueError("captured conditional source scope differs")
        for name in ("parameter_ppe", "parameter_sd"):
            axis = _vector(case[name], len(taxa))
            if any(
                cell < 0 or (name == "parameter_ppe" and cell == 0) for cell in axis
            ):
                raise ValueError("captured parameter axis differs")
        windows = {}
        for row in _records(case["results"]):
            window = _window(row, len(taxa))
            if window in windows:
                raise ValueError("captured occupied-window axis duplicates")
            windows[window] = row
        if (
            len(windows) != 23
            or sum(_integer(row["native_sample_count"]) for row in windows.values())
            != 45
        ):
            raise ValueError("captured emitted-window population differs")
        if (
            sum(
                _integer(row["reported_all_pollen_NISP_sum"])
                for row in windows.values()
            )
            != 43851
        ):
            raise ValueError("captured reported pollen denominator differs")
        cases[key] = (taxa, windows)
    parameter_profiles = sorted({key[0] for key in cases})
    if (
        len(cases) != 8
        or len(parameter_profiles) != 4
        or set(cases)
        != {(name, profile) for name in parameter_profiles for profile in profiles}
    ):
        raise ValueError("captured complete case population differs")
    summaries: list[ParameterSummary] = []
    comparison_profiles = set()
    for comparison in _records(report["chronology_comparisons"]):
        name = _token(comparison["parameter_profile"])
        if name in comparison_profiles or name not in parameter_profiles:
            raise ValueError("captured comparison axis differs")
        comparison_profiles.add(name)
        taxa, native = cases[name, profiles[0]]
        other_taxa, alternative = cases[name, profiles[1]]
        if taxa != other_taxa or taxa != comparison["parameter_taxa"]:
            raise ValueError("captured comparison taxon axis differs")
        union = sorted(set(native) | set(alternative))
        seen = set()
        changes: list[tuple[float, float, str, tuple[float, float]]] = []
        for pair in _records(comparison["windows"]):
            bounds = _vector(pair["window_cal_bp"], 2)
            if len(bounds) != 2:
                raise ValueError("captured comparison union or source row differs")
            window = bounds[0], bounds[1]
            if (
                window in seen
                or window not in union
                or pair["native"] != native.get(window)
                or pair["alternative"] != alternative.get(window)
                or pair["missing_window_is_not_zero_cover"] is not True
            ):
                raise ValueError("captured comparison union or source row differs")
            seen.add(window)
            if pair["native"] is None or pair["alternative"] is None:
                if pair["cover_alternative_minus_native"] is not None:
                    raise ValueError("missing window substituted by zero")
                continue
            delta = [
                right - left
                for left, right in zip(
                    _vector(_record(pair["native"])["conditional_cover"], len(taxa)),
                    _vector(
                        _record(pair["alternative"])["conditional_cover"], len(taxa)
                    ),
                    strict=True,
                )
            ]
            if delta != pair["cover_alternative_minus_native"]:
                raise ValueError("captured cover difference differs")
            changes.extend(
                (abs(value), value, taxa[i], window) for i, value in enumerate(delta)
            )
        if seen != set(union):
            raise ValueError("captured comparison union is incomplete")
        maximum = max(changes, key=lambda row: row[0])
        changed = sum(
            native[window]["hypothesized_panel_counts"]
            != alternative[window]["hypothesized_panel_counts"]
            for window in set(native) & set(alternative)
        )
        if changed != 16 or len(union) != 23:
            raise ValueError("captured chronology count-window population differs")
        totals: dict[str, ChronologyTotals] = {
            profile: {
                "mapped_pollen_NISP": sum(
                    _integer(row["panel_NISP_sum"])
                    for row in cases[name, profile][1].values()
                ),
                "residual_pollen_NISP": sum(
                    _integer(row["unparameterized_reported_NISP_sum"])
                    for row in cases[name, profile][1].values()
                ),
                "reported_pollen_NISP": 43851,
                "accepted_samples": 45,
                "occupied_windows": 23,
            }
            for profile in profiles
        }
        summaries.append(
            {
                "parameter_profile": name,
                "parameter_taxa": taxa,
                "chronology_totals": totals,
                "changed_count_windows": changed,
                "occupied_window_union": len(union),
                "largest_absolute_cover_change": maximum[0],
                "signed_cover_change": maximum[1],
                "taxon_at_maximum": maximum[2],
                "window_at_maximum_cal_bp": list(maximum[3]),
            }
        )
    if comparison_profiles != set(parameter_profiles):
        raise ValueError("captured comparison profiles incomplete")
    if (
        diagnostic["native_sample_population"] != 45
        or diagnostic["native_baseline_windows_exact"] != 92
        or diagnostic["total_saved_case_windows"] != 184
        or diagnostic["point_samples_moved_between_windows"] != 12
    ):
        raise ValueError("captured source-point diagnostic population differs")
    diagnostic_rows = {
        _token(row["parameter_profile"]): row
        for row in _records(diagnostic["parameter_summaries"])
    }
    if (
        len(diagnostic_rows) != 4
        or len(_records(diagnostic["parameter_summaries"])) != 4
    ):
        raise ValueError("captured diagnostic parameter profiles differ")
    for derived in summaries:
        recorded = diagnostic_rows.get(derived["parameter_profile"])
        if recorded is None or (
            derived["changed_count_windows"] != recorded["changed_count_windows"]
            or derived["occupied_window_union"]
            != recorded["occupied_window_union_count"]
            or derived["largest_absolute_cover_change"]
            != recorded["largest_absolute_conditional_cover_change"]
            or derived["signed_cover_change"]
            != recorded["signed_conditional_cover_change"]
            or derived["taxon_at_maximum"] != recorded["taxon_of_largest_change"]
            or derived["window_at_maximum_cal_bp"]
            != recorded["window_of_largest_change_cal_BP"]
            or recorded["native_only_windows"] != 0
            or recorded["alternative_only_windows"] != 0
        ):
            raise ValueError("derived saved-output summary differs from diagnostic")
        if len(_records(recorded["profiles"])) != 2:
            raise ValueError("captured diagnostic chronology profiles differ")
        for diagnostic_profile in _records(recorded["profiles"]):
            recorded_totals = derived["chronology_totals"].get(
                _token(diagnostic_profile["chronology"])
            )
            if (
                recorded_totals is None
                or diagnostic_profile["excluded_samples"] != {}
                or recorded_totals
                != {
                    "mapped_pollen_NISP": diagnostic_profile["mapped_NISP"],
                    "residual_pollen_NISP": diagnostic_profile["residual_NISP"],
                    "reported_pollen_NISP": diagnostic_profile["reported_NISP"],
                    "accepted_samples": diagnostic_profile["accepted_samples"],
                    "occupied_windows": diagnostic_profile["occupied_windows"],
                }
            ):
                raise ValueError(
                    "derived chronology denominators differ from diagnostic"
                )
    return {
        "schema_version": "tibetanus-retained-point-sensitivity-summary.v1",
        "scope": "Derived summary of saved aggregate output; no fresh model, source acquisition or chronology fit.",
        "native_sample_population": 45,
        "case_count": 8,
        "saved_case_window_rows_inspected": 184,
        "original_native_baseline_windows": 92,
        "source_point_bin_moves_from_retained_diagnostic": 12,
        "source_point_diagnostic_authority": "Foreground source-bound inspection; no native supervised custody or independent numerical oracle claimed.",
        "parameter_summaries": sorted(
            summaries, key=lambda row: row["parameter_profile"]
        ),
        "chronology_bounds_known": False,
        "historical_reproduction_claim": False,
        "chronology_accuracy_claim": False,
        "ecological_accuracy_claim": False,
        "raw_source_rights_admitted": False,
        "full_possible_time_domain_census": False,
    }
