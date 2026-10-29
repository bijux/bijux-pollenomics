"""Observe actual Swedish source joins, fixed-baseline scores and exact prior bytes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical controller entrypoint before helper imports")
_entry_directory = _entry_path.parent
_expected_python = {
    "contracts.py",
    "independent.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller import")
sys.path.insert(0, str(_entry_directory))

from contracts import (  # noqa: E402
    FAMILIES,
    PREDICTED,
    PREPARED,
    ROOT,
    SCORED,
    dump,
    exact,
    load,
    pin,
    report,
    require,
    sha,
    verify_inputs,
)
from independent import verify_preparation, verify_scores  # noqa: E402


def validate_stage(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    require(
        actual["id"] == expected["id"]
        and exact(actual["argv"], expected["argv"])
        and type(actual["actual_exit"]) is int
        and actual["actual_exit"] == 0
        and actual["timed_out"] is False,
        "Actual preceding stage differs/failed",
    )
    for stream in ("stdout", "stderr"):
        require(
            sha(Path(actual[stream])) == actual[stream + "_sha256"],
            "Actual stage log changed",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    verify_inputs(plan)
    family = args.family
    output = Path(plan["output"])
    base = output / family
    progress = load(output / "stage-progress.json")
    index = list(FAMILIES).index(family) * 4
    require(
        len(progress) == index + 3,
        "Exactly this cohort preceding native stages required",
    )
    for actual, expected in zip(progress, plan["stages"][: index + 3], strict=True):
        validate_stage(actual, expected)
    receipts = []
    for offset, stage in enumerate(("prepare", "predict", "score")):
        actual = progress[index + offset]
        path = output / "native-receipts" / (family + "-" + stage + ".json")
        record = load(path)
        emitted = json.loads(Path(actual["stdout"]).read_text().splitlines()[-1])
        require(
            exact(emitted["source_execution"], pin(path))
            and exact(record["plan"], pin(args.plan))
            and record["candidate"] == plan["candidate"]
            and record["family"] == family
            and record["stage"] == stage
            and type(record["source_exit"]) is int
            and record["source_exit"] == 0
            and type(record["metadata_exit"]) is int
            and record["metadata_exit"] == 0
            and record["counters"]["LRA_numerical_function_calls"] == 0,
            "Native source receipt/whole status differs",
        )
        for row in record["produced_files"]:
            require(
                pin(Path(row["path"])) == row, "Produced bytes changed between stages"
            )
        receipts.append(pin(path))
    source = verify_preparation(family, plan["studies"][family], base / "prepared")
    scores = verify_scores(base / "prepared", base / "predictions", base / "scores")
    comparisons = []
    for directory, names, tracked_prefix in (
        ("prepared", PREPARED, ""),
        ("predictions", PREDICTED, "predictions/"),
        ("scores", SCORED, ""),
    ):
        root = base / directory
        for entry in root.rglob("*"):
            require(
                not entry.is_symlink() and (entry.is_file() or entry.is_dir()),
                "Produced alias/special member",
            )
        require(
            sorted(
                p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
            )
            == sorted(names),
            "Complete actual output membership differs",
        )
        for name in names:
            generated = root / name
            original = ROOT / report(family) / (tracked_prefix + name)
            require(
                generated.read_bytes() == original.read_bytes(),
                "Current replay differs from exact retained scientific/output bytes: "
                + str(original),
            )
            comparisons.append(
                {
                    "generated": pin(generated),
                    "retained": pin(original),
                    "checker_actual_exit": 0,
                }
            )
    verify_inputs(plan)
    source.pop("outcomes")
    dump(
        base / "independent-review.json",
        {
            "schema_version": "swedish-direct-pollen-source-observation.v1",
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "family": family,
            "actual_native_source_receipts": receipts,
            "native_source_membership_and_mass": source,
            "independent_score_arithmetic": scores,
            "this_study_complete_ten_product_comparisons": comparisons,
            "prepared_product_count": 4,
            "prediction_product_count": 1,
            "scoring_product_count": 5,
            "source_metadata_defect": plan["source_metadata_defect"],
            "historical_protocol_freeze_reference_or_verification_files_reproduced": False,
            "previously_exposed_direct_pollen_development_only": True,
            "LRA_or_field_accuracy_independent_confirmation_rights_or_human_acceptance": False,
            "scope": plan["scope"],
        },
    )
    print(base / "independent-review.json")


if __name__ == "__main__":
    main()
