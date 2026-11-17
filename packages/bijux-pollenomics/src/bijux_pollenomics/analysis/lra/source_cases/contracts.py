"""Immutable bounded declarations for fixed-support conditional source cases."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, NoReturn

from ..engine.errors import LRARefusal

PROFILE = "source-fixed-support-analytical-v1"
LIMITS = {
    "max_cases": 16,
    "max_input_files": 128,
    "max_input_bytes": 8 * 1024 * 1024,
    "max_output_bytes": 64 * 1024 * 1024,
    "max_output_files": 4096,
    "max_covariance_cells": 1_000_000,
}


def refuse(detail: str) -> NoReturn:
    """Refuse an unsupported or inconsistent source-case declaration."""
    raise LRARefusal("invalid_source_cases", detail)


def canonical(value: object) -> bytes:
    """Encode finite JSON without changing array or source-reference identity."""
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode()
    except (TypeError, ValueError, UnicodeError) as exc:
        refuse(f"Require finite JSON: {type(exc).__name__}")


def digest(value: bytes) -> str:
    """Return the exact byte identity of a declaration or source member."""
    return hashlib.sha256(value).hexdigest()


def fields(value: object, expected: set[str]) -> dict[str, Any]:
    """Require an exact object shape rather than accepting ignored claims."""
    if not isinstance(value, dict) or set(value) != expected:
        refuse("Object fields differ from the source-case contract")
    return dict(value)


def positive(value: object, maximum: int) -> int:
    """Require a bounded native integer, excluding boolean equality."""
    if type(value) is not int or not 1 <= value <= maximum:
        refuse("Require a bounded positive native integer")
    return value


def identifier(value: object) -> str:
    """Require an unambiguous identifier suitable for owned child paths."""
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value) is None
    ):
        refuse("Require a simple exact case identifier")
    return value


def reference(value: object) -> dict[str, Any]:
    """Validate one independently pinned relative ordinary-file reference."""
    ref = fields(value, {"path", "sha256", "bytes"})
    path = ref["path"]
    if (
        not isinstance(path, str)
        or not path
        or "\\" in path
        or any(ord(c) < 32 for c in path)
    ):
        refuse("Require a canonical relative member path")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != path
        or any(p in {".", ".."} for p in path.split("/"))
    ):
        refuse("Member paths must stay inside their declared input root")
    if (
        not isinstance(ref["sha256"], str)
        or re.fullmatch("[0-9a-f]{64}", ref["sha256"]) is None
    ):
        refuse("Require an exact SHA256 member pin")
    if type(ref["bytes"]) is not int or not 0 <= ref["bytes"] <= 1024 * 1024:
        refuse("Require a native member byte bound of at most one MiB")
    return ref


def member(value: object) -> dict[str, Any]:
    """Bind an existing evidence identity and role to its exact source bytes."""
    result = fields(value, {"path", "sha256", "bytes", "evidence_id", "role"})
    reference({k: result[k] for k in ("path", "sha256", "bytes")})
    for key in ("evidence_id", "role"):
        if not isinstance(result[key], str) or not result[key].strip():
            refuse("Require a nonempty evidence identity and role")
    return result


def _normalize(value: object) -> dict[str, Any]:
    result = fields(
        value,
        {
            "schema_version",
            "profile",
            "purpose",
            "envelope_ref",
            "cases",
            "design",
            "limits",
        },
    )
    if (result["schema_version"], result["profile"], result["purpose"]) != (
        "lra-source-cases.v1",
        PROFILE,
        "exploratory",
    ):
        refuse("Only exploratory fixed-support analytical cases are supported")
    reference(result["envelope_ref"])
    limits = fields(result["limits"], set(LIMITS))
    for key, maximum in LIMITS.items():
        positive(limits[key], maximum)
    cases = result["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= limits["max_cases"]:
        refuse("Case inventory exceeds its declared finite bound")
    ids = []
    for value in cases:
        case = fields(
            value,
            {"case_id", "request_ref", "parameter_declaration_ref", "evidence_members"},
        )
        ids.append(identifier(case["case_id"]))
        reference(case["request_ref"])
        reference(case["parameter_declaration_ref"])
        if (
            not isinstance(case["evidence_members"], list)
            or not case["evidence_members"]
        ):
            refuse("Require independently pinned evidence members")
        for evidence in case["evidence_members"]:
            member(evidence)
    if len(set(ids)) != len(ids):
        refuse("Case identities must be unique")
    result["cases"] = sorted(cases, key=lambda case: case["case_id"])
    design = result["design"]
    if not isinstance(design, dict):
        refuse("Require an explicit design kind")
    if design.get("kind") == "unweighted_sensitivity":
        fields(design, {"kind"})
    elif design.get("kind") == "caller_weighted_finite_design":
        fields(design, {"kind", "law_ref"})
        reference(design["law_ref"])
    else:
        refuse("Source cases provide sensitivity or a caller-declared finite design")
    return result


@dataclass(frozen=True)
class SourceCasePlan:
    """Own canonical plan bytes independently of mutable caller containers."""

    canonical_json: str

    def __post_init__(self) -> None:
        """Prevent direct construction from bypassing normalization."""
        try:
            normalized = canonical(_normalize(json.loads(self.canonical_json))).decode()
        except (ValueError, TypeError) as exc:
            refuse(f"Invalid plan JSON: {type(exc).__name__}")
        if normalized != self.canonical_json:
            refuse("Plan constructor requires canonical normalized JSON")

    @classmethod
    def from_dict(cls, value: object) -> SourceCasePlan:
        """Validate and own a canonical copy without sorting taxon axes."""
        return cls(canonical(_normalize(json.loads(canonical(value)))).decode())

    def payload(self) -> dict[str, Any]:
        """Return an independent mutable view of the immutable plan."""
        return dict(json.loads(self.canonical_json))

    @property
    def sha256(self) -> str:
        """Identify normalized enumeration while retaining exact source pins."""
        return digest(self.canonical_json.encode())
