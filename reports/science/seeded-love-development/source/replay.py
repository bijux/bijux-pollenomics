"""Execute the one frozen seeded ring-preserving differential-evolution setting."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
from typing import Any


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def source_guard(protocol: dict[str, Any]) -> dict[str, Any]:
    directory = Path(__file__).absolute().parent
    names = {"replay.py", "inputs.py", "search.py"}
    require(
        {p.name for p in directory.iterdir()} == names
        and len(protocol["execution_sources"]) == 3
        and {r["path"] for r in protocol["execution_sources"]} == names,
        "Exact three-source namespace required",
    )
    for row in protocol["execution_sources"]:
        path = directory / row["path"]
        require(
            path.is_file()
            and path.stat().st_nlink == 1
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Independent scientific source required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Source changed before helper import",
        )
    return runpy.run_path(str(directory / "inputs.py"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    require(
        all(
            p.is_absolute()
            and ".." not in p.parts
            and not any(q.is_symlink() for q in (p, *p.parents))
            for p in (args.repository, args.prepared, args.protocol, args.output)
        ),
        "Absolute independent scientific paths required",
    )
    require(
        args.protocol.is_file()
        and args.protocol.stat().st_size <= 1024**2
        and args.protocol.stat().st_nlink == 1,
        "Bounded physical protocol required",
    )
    raw = args.protocol.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == args.protocol_sha256
        and re.fullmatch("[a-f0-9]{40}", args.candidate) is not None,
        "Exact protocol/current candidate required",
    )
    protocol = json.loads(raw)
    require(
        protocol["schema_version"] == "seeded-love-development-protocol.v1"
        and protocol["expected_new_scientific_calls"]
        == {
            "LOVEoptim_calls": 39,
            "REVEALS_calls": 0,
            "max_optimizer_attempts": 78,
            "forward_calls": 0,
            "score_calls": 0,
            "objective_certification_calls_max": 78,
        },
        "Finite seeded DE protocol required",
    )
    helper = source_guard(protocol)
    protocol = helper["decode"](raw)
    plan_raw = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"]).read_bytes()
    require(
        hashlib.sha256(plan_raw).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Same registered plan buffer required",
    )
    plan = helper["decode"](plan_raw)
    source = next(r for r in protocol["execution_sources"] if r["path"] == "replay.py")
    require(
        plan["candidate"] == args.candidate
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["repository"] == str(args.repository)
        and plan["scientific_mode"] == "seeded_ring_preserving_de"
        and plan["scientific_producer"]
        == {**source, "path": str(Path(__file__).absolute())}
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(raw),
        }
        and plan["expected_new_scientific_calls"]
        == protocol["expected_new_scientific_calls"]
        and plan["maximum_new_attempts"] == 78
        and args.output == Path(plan["output"]) / "products"
        and args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists(),
        "Exact registered seeded DE route/output required",
    )
    pairs, authority = helper["load"](args.repository, args.prepared, protocol)
    from bijux_pollenomics.analysis.lra.engine.discovery import (
        load_engine,
        required_capability_for_profile,
    )

    binding = load_engine(
        required_capability=required_capability_for_profile("ring-taxon-preserving")
    )
    search = runpy.run_path(str(Path(__file__).absolute().parent / "search.py"))
    args.output.mkdir(parents=True)
    require(
        protocol["setting"] == search["SETTING"],
        "Protocol and executed DE setting differ",
    )
    records = []
    with (args.output / "trials.jsonl").open("x") as ledger:

        def emit(value: dict[str, Any]) -> None:
            ledger.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        for pair in pairs:
            identity = {
                key: pair[key]
                for key in ("nominal_request_sha256", "seeded_request_sha256")
            }
            emit(
                {
                    "event": "request_started",
                    **identity,
                    "planned_ring_indices": [0, 1],
                    "setting": protocol["setting"],
                }
            )
            record = search["invoke"](pair)
            for disposition in record["ring_dispositions"]:
                emit(
                    {
                        "event": "ring_completed",
                        **identity,
                        "root_seed": record["root_seed"],
                        "local_seed": record["local_seed"],
                        **disposition,
                    }
                )
            emit(
                {
                    "event": "request_completed",
                    **identity,
                    "optimizer_attempts": record["optimizer_attempts"],
                    "elapsed_seconds": record["elapsed_seconds"],
                }
            )
            records.append(record)
    require(
        len(records) == len({r["nominal_request_sha256"] for r in records}) == 39
        and sum(r["LOVEoptim_calls"] for r in records) == 39
        and sum(len(r["ring_dispositions"]) for r in records) == 78
        and sum(r["optimizer_attempts"] for r in records) <= 78,
        "Complete39request/78ring search dispositions required",
    )
    helper["load"](args.repository, args.prepared, protocol)

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

    ledger = (args.output / "trials.jsonl").read_bytes()
    ledger_pin = {
        "path": "trials.jsonl",
        "sha256": hashlib.sha256(ledger).hexdigest(),
        "bytes": len(ledger),
    }
    diagnostics = write(
        "seeded-diagnostics.json",
        {
            "schema_version": "seeded-love-ring-diagnostics.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "records": records,
            "nominal_saved_authority": authority,
        },
    )
    write(
        "report.json",
        {
            "schema_version": "seeded-love-development.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "diagnostics": diagnostics,
            "trials": ledger_pin,
            "source_qualified_API_main_return": "Observed only if recorded by execution consumer",
            "unique_pairs": 39,
            "logical_ancestry": 2715,
            "contexts": 225,
            "sites": 15,
            "taxa": 30,
            "temporal_support": protocol["temporal_matching"],
            "calls": protocol["expected_new_scientific_calls"],
            "optimizer_attempts": sum(r["optimizer_attempts"] for r in records),
            "accepted_rings": sum(
                row["status"] == "accepted"
                for record in records
                for row in record["ring_dispositions"]
            ),
            "refused_rings": sum(
                row["status"] == "refused"
                for record in records
                for row in record["ring_dispositions"]
            ),
            "not_attempted_rings": sum(
                row["status"] == "not_attempted"
                for record in records
                for row in record["ring_dispositions"]
            ),
            "objective_certification_calls": sum(
                r["objective_certification_calls"] for r in records
            ),
            "engine_binding": binding.as_dict(),
            "setting": protocol["setting"],
            "scope": "Previously exposed TW5 seeded source-profile diagnostic. No held-out scoring, method selection, RcppDE trajectory parity, global optimum, physical inverse accuracy, uncertainty calibration or whole-sweep acceptance. Failed ring diagnostics are retained and never published as accepted predictions.",
        },
    )


if __name__ == "__main__":
    main()
