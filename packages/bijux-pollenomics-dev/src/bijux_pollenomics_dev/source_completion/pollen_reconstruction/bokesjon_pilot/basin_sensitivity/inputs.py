"""Authenticate the existing BOKE request and derive only declared basin evidence."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.analysis.lra.api import read_lra_product
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.workflow import read

from .protocol import BasinProfile, profiles_from_sources, static_geometry

BASELINE = Path(
    "artifacts/science/love-nonnegative-cover/cache/cal-bp-2700-3200/"
    "c3a99780c66f727ca71fe883b94fa74d421d21e1377d00a33c25357b431583e7"
)
BASELINE_SHA256 = "96c7d7e22fd3eec7291054f4ed063c3477b80cef5caf7c7aa40980f03fcb0dce"
REQUEST_SHA256 = "8b91a11f52b0ea27ecb0f2868d2d46cb6c5735860783e8aef805be1cac1aa050"
INPUT_ROOT = Path(
    "artifacts/physical-core/krageholm-regional-coupled/inputs/cal-bp-2700-3200"
)
BASIN_SOURCES = Path("data/neotoma/raw/bokesjon-core-sources/basin-sources.json")
BASIN_SOURCES_SHA256 = (
    "e1fcbb0aa17284465fca4e4eb5f2d2d678040e78bc514bf0489a6c19c5ad0cec"
)


@dataclass(frozen=True)
class BaselineInputs:
    """Authenticated original bytes; each request access returns an independent object."""

    request_bytes: bytes
    evidence: dict[str, bytes]
    directory: Path
    source_pins: tuple[dict[str, Any], ...]
    basin_sources: bytes

    @property
    def request(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.request_bytes))

    @property
    def profiles(self) -> tuple[BasinProfile, ...]:
        if hashlib.sha256(self.basin_sources).hexdigest() != BASIN_SOURCES_SHA256:
            raise ValueError("Basin source card identity differs")
        return profiles_from_sources(json.loads(self.basin_sources))


def load_basin_sources(
    repository: Path,
) -> tuple[bytes, tuple[BasinProfile, ...], dict[str, Any]]:
    """Authenticate authored fact-extraction bytes without claiming original capture."""
    raw, card = read(repository.absolute() / BASIN_SOURCES, BASIN_SOURCES_SHA256, 65536)
    return (
        raw,
        profiles_from_sources(card),
        {
            "path": str(BASIN_SOURCES),
            "sha256": BASIN_SOURCES_SHA256,
            "bytes": len(raw),
            "document_kind": "authored_fact_extraction_and_profile_declaration",
        },
    )


def load_inputs(repository: Path) -> BaselineInputs:
    """Verify the saved product and every consumed original evidence member."""
    repository = repository.absolute()
    basin_sources, _, basin_pin = load_basin_sources(repository)
    directory = repository / BASELINE
    read_lra_product(directory, expected_manifest_sha256=BASELINE_SHA256)
    raw, request = read(directory / "request.json", REQUEST_SHA256, 65536)
    evidence: dict[str, bytes] = {}
    pins: list[dict[str, Any]] = [
        basin_pin,
        {"path": str(BASELINE / "manifest.json"), "sha256": BASELINE_SHA256},
        {"path": str(BASELINE / "request.json"), "sha256": REQUEST_SHA256},
    ]
    for reference in request["evidence"]:
        name = reference["path"]
        if Path(name).name != name or name in evidence:
            raise ValueError("Unique basename evidence members required")
        body, _ = read(repository / INPUT_ROOT / name, reference["sha256"], 65536)
        evidence[name] = body
        pins.append(
            {
                "path": str(INPUT_ROOT / name),
                "sha256": reference["sha256"],
                "bytes": len(body),
            }
        )
    if len(evidence) != 9:
        raise ValueError("Exactly nine BOKE/KRAG evidence members required")
    return BaselineInputs(raw, evidence, directory, tuple(pins), basin_sources)


def _encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()


def materialize(
    inputs: BaselineInputs, profile: BasinProfile, destination: Path
) -> dict[str, Any]:
    """Bind changed geometry and its explicit conditional decision to original counts."""
    if hashlib.sha256(inputs.request_bytes).hexdigest() != REQUEST_SHA256:
        raise ValueError("Original request evidence differs")
    candidates = [row for row in inputs.profiles if row.name == profile.name]
    if len(candidates) != 1 or candidates[0].radius_m != profile.radius_m:
        raise ValueError("Profile differs from authenticated basin source facts")
    profile = candidates[0]
    request = inputs.request
    if destination.exists() or destination.is_symlink():
        raise ValueError("Absent profile input destination required")
    references = request["evidence"]
    if set(inputs.evidence) != {row["path"] for row in references} or any(
        hashlib.sha256(inputs.evidence[row["path"]]).hexdigest() != row["sha256"]
        for row in references
    ):
        raise ValueError("Original source evidence differs")
    evidence = deepcopy(inputs.evidence)
    geometry = static_geometry(
        json.loads(evidence["BOKE-geometry.json"]), profile.radius_m
    )
    evidence["BOKE-geometry.json"] = _encoded(geometry)
    evidence["decision.json"] = _encoded(
        {
            "inherited_decision": json.loads(evidence["decision.json"]),
            "basin_sensitivity": {
                "profile": profile.name,
                "radius_m": profile.radius_m,
                "source": profile.source,
                "basin_source_card": {
                    "path": str(BASIN_SOURCES),
                    "sha256": BASIN_SOURCES_SHA256,
                    "document_kind": "authored_fact_extraction_and_profile_declaration",
                },
                "scope": "Declared static modern circle, not dated basin or scientific acceptance",
                "fixed_support": "Center-relative500/1000m, shore+1 inversion, fully terrestrial annuli",
                "tolerance_percentage_points": 10,
                "tolerance_scope": "Profile sensitivity only, not measured vegetation accuracy",
            },
        }
    )
    request["local"]["basin"]["diameter_m"] = 2 * profile.radius_m
    geometry_id = request["local"]["basin"]["geometry_evidence_id"]
    request["rings"] = [
        dict(row, geometry_evidence_id=geometry_id)
        for row in geometry["inversion_rings"]
    ]
    for reference in references:
        reference["sha256"] = hashlib.sha256(evidence[reference["path"]]).hexdigest()
    request["versions"]["geometry"] = "bokesjon-static-basin-sensitivity.v1"
    destination.mkdir(parents=True)
    for name, body in evidence.items():
        (destination / name).write_bytes(body)
    return request
