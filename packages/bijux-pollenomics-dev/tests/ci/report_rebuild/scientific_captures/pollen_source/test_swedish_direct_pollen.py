"""Reject historical-role inflation, wrong training sources and unqualified native custody."""

from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_direct_pollen as subject,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "configs/ci/report-ownership.json").is_file()
)


@lru_cache(maxsize=1)
def records() -> list[Any]:
    prefix = ROOT / Path(subject.CAPTURE).parent / "execution"
    return [
        *[
            json.loads((prefix / n).read_bytes())
            for n in [
                "plan.json",
                "terminal.json",
                "swedish-direct-pollen-terminal.json",
                "runtime-custody-terminal.json",
            ]
        ],
        [
            json.loads((prefix / f / "independent-review.json").read_bytes())
            for f in subject.FAMILIES
        ],
        [
            json.loads(
                (prefix / "native-receipts" / (f + "-" + s + ".json")).read_bytes()
            )
            for f in subject.FAMILIES
            for s in ["prepare", "predict", "score"]
        ],
    ]


def owners() -> list[JsonObject]:
    result: list[JsonObject] = []
    for family in subject.FAMILIES:
        prefix = "docs/report/regions/nordic/" + family + "/"
        for role, suffix, paths in [
            (
                "retained_source",
                "source-preparation-products",
                sorted(prefix + n for n in subject.PREPARED_NAMES),
            ),
            (
                "unresolved",
                "report-products",
                sorted(
                    n for n in subject.HISTORICAL_UNRESOLVED if n.startswith(prefix)
                ),
            ),
        ]:
            result.append(
                {
                    "owner_id": "regions/nordic/" + family + "/" + suffix,
                    "role": role,
                    "paths": paths,
                    "producer_paths": [],
                    "producer_inputs": [],
                }
            )
    return result


def test_actual_six_source_stages_two_observers_and_historical_partition() -> None:
    subject.validate_native_records(*records())
    subject.validate_owner_partition(owners())


NATIVE_NEGATIVES: list[tuple[int, list[Any], Any]] = [
    (1, ["actual_exit"], True),
    (1, ["status"], "failed"),
    (1, ["before_pin_mismatches"], ["changed"]),
    (1, ["absent_input_paths_unchanged"], False),
    (2, ["actual_exit"], 1),
    (2, ["scientific_acceptance_claimed"], True),
    (
        2,
        ["historical_protocol_freeze_reference_or_verification_files_reproduced"],
        True,
    ),
    (3, ["delegate_actual_exit"], 1),
    (3, ["resource_bounds_met"], False),
    (3, ["timed_out"], True),
    (1, ["stages", 0, "actual_exit"], 1),
    (1, ["stages", 0, "argv"], ["substitute"]),
    (4, [0, "actual_exit"], True),
    (4, [0, "prepared_product_count"], 8),
    (
        4,
        [1, "historical_protocol_freeze_reference_or_verification_files_reproduced"],
        True,
    ),
    (
        4,
        [
            1,
            "LRA_or_field_accuracy_independent_confirmation_rights_or_human_acceptance",
        ],
        True,
    ),
    (5, [0, "metadata_exit"], False),
    (5, [1, "counters", "LRA_numerical_function_calls"], 1),
    (5, [1, "actual_read_paths"], ["/declared/sealed-outcomes/outcomes-SE.json.gz"]),
    (
        0,
        ["studies", "swedish-lake-transfer", "protocol", "training", "input_path"],
        "docs/report/regions/nordic/author-target-pollen/inputs/training-DK.json.gz",
    ),
    (
        0,
        ["studies", "swedish-neotoma-holdout", "protocol", "training", "input_sha256"],
        "0" * 64,
    ),
]


@pytest.mark.parametrize(("part", "path", "value"), NATIVE_NEGATIVES)
def test_native_scientific_training_and_typed_status_refusals(
    part: int, path: list[Any], value: Any
) -> None:
    base = records()
    bad = list(base)
    bad[part] = deepcopy(base[part])
    node = bad[part]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(ReportRebuildError):
        subject.validate_native_records(*bad)


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "duplicate",
        "historical_retained",
        "historical_produced",
        "wrong_training_recipe",
        "whole_old_membership",
        "unknown_overlap",
        "historical_overlap",
    ],
)
def test_only_eight_preparation_files_are_retained(case: str) -> None:
    rows = owners()
    if case == "missing":
        rows.pop(0)
    elif case == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif case == "historical_retained":
        rows[1]["role"] = "retained_source"
    elif case == "historical_produced":
        rows[1]["role"] = "executable"
    elif case == "wrong_training_recipe":
        rows[0]["producer_inputs"] = [
            "docs/report/regions/nordic/author-target-pollen/inputs/training-DK.json.gz"
        ]
    elif case == "whole_old_membership":
        first, second = rows[0]["paths"], rows[1]["paths"]
        assert isinstance(first, list) and isinstance(second, list)
        rows[0]["paths"] = [*first, *second]
    else:
        selected_paths = rows[0 if case == "unknown_overlap" else 1]["paths"]
        assert isinstance(selected_paths, list)
        rows.append(
            {
                "owner_id": "unrelated",
                "paths": [selected_paths[0]],
            }
        )
    with pytest.raises(ReportRebuildError):
        subject.validate_owner_partition(rows)


@pytest.mark.parametrize(
    "case",
    [
        "extra",
        "missing",
        "tamper",
        "symlink",
        "directory_alias",
        "FIFO",
        "bytecode",
        "escape",
    ],
)
def test_every_capsule_payload_is_regular_confined_and_declared(
    tmp_path: Path, case: str
) -> None:
    capsule = tmp_path / "capsule"
    capsule.mkdir()
    (capsule / "capture.json").write_text("{}\n")
    payload = b"public-source"
    (capsule / "source.txt").write_bytes(payload)
    members = {
        "source.txt": {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    }
    subject.validate_capsule_members(tmp_path, "capsule", members)
    if case == "extra":
        (capsule / "unexpected.txt").write_bytes(b"extra")
    elif case == "missing":
        (capsule / "source.txt").unlink()
    elif case == "tamper":
        (capsule / "source.txt").write_bytes(b"changed")
    elif case == "symlink":
        (capsule / "alias.txt").symlink_to("source.txt")
    elif case == "directory_alias":
        (capsule / "alias-directory").symlink_to(capsule, target_is_directory=True)
    elif case == "FIFO":
        os.mkfifo(capsule / "pipe")
    elif case == "bytecode":
        (capsule / "source.pyc").write_bytes(b"not-source")
        members["source.pyc"] = {
            "sha256": hashlib.sha256(b"not-source").hexdigest(),
            "bytes": 10,
        }
    else:
        (tmp_path / "outside.txt").write_bytes(payload)
        members["../outside.txt"] = members.pop("source.txt")
        (capsule / "source.txt").unlink()
    with pytest.raises(ReportRebuildError):
        subject.validate_capsule_members(tmp_path, "capsule", members)


def test_full_public_capsule_and_exact_preparation_inventory() -> None:
    entries = {
        name: InventoryEntry(
            path=name.removeprefix("docs/report/"),
            kind="file",
            sha256=row["sha256"],
            size=row["bytes"],
            canonical_sha256=row["sha256"],
        )
        for name, row in subject.PREPARED_PUBLICATIONS.items()
    }
    got, evidence = subject.validated_swedish_direct_pollen_capture(
        ROOT, entries, owners()
    )
    assert len(got) == 8 and evidence["prepared_products_admitted"] == 8
    historical = evidence["historical_unresolved_paths"]
    assert isinstance(historical, list) and len(historical) == 9
    first = next(iter(entries))
    bad = {**entries, first: replace(entries[first], size=True)}
    with pytest.raises(ReportRebuildError):
        subject.validated_swedish_direct_pollen_capture(ROOT, bad, owners())
