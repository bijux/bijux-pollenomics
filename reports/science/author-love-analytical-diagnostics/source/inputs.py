"""Join authenticated nominal regional fractions to fresh analytical request identities."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import runpy
from typing import Any


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def decode(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            require(key not in result, "Duplicate scientific JSON member")
            result[key] = value
        return result

    def refuse(value: str) -> None:
        raise ValueError("Nonfinite scientific JSON: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked(root: Path, row: dict[str, Any]) -> bytes:
    name = Path(row["path"])
    path = root / name
    require(
        ".." not in name.parts
        and path.is_file()
        and path.stat().st_nlink == 1
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Independent declared scientific file required",
    )
    raw = path.read_bytes()
    require(
        type(row["bytes"]) is int
        and len(raw) == row["bytes"]
        and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Declared scientific file changed: " + str(path),
    )
    return raw


def regional(
    row: dict[str, Any], payload: dict[str, Any], checksum: str, item_id: str
) -> list[float]:
    taxa = payload["taxa"]
    values = row["regional_cover"]
    require(
        row["request_sha256"] == checksum
        and row["item_id"] == item_id
        and row["taxa"] == taxa
        and len(taxa) == len(set(taxa)) == 30
        and type(row["regional_percent_precision_decimals"]) is int
        and row["regional_percent_precision_decimals"] == 3
        and isinstance(values, list)
        and len(values) == len(taxa)
        and all(
            type(v) in (int, float)
            and math.isfinite(v)
            and 0 <= v <= 1
            and abs(v * 100 - round(v * 100, 3)) <= 1e-10
            for v in values
        ),
        "Exact labelled thirty-taxon source3decimal percent/fraction handoff required",
    )
    total = math.fsum(values)
    require(
        type(row["regional_fraction_sum"]) in (int, float)
        and math.isfinite(row["regional_fraction_sum"])
        and abs(total - row["regional_fraction_sum"]) <= 1e-12
        and abs(total - 1) <= 30 * 0.000005 + 1e-12,
        "Raw regional fraction mass differs; never normalize the background",
    )
    return list(values)


def analytical(payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    require(
        payload["method_profile"] == "ring-taxon-preserving"
        and payload["configuration"]["love"]["method"] == "optimized"
        and payload["configuration"]["love"]["optimizer_backend"]
        == "scipy.slsqp-simplex-uniform"
        and payload["configuration"]["love"]["optimized_profile"]
        == "ring-taxon-preserving",
        "Exact admitted nominal profile required",
    )
    result["method_profile"] = "disqover-0.9.14-source-compatible"
    local = result["configuration"]["love"]
    local["method"] = "analytical"
    for key in (
        "optimizer_backend",
        "optimized_profile",
        "optimizer_iterations",
        "optimizer_max_evaluations",
        "optimizer_tolerance",
    ):
        del local[key]
    require(
        local["repeats"] == 1
        and local["max_ring"] == 2
        and local["stochastic"] is False
        and local["distance_weighting"] == "gpm neutral"
        and local["fall_speed_profile"] == "disqover-0.9.14-wrapper-v1"
        and result["configuration"]["reveals"]["stochastic"] is False,
        "Same deterministic nominal transport/parameter profile required",
    )
    return result


def load(
    repository: Path, prepared: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from bijux_pollenomics.analysis.lra.api import LRABatchItem
    from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        SourceExperimentSpec,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        make_request,
    )
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    for row in protocol["source_pins"]:
        checked(repository, row)
    borrowed = protocol["borrowed_sources"]
    for row in borrowed.values():
        checked(repository, row)
    common = runpy.run_path(str(repository / borrowed["common"]["path"]))
    admission = runpy.run_path(str(repository / borrowed["admission"]["path"]))
    descriptor = decode(
        checked(repository, protocol["prior_evidence"]["nominal_descriptor"])
    )
    rows = [row for row in descriptor["shards"] if row["method"] == "gpm neutral"]
    require(
        len(rows) == 1
        and rows[0]["training"] == protocol["prior_evidence"]["nominal_training"],
        "Exact nominal shard required",
    )
    authority = decode(
        checked(repository, protocol["prior_evidence"]["nominal_authority"])
    )
    require(
        authority["source_candidate"] == protocol["nominal_candidate"]
        and authority["independent_semantics"]["scientific_saved_products_admitted"]
        is True
        and authority["independent_semantics"]["approved"] is True,
        "Independent nominal saved-result authority required",
    )
    admitted = admission["admit_shard"](
        common,
        repository,
        rows[0],
        protocol["nominal_candidate"],
        protocol["nominal_training_protocol_sha256"],
    )
    require(
        len(protocol["inputs"]) == 37
        and {p.name for p in prepared.iterdir()}
        == {r["path"] for r in protocol["inputs"]},
        "Exact original37 input namespace required",
    )
    bodies = {r["path"]: checked(prepared, r) for r in protocol["inputs"]}
    require(
        len(bodies) == 37 and all(Path(name).name == name for name in bodies),
        "Unique original basename inputs required",
    )
    experiment = decode(bodies["experiment.json"])
    spec = SourceExperimentSpec(experiment)
    require(
        len(spec.sites) == 15
        and len(experiment["request_template"]["taxa"]) == 30
        and experiment["request_template"]["temporal_matching"]
        == protocol["temporal_matching"],
        "Exact15sites/30taxa/TW5 support required",
    )
    ancestry = runpy.run_path(str(repository / borrowed["requests"]["path"]))
    original = {
        "grouped_leave_one_out": grouped_leave_one_out,
        "make_request": make_request,
        "LRABatchItem": LRABatchItem,
    }
    contexts, _ = ancestry["contexts"](original, spec)
    numeric, logical = ancestry["requests"](original, spec, prepared, contexts)
    training = decode(
        checked(repository, protocol["prior_evidence"]["nominal_training"])
    )
    require(
        len(numeric) == 39
        and len(logical) == 2715
        and digest(logical) == digest(training["logical_requests"])
        and digest(logical) == protocol["logical_ancestry_sha256"]
        and set(numeric) == set(training["numerical_requests"]),
        "Full39request/2715ancestry closure changed",
    )
    result = []
    for checksum, item in sorted(numeric.items()):
        payload = validate_request(item.payload(), input_root=prepared).payload()
        require(item.request_sha256 == checksum, "Original request hash changed")
        local_ids = {
            row["local_record_id"]
            for row in logical
            if row["request_sha256"] == checksum
        }
        require(len(local_ids) == 1, "Exact numeric local identity required")
        vector = regional(
            training["numerical_requests"][checksum],
            payload,
            checksum,
            next(iter(local_ids)),
        )
        changed = analytical(payload)
        validated = validate_request(changed, input_root=prepared)
        require(
            validated.sha256 != checksum,
            "Analytical request must have its own identity",
        )
        result.append(
            {
                "nominal_request_sha256": checksum,
                "analytical_request_sha256": validated.sha256,
                "payload": validated.payload(),
                "regional_cover": vector,
            }
        )
    return result, {
        "original_native_exit": 1,
        "saved_products_admitted_separately": True,
        "nominal_candidate": protocol["nominal_candidate"],
        "logical_requests": 2715,
        "contexts": 225,
        "references": admitted["references"],
    }
