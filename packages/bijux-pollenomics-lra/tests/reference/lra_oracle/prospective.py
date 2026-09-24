"""Frozen prospective inputs for optimized-LOVE live-R parity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

DECLARATION = Path(__file__).with_name("optimized_prospective.json")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_ARCHIVE_SHA256 = (
    "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
)
EXPECTED_DECLARATION_SHA256 = (
    "7bd61e0c7feefadf81428261443674612c6767e957fd25ea65591aeab9602ded"
)
EXPECTED_RESOURCE_SHA256 = {
    "LOVEexamplePollen.json": (
        "40e94bd1b261097ba6417054975f60a6d525b239cf3604079030e0929f0e0fcc"
    ),
    "LOVEexampleParams.json": (
        "34e861280b7a6ee4bc2d938f2f7c891ea057c44cdc3bfd60e5c27eadca915430"
    ),
    "LOVEexampleRings.json": (
        "bd574247e704e446dd2d3d70895aeefeae6d6d9f067436e289692cf3a5048445"
    ),
}
EXPECTED_EXCLUDED_INPUT_SHA256 = {
    "case-a-taxa.csv": (
        "5d0a391b9d186bc1881390f9e0ddd515caae8d28765635099fcbdbc6c37ab9c2"
    ),
    "case-a-fractions.csv": (
        "717f2fc782b1eaa1df8f0a4e9523bde7069a94e2922f7f820ea3baae39f0bb29"
    ),
    "case-b-taxa.csv": (
        "7b98525bbcf481c0d9c9e74306836debece3f5c6d9de56712cac27d9d0b30424"
    ),
    "case-b-fractions.csv": (
        "e8b63fde9d73dfb438bab7a77b3ca4e79619bbffc628504603b085bcc6ede0e2"
    ),
}
TOLERANCE_RATIONALE = (
    "The prospective fixed-input gate allows only 1e-10 absolute plus 1e-10 "
    "relative cross-runtime floating-point drift, far below the source wrapper's "
    "1e-4 cover and 1e-2 pollen rounding; it is fixed before R execution and must "
    "not be relaxed after observing results."
)
EXPECTED_ACCEPTANCE = {
    "rtol": 1e-10,
    "atol": 1e-10,
    "tolerance_rationale": TOLERANCE_RATIONALE,
    "axes": "exact",
    "selected_candidate_index": "exact",
    "replay_termination": {
        "iterations": 1,
        "evaluations": "declared_candidate_count",
        "success": True,
    },
    "nonfinite_objective": "both_runtimes_return_nan",
    "all_nonfinite_replay": "both_runtimes_refuse",
    "stochastic_optimizer_trajectory": "excluded",
}
EXPECTED_CLAIM_BOUNDARY = [
    "The gate tests numerical translation and source-wrapper behavior only.",
    "Shared candidates do not establish identical stochastic optimizer trajectories.",
    "Synthetic source-shaped inputs do not establish ecological accuracy.",
]
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "declaration_id",
    "reference",
    "source_resources",
    "excluded_previously_observed_inputs",
    "acceptance",
    "claim_boundary",
    "taxa",
    "cases",
}


@dataclass(frozen=True, slots=True)
class ProspectiveOptimizedCase:
    """One source-compatible input fixed before reference execution."""

    case_id: str
    max_ring_love: int
    local_counts: np.ndarray
    regional_counts: np.ndarray
    candidates: np.ndarray
    input_sha256: str


@dataclass(frozen=True, slots=True)
class ProspectiveOptimizedDeclaration:
    """Validated declaration and its canonical byte identity."""

    declaration_id: str
    declaration_sha256: str
    taxa: tuple[str, ...]
    rtol: float
    atol: float
    cases: tuple[ProspectiveOptimizedCase, ...]
    raw: dict[str, Any]


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_counts(value: object, name: str, size: int) -> np.ndarray:
    counts = np.asarray(value)
    if counts.shape != (size,) or counts.dtype.kind not in "iu":
        raise ValueError(f"{name} must contain one integer count per taxon")
    if np.any(counts < 0) or int(counts.sum()) <= 0:
        raise ValueError(f"{name} must be nonnegative with positive total")
    counts = np.asarray(counts, dtype=float)
    counts.setflags(write=False)
    return counts


def load_prospective_optimized_declaration() -> ProspectiveOptimizedDeclaration:
    """Load and strictly validate the checked prospective declaration."""
    payload = DECLARATION.read_bytes()
    if hashlib.sha256(payload).hexdigest() != EXPECTED_DECLARATION_SHA256:
        raise ValueError("Prospective declaration bytes differ from the frozen input")
    raw = json.loads(payload)
    if set(raw) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("Prospective declaration fields are invalid")
    if raw.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported optimized-LOVE declaration schema")
    reference = raw.get("reference", {})
    if reference != {
        "package": "disqover",
        "version": "0.9.14",
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
    }:
        raise ValueError("Prospective declaration reference identity is invalid")
    archive = PROJECT_ROOT / "vendor" / "disqover_0.9.14.tar.gz"
    if _file_sha256(archive) != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Pinned DISQOVER archive bytes are invalid")
    if raw.get("source_resources") != EXPECTED_RESOURCE_SHA256:
        raise ValueError("Prospective source-resource identities are invalid")
    resource_directory = PROJECT_ROOT / "src/bijux_pollenomics_lra/resources/data"
    for name, expected in EXPECTED_RESOURCE_SHA256.items():
        if _file_sha256(resource_directory / name) != expected:
            raise ValueError(f"Prospective source resource bytes are invalid: {name}")
    if raw.get("excluded_previously_observed_inputs") != (
        EXPECTED_EXCLUDED_INPUT_SHA256
    ):
        raise ValueError("Previously observed input exclusions are invalid")
    acceptance = raw.get("acceptance", {})
    if acceptance != EXPECTED_ACCEPTANCE:
        raise ValueError("Prospective acceptance policy is invalid")
    if raw.get("claim_boundary") != EXPECTED_CLAIM_BOUNDARY:
        raise ValueError("Prospective claim boundary is invalid")
    rtol = float(acceptance.get("rtol", float("nan")))
    atol = float(acceptance.get("atol", float("nan")))

    taxa = tuple(raw.get("taxa", ()))
    if len(taxa) < 2 or len(taxa) != len(set(taxa)) or not all(taxa):
        raise ValueError("Prospective taxon axis must be unique and nonempty")
    declared_cases = raw.get("cases")
    if not isinstance(declared_cases, list) or len(declared_cases) < 3:
        raise ValueError("At least three prospective optimized-LOVE cases are required")

    cases: list[ProspectiveOptimizedCase] = []
    seen: set[str] = set()
    identities: set[str] = set()
    for item in declared_cases:
        if not isinstance(item, dict):
            raise TypeError("Prospective cases must be JSON objects")
        if set(item) != {
            "id",
            "max_ring_love",
            "local_counts",
            "regional_counts",
            "candidates",
        }:
            raise ValueError("Prospective case fields are invalid")
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("Prospective case IDs must be unique nonempty strings")
        seen.add(case_id)
        maximum = item.get("max_ring_love")
        if not isinstance(maximum, int) or not 7 <= maximum < 36:
            raise ValueError("Prospective max_ring_love must retain regional rings")
        local = _positive_counts(item.get("local_counts"), "local_counts", len(taxa))
        regional = _positive_counts(
            item.get("regional_counts"), "regional_counts", len(taxa)
        )
        candidates = np.asarray(item.get("candidates"), dtype=float)
        if candidates.ndim != 2 or candidates.shape[1] != len(taxa):
            raise ValueError("Prospective candidates must use the declared taxon axis")
        if len(candidates) < 3 or not np.isfinite(candidates).all():
            raise ValueError("Prospective candidates must be finite and nontrivial")
        if np.any(candidates < 0) or np.any(candidates > 1):
            raise ValueError("Prospective candidates must satisfy the source bounds")
        if np.any(candidates.sum(axis=1) <= 0):
            raise ValueError("Prospective candidates must have positive total cover")
        if len(np.unique(candidates, axis=0)) != len(candidates):
            raise ValueError("Prospective candidates must be distinct")
        candidates.setflags(write=False)
        identity = _canonical_sha256(item)
        if identity in identities:
            raise ValueError("Prospective case inputs must be distinct")
        identities.add(identity)
        cases.append(
            ProspectiveOptimizedCase(
                case_id=case_id,
                max_ring_love=maximum,
                local_counts=local,
                regional_counts=regional,
                candidates=candidates,
                input_sha256=identity,
            )
        )

    return ProspectiveOptimizedDeclaration(
        declaration_id=str(raw["declaration_id"]),
        declaration_sha256=hashlib.sha256(payload).hexdigest(),
        taxa=taxa,
        rtol=rtol,
        atol=atol,
        cases=tuple(cases),
        raw=raw,
    )
