"""Generate an independent, deterministic known-landscape validation oracle.

The simulator deliberately uses a small finite-cell inverse-square deposition
equation implemented here with the Python standard library.  It does not import
the production LRA engine, its forward preparation, its kernels, or its inverse
methods.  The product is therefore suitable as an external synthetic challenge,
but it is not evidence about real vegetation, calibrated uncertainty, or
scientific acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import cos, hypot, isclose, sin, sqrt
from typing import cast

JsonObject = dict[str, object]

KNOWN_LANDSCAPE_PROFILE = "independent-finite-cell-known-landscape-v1"
_RNG_PROFILE = "lcg64-fixed-multiplier-top53-v1"
_MASK_64 = (1 << 64) - 1
_TAXA = ("broadleaf", "conifer", "open_land")
_PPE = {"broadleaf": 2.4, "conifer": 1.2, "open_land": 0.8}
_FALL_SPEED = {"broadleaf": 0.025, "conifer": 0.031, "open_land": 0.018}
_OFFSETS = (
    (0.0, 0.0, 1.0),
    (-0.35, -0.35, 0.8),
    (-0.35, 0.35, 1.1),
    (0.35, -0.35, 0.9),
    (0.35, 0.35, 1.2),
    (-0.70, 0.0, 1.0),
    (0.70, 0.0, 1.0),
    (0.0, -0.70, 0.95),
    (0.0, 0.70, 1.05),
)


class KnownLandscapeError(ValueError):
    """A stable refusal from the independent synthetic oracle."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class KnownLandscapeReport:
    """Canonical, content-addressed output of the known-landscape suite."""

    canonical_bytes: bytes

    def payload(self) -> JsonObject:
        """Return a defensive JSON-object copy."""
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):  # pragma: no cover - constructor invariant
            raise KnownLandscapeError("invalid_report", "report is not a JSON object")
        return cast(JsonObject, value)

    @property
    def sha256(self) -> str:
        """Return the SHA-256 identity of the canonical report bytes."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class _Cell:
    cell_id: str
    x_m: float
    y_m: float
    area_m2: float
    cover: tuple[float, float, float]


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _closed(values: tuple[float, ...], *, name: str) -> tuple[float, ...]:
    if not values or any(value < 0 for value in values):
        raise KnownLandscapeError("invalid_composition", name)
    total = sum(values)
    if total <= 0:
        raise KnownLandscapeError("zero_composition", name)
    result = tuple(value / total for value in values)
    if not isclose(sum(result), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise KnownLandscapeError("unclosed_composition", name)
    return result


def _cover(kind: str, x_m: float, y_m: float) -> tuple[float, float, float]:
    if kind == "homogeneous":
        return (0.55, 0.30, 0.15)
    if kind != "heterogeneous":
        raise KnownLandscapeError("unsupported_landscape", kind)
    x_km, y_km = x_m / 1000.0, y_m / 1000.0
    raw = (
        1.20 + 0.34 * sin(x_km / 3.7) + 0.13 * cos(y_km / 2.9),
        0.90 + 0.23 * cos((x_km - y_km) / 4.1),
        0.55 + 0.19 * sin((x_km + y_km) / 3.3),
    )
    if any(value <= 0 for value in raw):  # pragma: no cover - bounded grid invariant
        raise KnownLandscapeError("invalid_landscape_surface", kind)
    closed = _closed(raw, name=kind)
    return closed[0], closed[1], closed[2]


def _cells(kind: str, extent_m: float) -> tuple[_Cell, ...]:
    if extent_m <= 0:
        raise KnownLandscapeError("invalid_support", "extent must be positive")
    cells = []
    base_area = 1_000_000.0
    for index, (x_scale, y_scale, area_scale) in enumerate(_OFFSETS):
        x_m, y_m = x_scale * extent_m, y_scale * extent_m
        cells.append(
            _Cell(
                f"cell-{index:02d}",
                x_m,
                y_m,
                base_area * area_scale,
                _cover(kind, x_m, y_m),
            )
        )
    return tuple(cells)


def _simulate(
    kind: str,
    *,
    extent_m: float,
    declared_support_m: float,
    basin_radius_m: float,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[_Cell, ...]]:
    if declared_support_m <= 0 or basin_radius_m <= 0:
        raise KnownLandscapeError(
            "invalid_support", "support and basin radius must be positive"
        )
    cells = _cells(kind, extent_m)
    if max(hypot(cell.x_m, cell.y_m) for cell in cells) > declared_support_m:
        raise KnownLandscapeError(
            "incomplete_spatial_support",
            "declared support omits at least one simulated landscape cell",
        )
    weights = tuple(
        cell.area_m2 / (hypot(cell.x_m, cell.y_m) + basin_radius_m) ** 2
        for cell in cells
    )
    cover_mass = tuple(
        sum(
            weight * cell.cover[taxon]
            for weight, cell in zip(weights, cells, strict=True)
        )
        for taxon in range(len(_TAXA))
    )
    support_cover = _closed(cover_mass, name="support-weighted vegetation")
    pollen_mass = tuple(
        support_cover[index] * _PPE[taxon] * _FALL_SPEED[taxon]
        for index, taxon in enumerate(_TAXA)
    )
    return support_cover, _closed(pollen_mass, name="pollen deposition"), cells


def _recover(
    pollen: tuple[float, ...],
    *,
    ppe: dict[str, float],
    fall_speed: dict[str, float],
) -> tuple[float, ...]:
    if set(ppe) != set(_TAXA) or set(fall_speed) != set(_TAXA):
        raise KnownLandscapeError("parameter_taxon_mismatch", "taxon keys differ")
    corrected = []
    for taxon, value in zip(_TAXA, pollen, strict=True):
        factor = ppe[taxon] * fall_speed[taxon]
        if factor <= 0:
            raise KnownLandscapeError("invalid_parameter", taxon)
        corrected.append(value / factor)
    return _closed(tuple(corrected), name="recovered vegetation")


def _mae(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(abs(a - b) for a, b in zip(left, right, strict=True)) / len(left)


def _next_uniform(state: int) -> tuple[int, float]:
    state = (state * 6_364_136_223_846_793_005 + 1_442_695_040_888_963_407) & _MASK_64
    return state, (state >> 11) / float(1 << 53)


def _multinomial(
    probabilities: tuple[float, ...], effort: int, state: int
) -> tuple[tuple[int, ...], int]:
    if effort <= 0:
        raise KnownLandscapeError("invalid_counting_effort", str(effort))
    counts = [0] * len(probabilities)
    boundaries = []
    running = 0.0
    for value in probabilities:
        running += value
        boundaries.append(running)
    boundaries[-1] = 1.0
    for _ in range(effort):
        state, uniform = _next_uniform(state)
        selected = next(
            index for index, boundary in enumerate(boundaries) if uniform < boundary
        )
        counts[selected] += 1
    return tuple(counts), state


def _wilson(count: int, total: int, nominal: float) -> tuple[float, float]:
    if nominal != 0.90:
        raise KnownLandscapeError("unsupported_nominal_coverage", str(nominal))
    z = 1.6448536269514722
    proportion = count / total
    denominator = 1.0 + z * z / total
    centre = (proportion + z * z / (2.0 * total)) / denominator
    half_width = (
        z
        * sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total**2))
        / denominator
    )
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def _vector(values: tuple[float, ...]) -> dict[str, float]:
    return dict(zip(_TAXA, values, strict=True))


def _cell_rows(cells: tuple[_Cell, ...]) -> list[JsonObject]:
    return [
        {
            "cell_id": cell.cell_id,
            "x_m": cell.x_m,
            "y_m": cell.y_m,
            "area_m2": cell.area_m2,
            "vegetation_fraction": _vector(cell.cover),
        }
        for cell in cells
    ]


def _base_case(
    case_id: str,
    kind: str,
    *,
    extent_m: float,
    declared_support_m: float,
    basin_radius_m: float,
    ppe: dict[str, float] | None = None,
    fall_speed: dict[str, float] | None = None,
    expected_disposition: str = "analytic_recovery",
) -> JsonObject:
    truth, pollen, cells = _simulate(
        kind,
        extent_m=extent_m,
        declared_support_m=declared_support_m,
        basin_radius_m=basin_radius_m,
    )
    assumed_ppe = dict(_PPE if ppe is None else ppe)
    assumed_fall = dict(_FALL_SPEED if fall_speed is None else fall_speed)
    recovered = _recover(pollen, ppe=assumed_ppe, fall_speed=assumed_fall)
    return {
        "case_id": case_id,
        "status": "success",
        "expected_disposition": expected_disposition,
        "landscape_kind": kind,
        "declared_support_m": declared_support_m,
        "landscape_extent_m": extent_m,
        "basin_radius_m": basin_radius_m,
        "cell_count": len(cells),
        "cells": _cell_rows(cells),
        "true_support_vegetation_fraction": _vector(truth),
        "expected_pollen_fraction": _vector(pollen),
        "assumed_ppe": assumed_ppe,
        "assumed_fall_speed_m_s": assumed_fall,
        "recovered_vegetation_fraction": _vector(recovered),
        "vegetation_mae_fraction": _mae(truth, recovered),
        "requested_draws": 0,
        "generated_draws": 0,
        "refused_draws": 0,
    }


def _noisy_case(
    case_id: str,
    *,
    effort: int,
    draws: int,
    seed: int,
    missing_dominant: bool = False,
) -> JsonObject:
    truth, pollen, cells = _simulate(
        "heterogeneous",
        extent_m=8_000.0,
        declared_support_m=8_000.0,
        basin_radius_m=175.0,
    )
    if draws <= 0:
        raise KnownLandscapeError("invalid_draw_count", str(draws))
    state = seed & _MASK_64
    rows: list[JsonObject] = []
    covered = 0
    width_sum = 0.0
    recovery_error_sum = 0.0
    for draw in range(draws):
        counts, state = _multinomial(pollen, effort, state)
        observed: list[int | None] = list(counts)
        if missing_dominant and draw == 0:
            observed[max(range(len(truth)), key=truth.__getitem__)] = None
        if any(value is None for value in observed):
            rows.append(
                {
                    "draw_id": f"draw-{draw:04d}",
                    "status": "refused",
                    "reason_code": "missing_dominant_taxon",
                    "counts": dict(zip(_TAXA, observed, strict=True)),
                }
            )
            continue
        integer_counts = cast(list[int], observed)
        observed_pollen = tuple(value / effort for value in integer_counts)
        recovered = _recover(
            observed_pollen,
            ppe=dict(_PPE),
            fall_speed=dict(_FALL_SPEED),
        )
        intervals = tuple(_wilson(count, effort, 0.90) for count in integer_counts)
        hits = tuple(
            lower <= value <= upper
            for value, (lower, upper) in zip(pollen, intervals, strict=True)
        )
        covered += sum(hits)
        width_sum += sum(upper - lower for lower, upper in intervals)
        error = _mae(truth, recovered)
        recovery_error_sum += error
        rows.append(
            {
                "draw_id": f"draw-{draw:04d}",
                "status": "success",
                "counts": dict(zip(_TAXA, integer_counts, strict=True)),
                "observed_pollen_fraction": _vector(observed_pollen),
                "recovered_vegetation_fraction": _vector(recovered),
                "vegetation_mae_fraction": error,
                "pollen_wilson_90": {
                    taxon: {
                        "lower": interval[0],
                        "upper": interval[1],
                        "covers_truth": hit,
                    }
                    for taxon, interval, hit in zip(_TAXA, intervals, hits, strict=True)
                },
            }
        )
    successes = sum(row["status"] == "success" for row in rows)
    refusals = len(rows) - successes
    if successes == 0:
        return {
            "case_id": case_id,
            "status": "refused",
            "expected_disposition": "expected_refusal",
            "reason_code": "no_complete_noisy_draws",
            "requested_draws": draws,
            "generated_draws": 0,
            "refused_draws": refusals,
            "draws": rows,
        }
    denominator = successes * len(_TAXA)
    return {
        "case_id": case_id,
        "status": "success" if refusals == 0 else "refused",
        "expected_disposition": (
            "expected_refusal" if refusals else "synthetic_noisy_coverage"
        ),
        "landscape_kind": "heterogeneous",
        "declared_support_m": 8_000.0,
        "basin_radius_m": 175.0,
        "cell_count": len(cells),
        "counting_effort": effort,
        "nominal_coverage": 0.90,
        "true_support_vegetation_fraction": _vector(truth),
        "expected_pollen_fraction": _vector(pollen),
        "requested_draws": draws,
        "generated_draws": successes,
        "refused_draws": refusals,
        "coverage_numerator": covered,
        "coverage_denominator": denominator,
        "coverage_fraction": covered / denominator,
        "mean_interval_width_fraction": width_sum / denominator,
        "mean_vegetation_mae_fraction": recovery_error_sum / successes,
        "draws": rows,
    }


def _refusal_case(case_id: str, error: KnownLandscapeError) -> JsonObject:
    return {
        "case_id": case_id,
        "status": "refused",
        "expected_disposition": "expected_refusal",
        "reason_code": error.reason_code,
        "detail": error.detail,
        "requested_draws": 0,
        "generated_draws": 0,
        "refused_draws": 0,
    }


def build_known_landscape_report(*, seed: int = 20_260_921) -> KnownLandscapeReport:
    """Build all declared analytic, noisy and adversarial synthetic cases."""
    if type(seed) is not int or seed < 0 or seed > _MASK_64:
        raise KnownLandscapeError(
            "invalid_seed", "seed must be an unsigned 64-bit integer"
        )
    cases = [
        _base_case(
            "homogeneous-noise-free",
            "homogeneous",
            extent_m=5_000.0,
            declared_support_m=5_000.0,
            basin_radius_m=175.0,
        ),
        _base_case(
            "heterogeneous-noise-free",
            "heterogeneous",
            extent_m=8_000.0,
            declared_support_m=8_000.0,
            basin_radius_m=175.0,
        ),
        _noisy_case("heterogeneous-noisy", effort=200, draws=128, seed=seed ^ 0xA5A5),
        _noisy_case("sparse-counts", effort=12, draws=128, seed=seed ^ 0x5A5A),
        _base_case(
            "misspecified-ppe",
            "heterogeneous",
            extent_m=8_000.0,
            declared_support_m=8_000.0,
            basin_radius_m=175.0,
            ppe={"broadleaf": 0.8, "conifer": 3.0, "open_land": 1.6},
            expected_disposition="expected_degradation",
        ),
        _base_case(
            "misspecified-fall-speed",
            "heterogeneous",
            extent_m=8_000.0,
            declared_support_m=8_000.0,
            basin_radius_m=175.0,
            fall_speed={"broadleaf": 0.040, "conifer": 0.012, "open_land": 0.030},
            expected_disposition="expected_degradation",
        ),
        _noisy_case(
            "missing-dominant-taxon",
            effort=200,
            draws=1,
            seed=seed ^ 0xC3C3,
            missing_dominant=True,
        ),
        _base_case(
            "variable-support-narrow",
            "heterogeneous",
            extent_m=2_500.0,
            declared_support_m=2_500.0,
            basin_radius_m=175.0,
        ),
        _base_case(
            "variable-support-wide",
            "heterogeneous",
            extent_m=12_000.0,
            declared_support_m=12_000.0,
            basin_radius_m=175.0,
        ),
    ]
    try:
        _simulate(
            "heterogeneous",
            extent_m=8_000.0,
            declared_support_m=1_000.0,
            basin_radius_m=175.0,
        )
    except KnownLandscapeError as error:
        cases.append(_refusal_case("incomplete-spatial-support", error))
    else:  # pragma: no cover - refusal contract
        raise KnownLandscapeError(
            "missing_expected_refusal", "incomplete support was accepted"
        )
    requested_draws = sum(cast(int, case["requested_draws"]) for case in cases)
    generated_draws = sum(cast(int, case["generated_draws"]) for case in cases)
    refused_draws = sum(cast(int, case["refused_draws"]) for case in cases)
    refusals = sum(case["status"] == "refused" for case in cases)
    payload = {
        "schema_version": "pollenomics-known-landscape-report.v1",
        "profile": KNOWN_LANDSCAPE_PROFILE,
        "seed": seed,
        "rng_profile": _RNG_PROFILE,
        "simulator": {
            "implementation": "stdlib finite-cell inverse-square deposition",
            "production_forward_imported": False,
            "production_inverse_imported": False,
            "cell_weight": "area_m2 / (distance_m + basin_radius_m)^2",
            "taxon_deposition": "support_cover * PPE * fall_speed",
            "coverage_interval": "two-sided Wilson marginal pollen interval",
        },
        "taxa": list(_TAXA),
        "true_parameters": {
            "ppe": _PPE,
            "fall_speed_m_s": _FALL_SPEED,
        },
        "cases": cases,
        "denominators": {
            "requested_cases": len(cases),
            "successful_cases": len(cases) - refusals,
            "refused_cases": refusals,
            "requested_noisy_draws": requested_draws,
            "generated_noisy_draws": generated_draws,
            "refused_noisy_draws": refused_draws,
        },
        "claims": {
            "independent_synthetic_forward_generator": True,
            "production_lra_recovery_validated": False,
            "real_observations_used": False,
            "empirical_ecological_accuracy": False,
            "predictive_intervals_calibrated_for_real_data": False,
            "reviewed_acceptance_thresholds_supplied": False,
            "scientifically_approved": False,
            "scientific_acceptance": "not_evaluated",
        },
    }
    return KnownLandscapeReport(_canonical_bytes(payload))
