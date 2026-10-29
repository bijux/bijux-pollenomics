"""Execute the frozen conditional circular-receiver diagnostic without new fits."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
import time
from typing import Any


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def source_guard(protocol: dict[str, Any]) -> dict[str, Any]:
    directory = Path(__file__).absolute().parent
    names = {"inputs.py", "receiver.py", "replay.py"}
    require(
        {p.name for p in directory.iterdir()} == names
        and len(protocol["execution_sources"]) == 3
        and {row["path"] for row in protocol["execution_sources"]} == names,
        "Exact three-source circular-receiver namespace required",
    )
    for row in protocol["execution_sources"]:
        path = directory / row["path"]
        require(
            path.is_file()
            and path.stat().st_nlink == 1
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Independent declared source member required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Scientific source changed before import",
        )
    return runpy.run_path(str(directory / "inputs.py"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    require(
        all(
            path.is_absolute()
            and ".." not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents))
            for path in (args.repository, args.prepared, args.protocol, args.output)
        ),
        "Absolute independent scientific paths required",
    )
    require(
        args.protocol.is_file()
        and args.protocol.stat().st_nlink == 1
        and args.protocol.stat().st_size <= 1024**2,
        "Bounded independent protocol required",
    )
    raw = args.protocol.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == args.protocol_sha256
        and re.fullmatch("[a-f0-9]{40}", args.candidate) is not None,
        "Exact protocol/current candidate required",
    )
    protocol = json.loads(raw)
    helper = source_guard(protocol)
    protocol = helper["decode"](raw)
    receiver = runpy.run_path(str(Path(__file__).absolute().parent / "receiver.py"))
    require(
        protocol["schema_version"] == "circular-receiver-development-protocol.v1"
        and protocol["setting"] == receiver["SETTING"]
        and protocol["selection_stratum"]
        == "diagnostic_only_until_matched_inverse_qualified"
        and protocol["expected_new_scientific_calls"]
        == {
            "optimizer_attempts": 0,
            "REVEALS_calls": 0,
            "LOVE_calls": 0,
            "maximum_circular_kernel_calls": 1800,
            "maximum_forward_calls": 675,
            "score_calls": 0,
        },
        "Exact originally declared conditional diagnostic setting required",
    )
    plan_raw = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"]).read_bytes()
    require(
        hashlib.sha256(plan_raw).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Exact registered plan buffer required",
    )
    plan = helper["decode"](plan_raw)
    source = next(
        row for row in protocol["execution_sources"] if row["path"] == "replay.py"
    )
    require(
        plan["candidate"] == args.candidate
        and plan["repository"] == str(args.repository)
        and plan["scientific_mode"] == "conditional_circular_receiver"
        and plan["scientific_producer"]
        == {**source, "path": str(Path(__file__).absolute())}
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(raw),
        }
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["maximum_new_attempts"] == 0
        and plan["expected_new_scientific_calls"]
        == protocol["expected_new_scientific_calls"]
        and args.output == Path(plan["output"]) / "products"
        and args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists(),
        "Exact registered circular-receiver route and new output required",
    )
    pairs, ancestry = helper["load"](args.repository, args.prepared, protocol)
    slots, inputs = helper["prediction_inputs"](
        args.repository, args.prepared, protocol, pairs, ancestry
    )
    args.output.mkdir(parents=True)
    tables = {}
    dispositions = []
    with (args.output / "trials.jsonl").open("x") as ledger:

        def emit(value: dict[str, Any]) -> None:
            ledger.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        for target, geometry in sorted(inputs["geometries"].items()):
            emit(
                {
                    "event": "response_table_started",
                    "target": target,
                    "geometry": geometry["source"],
                }
            )
            began = time.perf_counter()
            table = receiver["responses"](
                target, geometry, inputs["taxa"], inputs["parameters"]
            )
            table["elapsed_seconds"] = time.perf_counter() - began
            tables[target] = table
            emit(
                {
                    "event": "response_table_completed",
                    "target": target,
                    "status": table["status"],
                    "table_sha256": helper["digest"](table),
                    "kernel_calls": table["kernel_calls"],
                    "response": table,
                }
            )
        for slot in slots:
            began = time.perf_counter()
            row = receiver["predict"](
                slot, tables[slot["target"]], inputs["taxa"], inputs["parameters"]
            )
            row["elapsed_seconds"] = time.perf_counter() - began
            row["diagnostic_sha256"] = helper["digest"](row)
            dispositions.append(row)
            emit(
                {
                    "event": "prediction_disposition",
                    "identity": row["source_prediction_manifest_sha256"],
                    "diagnostic_sha256": row["diagnostic_sha256"],
                    "status": row["status"],
                    "disposition": row,
                }
            )
    require(
        len(tables) == 15
        and len(dispositions) == 675
        and sum(row["kind"] == "outer" for row in dispositions) == 45
        and sum(row["kernel_calls"] for row in tables.values()) <= 1800
        and sum(row["forward_calls"] for row in dispositions) <= 675,
        "Complete bounded diagnostic population required",
    )

    def write(name: str, value: Any) -> dict[str, Any]:
        body = (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        with (args.output / name).open("xb") as stream:
            stream.write(body)
        return {
            "path": name,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        }

    response_pin = write(
        "receiver-responses.json",
        {
            "schema_version": "circular-receiver-response-tables.v1",
            "setting": protocol["setting"],
            "taxa": inputs["taxa"],
            "parameters": inputs["parameters"],
            "tables": tables,
        },
    )
    prediction_pin = write(
        "prediction-dispositions.json",
        {
            "schema_version": "circular-receiver-prediction-dispositions.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "nominal_freeze": protocol["candidate_freeze"],
            "slots": dispositions,
        },
    )
    ledger_body = (args.output / "trials.jsonl").read_bytes()
    ledger_pin = {
        "path": "trials.jsonl",
        "sha256": hashlib.sha256(ledger_body).hexdigest(),
        "bytes": len(ledger_body),
    }
    write(
        "report.json",
        {
            "schema_version": "circular-receiver-development.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "nominal_candidate": protocol["nominal_candidate"],
            "nominal_authority": protocol["nominal_prediction_authority"],
            "original_native_exit": 1,
            "nominal_saved_products_admitted_separately": True,
            "unique_fit_requests_reused": 39,
            "contexts": 225,
            "diagnostic_slots": 675,
            "outer_slots": 45,
            "inner_slots": 630,
            "taxa": 30,
            "sites": 15,
            "response_tables": response_pin,
            "prediction_dispositions": prediction_pin,
            "trials": ledger_pin,
            "kernel_calls": sum(row["kernel_calls"] for row in tables.values()),
            "forward_calls": sum(row["forward_calls"] for row in dispositions),
            "predicted_diagnostic": sum(
                row["status"] == "predicted_diagnostic" for row in dispositions
            ),
            "refused": sum(row["status"] == "refused" for row in dispositions),
            "optimizer_attempts": 0,
            "new_spatial_fits": 0,
            "score_calls": 0,
            "setting": protocol["setting"],
            "selection_stratum": protocol["selection_stratum"],
            "matched_inverse_qualified": False,
            "scientific_acceptance": "not_evaluated",
            "scope": protocol["scope"],
            "scientific_main_return": "Not inferred from the unchanged execution consumer.",
        },
    )


if __name__ == "__main__":
    main()
