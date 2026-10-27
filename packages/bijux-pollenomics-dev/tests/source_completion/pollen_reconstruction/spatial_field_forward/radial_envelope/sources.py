"""Read qualified saved identities without raw counts or a new scientific replay."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from .exact_arithmetic import require

PROTOCOL = "reports/science/pollen-reconstruction/spatial-field-forward/radial-envelope/protocol.json"
CORES = ("BOKE", "BUS", "SOLSOE83")
AXIS = ("Betula", "Ulmus")
FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)


def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def decode(body: bytes) -> dict[str, Any]:
    value: Any = json.loads(body, object_pairs_hook=object_pairs)
    require(isinstance(value, dict), "JSON object required")
    assert isinstance(value, dict)
    json.dumps(value, allow_nan=False)
    return value


def confined(repository: Path, relative: str) -> Path:
    require(
        not Path(relative).is_absolute() and ".." not in Path(relative).parts,
        "relative confined source path required",
    )
    result = repository / relative
    require(
        result.is_file()
        and not result.is_symlink()
        and result.resolve().is_relative_to(repository.resolve()),
        "source missing or outside repository",
    )
    require(
        not any(parent.is_symlink() for parent in result.parents),
        "source ancestry alias",
    )
    return result


def bound(repository: Path, relative: str, pin: dict[str, Any]) -> bytes:
    require(set(pin) == {"bytes", "sha256"}, "data identity fields differ")
    body = confined(repository, relative).read_bytes()
    require(
        type(pin["bytes"]) is int
        and len(body) == pin["bytes"]
        and sha256(body).hexdigest() == pin["sha256"],
        "saved input byte identity differs",
    )
    return body


def prediction_inputs(
    repository: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """The old native scored-result path is intentionally never opened here."""
    protocol = decode(confined(repository, PROTOCOL).read_bytes())
    require(
        protocol["schema_version"] == "spatial-field-radial-envelope-protocol.v1",
        "prospective protocol schema differs",
    )
    require(
        protocol["cores"] == list(CORES) and protocol["axis"] == list(AXIS),
        "fixed scientific population differs",
    )
    require(
        protocol["design"]
        == {
            "coarse_rings": 8,
            "subdivisions_per_coarse_ring": 16,
            "refined_rings_per_geometry": 128,
            "taxon_geometries": 6,
            "fixed_homogeneous_ring_calls": 768,
            "endpoint_lattice_bits": 96,
        },
        "fixed partition/certificate design differs",
    )
    roles = (
        "source_prediction",
        "source_result",
        "source_verification",
        "source_execution",
    )
    require(
        set(protocol["repository_inputs"]) == {protocol[role] for role in roles},
        "four qualified saved inputs required",
    )
    prediction = decode(
        bound(
            repository,
            protocol["source_prediction"],
            protocol["repository_inputs"][protocol["source_prediction"]],
        )
    )
    observer = decode(
        bound(
            repository,
            protocol["source_verification"],
            protocol["repository_inputs"][protocol["source_verification"]],
        )
    )
    execution = decode(
        bound(
            repository,
            protocol["source_execution"],
            protocol["repository_inputs"][protocol["source_execution"]],
        )
    )
    require(
        prediction["schema_version"] == "spatial-field-forward-predictions.v1"
        and prediction["source_commit"] == protocol["prior_producer_source_commit"],
        "prior prediction authority differs",
    )
    require(
        execution["source_commit"] == protocol["prior_observer_source_commit"]
        and execution["exit_code"] == 0
        and execution["pytest_passed"] == 1,
        "prior independent qualification did not pass",
    )
    pins = protocol["repository_inputs"]
    require(
        observer["predictions_sha256"]
        == execution["source_results"]["predictions_sha256"]
        == pins[protocol["source_prediction"]]["sha256"]
        and observer["result_sha256"]
        == execution["source_results"]["result_sha256"]
        == pins[protocol["source_result"]]["sha256"],
        "prior prediction/result qualification identity differs",
    )
    require(
        (
            observer["source_rows"],
            observer["selected_samples"],
            observer["source_contexts"],
            observer["scores"]["scored_rows"],
            observer["scores"]["refused_rows"],
        )
        == (147, 59, 18, 54, 0),
        "prior complete eligible population differs",
    )
    require(
        prediction["axis"] == list(AXIS)
        and [row["core"] for row in prediction["geometry"]] == list(CORES),
        "saved geometry population/order differs",
    )
    require(
        len(prediction["contexts"])
        == len({row["context_id"] for row in prediction["contexts"]})
        == 18,
        "saved context population differs",
    )
    original_body = confined(repository, protocol["original_protocol"]).read_bytes()
    committed = subprocess.check_output(
        [
            "git",
            "-C",
            str(repository),
            "show",
            f"{protocol['prior_producer_source_commit']}:{protocol['original_protocol']}",
        ],
        timeout=10,
    )
    require(
        original_body == committed,
        "original physical protocol changed from its accepted source",
    )
    original = decode(original_body)
    return protocol, prediction, original
