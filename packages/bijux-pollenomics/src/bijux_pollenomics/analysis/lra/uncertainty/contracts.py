"""Immutable declarations for finite supplied synthetic joint realizations."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, NoReturn

from ..engine.errors import LRARefusal

PROFILE = "synthetic-explicit-joint-analytical-v1"
PLAN_SCHEMA = "lra-joint-realizations.v1"
MAX_NUMBER = 2**53 - 1
SCOPE = {
    "propagated": [
        "supplied_joint_PPE_realizations",
        "supplied_joint_calendar_BP_realizations",
        "supplied_joint_count_realizations",
        "paired_regional_to_local_reconstruction",
    ],
    "conditioned_on": [
        "supplied_finite_law",
        "fixed_basin_geometry",
        "fixed_fall_speeds",
        "fixed_taxonomy",
        "declared_bin_stationarity",
    ],
    "not_propagated": [
        "parameter_domain_selection",
        "spatial_model_fitting",
        "geometry",
        "calibration_model",
        "overdispersion",
        "posterior_predictive_observations",
    ],
    "scientific_law_authenticity_verified": False,
    "uncertainty_kind": "supplied_finite_law_pushforward",
    "empirical_coverage_verified": False,
}
NUMERICAL_REASONS = frozenset(
    {
        "invalid_input",
        "no_valid_local_rings",
        "unsupported_source_taxon_dimensions",
        "lra_numerical_refusal",
    }
)


def refuse(detail: str) -> NoReturn:
    raise LRARefusal("invalid_joint_plan", detail)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        refuse("Require an exact nonempty string identity")
    return str(value)


def number(value: object) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or abs(value) > MAX_NUMBER
        or not isfinite(value)
    ):
        refuse("Require a bounded finite native number, excluding booleans")
    return float(value)


def positive_integer(value: object, maximum: int = 1_000_000_000) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        refuse("Require a bounded positive integer")
    return int(value)


def exact_keys(value: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        refuse("Object fields differ from the joint contract")
    return dict(value)


def reference(value: object) -> dict[str, Any]:
    row = exact_keys(value, {"path", "sha256"})
    path = identity(row["path"])
    if (
        Path(path).is_absolute()
        or any(p in ("", ".", "..") for p in path.split("/"))
        or "\\" in path
    ):
        refuse("Reference paths must be normalized relative paths")
    checksum = identity(row["sha256"])
    if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
        refuse("Require a canonical SHA-256")
    return row


def mass(value: object) -> Fraction:
    row = exact_keys(value, {"numerator", "denominator"})
    return Fraction(
        positive_integer(row["numerator"]), positive_integer(row["denominator"])
    )


def parse_json(encoded: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                refuse("Duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(encoded, object_pairs_hook=pairs)
    if not isinstance(value, dict):
        refuse("Expected a JSON object")
    canonical(value)
    return value


@dataclass(frozen=True)
class JointLRAPlan:
    """Canonical bytes own a complete finite joint law; approval is not inferred."""

    canonical_json: str

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_json, str):
            refuse("Canonical plan must be a string")
        try:
            value = parse_json(self.canonical_json.encode("utf-8"))
            if canonical(value).decode("utf-8") != self.canonical_json:
                refuse("Plan bytes must be canonical")
            _validate(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise LRARefusal("invalid_joint_plan", str(exc)) from exc

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> JointLRAPlan:
        try:
            return cls(canonical(value).decode("utf-8"))
        except (TypeError, ValueError, OverflowError) as exc:
            raise LRARefusal("invalid_joint_plan", str(exc)) from exc

    @property
    def sha256(self) -> str:
        return digest(self.canonical_json.encode("utf-8"))

    def payload(self) -> dict[str, Any]:
        self.__post_init__()
        return parse_json(self.canonical_json.encode("utf-8"))


def _validate(value: dict[str, Any]) -> None:
    exact_keys(
        value,
        {
            "schema_version",
            "profile",
            "purpose",
            "data_kind",
            "base_request_ref",
            "law_evidence_ref",
            "bins",
            "realizations",
            "limits",
        },
    )
    if (
        value["schema_version"],
        value["profile"],
        value["purpose"],
        value["data_kind"],
    ) != (PLAN_SCHEMA, PROFILE, "exploratory", "synthetic"):
        refuse("Only supplied synthetic analytical joint realizations are supported")
    reference(value["base_request_ref"])
    reference(value["law_evidence_ref"])
    limits = exact_keys(
        value["limits"],
        {
            "max_realizations",
            "max_child_runs",
            "max_draw_cells",
            "max_covariance_cells",
        },
    )
    for key, hard in (
        ("max_realizations", 64),
        ("max_child_runs", 512),
        ("max_draw_cells", 1_000_000),
        ("max_covariance_cells", 1_000_000),
    ):
        positive_integer(limits[key], hard)
    bins, draws = value["bins"], value["realizations"]
    if (
        not isinstance(bins, list)
        or not bins
        or not isinstance(draws, list)
        or not draws
        or len(draws) > limits["max_realizations"]
        or len(draws) * len(bins) > limits["max_child_runs"]
    ):
        refuse("Joint draw/bin resource bounds exceeded")
    bin_ids: set[str] = set()
    intervals = []
    for row in bins:
        exact_keys(row, {"bin_id", "younger_bp", "older_bp", "membership"})
        key = identity(row["bin_id"])
        younger, older = number(row["younger_bp"]), number(row["older_bp"])
        if (
            key in bin_ids
            or younger >= older
            or row["membership"] != "younger_closed_older_open"
        ):
            refuse("Bins require unique IDs and positive half-open intervals")
        intervals.append((younger, older))
        bin_ids.add(key)
    ordered = sorted(intervals)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:], strict=False)):
        refuse("Allocation bins must not overlap")
    draw_ids: set[str] = set()
    shared: dict[tuple[str, str], bytes] = {}
    total = Fraction(0)
    for row in draws:
        exact_keys(
            row,
            {
                "draw_id",
                "mass",
                "ppe_realization_id",
                "ppe_by_taxon",
                "chronology_realization_id",
                "ages_by_sample_id",
                "count_realization_id",
                "counts_by_sample_id",
            },
        )
        key = identity(row["draw_id"])
        if key in draw_ids:
            refuse("Duplicate joint draw identity")
        draw_ids.add(key)
        total += mass(row["mass"])
        for tag, field in (
            ("ppe_realization_id", "ppe_by_taxon"),
            ("chronology_realization_id", "ages_by_sample_id"),
            ("count_realization_id", "counts_by_sample_id"),
        ):
            component_id = identity(row[tag])
            if not isinstance(row[field], dict) or not row[field]:
                refuse("Every realization requires explicit named component values")
            for name in row[field]:
                identity(name)
            value_bytes = canonical(row[field])
            pair = (tag, component_id)
            if pair in shared and shared[pair] != value_bytes:
                refuse("A reused component identity has contradictory values")
            shared[pair] = value_bytes
        for ppe in row["ppe_by_taxon"].values():
            if number(ppe) <= 0:
                refuse("PPE realizations must be strictly positive")
        for age in row["ages_by_sample_id"].values():
            number(age)
        for counts in row["counts_by_sample_id"].values():
            if (
                not isinstance(counts, list)
                or not counts
                or any(type(x) is not int or not 0 <= x <= MAX_NUMBER for x in counts)
            ):
                refuse("Count realizations require bounded nonnegative integers")
    if total != 1:
        refuse("Exact positive atom masses must sum to one")
