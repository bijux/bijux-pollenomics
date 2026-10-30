"""Run the explicitly declared four-place cohort through shared prediction APIs."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import workflow as shared
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts import flink_nordic

COHORT = "flink_nordic"
require = shared.require


def protocol(binding: dict[str, Any]) -> dict[str, Any]:
    """Bind the actual maintained cohort protocol, never the old three-place label."""
    require(set(binding) == {"path", "sha256", "bytes"}, "Closed protocol pin required")
    raw, declaration = shared.read(Path(binding["path"]), binding["sha256"], 65536)
    require(len(raw) == binding["bytes"], "Protocol size differs")
    require(
        declaration["schema_version"] == flink_nordic.SCHEMA
        and declaration["baseline_protocol_sha256"] == shared.PROTOCOL_SHA256
        and declaration["model_assumptions"] == flink_nordic.ASSUMPTIONS,
        "Declared four-place protocol differs",
    )
    return cast(dict[str, Any], declaration)


def input_scope(
    root: Path, manifest: Path, checksum: str, binding: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Authenticate all117members, including exact preserved nominal80 identities."""
    declaration = protocol(binding)
    path = Path(binding["path"])
    relative_protocol = Path(flink_nordic.PROTOCOL)
    require(
        tuple(path.parts[-len(relative_protocol.parts) :]) == relative_protocol.parts,
        "Canonical cohort protocol path required",
    )
    repository = path.parents[len(relative_protocol.parts) - 1]
    nominal_pins = [
        p
        for p in declaration["input_pins"]
        if p["path"] == declaration["nominal_manifest"]
    ]
    require(len(nominal_pins) == 1, "One original nominal inventory authority required")
    original_pin = nominal_pins[0]
    nominal_relative = Path(original_pin["path"])
    require(
        not nominal_relative.is_absolute() and ".." not in nominal_relative.parts,
        "Confined nominal authority required",
    )
    raw, nominal = shared.read(
        repository / nominal_relative, original_pin["sha256"], 65536
    )
    require(
        len(raw) == original_pin["bytes"]
        and type(nominal) is list
        and len(nominal) == 80,
        "Original nominal80 inventory differs",
    )
    shared.physical(root)
    _, pins = shared.read(manifest, checksum, 65536)
    require(
        type(pins) is list and len(pins) == 117,
        "Exact117-member cohort inventory required",
    )
    by_name: dict[str, dict[str, Any]] = {}
    total = 0
    for pin in pins:
        require(set(pin) == {"path", "sha256", "bytes"}, "Closed input pin required")
        relative = Path(pin["path"])
        require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and relative.as_posix() == pin["path"]
            and pin["path"] not in by_name,
            "Confined unique input member required",
        )
        raw, _ = shared.read(root / relative, pin["sha256"], 65536)
        require(len(raw) == pin["bytes"], "Input member size differs")
        total += len(raw)
        by_name[pin["path"]] = pin
    old_members = {"inputs.json", "source-pins.json"}
    new_members = {"cohort-inputs.json"}
    for name in shared.NAMES:
        old_members.update(
            f"{name}/{member}.json"
            for member in (
                "chronology",
                "taxa",
                "parameters",
                "dependency_lock",
                "decision",
                "BOKE-raw",
                "BUS-raw",
                "SOLSOE83-raw",
                "BOKE-geometry",
                "BUS-geometry",
                "SOLSOE83-geometry",
                "experiment",
                "projection",
            )
        )
        new_members.update(
            f"{name}/{member}.json"
            for member in (
                "FLINK-raw",
                "FLINK-geometry",
                "cohort-chronology",
                "cohort-decision",
                "cohort-experiment",
                "cohort-projection",
            )
        )
    require(
        set(by_name) == old_members | new_members and total <= 2097152,
        "Closed cohort namespace/budget differs",
    )
    require(
        len({p["path"] for p in nominal}) == 80
        and {p["path"] for p in nominal} == old_members
        and all(by_name[p["path"]] == p for p in nominal),
        "Original nominal member bytes changed",
    )
    actual = set()
    for member in root.rglob("*"):
        shared.physical(member)
        require(member.is_dir() or member.is_file(), "Special input refused")
        if member.is_file():
            actual.add(member.relative_to(root).as_posix())
    require(actual == set(by_name), "Unlisted cohort input member")
    _, index = shared.read(
        root / "cohort-inputs.json", by_name["cohort-inputs.json"]["sha256"], 65536
    )
    require(
        index["schema_version"] == flink_nordic.SCHEMA
        and index["protocol"] == declaration
        and index["nominal_members_preserved"] == 80
        and [r["directory"] for r in index["experiments"]] == list(shared.NAMES),
        "Cohort index/protocol differs",
    )
    for row in index["experiments"]:
        reference = row["experiment"]
        require(
            reference["path"] == "cohort-experiment.json"
            and reference["sha256"]
            == by_name[row["directory"] + "/cohort-experiment.json"]["sha256"],
            "Cohort experiment/index differs",
        )
        _, payload = shared.read(
            root / row["directory"] / reference["path"], reference["sha256"], 65536
        )
        require(
            [s["site_id"] for s in payload["sites"]]
            == [
                "neotoma-site-28872",
                "neotoma-site-28869",
                "neotoma-site-3432",
                "neotoma-site-28889",
            ],
            "Exact four-place population required",
        )
        require(
            len({s["record_id"] for s in payload["sites"]}) == 4
            and payload["baselines"] == list(shared.METHODS),
            "Record or method axis differs",
        )
    return index["experiments"], pins


def prediction_receipt(
    directory: Path, checksum: str, api: dict[str, Any]
) -> dict[str, Any]:
    """Preserve four fold-atomic outcomes and all12dependent method dispositions."""
    product, manifest, folds, predictions, methods = api["reopen"](
        directory, expected_manifest_sha256=checksum
    )
    require(
        len(folds) == 4 and tuple(methods) == shared.METHODS,
        "Four-fold/method population differs",
    )
    scientific = manifest["scientific_payload"]
    failures = scientific["failures"]
    require(
        len(predictions) + len(failures) * 3 == 12,
        "Twelve dependent method dispositions required",
    )
    failure_by_fold = {r["fold_id"]: r for r in failures}
    require(
        len(failure_by_fold) == len(failures) and set(failure_by_fold).issubset(folds),
        "Duplicate or foreign fold failure",
    )
    require(
        set(predictions).issubset(
            {(fold, method) for fold in folds for method in methods}
        ),
        "Foreign prediction method/fold",
    )
    dispositions = []
    for fold in folds:
        available = [(fold, method) in predictions for method in methods]
        require(
            all(available)
            and fold not in failure_by_fold
            or not any(available)
            and fold in failure_by_fold,
            "Fold-atomic prediction/refusal contract differs",
        )
        for method in methods:
            if (fold, method) in predictions:
                dispositions.append(
                    {"fold_id": fold, "method": method, "status": "predicted"}
                )
            else:
                failure = failure_by_fold[fold]
                require(
                    failure["status"] in {"refused", "not_run"},
                    "Unknown fold failure status",
                )
                dispositions.append(
                    {
                        "fold_id": fold,
                        "method": method,
                        **{
                            k: failure[k]
                            for k in (
                                "status",
                                "reason_code",
                                "detail",
                                "exception_type",
                            )
                            if k in failure
                        },
                    }
                )
    return {
        "directory": str(product.directory),
        "manifest_sha256": product.manifest_sha256,
        "scientific_content_sha256": product.scientific_content_sha256,
        "failures": failures,
        "interrupted": scientific.get("interrupted", False),
        "retained_tables": {
            name: manifest["files"][name]
            for name in (
                "training.json",
                "preparations.json",
                "operations.json",
                "failures.json",
                "predictions.json",
            )
        },
        "method_dispositions": dispositions,
        "status_counts": dict(Counter(row["status"] for row in dispositions)),
    }


def batch(
    input_root: Path,
    manifest: Path,
    manifest_sha256: str,
    output: Path,
    *,
    phase: str,
    execution_epoch: str,
    protocol_path: Path,
    protocol_sha256: str,
    prediction_index: Path | None = None,
    prediction_index_sha256: str | None = None,
) -> dict[str, Any]:
    """Retain every declared cohort prediction or post-freeze score disposition."""
    raw, _ = shared.read(protocol_path, protocol_sha256, 65536)
    binding = {"path": str(protocol_path), "sha256": protocol_sha256, "bytes": len(raw)}
    return shared.batch(
        input_root,
        manifest,
        manifest_sha256,
        output,
        phase=phase,
        execution_epoch=execution_epoch,
        prediction_index=prediction_index,
        prediction_index_sha256=prediction_index_sha256,
        protocol_binding=binding,
        cohort=COHORT,
    )


def main() -> None:
    """Parse arguments for the declared source-bound conditional calculation."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("phase", choices=("prepare", "score"))
    for field in ("input-root", "input-manifest", "output", "protocol"):
        parser.add_argument("--" + field, type=Path, required=True)
    for field in ("input-manifest-sha256", "protocol-sha256", "execution-epoch"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--prediction-index", type=Path)
    parser.add_argument("--prediction-index-sha256")
    args = parser.parse_args()
    result = batch(
        args.input_root,
        args.input_manifest,
        args.input_manifest_sha256,
        args.output,
        phase=args.phase,
        execution_epoch=args.execution_epoch,
        protocol_path=args.protocol,
        protocol_sha256=args.protocol_sha256,
        prediction_index=args.prediction_index,
        prediction_index_sha256=args.prediction_index_sha256,
    )
    print(
        json.dumps(
            {
                "phase": result["phase"],
                "cohort": result["cohort"],
                "bin_status_counts": result["bin_status_counts"],
            }
        )
    )


if __name__ == "__main__":
    main()
