"""Copy only the frozen public packet; never import retained code or decode private data."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Any

from contracts import (
    checkpoint,
    execution_scope,
    require,
    stage_plan,
    strict_equal,
    write,
)
from members import descriptor, encoded, specification, validate_capture
from retained import authenticate
from source_inputs import pin


def materialization(
    plan: dict[str, Any], retained: dict[str, Any], digest: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require(
        strict_equal(retained["identities"], plan["retained_execution_references"])
        and strict_equal(
            retained["original_references"], plan["original_country_references"]
        ),
        "Frozen original/saved reference roles changed",
    )
    forecast, payloads = specification(retained, plan["candidate"], "0" * 64)
    require(
        strict_equal(plan["materialization"], descriptor(forecast, payloads)),
        "Complete frozen public/private materialization changed",
    )
    capture, _ = specification(retained, plan["candidate"], digest)
    return capture, payloads


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = stage_plan(args.plan)
    authority, scope = execution_scope(plan)
    retained = authenticate()
    digest = os.environ["BIJUX_REGISTERED_PLAN_SHA256"]
    capture, payloads = materialization(plan, retained, digest)
    output = Path(plan["output"])
    packet = output / "packet"
    require(not packet.exists() and not packet.is_symlink(), "Fresh packet required")
    checkpoint(
        authority,
        scope,
        plan["owned_namespace_snapshots"],
        plan["original_physical_ancestry_paths"],
    )
    packet.mkdir()
    (packet / "members").mkdir()
    for row in payloads:
        expected = row["source_identity"]
        source = Path(expected["path"])
        require(pin(source) == expected, "Frozen public source changed before copy")
        raw = source.read_bytes()
        require(
            len(raw) == expected["bytes"]
            and hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "Same-buffer public source differs",
        )
        with (packet / row["member"]).open("xb") as stream:
            stream.write(raw)
    with (packet / "capture.json").open("xb") as stream:
        stream.write(encoded(capture))
    witness = validate_capture(packet, capture)
    checkpoint(
        authority,
        scope,
        plan["owned_namespace_snapshots"],
        plan["original_physical_ancestry_paths"],
    )
    write(
        output / "assembly-receipt.json",
        {
            "schema_version": "sweden-portable-returned-country-source-assembly.v1",
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "registered_plan_sha256": digest,
            "capture": pin(packet / "capture.json"),
            "public_members": len(capture["members"]),
            "public_payload_bytes": sum(
                row["bytes"] for row in capture["members"].values()
            ),
            "country_receipt_sha256": witness["current_receipt_sha256"],
            "original_controller_actual_exit": 1,
            "original_whole_actual_exit": 1,
            "country_call_returned_normally": True,
            "saved_observer_actual_exit": 0,
            "saved_whole_actual_exit": 0,
            "country_API_normalizer_model_R_or_HTTP_repeated": False,
            "private_runtime_bytecode_bodies_published": False,
        },
    )
    print(
        __import__("json").dumps(
            {"assembly": pin(output / "assembly-receipt.json"), "actual_exit": 0}
        )
    )
