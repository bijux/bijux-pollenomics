"""Synthetic all-owner, chronology, complete-window and closed-I/O controls."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    same,
)

from . import verification
from .fixtures import cell, fixture, native_samples
from .native_owners import selected_age
from .population import expected_core


@pytest.mark.parametrize("index,members", [(0, 19), (1, 9)])
def test_every_native_owner_and_six_halfopen_windows(index: int, members: int) -> None:
    source, core, protocol = fixture(index)
    original = deepcopy(source)
    result = expected_core(source, core, protocol)
    count = core["identity"]["source_sample_count"]
    assert source == original
    assert [r["sample_id"] for r in result["samples"]] == list(
        range(10000, 10000 + count)
    )
    assert result["population"]["samples"] == count
    assert (
        result["chronology"]["selected_chronology_id"]
        == core["chronology"]["selected_id"]
    )
    assert (
        result["chronology"]["native_collection_default_reference"]
        == core["chronology"]["native_collection_default_reference"]
    )
    assert (
        result["chronology"]["native_chronology_declarations"]
        == source["rows"][0]["site"]["collectionunit"]["chronologies"]
    )
    assert all(
        r["member_count"] == members
        and r["panel_counts"] == [4 * members, 2 * members]
        and r["pollen_N"] == 9 * members
        and r["excluded_pollen_N"] == 3 * members
        for r in result["windows"]
    )
    assert result["source_totals"]["panel_N"] == 6 * count
    assert result["source_totals"]["pollen_N"] == 9 * count
    assert (
        result["native_source_metadata"]["outer_dataset_metadata"]["doi"]
        == "synthetic citation"
    )
    assert result["samples"][6]["age_disposition"] == "outside_requested_windows"
    assert result["samples"][7]["age_disposition"] == "negative_native_age_retained"
    assert "ageyounger" not in result["samples"][0]["selected_age"]
    assert result["engine_calls"] == result["model_fits"] == 0


def test_new_oracle_matches_producer_on_artificial_sources_only() -> None:
    from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support.projection import (
        project,
    )

    for index in (0, 1):
        source, core, protocol = fixture(index)
        same(project(source, core, protocol), expected_core(source, core, protocol))


@pytest.mark.parametrize(
    "kind,state",
    [
        ("missing", "missing_selected_age"),
        ("duplicate", "duplicate_selected_age"),
        ("wrong_type", "incompatible_selected_age_type_or_name"),
        ("wrong_name", "incompatible_selected_age_type_or_name"),
        ("boolean", "invalid_selected_age_value"),
        ("nonfinite", "invalid_selected_age_value"),
        ("outside_bound", "conflicting_selected_age_bounds"),
    ],
)
def test_unassignable_owner_suppresses_all_own_windows_not_other_core(
    kind: str, state: str
) -> None:
    source, core, protocol = fixture()
    owner = native_samples(source)[-1]
    claims = owner["ages"]
    selected = claims[1]
    if kind == "missing":
        claims.pop()
    elif kind == "duplicate":
        claims.append(deepcopy(selected))
    elif kind == "wrong_type":
        selected["agetype"] = "Radiocarbon years BP"
    elif kind == "wrong_name":
        selected["chronologyname"] = "other named model"
    elif kind == "boolean":
        selected["age"] = True
    elif kind == "nonfinite":
        selected["age"] = Decimal("1e999")
    else:
        selected["ageolder"] = selected["age"] - 1
    result = expected_core(source, core, protocol)
    assert result["samples"][-1]["selected_age_status"] == state
    assert all(
        w["status"] == "suppressed_unassignable_age"
        and w["panel_N"] is None
        and w["pollen_N"] is None
        and w["unassignable_source_sample_ids"] == [owner["sampleid"]]
        for w in result["windows"]
    )
    assert result["source_totals"]["panel_N"] == 900
    other, other_core, other_protocol = fixture(1)
    assert all(
        w["status"] == "supported"
        for w in expected_core(other, other_core, other_protocol)["windows"]
    )


def test_absent_and_null_bounds_stay_distinct_and_never_gain_precision() -> None:
    source, core, protocol = fixture()
    claims = native_samples(source)[0]["ages"]
    before = deepcopy(claims)
    assert selected_age(claims, core)[0] == "selected_typed_point"
    assert claims == before and "ageyounger" not in claims[1]
    claims[1]["ageyounger"] = None
    result = expected_core(source, core, protocol)
    selected = result["samples"][0]["selected_age"]
    assert selected["ageyounger"] is None and "ageolder" not in selected
    assert result["samples"][0]["native_ages"] == claims


def test_outside_window_panel_missing_does_not_disqualify_supported_windows() -> None:
    source, core, protocol = fixture()
    sample = native_samples(source)[6]
    sample["datum"].pop(1)
    result = expected_core(source, core, protocol)
    assert result["source_totals"]["panel_counts"] is None
    assert result["samples"][6]["taxa"][1]["status"] == "missing_literal"
    assert all(w["status"] == "supported" for w in result["windows"])


@pytest.mark.parametrize(
    "defect,status",
    [
        ("missing", "suppressed_incomplete_panel"),
        ("zero", "suppressed_zero_panel"),
        ("full_duplicate", "suppressed_full_mass"),
        ("empty", "empty_window"),
    ],
)
def test_no_complete_case_subset_or_absent_to_zero_replacement(
    defect: str, status: str
) -> None:
    source, core, protocol = fixture()
    samples = native_samples(source)
    if defect == "missing":
        samples[0]["datum"].pop(1)
    elif defect == "zero":
        for sample in samples:
            if sample["ages"][1]["age"] == 2700:
                sample["datum"][0]["value"] = sample["datum"][1]["value"] = 0
    elif defect == "full_duplicate":
        samples[0]["datum"].append(cell("Pinus", 385, 3))
    else:
        for sample in samples:
            sample["ages"][1]["age"] = 5700
    result = expected_core(source, core, protocol)
    assert result["windows"][0]["status"] == status
    assert result["windows"][0]["member_count"] == (0 if defect == "empty" else 19)
    if defect == "zero":
        assert result["windows"][0]["panel_counts"] == [0, 0]
    elif defect == "missing":
        assert result["windows"][0]["panel_counts"] is None
    elif defect == "full_duplicate":
        assert result["samples"][0]["known_valid_pollen_cell_sum"] == 12
        assert result["samples"][0]["pollen_N"] is None


def test_count_tokens_preserve_arbitrary_integer_and_decimal_invalidity() -> None:
    source, core, protocol = fixture()
    native_samples(source)[0]["datum"][0]["value"] = 2**80
    native_samples(source)[0]["datum"][1]["value"] = Decimal("1.0")
    result = expected_core(source, core, protocol)
    assert result["samples"][0]["panel_counts"] == [2**80, None]
    assert result["samples"][0]["taxa"][1]["status"] == "invalid_count"
    assert result["samples"][0]["known_valid_pollen_cell_sum"] == 2**80 + 3


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_owner",
        "boolean_owner",
        "outer_owner",
        "inner_owner",
        "default_reference",
        "false_flag",
        "integer_flag",
        "duplicate_declaration",
        "wrong_selected_metadata",
        "duplicate_core",
    ],
)
def test_source_identity_and_chronology_cannot_be_silently_rebound(defect: str) -> None:
    source, core, protocol = fixture()
    site = source["rows"][0]["site"]
    unit = site["collectionunit"]
    if defect == "duplicate_owner":
        native_samples(source)[1]["sampleid"] = native_samples(source)[0]["sampleid"]
    elif defect == "boolean_owner":
        native_samples(source)[0]["sampleid"] = True
    elif defect == "outer_owner":
        site["dataset"]["datasetid"] += 1
    elif defect == "inner_owner":
        unit["dataset"]["datasetid"] += 1
    elif defect == "default_reference":
        unit["defaultchronology"] = core["chronology"]["selected_id"]
    elif defect in ("false_flag", "integer_flag"):
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = (
            False if defect == "false_flag" else 1
        )
    elif defect == "duplicate_declaration":
        unit["chronologies"].append(deepcopy(unit["chronologies"][0]))
    elif defect == "wrong_selected_metadata":
        unit["chronologies"][1]["chronology"]["chronology"]["chronologyname"] = "other"
    else:
        source["rows"].append(deepcopy(source["rows"][0]))
    with pytest.raises(ValueError):
        expected_core(source, core, protocol)


def io_fixture(root: Path) -> tuple[Path, Path, Path]:
    repository, products = root / "repository", root / "repository/artifacts/products"
    products.mkdir(parents=True)
    source0, _, protocol = fixture()
    source1, _, _ = fixture(1)

    def write(path: str, value: Any) -> dict[str, Any]:
        body = (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode()
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return {"path": path, "bytes": len(body), "sha256": sha256(body).hexdigest()}

    for source, core in zip((source0, source1), protocol["cores"], strict=True):
        core["source"] = write(core["source"]["path"], source)
    policy = {
        "schema_version": "krageholm-regional-literal-panel-protocol.v1",
        "taxa": protocol["taxa"],
        "windows": protocol["windows"],
        **{k: "synthetic " + k for k in verification.INHERITED},
    }
    manifest = {
        "parts": [
            {
                "filename": Path(c["source"]["path"]).name,
                "downloaded_dataset_ids": [c["identity"]["dataset_id"]],
            }
            for c in protocol["cores"]
        ]
    }
    protocol["provenance"]["raw_manifest"] = write("metadata/manifest.json", manifest)
    baseline = {
        "input_artifacts": {
            "raw_archive": {
                "path": str(Path(protocol["cores"][0]["source"]["path"]).parent),
                "manifest_sha256": protocol["provenance"]["raw_manifest"]["sha256"],
                "part_sha256": {
                    Path(c["source"]["path"]).name: c["source"]["sha256"]
                    for c in protocol["cores"]
                },
            }
        }
    }
    protocol["provenance"]["relational_baseline"] = write(
        "metadata/baseline.json", baseline
    )
    protocol["provenance"]["literal_policy"] = write("metadata/policy.json", policy)
    protocol_pin = write("protocol.json", protocol)
    enriched = {**protocol, **{k: policy[k] for k in verification.INHERITED}}
    members = {}
    for source, core in zip((source0, source1), protocol["cores"], strict=True):
        pin = write(
            "artifacts/products/" + core["key"] + ".json",
            expected_core(source, core, enriched),
        )
        members[core["key"]] = {**pin, "path": Path(pin["path"]).name}
    result = {
        "schema_version": "nordic-literal-window-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": "a" * 40,
        "index_sha256": "b" * 64,
        "python_files_checked": 1,
        "protocol_sha256": protocol_pin["sha256"],
        "source_guards_passed": True,
        "sourcepins": [protocol["provenance"][k] for k in verification.PROVENANCE]
        + [c["source"] for c in protocol["cores"]],
        "products": members,
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "resources": {
            "elapsed_seconds": 1.0,
            "peak_rss_bytes": 1000000,
            "output_bytes": sum(p.stat().st_size for p in products.iterdir()),
        },
    }
    write("artifacts/products/result.json", result)
    return repository, products, repository / "protocol.json"


@pytest.fixture
def closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    # This isolates I/O/contract tests; actual CLI uses the real Git/byte guard.
    monkeypatch.setattr(
        verification,
        "code_state",
        lambda _: {
            "head": "a" * 40,
            "index_sha256": "b" * 64,
            "python_files": {"owner.py": "c" * 64},
        },
    )
    return io_fixture(tmp_path)


def test_closed_products_verify_all222owners_and12windows(
    closed: tuple[Path, Path, Path],
) -> None:
    facts = verification.verify(*closed)
    assert facts["native_sample_owners_checked"] == 222
    assert len(facts["cores"]) == 2
    assert all(c["fixed_windows_checked"] == 6 for c in facts["cores"])


@pytest.mark.parametrize(
    "defect",
    [
        "source_byte",
        "source_order",
        "wrong_epoch",
        "wrong_index",
        "code_count",
        "product_pin",
        "hidden_file",
        "false_guard",
        "claim_model",
        "resource",
        "sourcepin_type",
    ],
)
def test_closed_identity_inventory_epoch_and_resource_disagreements_refuse(
    closed: tuple[Path, Path, Path], defect: str
) -> None:
    repository, products, protocol_path = closed
    result_path = products / "result.json"
    result = json.loads(result_path.read_text())
    if defect == "source_byte":
        protocol = json.loads(protocol_path.read_text())
        path = repository / protocol["cores"][0]["source"]["path"]
        path.write_bytes(path.read_bytes().replace(b'"Betula"', b'"WrongX"', 1))
    elif defect == "source_order":
        result["sourcepins"].reverse()
    elif defect == "wrong_epoch":
        result["source_commit"] = "f" * 40
    elif defect == "wrong_index":
        result["index_sha256"] = "f" * 64
    elif defect == "code_count":
        result["python_files_checked"] = 2
    elif defect == "product_pin":
        result["products"]["laihalampi"]["sha256"] = "f" * 64
    elif defect == "hidden_file":
        (products / "hidden.json").write_text("{}")
    elif defect == "false_guard":
        result["source_guards_passed"] = False
    elif defect == "claim_model":
        result["model_fits"] = 1
    elif defect == "resource":
        result["resources"]["peak_rss_bytes"] = 2 * 1024**3
    else:
        result["source_acquisition"] = 0
    result_path.write_text(json.dumps(result))
    with pytest.raises((ValueError, KeyError)):
        verification.verify(repository, products, protocol_path)


def test_guard_detects_code_epoch_change_after_all_literal_comparison(
    closed: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    states = iter(
        [
            {
                "head": "a" * 40,
                "index_sha256": "b" * 64,
                "python_files": {"owner.py": "c" * 64},
            },
            {
                "head": "a" * 40,
                "index_sha256": "d" * 64,
                "python_files": {"owner.py": "c" * 64},
            },
        ]
    )
    monkeypatch.setattr(verification, "code_state", lambda _: next(states))
    with pytest.raises(ValueError, match="changed"):
        verification.verify(*closed)
