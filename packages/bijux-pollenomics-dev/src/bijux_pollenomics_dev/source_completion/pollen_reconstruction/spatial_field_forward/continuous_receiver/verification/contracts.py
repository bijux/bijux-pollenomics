"""Exact study contracts, bounded inputs and observer resource checks."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time
from typing import Any, cast

from ..arithmetic import Interval, Jet

EPSILON = Fraction(1, 10**9)


LEGACY_ABSOLUTE = Fraction(1e-9)


LEGACY_RELATIVE = Fraction(1e-8)


RULE = "closed-newton-cotes-seven.v1"


WEIGHTS = (41, 216, 27, 272, 27, 216, 41)


PEANO_DIVISOR = 1567641600


LATTICE = 2**96


MAX_BYTES = 5_000_000


OWNERS = tuple(
    (core, taxon)
    for core in ("BOKE", "BUS", "SOLSOE83")
    for taxon in ("Betula", "Ulmus")
)


INPUT_NAMES = (
    "reports/science/pollen-reconstruction/spatial-field-forward/result.json",
    "reports/science/pollen-reconstruction/spatial-field-forward/protocol.json",
)


Function = Callable[[tuple[Jet, ...]], Jet]


Box = tuple[tuple[Fraction, Fraction], ...]


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


class VerificationError(ValueError):
    """A source, coverage or mathematical certificate obligation failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def integer(value: object, label: str, maximum: int = 2**53 - 1) -> int:
    require(type(value) is int and 0 <= value <= maximum, f"Invalid {label}")
    return cast(int, value)


def rational(value: object) -> Fraction:
    require(type(value) is str, "Exact rational string required")
    try:
        result = Fraction(cast(str, value))
    except (ValueError, ZeroDivisionError) as error:
        raise VerificationError("Invalid rational string") from error
    require(str(result) == value, "Noncanonical rational encoding")
    return result


def finite(value: object) -> Fraction:
    require(
        type(value) in (int, float) and math.isfinite(cast(float, value)),
        "Finite native number required",
    )
    return Fraction(cast(int | float, value))


def encoded(value: Interval) -> list[str]:
    return [str(value.lower), str(value.upper)]


def bounds(value: object) -> Interval:
    require(
        isinstance(value, list) and len(value) == 2, "Two interval endpoints required"
    )
    a, b = (rational(item) for item in cast(list[object], value))
    require(
        a <= b and (a * LATTICE).denominator == 1 and (b * LATTICE).denominator == 1,
        "Invalid96-bit interval",
    )
    return Interval(a, b)


def overlaps(first: Interval, second: Interval, label: str) -> None:
    require(
        max(first.lower, second.lower) <= min(first.upper, second.upper),
        f"Independent enclosure disagrees: {label}",
    )


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def parse(raw: bytes) -> dict[str, Any]:
    result = json.loads(
        raw,
        object_pairs_hook=_unique,
        parse_constant=lambda value: (_ for _ in ()).throw(
            VerificationError(f"NonfiniteJSON:{value}")
        ),
    )
    require(isinstance(result, dict), "JSON object required")
    return cast(dict[str, Any], result)


def identity(raw: bytes) -> dict[str, Any]:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _same_json(first: object, second: object) -> bool:
    return json.dumps(
        first, sort_keys=True, separators=(",", ":"), allow_nan=False
    ) == json.dumps(second, sort_keys=True, separators=(",", ":"), allow_nan=False)


def bound_file(path: Path, pin: Mapping[str, Any]) -> bytes:
    require(
        not path.is_symlink() and path.is_file(), "Regular nonsymlink input required"
    )
    with path.open("rb") as stream:
        raw = stream.read(integer(pin["bytes"], "bounded input bytes", MAX_BYTES) + 1)
    require(identity(raw) == dict(pin), f"Input identity differs:{path.name}")
    return raw


@dataclass
class Clock:
    seconds: float = 160
    started: float = 0
    current_case: tuple[str, str] | None = None
    current_domain: int | None = None
    completed_leaves: int = 0

    def __post_init__(self) -> None:
        require(
            type(self.seconds) in (int, float) and 0 < self.seconds <= 160,
            "Observer work budget exceeds160s",
        )
        if not self.started:
            self.started = time.monotonic()

    def check(self) -> None:
        require(
            time.monotonic() - self.started < self.seconds,
            "Independent fixed-leaf work budget exhausted",
        )
        require(_rss() <= 805306368, "Observer RSS budget exceeded")


def _rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024
