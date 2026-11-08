"""Exact retained-law inputs without native capture or numerical target parsing."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, cast

from ..kernel import Geometry
from ..verification.contracts import OWNERS, RESOURCE_LIMITS
from . import METHOD

FREEZE = "artifacts/physical-core/spatial-field-forward/continuous-receiver/study/input-freeze.json"
FREEZE_SHA = "c32b78b844f31d11e587bcc69a91cb50bb8fae943ee37f0cad057b4b6c807c4f"
CAPTURE_SOURCE = "6ea7d2e1845350ab506fb49f669389198abf40bb"
PUBLIC_INPUTS = (
    "reports/science/pollen-reconstruction/spatial-field-forward/result.json",
    "reports/science/pollen-reconstruction/spatial-field-forward/protocol.json",
)


def require(condition: object, reason: str) -> None:
    """Refuse changed law, ownership, resources or source bytes."""
    if not condition:
        raise ValueError(reason)


def decode(raw: bytes) -> dict[str, Any]:
    """Read metadata with duplicate-key and nonfinite-value refusal."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "Duplicate scientific metadata key")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    require(isinstance(value, dict), "Scientific metadata object required")
    json.dumps(value, allow_nan=False)
    return cast(dict[str, Any], value)


def rational(value: object) -> Fraction:
    """Keep canonical original binary64-exact fractions; never roundtrip a float."""
    require(type(value) is str, "Original canonical rational string required")
    result = Fraction(cast(str, value))
    require(str(result) == value, "Original canonical rational spelling required")
    return result


def read_regular(root: Path, relative: str, maximum: int) -> bytes:
    """Read an owned bounded body with every symbolic route refused."""
    path = PurePosixPath(relative)
    require(
        path.parts
        and not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == relative
        and not any(c in relative for c in "\\\0"),
        "Scientific input path escapes its owner",
    )
    target = root
    for component in path.parts:
        target /= component
        require(not target.is_symlink(), "Symbolic scientific input refused")
    require(
        target.is_file() and target.stat().st_size <= maximum,
        "Scientific input missing or oversized",
    )
    return target.read_bytes()


def identity(raw: bytes) -> dict[str, str | int]:
    """Bind opaque original inputs without parsing their numeric targets."""
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def validate_protocol(protocol: dict[str, Any]) -> None:
    """Require original law, six owners, eighteen goals and unchanged ceilings."""
    require(
        protocol.get("schema_version") == "continuous-receiver-angle-moments-study.v1"
        and protocol.get("method") == METHOD,
        "Unknown receiver-angle study method",
    )
    require(
        protocol.get("cases")
        == [{"core": core, "taxon": taxon} for core, taxon in OWNERS],
        "Original six-owner population differs",
    )
    require(
        protocol.get("input_freeze")
        == {"path": FREEZE, "bytes": 3915, "sha256": FREEZE_SHA}
        and protocol.get("captured_law_source_commit") == CAPTURE_SOURCE,
        "Original captured-law identity differs",
    )
    require(
        protocol.get("law")
        == {
            "survival": "exp(-A*d^(1/8))",
            "receiver": "original uniform disk radius R",
            "source_annulus": "original R<=r<=L",
            "angular_weight": "original two-anchor circle mean h(r)",
            "native_prefix_recapture": False,
            "historical_A_authenticated": False,
        }
        and protocol["law"]["native_prefix_recapture"] is False
        and protocol["law"]["historical_A_authenticated"] is False,
        "Original continuous law differs",
    )
    require(
        protocol.get("numerical_contract")
        == {
            "epsilon_exact": "1/1000000000",
            "coefficient_population": 18,
            "arithmetic_bits": 96,
            "rule": "closed-newton-cotes-seven.v1",
            "derivative_order": 8,
            "binomial_degree": 5,
            "maximum_angular_degree": 10,
            "maximum_displacement_bands": 11,
            "cap_domain": "L>3R",
            "expansion_domain": "qbar<14/15",
            "radial_full_width_budget_exact": "1/8000000000",
            "series_remainder": "whole J widened both ways once after finite-polynomial quadrature",
            "stopping": "all three actual final coefficient widths <= epsilon",
        },
        "Original precision or declared numerical representation differs",
    )
    require(
        protocol.get("resources") == RESOURCE_LIMITS
        and all(type(value) is int for value in protocol["resources"].values()),
        "Original study resource ceilings differ",
    )
    require(
        protocol.get("independent_resources")
        == {
            "wall_seconds": 180,
            "integration_work_seconds": 160,
            "peak_rss_bytes_posthoc": 805306368,
            "all_output_bytes": 5000000,
        }
        and all(
            type(value) is int for value in protocol["independent_resources"].values()
        ),
        "Original observer ceilings differ",
    )


@dataclass(frozen=True)
class FrozenInputs:
    """Retained exact geometry and byte-bound opaque predecessors, no new targets."""

    protocol: dict[str, Any]
    freeze: dict[str, Any]
    geometries: tuple[Geometry, ...]
    identities: dict[str, dict[str, str | int]]


def read_inputs(root: Path, protocol_path: Path) -> FrozenInputs:
    """Authenticate original capture and parse only its mathematical input fields."""
    relative = protocol_path.relative_to(root).as_posix()
    protocol_raw = read_regular(root, relative, 1_000_000)
    protocol = decode(protocol_raw)
    validate_protocol(protocol)
    freeze_raw = read_regular(root, FREEZE, 3915)
    require(
        identity(freeze_raw) == {"bytes": 3915, "sha256": FREEZE_SHA},
        "Original frozen-law bytes differ",
    )
    freeze = decode(freeze_raw)
    require(
        freeze.get("schema_version") == "continuous-receiver-input-freeze.v1"
        and freeze.get("source_commit") == CAPTURE_SOURCE
        and freeze.get("historical_A_authenticated") is False,
        "Retained capture scope differs",
    )
    identities = {relative: identity(protocol_raw), FREEZE: identity(freeze_raw)}
    require(
        set(freeze["input_files"]) == set(PUBLIC_INPUTS),
        "Opaque original input owners differ",
    )
    for name in PUBLIC_INPUTS:
        pin = freeze["input_files"][name]
        raw = read_regular(root, name, pin["bytes"])
        require(identity(raw) == pin, "Opaque original input identity differs")
        identities[name] = identity(raw)
    old_protocol = freeze["protocol_file"]
    raw = read_regular(root, old_protocol["path"], old_protocol["bytes"])
    require(
        identity(raw) == {k: old_protocol[k] for k in ("bytes", "sha256")},
        "Original capture protocol identity differs",
    )
    identities[old_protocol["path"]] = identity(raw)
    prefixes = freeze["native_prefix"]
    require(
        [row["taxon"] for row in prefixes] == ["Betula", "Ulmus"],
        "Retained native prefix owners differ",
    )
    coefficients = []
    for row in prefixes:
        captured = row["A"]
        require(
            type(captured["numerator"]) is int
            and type(captured["denominator"]) is int
            and captured["denominator"] > 0,
            "Retained A fraction is malformed",
        )
        coefficients.append(Fraction(captured["numerator"], captured["denominator"]))
    rows = freeze["cases"]
    require(
        len(rows) == 6
        and [(row["core"], row["taxon"]) for row in rows] == list(OWNERS),
        "Frozen owner population differs",
    )
    models = []
    for index, row in enumerate(rows):
        require(
            type(row["case_index"]) is int and row["case_index"] == index,
            "Frozen case identity differs",
        )
        values = row["geometry"]
        first = tuple(rational(value) for value in values["first_anchor_xy_m"])
        second = tuple(rational(value) for value in values["second_anchor_xy_m"])
        require(len(first) == len(second) == 2, "Original planar anchors differ")
        model = Geometry(
            rational(values["coefficient_A"]),
            rational(values["receiver_radius_m"]),
            rational(values["outer_radius_m"]),
            (first[0], first[1]),
            (second[0], second[1]),
        )
        require(
            model.coefficient == coefficients[index % 2] and model.coefficient > 0,
            "Frozen coefficient does not match retained native A",
        )
        models.append(model)
    return FrozenInputs(protocol, freeze, tuple(models), identities)
