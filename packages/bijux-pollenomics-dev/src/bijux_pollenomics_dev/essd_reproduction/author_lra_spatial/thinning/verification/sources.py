"""Postfreeze custody and orchestration of independent thinning source joins.

Original source custody is reused; original models and numerical prediction
producers are never replayed. Native projection and cohort ordering have their
own pure boundaries.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.source_audit import (
    bind_sources,
)

from .cohort import audit_cohort
from .predictions import require, same
from .projection import audit_projection


def read_pin(root: Path, pin: dict[str, Any], *, archived: bool = False) -> Any:
    require(set(pin) == {"path", "bytes", "sha256"}, "closed source pin")
    require(
        type(pin["bytes"]) is int and 0 < pin["bytes"] <= 140 * 1024**2,
        "source size ceiling",
    )
    sha = pin["sha256"]
    require(
        type(sha) is str
        and len(sha) == 64
        and all(c in "0123456789abcdef" for c in sha),
        "source SHA",
    )
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "ordinary source locator",
    )
    path = root / "objects" / sha[:2] / sha if archived else root / relative
    require(
        path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)),
        "ordinary nonsymlink source",
    )
    require(path.stat().st_size == pin["bytes"], "source byte size")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == sha, "source byte digest")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            require(key not in out, "duplicate JSON key")
            out[key] = value
        return out

    def invalid(value: str) -> Any:
        raise ValueError("Nonfinite original source: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def audit_inputs(
    repository: Path, archive: Path, protocol: dict[str, Any], packet: dict[str, Any]
) -> tuple[dict[str, dict[str, int]], dict[str, Any]]:
    """Bind all native sources before returning only the ten scoring count owners."""
    pins = protocol["qualified_sources"]
    require(
        set(pins)
        == {
            "result",
            "inputs",
            "nominal",
            "prediction_manifest",
            "candidates",
            "outer_scores",
            "choices",
            "selection_manifest",
            "protocol",
            "verification",
        },
        "qualified source role inventory",
    )
    documents = {key: read_pin(repository, pin) for key, pin in pins.items()}
    old_protocol, upstream = documents["protocol"], documents["inputs"]
    result, verified = documents["result"], documents["verification"]
    require(
        result["source_commit"]
        == verified["source_commit"]
        == protocol["upstream_source_commit"]
        and result["source_guards_passed"] is True
        and verified["source_guards_passed"] is True
        and verified["status"] == "verified",
        "qualified source epoch and guards",
    )
    require(
        verified["sources"]["passed"] is True
        and verified["numerical_predictions"]["status"]
        == verified["selection_and_scoring"]["status"]
        == "passed",
        "original independent qualification",
    )
    require(
        result["protocol_sha256"] == pins["protocol"]["sha256"],
        "qualified protocol identity",
    )

    def member(
        parent: dict[str, Any], row: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        require(Path(row["path"]).name == row["path"], "direct original product member")
        same({**row, "path": str(Path(parent["path"]).parent / row["path"])}, expected)

    for key in ("inputs", "nominal", "candidates", "choices", "outer_scores"):
        member(pins["result"], result["products"][key], pins[key])
    for key in ("prediction_manifest", "selection_manifest"):
        member(pins["result"], result[key], pins[key])
    for key in ("inputs", "nominal", "candidates"):
        member(
            pins["prediction_manifest"],
            documents["prediction_manifest"]["files"][key],
            pins[key],
        )
    member(
        pins["selection_manifest"],
        documents["selection_manifest"]["files"]["choices"],
        pins["choices"],
    )
    member(
        pins["selection_manifest"],
        documents["selection_manifest"]["prediction_manifest"],
        pins["prediction_manifest"],
    )
    nominal = documents["nominal"]
    require(
        nominal["passed"] is True
        and nominal["failures"] == []
        and nominal["forward_calls"]
        == nominal["vegetation_comparisons"]
        == nominal["pollen_comparisons"]
        == nominal["reference_baselines"]
        == 675
        and nominal["contexts"] == 225
        and nominal["maximum_vegetation_absolute_error"]
        == nominal["maximum_pollen_absolute_error"]
        == 0.0
        and nominal["absolute_tolerance"] == 1e-12,
        "qualified original nominal correspondence",
    )
    counts, source_facts = bind_sources(repository, archive, old_protocol, upstream)
    require(
        set(packet)
        == {
            "schema_version",
            "taxa",
            "groups",
            "cohort",
            "contexts",
            "observation_refs",
            "geometries",
            "geometry_refs",
            "pair_catalogue",
            "retained_reference_predictions",
            "sources",
            "support",
            "summary",
        },
        "closed new packet without duplicate original bank",
    )
    expected_sources = [
        *upstream["sources"],
        *[{**pin, "storage": "repository"} for pin in pins.values()],
    ]
    same(
        sorted(packet["sources"], key=lambda p: (p["storage"], p["path"])),
        sorted(expected_sources, key=lambda p: (p["storage"], p["path"])),
    )
    same(packet["taxa"], upstream["taxa"])
    same(packet["groups"], upstream["groups"])
    same(packet["support"], upstream["support"])
    catalogue = {pin["path"]: pin for pin in old_protocol["author_inputs"]}
    experiment = read_pin(archive, catalogue["experiment.json"], archived=True)
    sites = experiment["sites"]
    expected_geometry = {
        s["record_id"]: read_pin(
            archive, catalogue[s["geometry"]["path"]], archived=True
        )
        for s in sites
    }
    same(packet["geometries"], expected_geometry)
    same(
        packet["geometry_refs"],
        {s["record_id"]: catalogue[s["geometry"]["path"]] for s in sites},
    )
    cohort_facts = audit_cohort(packet, protocol)
    native = read_pin(
        archive, old_protocol["sources"]["nominal_training"], archived=True
    )
    metrics = audit_projection(
        protocol,
        packet,
        upstream,
        experiment,
        expected_geometry,
        native,
        old_protocol,
        documents,
        counts,
    )
    selected = packet["cohort"]["selected"]
    return {o: counts[o] for o in selected}, {
        "status": "passed",
        "original_source_join": source_facts,
        "cohort": cohort_facts,
        "new_contexts": 10,
        "native_pairs": 17,
        "retained_references": 40,
        "retained_reference_metrics": metrics,
        "scope": "Original source custody plus fresh nine-owner closures and immutable references; no old numerical study or model rerun",
    }
