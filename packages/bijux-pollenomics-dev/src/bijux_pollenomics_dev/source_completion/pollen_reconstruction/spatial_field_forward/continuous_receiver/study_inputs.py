"""Owned public geometry selection and one captured native prefix per taxon."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np

from bijux_pollenomics_lra.dispersal.kernels import gpm_values

from ..radial_envelope import BITS
from .coefficients import EPSILON
from .kernel import Geometry
from .quadrature import SEVEN_NODE_RULE, rule_definition
from .radial_partition import DYADIC_RADIAL, MAX_BANDS

CORES = ("BOKE", "BUS", "SOLSOE83")
AXIS = ("Betula", "Ulmus")
OWNERS = tuple((core, taxon) for core in CORES for taxon in AXIS)
SOURCE_RESULT = (
    "reports/science/pollen-reconstruction/spatial-field-forward/result.json"
)
SOURCE_PROTOCOL = (
    "reports/science/pollen-reconstruction/spatial-field-forward/protocol.json"
)
INPUT_PATHS = (SOURCE_RESULT, SOURCE_PROTOCOL)
LEGACY_ATOL = Fraction(1e-9)
LEGACY_RTOL = Fraction(1e-8)
RESOURCE_LIMITS = {
    "wall_seconds": 180,
    "integration_work_seconds": 160,
    "closure_seconds_reserved": 20,
    "peak_rss_bytes_posthoc": 805306368,
    "all_output_bytes": 5000000,
    "per_case_maximum_leaves": 4096,
    "per_case_maximum_attempted_panels": 8191,
    "per_case_maximum_node_evaluations": 73719,
    "per_case_maximum_live_queue": 4096,
    "all_cases_maximum_leaves": 24576,
    "all_cases_maximum_attempted_panels": 49146,
    "all_cases_maximum_node_evaluations": 442314,
}


def require(condition: bool, reason: str) -> None:
    """Refuse an input when its required study condition fails."""
    if not condition:
        raise ValueError(reason)


def finite(value: object) -> Fraction:
    """Convert a finite native integer or binary64 value to a fraction."""
    if type(value) not in (int, float):
        raise ValueError("Finite native int or binary64 required")
    assert isinstance(value, (int, float))
    require(math.isfinite(value), "Finite native int or binary64 required")
    return Fraction(value)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError(f"Nonfinite JSON literal: {value}")


def decode_json(value: bytes) -> dict[str, Any]:
    """Decode a JSON object while rejecting duplicate and nonfinite members."""
    result = json.loads(value, object_pairs_hook=_object, parse_constant=_nonfinite)
    require(type(result) is dict, "JSON object required")
    return result  # type: ignore[no-any-return]


def validate_protocol(protocol: dict[str, Any]) -> None:
    """Require the fixed population, arithmetic, method and resource contract."""
    require(
        protocol["schema_version"] == "continuous-receiver-study.v1",
        "Unknown study protocol",
    )
    require(
        protocol["population"]["cases"]
        == [{"core": core, "taxon": taxon} for core, taxon in OWNERS],
        "Study case population/order differs",
    )
    require(
        type(protocol["population"]["case_count"]) is int
        and protocol["population"]["case_count"] == 6,
        "Six study cases required",
    )
    require(
        type(protocol["population"]["complete_coefficient_population"]) is int
        and protocol["population"]["complete_coefficient_population"] == 18,
        "Eighteen declared coefficients required",
    )
    require(
        type(protocol["population"]["coefficients_per_case"]) is list
        and protocol["population"]["coefficients_per_case"] == ["K", "B1", "B2"],
        "Coefficient axis/order differs",
    )
    require(
        protocol["population"]["retain_all_case_statuses"] is True,
        "Every declared case status must be retained",
    )
    require(
        protocol["method"]["rule"] == SEVEN_NODE_RULE
        and protocol["method"]["partition"] == DYADIC_RADIAL,
        "Study rule/partition differs",
    )
    require(
        set(protocol["input_files"]) == set(INPUT_PATHS),
        "Exactly the two declared public inputs required",
    )
    for pin in protocol["input_files"].values():
        require(
            set(pin) == {"bytes", "sha256"}
            and type(pin["bytes"]) is int
            and 0 < pin["bytes"] <= 1_000_000,
            "Invalid bounded input receipt",
        )
        require(
            type(pin["sha256"]) is str
            and len(pin["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in pin["sha256"]),
            "Invalid input digest",
        )
    for name, expected in RESOURCE_LIMITS.items():
        require(
            type(protocol["resources"][name]) is int
            and protocol["resources"][name] == expected,
            "Study resource profile differs",
        )
    contract = protocol["numerical_contract"]
    require(
        contract["epsilon_exact"] == str(EPSILON)
        and contract["saved_point_absolute_error_exact"] == str(EPSILON),
        "Exact numerical goal differs",
    )
    require(
        finite(contract["legacy_correspondence_absolute"]) == LEGACY_ATOL
        and finite(contract["legacy_correspondence_relative"]) == LEGACY_RTOL,
        "Legacy correspondence settings differ",
    )
    for name, expected in (
        ("arithmetic_bits", BITS),
        ("quadrature_derivative_order", rule_definition(SEVEN_NODE_RULE)[0]),
        ("maximum_radial_bands", MAX_BANDS),
    ):
        require(
            type(contract[name]) is int and contract[name] == expected,
            "Typed numerical method contract differs",
        )


def read_inputs(
    repository: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the two declared public input receipts with exact byte identities."""
    validate_protocol(protocol)
    values = []
    for name in INPUT_PATHS:
        path = repository / name
        require(
            path.resolve().is_relative_to(repository.resolve())
            and not path.is_symlink(),
            "Input escapes owning repository",
        )
        pin = protocol["input_files"][name]
        with path.open("rb") as stream:
            raw = stream.read(pin["bytes"] + 1)
        require(
            len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"],
            "Public input receipt mismatch",
        )
        values.append(decode_json(raw))
    return values[0], values[1]


@dataclass(frozen=True)
class Reference:
    """Store one saved-reference target and its exact rational value."""

    name: str
    target: str
    value: Fraction


@dataclass(frozen=True)
class StudyCase:
    """Bind a core and taxon to geometry, anchor order and references."""

    core: str
    taxon: str
    anchor_order: tuple[str, str]
    geometry: Geometry
    references: tuple[Reference, ...]


@dataclass(frozen=True)
class StudyInputs:
    """Group source-owned cases, native-prefix records and environment metadata."""

    cases: tuple[StudyCase, ...]
    native_prefix: tuple[dict[str, Any], ...]
    environment: dict[str, str]

    @property
    def geometries(self) -> tuple[Geometry, ...]:
        """Return the ordered geometry population from the declared cases."""
        return tuple(case.geometry for case in self.cases)


def _captured(value: float) -> dict[str, str | int]:
    numerator, denominator = value.as_integer_ratio()
    return {"hex": value.hex(), "numerator": numerator, "denominator": denominator}


def prepare_inputs(
    result: dict[str, Any], original: dict[str, Any], protocol: dict[str, Any]
) -> StudyInputs:
    """Select metadata first; capture only after all six source owners validate."""
    validate_protocol(protocol)
    require(
        result["schema_version"] == "spatial-field-forward-account.v1"
        and original["schema_version"] == "spatial-field-forward-protocol.v1",
        "Unexpected public source schema",
    )
    require(
        result["axis"] == list(AXIS) and original["projected_axis"] == list(AXIS),
        "Source taxon axis differs",
    )
    fall = result["fall_speed_m_s"]
    require(
        type(fall) is list
        and len(fall) == 2
        and [finite(value) for value in fall] == [Fraction(0.024), Fraction(0.032)],
        "Source fall-speed axis differs",
    )
    physical = original["physical"]
    profile = {
        "wind_speed_m_s": 3.0,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
        "regional_extent_m": 100000.0,
    }
    require(
        all(
            finite(physical[name]) == Fraction(value) for name, value in profile.items()
        ),
        "Closed physical profile differs",
    )
    require(
        finite(physical["turbulence_parameter"]) / 2 == Fraction(1, 8),
        "Exact displacement exponent differs",
    )
    cores = original["cores"]
    require(
        type(cores) is list and [row["id"] for row in cores] == list(CORES),
        "Core population/order differs",
    )
    radii = tuple(finite(row["radius_m"]) for row in cores)
    require(
        radii == (Fraction(80), Fraction(69), Fraction(89)),
        "Declared receiving radii differ",
    )
    rows = result["geometry"]
    require(
        type(rows) is list
        and [(row["core"], row["taxon"]) for row in rows] == list(OWNERS),
        "Missing, duplicate, reordered or foreign geometry owner",
    )
    selected = []
    coordinates: dict[
        str, tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
    ] = {}
    for (core, taxon), row in zip(OWNERS, rows, strict=True):
        anchors = tuple(name for name in CORES if name != core)
        require(row["anchor_order"] == list(anchors), "Anchor order/ownership differs")
        xy = row["anchor_xy_m"]
        require(
            type(xy) is list
            and len(xy) == 2
            and all(type(point) is list and len(point) == 2 for point in xy),
            "Two planar anchor points required",
        )
        points = (
            tuple(finite(value) for value in xy[0]),
            tuple(finite(value) for value in xy[1]),
        )
        first, second = (points[0][0], points[0][1]), (points[1][0], points[1][1])
        require(first != second, "Distinct source anchors required")
        if core in coordinates:
            require(
                coordinates[core] == (first, second),
                "Cross-taxon projected anchors disagree",
            )
        coordinates[core] = first, second
        baseline, primary = row["homogeneous_baseline"], row["primary"]
        require(
            baseline["taxon"] == taxon and baseline["status"] == "qualified",
            "Saved homogeneous reference owner/status differs",
        )
        factors = primary["anchor_factors"]
        require(
            type(factors) is list and len(factors) == 2,
            "Two serialized primary factors required",
        )
        standalone, primary_k = (
            finite(baseline["factor"]),
            finite(primary["homogeneous_factor"]),
        )
        b1, b2 = finite(factors[0]), finite(factors[1])
        require(
            min(standalone, primary_k, b1, b2) > 0,
            "Saved positive reference domain differs",
        )
        references = (
            Reference("standalone_K", "K", standalone),
            Reference("primary_K", "K", primary_k),
            Reference("primary_anchor_sum", "K", b1 + b2),
            Reference("primary_B1", "B1", b1),
            Reference("primary_B2", "B2", b2),
        )
        selected.append((core, taxon, anchors, first, second, references))
    prefixes = []
    coefficients = {}
    for taxon, speed in zip(AXIS, fall, strict=True):
        parameters = {
            name: float(physical[name])
            for name in (
                "diffusion_coefficient",
                "turbulence_parameter",
                "wind_speed_m_s",
            )
        }
        parameters["fall_speed_m_s"] = float(speed)
        survival = float(
            gpm_values(
                1.0,
                parameters["fall_speed_m_s"],
                parameters["diffusion_coefficient"],
                parameters["turbulence_parameter"],
                parameters["wind_speed_m_s"],
            )
        )
        require(
            math.isfinite(survival) and 0 < survival < 1,
            "Native prefix survival is outside (0,1)",
        )
        coefficient = -math.log(survival)
        require(
            math.isfinite(coefficient) and coefficient > 0,
            "Native captured A must be finite and positive",
        )
        coefficients[taxon] = Fraction(coefficient)
        prefixes.append(
            {
                "taxon": taxon,
                "parameters": parameters,
                "S1": _captured(survival),
                "A": _captured(coefficient),
            }
        )
    cases = tuple(
        StudyCase(
            core,
            taxon,
            (anchors[0], anchors[1]),
            Geometry(
                coefficients[taxon],
                radii[CORES.index(core)],
                finite(physical["regional_extent_m"]),
                first,
                second,
            ),
            references,
        )
        for core, taxon, anchors, first, second, references in selected
    )
    return StudyInputs(
        cases,
        tuple(prefixes),
        {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    )


def geometry_record(geometry: Geometry) -> dict[str, Any]:
    """Serialize exact geometry fields as rational strings."""
    return {
        "coefficient_A": str(geometry.coefficient),
        "receiver_radius_m": str(geometry.receiver),
        "outer_radius_m": str(geometry.outer),
        "first_anchor_xy_m": [str(value) for value in geometry.first],
        "second_anchor_xy_m": [str(value) for value in geometry.second],
    }
