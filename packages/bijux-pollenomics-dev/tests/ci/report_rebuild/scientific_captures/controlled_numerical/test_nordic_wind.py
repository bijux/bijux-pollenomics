"""Keep reviewed scalar outcomes and their separate owner immutable on transport."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical.nordic_wind import (
    OWNER,
    PRODUCT,
    validated_nordic_wind_reference,
)

_Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]]]


@pytest.fixture
def reference(tmp_path: Path) -> _Fixture:
    repository = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    raw = (repository / PRODUCT).read_bytes()
    target = tmp_path / PRODUCT
    target.parent.mkdir(parents=True)
    target.write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    entry = InventoryEntry(
        path=PRODUCT.removeprefix("docs/report/"),
        kind="file",
        size=len(raw),
        sha256=sha,
        canonical_sha256=sha,
    )
    owners: list[dict[str, Any]] = [
        {
            "owner_id": OWNER,
            "role": "retained_source",
            "paths": [PRODUCT],
            "producer_paths": [],
            "producer_inputs": [],
        }
    ]
    return tmp_path, {PRODUCT: entry}, owners


def test_complete_reference_preserves_science_and_publication_epochs(
    reference: _Fixture,
) -> None:
    root, tracked, owners = reference
    before = copy.deepcopy(owners)
    entries, evidence = validated_nordic_wind_reference(root, tracked, owners)
    assert len(entries) == 1 and entries[0] == tracked[PRODUCT] and owners == before
    assert evidence["new_R_kernel_moment_or_model_calls"] == 0
    assert evidence["original_epochs"] == {
        "baseline_source": "33d45ecfd6be7d275b69a7a7350bb72ae7c5269e",
        "saved_wind_execution": "1413f8fc7e73d3920d9abc6e4999f28ec722a935",
        "actual_reference_execution": "cc29d8b492328f25b5b14c91e3e62b6c88abf62e",
        "canonical_reference_source_adoption": "54febf2f0a0c56189582c6696093e471b5bd381b",
    }
    assert "publication HEAD is not a rerun" in str(evidence["scope"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra-owner",
        "duplicate-owner",
        "extra-path",
        "role",
        "producer",
        "inputs",
        "malformed-paths",
    ],
)
def test_unreviewed_declaration_refuses(reference: _Fixture, mutation: str) -> None:
    root, tracked, owners = reference
    if mutation == "missing":
        owners.clear()
    elif mutation == "extra-owner":
        owners.append({**owners[0], "owner_id": OWNER + "/foreign"})
    elif mutation == "duplicate-owner":
        owners.append(copy.deepcopy(owners[0]))
    elif mutation == "extra-path":
        owners[0]["paths"] = [PRODUCT, PRODUCT + ".foreign"]
    elif mutation == "role":
        owners[0]["role"] = "maintained_editorial"
    elif mutation == "producer":
        owners[0]["producer_paths"] = ["run.py"]
    elif mutation == "inputs":
        owners[0]["producer_inputs"] = ["invented.json"]
    else:
        owners[0]["paths"] = [True]
    with pytest.raises(ReportRebuildError, match="owner|declaration"):
        validated_nordic_wind_reference(root, tracked, owners)


@pytest.mark.parametrize(
    "mutation",
    ["missing-file", "missing-inventory", "symlink", "hardlink", "relabel", "refusal"],
)
def test_nonidentical_or_aliased_products_refuse(
    reference: _Fixture, mutation: str
) -> None:
    root, tracked, owners = reference
    path = root / PRODUCT
    if mutation == "missing-file":
        path.unlink()
    elif mutation == "missing-inventory":
        tracked.clear()
    elif mutation == "symlink":
        original = path.with_suffix(".original.json")
        path.rename(original)
        path.symlink_to(original.name)
    elif mutation == "hardlink":
        path.with_suffix(".alias.json").hardlink_to(path)
    else:
        value = json.loads(path.read_bytes())
        if mutation == "relabel":
            value["epochs"]["actual_reference_execution"] = "f" * 40
        else:
            value["population"].update(completed=45, refused=1)
            value["passed"] = False
        raw = (json.dumps(value, indent=2) + "\n").encode()
        path.write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        tracked[PRODUCT] = InventoryEntry(
            path=PRODUCT.removeprefix("docs/report/"),
            kind="file",
            size=len(raw),
            sha256=sha,
            canonical_sha256=sha,
        )
    with pytest.raises(ReportRebuildError):
        validated_nordic_wind_reference(root, tracked, owners)


def test_absent_reference_has_no_admission(tmp_path: Path) -> None:
    assert validated_nordic_wind_reference(tmp_path, {}, []) == ((), {})


def test_foreign_owner_of_untracked_reference_cannot_disappear(
    reference: _Fixture,
) -> None:
    root, tracked, owners = reference
    tracked.clear()
    owners[0]["owner_id"] = OWNER + "/foreign"
    with pytest.raises(ReportRebuildError, match="owner differs"):
        validated_nordic_wind_reference(root, tracked, owners)
