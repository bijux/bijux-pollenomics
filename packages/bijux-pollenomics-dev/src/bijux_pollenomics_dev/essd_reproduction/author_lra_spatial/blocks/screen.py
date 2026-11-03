"""Screen declared source footprints and saved request coverage before block fits."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.fitted.admission import (
    Footprint,
)
from bijux_pollenomics.analysis.lra_validation.spatial.support import support_separation
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..inputs import decode, require
from ..products import code_state, reopen, resources, write


def _number(value: Any) -> float:
    require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "Finite nonnegative block support scalar required",
    )
    return float(value)


def screen_blocks(packet: dict[str, Any], *, minimum_buffer_m: float) -> dict[str, Any]:
    """Keep geometry admission separate from hypothetical unbuffered fit reuse."""
    minimum = _number(minimum_buffer_m)
    require(minimum > 0, "A positive separation buffer is required")
    require(
        packet["schema_version"] == "author-lra-spatial-block-inputs.v1",
        "Declared block input schema required",
    )
    sites = packet["sites"]
    require(
        type(sites) is list and len(sites) >= 4,
        "A complete two-block site population is required",
    )
    require(
        all(
            type(row[key]) is str and row[key]
            for row in sites
            for key in ("record_id", "group_id", "block_id")
        ),
        "Literal source and block identities required",
    )
    index = {row["record_id"]: row for row in sites}
    require(
        len(index) == len(sites) == len({row["group_id"] for row in sites}),
        "Distinct source physical groups are required",
    )
    blocks = sorted({row["block_id"] for row in sites})
    require(
        len(blocks) == 2 and all(isinstance(value, str) and value for value in blocks),
        "Exactly two declared geographic blocks required",
    )
    priority = packet["regional_priority"]
    require(
        len(priority) == len(set(priority)) == len(index)
        and set(priority) == set(index),
        "Complete original regional priority required",
    )
    for row in sites:
        for name in ("source_radius_m", "target_radius_m", "coordinate_uncertainty_m"):
            _number(row[name])
        require(
            row["source_radius_m"] > 0 and row["target_radius_m"] > 0,
            "Positive declared source and target footprints required",
        )
    saved = {
        (row["local_record_id"], row["regional_anchor_record_id"]): row[
            "request_sha256"
        ]
        for row in packet["saved_pairs"]
    }
    require(
        len(saved) == len(packet["saved_pairs"]) == len(set(saved.values())),
        "Unique saved local/anchor request identities required",
    )
    require(
        all(
            local in index and anchor in index and local != anchor
            for local, anchor in saved
        ),
        "Foreign saved pair owner",
    )
    result_blocks, roles = [], []
    required: set[tuple[str, str]] = set()
    for block in blocks:
        targets = sorted(
            record for record, row in index.items() if row["block_id"] == block
        )
        training = sorted(set(index) - set(targets))
        require(
            len(targets) >= 2 and len(training) >= 2,
            "Two populated blocks with inner-site roles required",
        )
        comparisons = []
        excluded_groups = set()
        for source in training:
            source_row = index[source]
            for target in targets:
                target_row = index[target]
                distance = support_separation(
                    Footprint(
                        target_row["latitude"],
                        target_row["longitude"],
                        target_row["target_radius_m"],
                        target_row["coordinate_uncertainty_m"],
                    ),
                    Footprint(
                        source_row["latitude"],
                        source_row["longitude"],
                        source_row["source_radius_m"],
                        source_row["coordinate_uncertainty_m"],
                    ),
                )
                eligible = distance.lower_bound_m >= minimum
                if not eligible:
                    excluded_groups.add(source_row["group_id"])
                comparisons.append(
                    {
                        "source_record_id": source,
                        "target_record_id": target,
                        "source_group_id": source_row["group_id"],
                        "target_group_id": target_row["group_id"],
                        "distance": asdict(distance),
                        "eligible": eligible,
                    }
                )
        admitted = [
            record
            for record in training
            if index[record]["group_id"] not in excluded_groups
        ]
        result_blocks.append(
            {
                "block_id": block,
                "target_record_ids": targets,
                "candidate_training_record_ids": training,
                "admitted_training_record_ids": admitted,
                "excluded_training_record_ids": sorted(set(training) - set(admitted)),
                "regional_anchor_record_id": next(
                    (owner for owner in priority if owner in admitted), None
                ),
                "comparisons": comparisons,
                "target_dispositions": [
                    {
                        "record_id": target,
                        "status": "support_admitted"
                        if admitted
                        else "refused_no_admitted_training",
                    }
                    for target in targets
                ],
            }
        )
        for kind, inner in [
            ("outer", None),
            *(("inner", record) for record in training),
        ]:
            allowed = [record for record in training if record != inner]
            anchor = next(owner for owner in priority if owner in allowed)
            pairs = [(record, anchor) for record in allowed if record != anchor]
            required.update(pairs)
            roles.append(
                {
                    "heldout_block_id": block,
                    "kind": kind,
                    "inner_target": inner,
                    "training_record_ids": allowed,
                    "forbidden_record_ids": sorted(
                        [*targets, *([] if inner is None else [inner])]
                    ),
                    "regional_anchor_record_id": anchor,
                    "required_pairs": [
                        {
                            "local_record_id": local,
                            "regional_anchor_record_id": regional,
                            "request_sha256": saved.get((local, regional)),
                        }
                        for local, regional in pairs
                    ],
                    "status": "all_pairs_covered"
                    if all(pair in saved for pair in pairs)
                    else "missing_saved_pair",
                }
            )
    return {
        "schema_version": "author-lra-block-screen.v1",
        "minimum_buffer_m": minimum,
        "blocks": result_blocks,
        "unbuffered_pair_inventory": roles,
        "summary": {
            "sites": len(sites),
            "blocks": len(blocks),
            "cross_block_comparisons": sum(
                len(row["comparisons"]) for row in result_blocks
            ),
            "admitted_source_roles": sum(
                len(row["admitted_training_record_ids"]) for row in result_blocks
            ),
            "excluded_source_roles": sum(
                len(row["excluded_training_record_ids"]) for row in result_blocks
            ),
            "target_roles": len(sites),
            "admitted_target_roles": sum(
                len(row["target_dispositions"])
                for row in result_blocks
                if row["admitted_training_record_ids"]
            ),
            "unbuffered_roles": len(roles),
            "distinct_required_pairs": len(required),
            "distinct_covered_pairs": len(required & set(saved)),
            "distinct_missing_pairs": len(required - set(saved)),
        },
        "scope": "geometry_and_request_inventory_only",
    }


def produce(
    repository: Path, archive: Path, data_root: Path, protocol_path: Path, output: Path
) -> dict[str, Any]:
    """Bind original metadata, screen once, and preserve the complete refusal ledger."""
    from .inputs import check_block_sources, load_block_inputs

    started = time.monotonic()
    repository = repository.resolve(strict=True)
    archive, data_root = archive.resolve(strict=True), data_root.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    state = code_state(repository)
    packet = load_block_inputs(repository, archive, data_root, protocol)
    screen = screen_blocks(
        packet, minimum_buffer_m=protocol["policy"]["minimum_buffer_m"]
    )
    expected = protocol["expected"]
    require(
        len(packet["sites"]) == expected["sites"]
        and sorted({site["block_id"] for site in packet["sites"]}) == expected["blocks"]
        and len(packet["saved_pairs"]) == expected["saved_pairs"]
        and screen["summary"]["cross_block_comparisons"]
        == expected["cross_block_comparisons"],
        "Prospective source population differs",
    )
    output.mkdir()
    maximum = protocol["limits"]["max_output_bytes"]
    pins = {
        "inputs": write(output, "inputs.json", packet, maximum),
        "screen": write(output, "screen.json", screen, maximum),
    }
    for pin in pins.values():
        reopen(output, pin)
    check_block_sources(repository, archive, data_root, packet)
    require(
        protocol_path.read_bytes() == raw_protocol and code_state(repository) == state,
        "Source code, protocol, HEAD or index changed",
    )
    result = {
        "status": "screened_awaiting_independent_verification",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
        "products": pins,
        "source_guards_passed": True,
        "resources": resources(started, output, protocol["limits"]),
    }
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Run one explicit geometry-only block feasibility screen."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "archive", "data-root", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = produce(
        args.repository, args.archive, args.data_root, args.protocol, args.output
    )
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
