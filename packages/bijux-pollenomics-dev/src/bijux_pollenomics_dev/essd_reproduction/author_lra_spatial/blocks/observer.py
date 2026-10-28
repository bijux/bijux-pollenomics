"""Read original block metadata and certify the frozen support decisions independently."""

from __future__ import annotations

import argparse
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..inputs import decode, require
from ..products import code_state, reopen, resources, write
from .audit import audit_block_screen
from .inputs import check_block_sources


def _original(root: Path, pin: dict[str, Any], *, archived: bool = False) -> bytes:
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "Relative original metadata reference required",
    )
    path = (
        root / "objects" / pin["sha256"][:2] / pin["sha256"]
        if archived
        else root / relative
    )
    require(
        path.is_file()
        and not any(part.is_symlink() for part in (path, *path.parents))
        and path.stat().st_size == pin["bytes"],
        "Ordinary original metadata object required",
    )
    raw = path.read_bytes()
    require(
        len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
        "Original metadata identity changed",
    )
    return raw


def bind_metadata(
    repository: Path,
    archive: Path,
    data_root: Path,
    protocol: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Independently join original CSV/geometry owners and saved request identities."""
    source = protocol["sources"]
    parent = decode(_original(repository, source["parent_protocol"]))
    nominal = decode(_original(repository, source["nominal_inputs"]))
    rows = list(
        csv.DictReader(
            StringIO(_original(data_root, source["site_metadata"]).decode("utf-8-sig")),
            strict=True,
        )
    )
    native = {row["filename"]: row for row in rows}
    require(
        len(native) == len(rows) == 17,
        "Seventeen original native metadata rows required",
    )
    pins = {row["path"]: row for row in parent["author_inputs"]}
    experiment = decode(_original(archive, pins["experiment.json"], archived=True))
    originals = {row["record_id"]: row for row in experiment["sites"]}
    actual = {row["record_id"]: row for row in packet["sites"]}
    require(
        len(actual) == len(packet["sites"]) == 15
        and set(actual) == set(originals) == set(nominal["groups"]),
        "Complete original fifteen-site ownership required",
    )
    require(
        packet["regional_priority"] == experiment["regional_priority"],
        "Original priority changed",
    )
    exclusions = sorted(set(native) - {site["site_id"] for site in originals.values()})
    require(
        exclusions == packet["excluded_source_block_ids"] == ["EXEBRID", "WHH11"]
        and packet["excluded_source_block_reasons"]
        == dict.fromkeys(exclusions, "outside_author_TW5_cohort"),
        "Source-only exclusions changed",
    )
    require(
        packet["policy"] == protocol["policy"],
        "Prospective support interpretation changed",
    )
    roles = set()
    pairs: dict[tuple[str, str], str] = {}
    inverse: dict[str, tuple[str, str]] = {}
    cutoff_by_owner: dict[str, set[float]] = {record: set() for record in originals}
    for context in nominal["contexts"]:
        outer, target = context["outer_target"], context["target"]
        require((outer, target) not in roles, "Duplicate saved metadata role")
        roles.add((outer, target))
        cutoff_by_owner[target].add(context["forward"]["regional_cutoff_m"])
        for predictor in context["predictors"]:
            pair = predictor["record_id"], context["anchor"]
            sha = predictor["request_sha256"]
            require(
                pairs.get(pair, sha) == sha and inverse.get(sha, pair) == pair,
                "Saved pair/request identity changed",
            )
            pairs[pair], inverse[sha] = sha, pair
    require(
        roles == {(outer, target) for outer in originals for target in originals}
        and len(pairs) == len(inverse) == 39,
        "Complete saved metadata roles and request population required",
    )
    expected_pairs = [
        {
            "local_record_id": local,
            "regional_anchor_record_id": anchor,
            "request_sha256": sha,
        }
        for (local, anchor), sha in sorted(pairs.items())
    ]
    require(packet["saved_pairs"] == expected_pairs, "Source pair projection differs")
    blocks: dict[str, int] = {}
    for record, site in originals.items():
        row = native[site["site_id"]]
        pin = pins[site["geometry"]["path"]]
        require(
            site["geometry"] == {"path": pin["path"], "sha256": pin["sha256"]},
            "Original geometry pin differs",
        )
        geometry = decode(_original(archive, pin, archived=True))
        radii = [
            ring["outer_m"]
            for name in ("inversion_rings", "forward_rings")
            for ring in geometry[name]
        ]
        require(
            cutoff_by_owner[record] == {100000.0},
            "Explicit saved forward cutoff differs",
        )
        radii.extend(cutoff_by_owner[record])
        declared = experiment["request_template"]["configuration"]["reveals"]
        if "region_cutoff_m" in declared:
            radii.append(declared["region_cutoff_m"])
        expected_site = {
            "record_id": record,
            "group_id": nominal["groups"][record],
            "block_id": row["LCGRID_ID"],
            "latitude": float(row["latdd"]),
            "longitude": float(row["londd"]),
            "source_radius_m": float(max(radii)),
            "target_radius_m": float(experiment["local_support_radius_m"]),
            "coordinate_uncertainty_m": 0.0,
            "geometry_reference": pin,
            "basin_shoreline_radius_m": float(row["radius"]),
        }
        require(
            actual[record] == expected_site
            and expected_site["latitude"] == geometry["latitude"]
            and expected_site["longitude"] == geometry["longitude"]
            and expected_site["basin_shoreline_radius_m"]
            == geometry["basin"]["diameter_m"] / 2,
            "Literal source geometry, shoreline, grid or footprint projection differs",
        )
        blocks[row["LCGRID_ID"]] = blocks.get(row["LCGRID_ID"], 0) + 1
    require(blocks == {"512": 8, "562": 7}, "Native block population differs")
    check_block_sources(repository, archive, data_root, packet)
    return {
        "sites": 15,
        "native_metadata_rows": 17,
        "blocks": blocks,
        "saved_request_pairs": 39,
        "original_geometry_objects": 15,
        "raw_outcomes_opened": 0,
        "prediction_values_consumed": 0,
    }


def observe(
    repository: Path,
    archive: Path,
    data_root: Path,
    protocol_path: Path,
    products: Path,
    output: Path,
) -> dict[str, Any]:
    """Authenticate products and verify source joins plus independent geometric bounds."""
    started = time.monotonic()
    repository, archive, data_root = (
        path.resolve(strict=True) for path in (repository, archive, data_root)
    )
    products = products.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    state = code_state(repository)
    raw_result = (products / "result.json").read_bytes()
    result = decode(raw_result)
    require(
        result["source_commit"] == state["head"]
        and result["index_sha256"] == state["index_sha256"]
        and result["protocol_sha256"] == hashlib.sha256(raw_protocol).hexdigest()
        and result["source_guards_passed"] is True,
        "Screen producer epoch differs",
    )
    packet = reopen(products, result["products"]["inputs"])
    screened = reopen(products, result["products"]["screen"])
    sources = bind_metadata(repository, archive, data_root, protocol, packet)
    audited = audit_block_screen(packet, screened)
    check_block_sources(repository, archive, data_root, packet)
    for pin in result["products"].values():
        reopen(products, pin)
    require(
        protocol_path.read_bytes() == raw_protocol
        and (products / "result.json").read_bytes() == raw_result
        and code_state(repository) == state,
        "Consumed source, products, HEAD or index changed",
    )
    output.mkdir()
    facts = {
        "status": "verified",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "source_metadata": sources,
        "geometry_and_roles": audited,
        "resources": resources(started, output, protocol["limits"], observer=True),
    }
    write(output, "verification.json", facts, protocol["limits"]["max_output_bytes"])
    resources(started, output, protocol["limits"], observer=True)
    return facts


def main() -> None:
    """Read back the exact declared model-free geographic block screen."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "repository",
        "archive",
        "data-root",
        "protocol",
        "products",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = observe(
        args.repository,
        args.archive,
        args.data_root,
        args.protocol,
        args.products,
        args.output,
    )
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
