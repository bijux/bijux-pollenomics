"""Finite scientific identities and exclusive files for the nested transport diagnostic."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
from typing import Any

METHODS = ("gpm neutral", "ppe-minus-source-sd", "ppe-plus-source-sd")
SOURCE_NAMES = {"common.py", "requests.py", "training.py", "selection.py", "replay.py"}
PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/"


def decode(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate scientific metadata key")
            result[key] = value
        return result

    def refuse(_value: str) -> None:
        raise ValueError("Nonfinite scientific metadata")

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
    if (
        ".." in name.parts
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_nlink != 1
    ):
        raise ValueError("Physical declared scientific member required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
        raise ValueError("Scientific member changed: " + str(path))
    return raw


def write(path: Path, value: Any) -> dict[str, Any]:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def module(directory: Path, protocol: dict[str, Any], name: str) -> dict[str, Any]:
    row = next(row for row in protocol["execution_sources"] if row["path"] == name)
    checked(directory, row)
    return runpy.run_path(str(directory / name))


def guard(
    repository: Path, prepared: Path, directory: Path, protocol: dict[str, Any]
) -> None:
    if (
        protocol["schema_version"] != "author-love-nested-ppe-protocol.v1"
        or tuple(protocol["methods"]) != METHODS
        or protocol["counts"]
        != {
            "outer_folds": 15,
            "inner_folds": 210,
            "unique_requests_per_method": 39,
            "logical_requests_per_method": 2715,
            "prior_attempts_reused": 2496,
            "nominal_new_attempts": 0,
            "ppe_new_attempts": 4992,
            "max_new_attempts": 4992,
            "candidate_prediction_slots": 2025,
            "selected_outer_prediction_slots": 45,
        }
        or protocol["optimizer"]
        != {
            "rings": 2,
            "starts_per_ring": 32,
            "maxiter": 300,
            "max_search_evaluations": 16000,
            "ftol": 1e-8,
            "seed": 7,
        }
    ):
        raise ValueError("Exact finite scientific transport protocol required")
    if {p.name for p in directory.iterdir()} != SOURCE_NAMES or any(
        p.is_symlink() or not p.is_file() for p in directory.iterdir()
    ):
        raise ValueError("Exact five-source diagnostic namespace required")
    if (
        protocol["nominal_source_candidate"]
        != "70dd58ce28071d3b4ef34af2c800370a52d42bf9"
        or protocol["nominal_training_protocol_sha256"]
        != "7953aec717a0bf440eca6d26e5c4d9bca03e3d783a005ab311f09d3d9b4db4dd"
        or protocol["nominal_admission_source"]["sha256"]
        != "e60bc275372655b400e1ae0a92e97abb05cb36824ff64c935493a72f1b4f862a"
    ):
        raise ValueError(
            "Exact separately qualified historical nominal identity required"
        )
    checked(repository, protocol["nominal_admission_source"])
    for row in protocol["execution_sources"]:
        checked(directory, row)
    if (
        len(protocol["execution_sources"]) != 5
        or {row["path"] for row in protocol["execution_sources"]} != SOURCE_NAMES
    ):
        raise ValueError("Exact five-source identities required")
    if (
        len(protocol["inputs"]) != 37
        or {p.name for p in prepared.iterdir()}
        != {row["path"] for row in protocol["inputs"]}
        or any(Path(row["path"]).name != row["path"] for row in protocol["inputs"])
    ):
        raise ValueError("Exact original37 scientific input namespace required")
    for row in protocol["inputs"]:
        checked(prepared, row)
    for row in protocol["source_pins"]:
        checked(repository, row)
    for row in protocol["prior_evidence"].values():
        checked(repository, row)
    checked(repository, protocol["source_snapshot"])
    from importlib.metadata import version

    for name, expected in protocol["versions"].items():
        if version(name) != expected:
            raise ValueError("Qualified numerical/source-engine version changed")
    previous = decode(
        checked(repository, protocol["prior_evidence"]["cohort_protocol"])
    )
    if (
        previous["source_pins"] != protocol["reused_source_pins"]
        or previous["versions"] != protocol["versions"]
        or previous["inputs"] != protocol["inputs"]
        or previous["runtime_reference_sha256"] != protocol["runtime_reference_sha256"]
    ):
        raise ValueError("Prior numeric source/runtime/input equivalence differs")


def libraries(repository: Path) -> dict[str, dict[str, Any]]:
    return {
        name: runpy.run_path(str(repository / PREFIX / path))
        for name, path in {
            "original": "optimizer-gradient/replay.py",
            "starts": "optimizer-start-sensitivity/replay.py",
            "math": "development-fold/training.py",
            "pool": "cohort-development/pool.py",
            "cohort": "cohort-development/replay.py",
        }.items()
    }


def admit_new_shard(
    repository: Path,
    row: dict[str, Any],
    candidate: str,
    protocol_sha256: str,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Require the actual reviewed-source fit plan and its exact saved-product locations."""
    plan = decode(checked(repository, row["plan"]))
    terminal = decode(checked(repository, row["native_terminal"]))
    producer = plan["scientific_producer"]
    producer_expected = next(
        pin for pin in protocol["execution_sources"] if pin["path"] == "replay.py"
    )
    protocol_pin = plan["scientific_protocol"]
    if (
        row["plan"]["sha256"] != row["plan_sha256"]
        or terminal["plan_sha256"] != row["plan_sha256"]
        or plan["candidate"] != candidate
        or terminal["candidate"] != candidate
        or plan["scientific_mode"] != "fit"
        or plan["transport_method"] != row["method"]
        or protocol_pin["sha256"] != protocol_sha256
        or any(producer[key] != producer_expected[key] for key in ("sha256", "bytes"))
    ):
        raise ValueError("Actual source/protocol/scenario-specific fit plan required")
    checked(repository, producer)
    if digest(decode(checked(repository, protocol_pin))) != digest(protocol):
        raise ValueError("Fit plan protocol differs from evaluation scenario contract")
    output = repository / plan["output"]
    if (
        not output.is_absolute()
        or ".." in output.parts
        or not output.is_relative_to(repository / "artifacts")
        or repository / row["native_terminal"]["path"] != output / "terminal.json"
        or any(
            repository / row[role]["path"] != output / "products" / name
            for role, name in (
                ("training", "training.json"),
                ("trials", "trials.jsonl"),
            )
        )
    ):
        raise ValueError(
            "Fit terminal and saved products must belong to the registered plan output"
        )
    arguments = plan["scientific_arguments"]
    if (
        not isinstance(arguments, list)
        or len(arguments) != 16
        or arguments[::2]
        != [
            "--repository",
            "--prepared",
            "--protocol",
            "--protocol-sha256",
            "--candidate",
            "--output",
            "--mode",
            "--method",
        ]
    ):
        raise ValueError("Exact fit scientific argument route required")
    prepared = Path(arguments[3])
    expected_arguments = [
        "--repository",
        str(repository),
        "--prepared",
        str(prepared),
        "--protocol",
        protocol_pin["path"],
        "--protocol-sha256",
        protocol_sha256,
        "--candidate",
        candidate,
        "--output",
        str(output / "products"),
        "--mode",
        "fit",
        "--method",
        row["method"],
    ]
    if (
        arguments != expected_arguments
        or not prepared.is_absolute()
        or ".." in prepared.parts
    ):
        raise ValueError("Scientific arguments differ from pinned fit plan")
    wanted = [
        producer,
        protocol_pin,
        *protocol["source_pins"],
        *protocol["prior_evidence"].values(),
    ]
    wanted.extend(
        {**pin, "path": str(prepared / pin["path"])} for pin in protocol["inputs"]
    )
    wanted.extend(
        {**pin, "path": str(Path(producer["path"]).parent / pin["path"])}
        for pin in protocol["execution_sources"]
    )

    def identity(pin: dict[str, Any]) -> tuple[str, str, int]:
        return str(repository / pin["path"]), pin["sha256"], pin["bytes"]

    if not {identity(pin) for pin in wanted} <= {
        identity(pin) for pin in plan["input_pins"]
    }:
        raise ValueError("Fit plan omits exact scientific source/prior/input members")
    resources = {
        "overall_timeout_seconds": 600,
        "declared_memory_bytes": 8 * 1024**3,
        "declared_storage_bytes": 256 * 1024**2,
        "maximum_parallel_workers": 1,
        "numerical_threads_per_worker": 1,
    }
    controls = plan["execution_sources"]
    for name, expected_sha, expected_bytes in (
        (
            "consume.py",
            "a285a50029e5a51cd9d3ee4c2cd88d903e7e3ff93356c4d01244e9430cf0a100",
            3413,
        ),
        (
            "prepare.py",
            "d2392f4b4467fa247176e6c8abc0495d91da43ed0ec6359dc1e74b55b35b8ce8",
            24950,
        ),
    ):
        if (
            controls[name]["sha256"] != expected_sha
            or controls[name]["bytes"] != expected_bytes
        ):
            raise ValueError("Exact reviewed generic PPE launcher source required")
        checked(repository, controls[name])
    executor, profile = plan["source_runtime_executor"], plan["source_runtime_profile"]
    if (
        executor["sha256"]
        != "491c5379cbb1a004a5cc3084a2d45846d7c74843beed5dce34b89ddbaabefb38"
        or profile["sha256"]
        != "3331ec5104b2d083c886dcb10ad62551c2f69ff7d00d604aba60b10023e9e08b"
        or Path(controls["consume.py"]["path"]).parent
        != Path(controls["prepare.py"]["path"]).parent
    ):
        raise ValueError(
            "Qualified SOURCE3331 and coherent launcher namespace required"
        )
    cache = str(output.parent / "scratch/unused-pycache")
    interpreter = "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
    prefix = [interpreter, "-I", "-S", "-B", "-X", "pycache_prefix=" + cache]
    if (
        plan["absent_pycache_prefix"] != cache
        or plan["stages"][0]["argv"] != [*prefix, controls["consume.py"]["path"]]
        or plan["runtime_stage_argv"]
        != [
            *prefix,
            executor["path"],
            "--profile",
            profile["path"],
            "--profile-sha256",
            profile["sha256"],
            "--mode",
            "python",
            "--",
            controls["consume.py"]["path"],
            "--scientific-stage",
        ]
    ):
        raise ValueError(
            "Exact reviewed consume-to-SOURCE scientific-stage route required"
        )
    stages = terminal["stages"]
    if (
        plan["resources"] != resources
        or terminal["resources"] != resources
        or len(plan["stages"]) != 1
        or len(stages) != 1
        or plan["stages"][0]["id"] != "nested-ppe-fit"
        or plan["stages"][0]["timeout_seconds"] != 600
        or plan["stages"][0]["must_succeed"] is not True
        or any(stages[0].get(key) != value for key, value in plan["stages"][0].items())
        or type(terminal["actual_exit"]) is not int
        or terminal["actual_exit"] != 0
        or type(stages[0]["actual_exit"]) is not int
        or stages[0]["actual_exit"] != 0
        or stages[0]["timed_out"] is not False
        or terminal["source_pins_before_mismatches"]
        or terminal["source_pins_after_mismatches"]
    ):
        raise ValueError(
            "Actual completed fit native zero must match registered stage and bounds"
        )
    for key, limit in (
        ("output_bytes", resources["declared_storage_bytes"]),
        ("completed_child_peak_rss_bytes_macos", resources["declared_memory_bytes"]),
    ):
        if type(terminal[key]) is not int or not 0 <= terminal[key] <= limit:
            raise ValueError(
                "Exact bounded completed fit resource observation required"
            )
    return {
        "native_terminal": row["native_terminal"],
        "references": [row["plan"], row["native_terminal"]],
    }
