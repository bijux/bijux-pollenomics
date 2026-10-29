"""Independently reconstruct portable source roles and authenticate every retained member."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from assemble import materialization
from contracts import (
    checkpoint,
    execution_scope,
    load,
    require,
    stage_plan,
    strict_equal,
    write,
)
from members import encoded, validate_capture
from retained import authenticate
from source_inputs import pin


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = stage_plan(args.plan)
    authority, scope = execution_scope(plan)
    retained = authenticate()
    digest = os.environ["BIJUX_REGISTERED_PLAN_SHA256"]
    expected, _ = materialization(plan, retained, digest)
    output = Path(plan["output"])
    packet = output / "packet"
    raw = (packet / "capture.json").read_bytes()
    require(
        raw == encoded(expected),
        "Actual whole capture bytes differ from independent role reconstruction",
    )
    witness = validate_capture(packet, expected)
    assembly = load(output / "assembly-receipt.json")
    require(
        type(assembly["actual_exit"]) is int
        and assembly["actual_exit"] == 0
        and assembly["registered_plan_sha256"] == digest
        and assembly["candidate"] == plan["candidate"]
        and assembly["capture"] == pin(packet / "capture.json")
        and assembly["country_receipt_sha256"] == witness["current_receipt_sha256"]
        and assembly["country_API_normalizer_model_R_or_HTTP_repeated"] is False
        and assembly["private_runtime_bytecode_bodies_published"] is False,
        "Actual metadata assembly/capture role differs",
    )
    require(
        strict_equal(witness, retained["witness"]),
        "Independent portable native witness differs",
    )
    checkpoint(
        authority,
        scope,
        plan["owned_namespace_snapshots"],
        plan["original_physical_ancestry_paths"],
    )
    write(
        output / "independent-portable-country-review.json",
        {
            "schema_version": "sweden-portable-returned-country-independent-review.v1",
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "registered_plan_sha256": digest,
            "capture": pin(packet / "capture.json"),
            "assembly": pin(output / "assembly-receipt.json"),
            "public_members": len(expected["members"]),
            "public_payload_bytes": sum(
                row["bytes"] for row in expected["members"].values()
            ),
            "country_receipt_sha256": witness["current_receipt_sha256"],
            "complete_original_ordered_input_counts": {
                key: len(rows)
                for key, rows in expected["identity_only_roles"][
                    "ordered_original_input_roles"
                ].items()
            },
            "native_witness": witness,
            "complete_public_namespace_and_all_member_bytes_verified": True,
            "private_runtime_bytecode_bodies_published": False,
            "captured_code_imported_or_executed": False,
            "country_API_normalizer_model_R_or_HTTP_repeated": False,
        },
    )
    print(
        __import__("json").dumps(
            {
                "independent_review": pin(
                    output / "independent-portable-country-review.json"
                ),
                "actual_exit": 0,
            }
        )
    )
