"""Bind the fixed true-survival experiment to qualified saved source owners."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
from typing import Any

from ..radial_envelope_workflow import nested_edges, read_prediction_inputs
from .kernel import Geometry
from .study_inputs import (
    AXIS,
    CORES,
    OWNERS,
    decode_json,
    finite,
    geometry_record,
    require,
)

BASE = "reports/science/pollen-reconstruction/spatial-field-forward/"
PROTOCOL = BASE + "continuous-receiver/monotone-rings.json"
CAPTURE = "artifacts/physical-core/spatial-field-forward/continuous-receiver/study/input-freeze.json"
RADIAL_PROTOCOL = BASE + "radial-envelope/protocol.json"
CONTINUOUS_PROTOCOL = BASE + "continuous-receiver/protocol.json"


@dataclass(frozen=True)
class RingInputs:
    protocol: dict[str, Any]
    prediction: dict[str, Any]
    original: dict[str, Any]
    freeze: dict[str, Any]
    geometries: tuple[Geometry, ...]
    edges: tuple[tuple[Fraction, ...], ...]
    scored_path: Path


def identity(raw: bytes) -> dict[str, str | int]:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def validate_protocol(protocol: dict[str, Any]) -> None:
    if "frontier" in protocol:
        require(
            protocol["frontier"]
            == {
                "priority": "coefficient_contribution",
                "q_uncertainty_full_width_exact": "1/16000000000",
            },
            "Unknown or changed coefficient-contribution contract",
        )
    require(
        protocol["numerical_contract"]["all_initial_endpoints_before_refinement"]
        is True
        and all(
            type(protocol["numerical_contract"][k]) is int
            for k in (
                "arithmetic_bits",
                "endpoint_population",
                "coefficient_population",
                "prediction_contexts",
                "family_slots",
            )
        ),
        "Typed scientific population contract differs",
    )
    require(
        protocol["schema_version"] == "continuous-receiver-monotone-rings.v1"
        and protocol["cases"] == [{"core": c, "taxon": t} for c, t in OWNERS],
        "Fixed ring owner population differs",
    )
    require(
        all(
            type(v) is int
            for name in ("resources", "independent_resources")
            for v in protocol[name].values()
        ),
        "Typed resource bounds required",
    )
    require(
        protocol["numerical_contract"]
        == {
            "endpoint_full_width_exact": "1/10000000000",
            "coefficient_full_width_exact": "1/1000000000",
            "arithmetic_bits": 96,
            "rule": "closed-newton-cotes-seven.v1",
            "endpoint_population": 774,
            "coefficient_population": 18,
            "prediction_contexts": 18,
            "family_slots": 54,
            "all_initial_endpoints_before_refinement": True,
        },
        "Prospective numerical population or precision differs",
    )
    require(
        protocol["resources"]
        == {
            "wall_seconds": 180,
            "integration_work_seconds": 160,
            "peak_rss_bytes_posthoc": 805306368,
            "all_output_bytes": 5000000,
            "per_case_maximum_leaves": 4096,
            "per_case_maximum_attempted_panels": 8191,
            "per_case_maximum_node_evaluations": 73719,
            "per_case_maximum_live_queue": 4096,
        }
        and protocol["independent_resources"]
        == {
            "wall_seconds": 180,
            "replay_work_seconds": 160,
            "peak_rss_bytes_posthoc": 805306368,
            "all_output_bytes": 5000000,
        },
        "Declared resource bounds differ",
    )
    for key in (
        "no_new_fits",
        "no_new_point_forecasts",
        "no_parameter_or_score_tuning",
        "retain_all_refusals",
    ):
        require(protocol[key] is True, "Scientific scope guard differs")
    require(protocol["unchanged_rerun_permitted"] is False, "Retry guard differs")


def _captured(row: dict[str, Any]) -> Fraction:
    require(set(row) == {"hex", "numerator", "denominator"}, "Invalid captured float")
    value = float.fromhex(row["hex"])
    require(
        math.isfinite(value)
        and value.hex() == row["hex"]
        and type(row["numerator"]) is type(row["denominator"]) is int
        and value.as_integer_ratio() == (row["numerator"], row["denominator"]),
        "Captured exact float identity differs",
    )
    return Fraction(value)


def select_geometry(
    public: dict[str, Any],
    original: dict[str, Any],
    freeze: dict[str, Any],
    prediction: dict[str, Any],
    protocol: dict[str, Any],
) -> tuple[tuple[Geometry, ...], tuple[tuple[Fraction, ...], ...]]:
    """Reuse captured A; no native prefix call or reprojection occurs here."""
    require(
        freeze["source_commit"] == protocol["captured_law_source_commit"]
        and freeze["schema_version"] == "continuous-receiver-input-freeze.v1"
        and freeze["historical_A_authenticated"] is False,
        "Captured-law scope differs",
    )
    require(
        public["axis"] == prediction["axis"] == list(AXIS)
        and [(r["core"], r["taxon"]) for r in public["geometry"]] == list(OWNERS)
        and [(r["core"], r["taxon"]) for r in freeze["cases"]] == list(OWNERS)
        and [g["core"] for g in prediction["geometry"]] == list(CORES),
        "Saved scientific axes or owners differ",
    )
    prefixes = freeze["native_prefix"]
    require([p["taxon"] for p in prefixes] == list(AXIS), "Prefix axis differs")
    coefficients = []
    for index, row in enumerate(prefixes):
        require(
            row["parameters"]
            == {
                "fall_speed_m_s": (0.024, 0.032)[index],
                "diffusion_coefficient": 0.12,
                "turbulence_parameter": 0.25,
                "wind_speed_m_s": 3.0,
            },
            "Captured native parameters differ",
        )
        survival, coefficient = _captured(row["S1"]), _captured(row["A"])
        require(
            0 < survival < 1
            and coefficient > 0
            and Fraction(-math.log(float(survival))) == coefficient,
            "Captured A is inconsistent with its S1",
        )
        coefficients.append(coefficient)
    declared = original["cores"]
    require([c["id"] for c in declared] == list(CORES), "Original core axis differs")
    require(
        [finite(c["radius_m"]) for c in declared] == [80, 69, 89]
        and finite(original["physical"]["regional_extent_m"]) == 100000,
        "Original radius support differs",
    )
    geometries, edges = [], []
    for index, ((core, _), row, frozen) in enumerate(
        zip(OWNERS, public["geometry"], freeze["cases"], strict=True)
    ):
        saved = prediction["geometry"][index // 2]
        require(
            row["anchor_order"] == saved["anchor_order"] == frozen["anchor_order"]
            and row["anchor_xy_m"] == saved["anchor_xy_m"],
            "Source anchor ownership differs",
        )
        first, second = row["anchor_xy_m"]
        geometry = Geometry(
            coefficients[index % 2],
            finite(declared[index // 2]["radius_m"]),
            Fraction(100000),
            (finite(first[0]), finite(first[1])),
            (finite(second[0]), finite(second[1])),
        )
        require(
            frozen["geometry"] == geometry_record(geometry), "Frozen geometry differs"
        )
        exact_edges = tuple(Fraction(v) for v in nested_edges(saved, 100000.0))
        require(
            len(exact_edges) == 129
            and [str(v) for v in exact_edges] == protocol["edges_exact"][core],
            "Declared nested edge construction differs",
        )
        geometries.append(geometry)
        edges.append(exact_edges)
    return tuple(geometries), tuple(edges)


def read_ring_inputs(repository: Path, protocol_path: Path) -> RingInputs:
    protocol = decode_json(protocol_path.read_bytes())
    validate_protocol(protocol)
    radial = decode_json((repository / RADIAL_PROTOCOL).read_bytes())
    expected = {
        BASE + "protocol.json",
        BASE + "result.json",
        RADIAL_PROTOCOL,
        CONTINUOUS_PROTOCOL,
        CAPTURE,
        *radial["repository_inputs"],
    }
    require(
        set(protocol["input_files"]) == expected, "Scientific input population differs"
    )
    for name, pin in protocol["input_files"].items():
        path = repository / name
        require(
            not Path(name).is_absolute()
            and ".." not in Path(name).parts
            and path.resolve().is_relative_to(repository)
            and not path.is_symlink()
            and 0 < path.stat().st_size <= 1_000_000,
            "Unsafe or oversized scientific input",
        )
        require(identity(path.read_bytes()) == pin, "Raw scientific input changed")
    prediction, original = read_prediction_inputs(repository, radial)
    public = decode_json((repository / (BASE + "result.json")).read_bytes())
    freeze = decode_json((repository / CAPTURE).read_bytes())
    geometries, edges = select_geometry(public, original, freeze, prediction, protocol)
    return RingInputs(
        protocol,
        prediction,
        original,
        freeze,
        geometries,
        edges,
        repository / radial["source_result"],
    )
