"""Derived unit reports preserve source scopes, null references and capture bytes."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.unit_resources import (
    capture_neotoma_unit_resources,
)

from ..resources.native_payloads import response
from .test_capture import limits, prepared
from .test_profiles import payload


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.unit_resources.qualification"
    )


def captured(
    tmp_path: Path,
    *,
    protected: bool = False,
    empty: bool = False,
    foreign: bool = False,
) -> tuple[Path, Any, Path, dict[str, Path]]:
    plan, roster, sources = prepared(tmp_path, protected=protected)
    value = payload()
    if empty:
        value["data"] = []
    elif foreign:
        value["data"][0]["speleothem"]["siteid"] = 999
    root = tmp_path / "units"
    result = capture_neotoma_unit_resources(
        root,
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, json.dumps(value).encode()),
    )
    return root, result, roster, sources


def test_derived_unit_report_keeps_original_unqualified_ledger_and_nulls(
    tmp_path: Path,
) -> None:
    root, result, roster, sources = captured(tmp_path)
    before = {p: p.read_bytes() for p in root.iterdir()}
    report = owner().qualify_neotoma_unit_capture(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
    )
    assert report["source_capture_relabelled"] is False
    assert report["partitions"] == {"parsed_unit_source": 1}
    row = report["units"][0]
    assert row["scope"]["native_dataset_ids"] == [201, 202]
    assert (
        row["source_terminal_status"] == "received_complete_unqualified_unit_resource"
    )
    for field in ("vegetationcoverpercent", "landusecoverpercent"):
        assert row["summary"]["reference_field_availability"][field] == {
            "explicit_null_rows": 1,
            "non_null_rows": 0,
        }
    assert before == {p: p.read_bytes() for p in root.iterdir()}


def test_protected_unit_qualification_never_calls_native_body_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result, roster, sources = captured(tmp_path, protected=True)
    monkeypatch.setattr(
        owner(),
        "read_neotoma_unit_body",
        lambda *a, **k: pytest.fail("protected native buffer opened"),
    )
    report = owner().qualify_neotoma_unit_capture(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
    )
    assert report["partitions"] == {"not_qualified_exposure_role": 1}


def test_empty_unit_api_is_not_global_entity_absence(tmp_path: Path) -> None:
    root, result, roster, sources = captured(tmp_path, empty=True)
    report = owner().qualify_neotoma_unit_capture(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
    )
    assert report["partitions"] == {"unavailable_unit_api_empty": 1}
    assert report["units"][0]["absence_certified"] is False


def test_foreign_native_unit_retains_scope_and_refusal_reason(tmp_path: Path) -> None:
    root, result, roster, sources = captured(tmp_path, foreign=True)
    report = owner().qualify_neotoma_unit_capture(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
    )
    assert report["partitions"] == {"refused_unit_source": 1}
    assert report["units"][0]["scope"]["native_dataset_ids"] == [201, 202]
    assert "owner" in report["units"][0]["reason"]


def test_current_returned_buffer_is_authenticated_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result, roster, sources = captured(tmp_path)
    from bijux_pollenomics.collection.sources.neotoma.capture.unit_resources import (
        replay,
    )

    original = replay.replay_neotoma_unit_resources

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / result.units[0]["attempts"][0]["body_file"]).write_bytes(
            b'{"foreign":true}'
        )
        return value

    monkeypatch.setattr(replay, "replay_neotoma_unit_resources", swap)
    with pytest.raises(ValueError):
        owner().qualify_neotoma_unit_capture(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )
