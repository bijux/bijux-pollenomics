"""Immutable, content-bound conditional pollen observation draws."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import fsum
from typing import Any

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

PROFILE = "fixed-probability-multinomial-observation-v1"


def _probability_closure(
    values: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Single numerical authority for declared binary64 normalization/residual."""
    original = np.asarray(values, dtype=float)
    normalized = original / fsum(original)
    largest = int(np.argmax(normalized))
    order = tuple(i for i in range(len(values)) if i != largest) + (largest,)
    effective = normalized[list(order)].copy()
    effective[-1] = 1 - fsum(effective[:-1])
    if not 0 < effective[-1] <= 1:
        raise ValidationError("Binary64 probability closure failed")
    return order, tuple(float(value) for value in effective)


@dataclass(frozen=True)
class PollenObservationDraws:
    """Authoritative result bytes; returned dictionaries are independent copies."""

    canonical_result_json: str
    result_sha256: str

    def __post_init__(self) -> None:
        try:
            result = json.loads(self.canonical_result_json)
            if (
                not isinstance(result, dict)
                or result.get("schema_version") != "lra-pollen-observation-draws.v1"
                or result.get("profile") != PROFILE
                or canonical_json(result) != self.canonical_result_json
                or sha256_object(result) != self.result_sha256
            ):
                raise ValueError("Result bytes and identity disagree")
            _validate_payload(result)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                str(exc), reason_code="observation_draw_identity_mismatch"
            ) from exc

    def as_dict(self) -> dict[str, Any]:
        """Return fresh JSON data without sharing mutable result state."""
        self.__post_init__()
        result: dict[str, Any] = json.loads(self.canonical_result_json)
        return result


def _validate_payload(result: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "profile",
        "declaration",
        "declaration_sha256",
        "draw_ids",
        "counts",
        "count_units",
        "draw_scope",
        "marginal_predictive_intervals",
        "interval_profile",
        "interval_kind",
        "interval_numeric_profile",
        "numerical_boundary_separation",
        "sampling_probability_note",
        "propagated_sources",
        "conditioned_on",
        "not_propagated",
        "simultaneous_coverage_claimed",
        "empirical_coverage_verified",
        "scientific_acceptance",
        "r_source_parity_claimed",
    }
    if set(result) != expected:
        raise ValueError("Incomplete or unexpected observation result fields")
    declaration = result["declaration"]
    declared_fields = {
        "profile",
        "taxa",
        "input_pollen_fraction",
        "effective_pollen_fraction",
        "closure_profile",
        "effort",
        "effort_evidence_sha256",
        "prediction_sha256",
        "repeats",
        "seed",
        "coverage",
        "rng",
        "numpy_version",
        "scipy_version",
        "engine_version",
        "numerical_backend",
    }
    if not isinstance(declaration, dict) or set(declaration) != declared_fields:
        raise ValueError("Incomplete observation declaration")
    if (
        declaration["profile"] != PROFILE
        or sha256_object(declaration) != result["declaration_sha256"]
    ):
        raise ValueError("Observation declaration identity differs")
    for name in ("prediction_sha256", "effort_evidence_sha256"):
        value = declaration[name]
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError("Invalid parent evidence identity")
    if (
        declaration["closure_profile"] != "binary64-normalize-largest-residual-v1"
        or declaration["rng"] != "numpy.random.Generator(PCG64)"
    ):
        raise ValueError("Unsupported observation closure or generator profile")
    for name in (
        "numpy_version",
        "scipy_version",
        "engine_version",
        "numerical_backend",
    ):
        value = declaration[name]
        if not isinstance(value, str) or not value or value != value.strip():
            raise ValueError("Observation provider identities require nonempty strings")
    if (
        not isinstance(result["sampling_probability_note"], str)
        or not result["sampling_probability_note"].strip()
    ):
        raise ValueError("Sampling probability note requires text")
    taxa = declaration["taxa"]
    if (
        not isinstance(taxa, list)
        or not 1 <= len(taxa) <= 128
        or any(not isinstance(t, str) or not t or t != t.strip() for t in taxa)
        or taxa != sorted(set(taxa))
    ):
        raise ValueError("Invalid observation taxon denominator")
    for field, low, high in (
        ("effort", 1, 2**31 - 1),
        ("repeats", 2, 10000),
        ("seed", 0, 2**32 - 1),
    ):
        value = declaration[field]
        if type(value) is not int or not low <= value <= high:
            raise ValueError("Invalid bounded observation integer")
    effort, repeats = declaration["effort"], declaration["repeats"]
    if len(taxa) * repeats > 1_000_000:
        raise ValueError("Observation storage bound exceeded")
    level = declaration["coverage"]
    if type(level) not in (int, float) or not 0 < level < 1:
        raise ValueError("Invalid nominal coverage")
    for name in ("input_pollen_fraction", "effective_pollen_fraction"):
        values = declaration[name]
        if (
            not isinstance(values, dict)
            or set(values) != set(taxa)
            or any(
                type(v) not in (float, int) or not 0 <= v <= 1 for v in values.values()
            )
            or abs(fsum(values.values()) - 1) > 1e-12
        ):
            raise ValueError("Invalid observation probability denominator")
    nominal = tuple(
        float(declaration["input_pollen_fraction"][taxon]) for taxon in taxa
    )
    order, ordered_probabilities = _probability_closure(nominal)
    expected_probabilities = {
        taxa[index]: probability
        for index, probability in zip(order, ordered_probabilities, strict=True)
    }
    if declaration["effective_pollen_fraction"] != expected_probabilities:
        raise ValueError("Effective probabilities differ from the declared closure")
    draws = result["counts"]
    if not isinstance(draws, list) or len(draws) != repeats:
        raise ValueError("Missing joint count draws")
    for row in draws:
        if (
            not isinstance(row, list)
            or len(row) != len(taxa)
            or any(type(x) is not int or not 0 <= x <= effort for x in row)
            or sum(row) != effort
        ):
            raise ValueError("Count draw violates its taxon denominator or effort")
    for row in draws:
        if any(
            expected_probabilities[taxon] == 0 and count != 0
            for taxon, count in zip(taxa, row, strict=True)
        ):
            raise ValueError(
                "Count draw is impossible under a zero-probability category"
            )
    if result["draw_ids"] != [
        f"{result['declaration_sha256']}:{i}" for i in range(repeats)
    ]:
        raise ValueError("Joint draw identities differ from their declaration")
    intervals = result["marginal_predictive_intervals"]
    if not isinstance(intervals, dict) or set(intervals) != set(taxa):
        raise ValueError("Predictive interval taxon denominator differs")
    for item in intervals.values():
        if not isinstance(item, dict) or set(item) != {
            "lower_count",
            "upper_count",
            "lower_fraction",
            "upper_fraction",
        }:
            raise ValueError("Incomplete predictive interval")
        lo, hi = item["lower_count"], item["upper_count"]
        if (
            type(lo) is not int
            or type(hi) is not int
            or not 0 <= lo <= hi <= effort
            or type(item["lower_fraction"]) not in (float, int)
            or type(item["upper_fraction"]) not in (float, int)
            or item["lower_fraction"] != lo / effort
            or item["upper_fraction"] != hi / effort
        ):
            raise ValueError("Predictive count/fraction bounds disagree")
    if type(result["numerical_boundary_separation"]) not in (int, float):
        raise ValueError(
            "Numerical boundary separation must be numeric, excluding bool"
        )
    literals = {
        "count_units": "pollen_grains",
        "draw_scope": "joint_multinomial_taxon_counts",
        "interval_profile": "fixed-probability-binomial-equal-tail-v1",
        "interval_kind": "conditional_predictive_observation",
        "interval_numeric_profile": "exact-rational-boundary-v1"
        if effort <= 256
        else "scipy-cdf-separated-boundary-v1",
        "numerical_boundary_separation": 0.0 if effort <= 256 else 1e-12,
        "propagated_sources": ["observation_process"],
        "conditioned_on": ["fixed_pollen_probabilities", "predeclared_sampling_effort"],
        "scientific_acceptance": "not_evaluated",
    }
    if any(result[k] != v for k, v in literals.items()) or any(
        result[k] is not False
        for k in (
            "simultaneous_coverage_claimed",
            "empirical_coverage_verified",
            "r_source_parity_claimed",
        )
    ):
        raise ValueError("Observation uncertainty scope changed")
    if result["not_propagated"] != [
        "model_fitting",
        "spatial_model",
        "PPE",
        "chronology",
        "geometry",
        "regional_reconstruction",
        "local_reconstruction",
        "effort_uncertainty",
        "overdispersion",
    ]:
        raise ValueError("Required uncertainty omissions changed")
