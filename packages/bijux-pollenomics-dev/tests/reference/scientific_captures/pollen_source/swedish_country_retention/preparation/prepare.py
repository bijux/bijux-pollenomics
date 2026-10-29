"""Freeze original returned products for two portable metadata stages; copy no data."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from contracts import (
    PYTHON,
    RESOURCES,
    ROOT,
    SOURCE,
    checkpoint,
    fresh_output,
    identity,
    registered_plan,
    require,
)
from data_roles import verify_selection
from members import descriptor, encoded, specification
from retained import authenticate
from source_admission import reviewed_controls
from source_inputs import InputScope, pin, verify_entry_aliases, verify_rows
from source_runtime import authenticate_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, peer, controlled = reviewed_controls(SOURCE)
    require(pin(peer)["sha256"] == args.review_sha256, "Exact source approval differs")
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Clean current candidate required",
    )
    output = fresh_output(args.output)
    require(
        output.parent == ROOT / "artifacts/science",
        "Separate science output root required",
    )
    retained = authenticate()
    original = retained["saved_plan"]
    owned = Path(original["owned_repository"])
    declared = registered_plan(
        SOURCE / "declared-inputs.json", pin(SOURCE / "declared-inputs.json")["sha256"]
    )
    require(
        declared == original["source_declaration"], "Exact original data roles required"
    )
    verify_selection(owned, declared, original["source_input_selection"])
    verify_entry_aliases(
        original["runtime_entry_raw_aliases"], original["runtime_entry_lexical_paths"]
    )
    scope = InputScope(controlled, [PYTHON])
    scope.extend(retained["input_pins"])
    authority, runtime_rows = authenticate_runtime()
    require(
        authority == original["qualified_source_runtime"],
        "Complete original runtime changed",
    )
    scope.extend(runtime_rows)
    snapshots = retained["snapshots"]
    ancestry = retained["original_physical_ancestry_paths"]
    capture, payloads = specification(retained, args.candidate, "0" * 64)
    payload_bytes = sum(row["bytes"] for row in capture["members"].values())
    plan: dict[str, Any] = deepcopy(original)
    plan.update(
        id="sweden-country-portable-source-"
        + args.candidate[:12]
        + "-"
        + str(pin(SOURCE / "prepared-source-manifest.json")["sha256"])[:12],
        candidate=args.candidate,
        output=str(output),
        canonical_identity_at_source_freeze=before,
        original_country_execution_candidate=retained["country_plan"]["candidate"],
        saved_country_observation_candidate=original["candidate"],
        saved_country_observation_plan=retained["identities"]["saved-plan"],
        retained_execution_references=retained["identities"],
        original_country_references=retained["original_references"],
        materialization=descriptor(capture, payloads),
        retained_logical_output_bytes=retained["retained_logical_output_bytes"],
        owned_namespace_snapshots=snapshots,
        original_physical_ancestry_paths=ancestry,
        qualified_source_runtime=authority,
        resources=deepcopy(RESOURCES),
        scope="Two public-source metadata stages only. Actual country call returned normally inside original controller1/whole1; separate saved observer0/whole0 is retained. No recovered full return, read ledger or import origins, and no country/API/data normalization/model/R/HTTP repetition.",
    )
    for name in (
        "input_pins",
        "qualified_input_namespaces",
        "runtime_entry_raw_aliases",
        "runtime_entry_lexical_paths",
    ):
        plan.pop(name, None)
    plan["environment"] = {
        **original["environment"],
        "TMPDIR": str(output / "scratch"),
        "XDG_CACHE_HOME": str(output / "cache"),
        "MPLCONFIGDIR": str(output / "cache/matplotlib"),
    }
    plan_path = output / "plan.json"
    plan["stages"] = [
        {
            "id": name,
            "action": action,
            "timeout_seconds": 180,
            "argv": [
                str(PYTHON),
                "-I",
                "-B",
                str(SOURCE / "entry.py"),
                action,
                "--plan",
                str(plan_path),
            ],
        }
        for name, action in (
            ("portable-returned-country-source-assembly", "assembler"),
            ("independent-portable-country-source-observer", "observer"),
        )
    ]
    plan["argv"] = [
        str(PYTHON),
        "-I",
        "-B",
        str(SOURCE / "entry.py"),
        "launch",
        "--plan",
        str(plan_path),
        "--registered-plan-sha256",
        "ACTUAL_REGISTERED_PLAN_SHA256",
    ]
    plan["working_directory"] = str(owned)
    plan["input_pins"] = scope.rows
    plan["qualified_input_namespaces"] = deepcopy(scope.source_namespaces)
    plan["runtime_entry_raw_aliases"] = deepcopy(scope.aliases)
    plan["runtime_entry_lexical_paths"] = list(scope.entries)
    forecast = encoded(plan)
    require(
        len(forecast) <= declared["maximum_plan_bytes"],
        "Exact pretty plan exceeds128MiB metadata limit",
    )
    require(
        len(forecast)
        + len(encoded(capture))
        + payload_bytes
        + retained["retained_logical_output_bytes"]
        + 16 * 1024**2
        <= RESOURCES["declared_storage_bytes"],
        "Inclusive original/new storage forecast exceeds1GiB",
    )
    checkpoint(authority, scope, snapshots, ancestry)
    verify_entry_aliases(
        original["runtime_entry_raw_aliases"], original["runtime_entry_lexical_paths"]
    )
    verify_selection(owned, declared, original["source_input_selection"])
    verify_rows(retained["input_pins"])
    require(
        identity() == before, "Current candidate changed before first output mutation"
    )
    output.mkdir()
    for name in ("scratch", "cache", "cache/matplotlib"):
        (output / name).mkdir()
    scope.bind(plan)
    checkpoint(authority, scope, snapshots, ancestry)
    require(
        identity() == before and encoded(plan) == forecast,
        "Candidate or exact forecast changed before plan publication",
    )
    # Publish the exact same pretty-encoded buffer that passed the pre-write forecast.
    with plan_path.open("xb") as stream:
        stream.write(forecast)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "public_member_count": len(capture["members"]),
                "public_payload_bytes": payload_bytes,
                "capture_metadata_bytes": len(encoded(capture)),
                "copied_original_data_or_source": False,
                "country_calls": 0,
            }
        )
    )
