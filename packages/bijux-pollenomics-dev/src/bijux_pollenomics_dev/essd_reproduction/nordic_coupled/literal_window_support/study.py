"""Bind two retained native cores to complete literal window accounting."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ...author_lra_spatial.products import code_state, resources, write
from ...physical_forward.inputs import decode, require
from ..native_panel_source import buffer
from .projection import project

PROVENANCE = ("raw_manifest", "relational_baseline", "literal_policy")
INHERITED = (
    "count_policy",
    "literal_status_precedence",
    "full_mass_policy",
    "age_numeric_interpretation",
    "suppression_semantics",
)


def read_pin(repository: Path, pin: dict[str, Any], maximum: int) -> bytes:
    """Read one exact ordinary repository source without following aliases."""
    require(set(pin) == {"path", "bytes", "sha256"}, "Closed source pin required")
    relative = Path(pin["path"])
    require(
        not relative.is_absolute()
        and ".." not in relative.parts
        and type(pin["bytes"]) is int
        and 0 < pin["bytes"] <= maximum
        and type(pin["sha256"]) is str
        and re.fullmatch("[0-9a-f]{64}", pin["sha256"]) is not None,
        "Bounded source path, size and SHA required",
    )
    return buffer(repository / relative, pin["sha256"], pin["bytes"], maximum)


def load_contract(repository: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    """Join source part identities to both retained manifest authorities."""
    require(
        protocol["schema_version"] == "nordic-literal-window-support-protocol.v1"
        and set(protocol["provenance"]) == set(PROVENANCE)
        and protocol["inherited_policy_fields"] == list(INHERITED)
        and protocol["source_max_bytes"] == 32 * 1024**2
        and [core["key"] for core in protocol["cores"]] == ["laihalampi", "dalmutladdo"]
        and [core["identity"]["source_sample_count"] for core in protocol["cores"]]
        == [150, 72],
        "Exact declared two-core source contract required",
    )
    documents = {
        key: decode(read_pin(repository, protocol["provenance"][key], 1024**2))
        for key in PROVENANCE
    }
    manifest, baseline, policy = (documents[key] for key in PROVENANCE)
    require(
        policy["schema_version"] == "krageholm-regional-literal-panel-protocol.v1"
        and policy["taxa"] == protocol["taxa"]
        and policy["windows"] == protocol["windows"]
        and baseline["input_artifacts"]["raw_archive"]["manifest_sha256"]
        == protocol["provenance"]["raw_manifest"]["sha256"],
        "Retained literal policy or manifest identity differs",
    )
    parts = {row["filename"]: row for row in manifest["parts"]}
    require(len(parts) == len(manifest["parts"]), "Unique native source parts required")
    for core in protocol["cores"]:
        source, identity = core["source"], core["identity"]
        name = Path(source["path"]).name
        require(
            name in parts
            and baseline["input_artifacts"]["raw_archive"]["part_sha256"][name]
            == source["sha256"]
            and source["path"]
            == str(Path(baseline["input_artifacts"]["raw_archive"]["path"]) / name)
            and [
                row["filename"]
                for row in manifest["parts"]
                if identity["dataset_id"] in row["downloaded_dataset_ids"]
            ]
            == [name],
            "Selected dataset does not have one exact retained native part",
        )
    return {
        **deepcopy(protocol),
        **{key: deepcopy(policy[key]) for key in INHERITED},
    }


def produce(repository: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    """Account for all owners; do not construct a fit or scientific prediction."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    state = code_state(repository)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    contract = load_contract(repository, protocol)
    sourcepins = [protocol["provenance"][key] for key in PROVENANCE] + [
        core["source"] for core in protocol["cores"]
    ]
    maximum = protocol["limits"]["max_output_bytes"]
    output.mkdir()
    products = {}
    for core in contract["cores"]:
        raw = read_pin(repository, core["source"], protocol["source_max_bytes"])
        native = decode(raw)
        result = project(native, core, contract)
        products[core["key"]] = write(output, core["key"] + ".json", result, maximum)
        del raw, native, result
    for pin in sourcepins:
        read_pin(repository, pin, protocol["source_max_bytes"])
    require(
        protocol_path.read_bytes() == raw_protocol and code_state(repository) == state,
        "Consumed source, protocol, Python, HEAD or index changed",
    )
    result = {
        "schema_version": "nordic-literal-window-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "sourcepins": sourcepins,
        "products": products,
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "resources": resources(started, output, protocol["limits"]),
    }
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Publish the complete native source-support audit under declared bounds."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.repository, args.protocol, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
