"""Bind the six scientific owners and captured native law to public inputs."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
import math
import sys
from typing import Any, cast

from .contracts import (
    EPSILON,
    INPUT_NAMES,
    LEGACY_ABSOLUTE,
    LEGACY_RELATIVE,
    OWNERS,
    RESOURCE_LIMITS,
    RULE,
    VerificationError,
    bounds,
    encoded,
    finite,
    integer,
    require,
)
from .geometry import Geometry


def validate_protocol(value: Mapping[str, Any]) -> None:
    """Require the fixed study population, arithmetic and resource contract."""
    require(
        value.get("schema_version") == "continuous-receiver-study.v1",
        "Unknown study protocol",
    )
    population = value.get("population", {})
    require(
        population.get("cases") == [{"core": a, "taxon": b} for a, b in OWNERS]
        and type(population.get("case_count")) is int
        and population["case_count"] == 6,
        "Protocol case population differs",
    )
    require(
        population.get("coefficients_per_case") == ["K", "B1", "B2"]
        and type(population.get("complete_coefficient_population")) is int
        and population["complete_coefficient_population"] == 18
        and population.get("retain_all_case_statuses") is True,
        "Protocol complete coefficient population differs",
    )
    require(
        value.get("method", {}).get("rule") == RULE
        and value["method"].get("partition") == "dyadic_radial",
        "Protocol numerical method differs",
    )
    contract = value.get("numerical_contract", {})
    expected = {
        "epsilon_exact": str(EPSILON),
        "saved_point_absolute_error_exact": str(EPSILON),
        "legacy_correspondence_absolute": 1e-9,
        "legacy_correspondence_relative": 1e-8,
        "arithmetic_bits": 96,
        "quadrature_derivative_order": 8,
        "maximum_radial_bands": 11,
    }
    require(
        set(contract) == set(expected)
        and all(
            type(contract[k]) is type(v) and contract[k] == v
            for k, v in expected.items()
        ),
        "Typed numerical contract differs",
    )
    require(
        set(value.get("input_files", {})) == set(INPUT_NAMES),
        "Unexpected public input population",
    )
    for pin in value["input_files"].values():
        require(
            isinstance(pin, dict) and set(pin) == {"bytes", "sha256"},
            "Malformed public input pin",
        )
        require(
            integer(pin["bytes"], "input byte count", 1_000_000) > 0,
            "Empty public input",
        )
        require(
            isinstance(pin["sha256"], str)
            and len(pin["sha256"]) == 64
            and set(pin["sha256"]) <= set("0123456789abcdef"),
            "Invalid public input SHA",
        )
    for name, expected_value in RESOURCE_LIMITS.items():
        require(
            type(value["resources"].get(name)) is int
            and value["resources"][name] == expected_value,
            "Protocol resource cap differs",
        )


def _captured(value: object, label: str) -> tuple[float, Fraction]:
    require(
        isinstance(value, dict) and set(value) == {"hex", "numerator", "denominator"},
        f"Invalid {label} capture",
    )
    row = cast(dict[str, Any], value)
    require(type(row["hex"]) is str, "Native hex string missing")
    try:
        native = float.fromhex(row["hex"])
    except ValueError as error:
        raise VerificationError("Invalid native hex") from error
    require(
        math.isfinite(native) and native.hex() == row["hex"],
        "Noncanonical/nonfinite native capture",
    )
    numerator = integer(row["numerator"], f"{label} numerator", 2**1075)
    denominator = integer(row["denominator"], f"{label} denominator", 2**1075)
    require(
        denominator > 0 and (numerator, denominator) == native.as_integer_ratio(),
        "Native ratio/hex disagree",
    )
    return native, Fraction(numerator, denominator)


def select_sources(
    source: Mapping[str, Any], original: Mapping[str, Any], freeze: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Bind exact case owners and native-prefix values to the source freeze."""
    import platform

    import numpy as np

    from bijux_pollenomics_lra.dispersal.kernels import gpm_values

    require(
        source.get("schema_version") == "spatial-field-forward-account.v1"
        and original.get("schema_version") == "spatial-field-forward-protocol.v1",
        "Public source schema differs",
    )
    axis = ["Betula", "Ulmus"]
    require(
        source.get("axis") == original.get("projected_axis") == axis,
        "Public taxon axis differs",
    )
    fall = cast(list[Any], source.get("fall_speed_m_s"))
    require(
        isinstance(fall, list) and len(fall) == 2 and all(finite(x) > 0 for x in fall),
        "Native fall-speed axis differs",
    )
    physical = original["physical"]
    require(
        finite(physical["turbulence_parameter"]) / 2 == Fraction(1, 8),
        "Displacement exponent differs",
    )
    require(
        all(
            finite(physical[name]) > 0
            for name in ("wind_speed_m_s", "diffusion_coefficient", "regional_extent_m")
        ),
        "Positive physical metadata required",
    )
    cores = cast(list[dict[str, Any]], original.get("cores"))
    require(
        isinstance(cores, list)
        and [x.get("id") for x in cores] == ["BOKE", "BUS", "SOLSOE83"],
        "Core source ownership differs",
    )
    radii = {row["id"]: finite(row["radius_m"]) for row in cores}
    require(freeze.get("historical_A_authenticated") is False, "Historical A promoted")
    environment = {
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
    require(
        freeze.get("environment") == environment, "Native-prefix environment differs"
    )
    prefixes = cast(list[dict[str, Any]], freeze.get("native_prefix"))
    require(
        isinstance(prefixes, list) and [row.get("taxon") for row in prefixes] == axis,
        "Native prefix population differs",
    )
    coefficients = {}
    for index, row in enumerate(prefixes):
        parameters = {
            key: float(physical[key])
            for key in (
                "diffusion_coefficient",
                "turbulence_parameter",
                "wind_speed_m_s",
            )
        }
        parameters["fall_speed_m_s"] = float(fall[index])
        require(
            isinstance(row.get("parameters"), dict)
            and set(row["parameters"]) == set(parameters),
            "Native prefix parameter population differs",
        )
        require(
            all(
                type(row["parameters"][key]) is float
                and row["parameters"][key].hex() == value.hex()
                for key, value in parameters.items()
            ),
            "Native prefix call parameters differ",
        )
        s1, s1_exact = _captured(row.get("S1"), "S1")
        a, a_exact = _captured(row.get("A"), "A")
        require(0 < s1_exact < 1 and a_exact > 0, "Native survival/A domain differs")
        current = float(
            gpm_values(
                1.0,
                parameters["fall_speed_m_s"],
                parameters["diffusion_coefficient"],
                parameters["turbulence_parameter"],
                parameters["wind_speed_m_s"],
            )
        )
        require(
            current.hex() == s1.hex() and (-math.log(current)).hex() == a.hex(),
            "Captured prefix differs from current native call",
        )
        coefficients[axis[index]] = a_exact
    geometry_rows = cast(list[dict[str, Any]], source.get("geometry"))
    require(
        isinstance(geometry_rows, list)
        and [(r.get("core"), r.get("taxon")) for r in geometry_rows] == list(OWNERS),
        "Public geometry population differs",
    )
    cases: list[dict[str, Any]] = []
    coordinates: dict[
        str, tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
    ] = {}
    for i, ((core, taxon), row) in enumerate(zip(OWNERS, geometry_rows, strict=True)):
        anchors = [name for name in ("BOKE", "BUS", "SOLSOE83") if name != core]
        require(
            row.get("anchor_order") == anchors, "Saved anchor ownership/order differs"
        )
        xy = cast(list[list[Any]], row.get("anchor_xy_m"))
        require(
            isinstance(xy, list)
            and len(xy) == 2
            and all(isinstance(point, list) and len(point) == 2 for point in xy),
            "Two native anchor points required",
        )
        first = (finite(xy[0][0]), finite(xy[0][1]))
        second = (finite(xy[1][0]), finite(xy[1][1]))
        if core in coordinates:
            require(coordinates[core] == (first, second), "Cross-taxon anchor mismatch")
        coordinates[core] = (first, second)
        geometry = Geometry(
            coefficients[taxon],
            radii[core],
            finite(physical["regional_extent_m"]),
            first,
            second,
        )
        baseline, primary = row["homogeneous_baseline"], row["primary"]
        require(
            baseline.get("taxon") == taxon and baseline.get("status") == "qualified",
            "Saved standalone reference owner differs",
        )
        factors = primary.get("anchor_factors")
        require(
            isinstance(factors, list) and len(factors) == 2,
            "Primary reference population differs",
        )
        standalone, primary_k, b1, b2 = (
            finite(baseline["factor"]),
            finite(primary["homogeneous_factor"]),
            finite(factors[0]),
            finite(factors[1]),
        )
        require(
            min(standalone, primary_k, b1, b2) > 0,
            "Saved positive reference domain differs",
        )
        references = [
            ("standalone_K", "K", standalone),
            ("primary_K", "K", primary_k),
            ("primary_anchor_sum", "K", b1 + b2),
            ("primary_B1", "B1", b1),
            ("primary_B2", "B2", b2),
        ]
        cases.append(
            {
                "case_index": i,
                "core": core,
                "taxon": taxon,
                "anchor_order": anchors,
                "geometry": geometry,
                "references": references,
            }
        )
    expected = [
        {key: row[key] for key in ("case_index", "core", "taxon", "anchor_order")}
        | {"geometry": row["geometry"].encoded()}
        for row in cases
    ]
    require(
        isinstance(freeze.get("cases"), list)
        and [
            integer(row.get("case_index"), "frozen case index", 5)
            for row in freeze["cases"]
        ]
        == list(range(6)),
        "Frozen case index differs",
    )
    require(
        freeze.get("cases") == expected,
        "Input freeze differs from original public geometry",
    )
    return cases


def reference_checks(
    references: list[tuple[str, str, Fraction]], saved: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Record certified endpoint differences from named saved references."""
    result = []
    for name, target, value in references:
        interval = bounds(saved[target])
        maximum = max(abs(value - interval.lower), abs(value - interval.upper))
        tolerance = LEGACY_ABSOLUTE + LEGACY_RELATIVE * abs(value)
        result.append(
            {
                "name": name,
                "target": target,
                "value_exact": str(value),
                "bounds": encoded(interval),
                "max_absolute_error_exact": str(maximum),
                "absolute_error_certified": maximum <= EPSILON,
                "correspondence_tolerance_exact": str(tolerance),
                "correspondence_pass": maximum <= tolerance,
            }
        )
    return result
