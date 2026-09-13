"""Retained contradictions versus distinct workbook replay authenticity."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells.models import (
    decoded,
    encoded,
    object_value,
)
from bijux_pollenomics.collection.sources.rootsi.cells.publication import publish
from bijux_pollenomics.collection.sources.rootsi.cells.reading import (
    read_bundle,
    replay_bundle,
)

from .support import (
    SyntheticParser,
    capture_fixture,
    repin,
    synthetic_capture_authority,
)


@pytest.mark.parametrize(
    "change",
    [
        "delete_cell",
        "duplicate_cell",
        "position",
        "accounting",
        "science",
        "parser_bool",
        "inventory_pin",
        "available_count",
    ],
)
def test_rehashed_retained_contradictions_refuse(tmp_path: Path, change: str) -> None:
    """Correct byte inventories cannot excuse contradictory internal records."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    path = bundle.directory / "cells.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    if change == "delete_cell":
        path.write_bytes(b"".join(lines[:-1]))
    elif change == "duplicate_cell":
        path.write_bytes(b"".join([lines[0], *lines]))
    elif change == "position":
        row = object_value(decoded(lines[0]), "cell")
        row["row"] = 1
        lines[0] = encoded(row)
        path.write_bytes(b"".join(lines))
    elif change == "accounting":
        path = bundle.directory / "accounting.json"
        row = object_value(decoded(path.read_bytes()), "accounting")
        row["scientifically_admitted_observations"] = 1
        path.write_bytes(encoded(row))
    else:
        path = bundle.directory / "manifest.json"
        row = object_value(decoded(path.read_bytes()), "manifest")
        if change in {"inventory_pin", "available_count"}:
            binding = object_value(row["capture"], "capture")
            binding[
                "inventory_sha256"
                if change == "inventory_pin"
                else "available_workbooks"
            ] = "a" * 64 if change == "inventory_pin" else 80
            row["capture"] = binding
        elif change == "science":
            row["scientific_admission"] = "accepted"
        else:
            parser = object_value(row["parser"], "parser")
            parser["formatting_info"] = 1
            row["parser"] = parser
        path.write_bytes(encoded(row))
    with pytest.raises(IntakeRefusal), synthetic_capture_authority(capture):
        read_bundle(bundle.directory, repin(bundle.directory))


def test_internally_coherent_text_forgery_requires_native_replay(
    tmp_path: Path,
) -> None:
    """Pinned consistency alone does not assert authenticity of repinned replacements."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    path = bundle.directory / "cells.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    row = object_value(decoded(lines[1]), "cell")
    row["decoded_value"] = "coherently replaced text"
    lines[1] = encoded(row)
    path.write_bytes(b"".join(lines))
    with synthetic_capture_authority(capture):
        retained = read_bundle(bundle.directory, repin(bundle.directory))
        with pytest.raises(IntakeRefusal, match="workbook_replay_mismatch"):
            replay_bundle(retained, capture, SyntheticParser())


def test_duplicate_json_key_and_uninventoried_file_refuse(tmp_path: Path) -> None:
    """Reject duplicate parsing and unaccounted retained members."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    path = bundle.directory / "cells.jsonl"
    payload = path.read_bytes()
    path.write_bytes(payload.replace(b'"row":0', b'"row":999,"row":0', 1))
    with (
        pytest.raises(IntakeRefusal, match="duplicate_json_key"),
        synthetic_capture_authority(capture),
    ):
        read_bundle(bundle.directory, repin(bundle.directory))
    path.write_bytes(payload)
    (bundle.directory / "unowned.txt").write_text("unowned")
    with pytest.raises(IntakeRefusal, match="bundle_inventory"):
        read_bundle(bundle.directory, bundle.manifest_sha256)


def test_unpatched_reader_refuses_arbitrary_retained_capture(tmp_path: Path) -> None:
    """No fixture authority substitution is used for the public unknown-capture test."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    with pytest.raises(IntakeRefusal, match="unrecognized_capture"):
        read_bundle(bundle.directory, repin(bundle.directory))


@pytest.mark.parametrize(
    ("field", "value"),
    [("archive_member", "rootsi/invented.xls"), ("sha256", "b" * 64), ("bytes", 1)],
)
def test_selected_binding_must_belong_to_pinned_roster(
    tmp_path: Path, field: str, value: object
) -> None:
    """The roster join refuses before unrelated workbook or cell identity checks."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    path = bundle.directory / "manifest.json"
    manifest = object_value(decoded(path.read_bytes()), "manifest")
    binding = object_value(manifest["capture"], "capture")
    native = {**capture.workbooks[0].as_dict(), field: value}
    binding["selected_workbooks"] = [native]
    manifest["capture"] = binding
    path.write_bytes(encoded(manifest))
    with (
        pytest.raises(IntakeRefusal, match="workbook_not_in_retained_roster"),
        synthetic_capture_authority(capture),
    ):
        read_bundle(bundle.directory, repin(bundle.directory))


def test_rehashed_native_inventory_bytes_cannot_change_capture(tmp_path: Path) -> None:
    """Ordinary manifest rehashing cannot replace the pinned source roster bytes."""
    capture = capture_fixture(tmp_path)
    bundle = publish(capture, tmp_path / "review", SyntheticParser())
    path = bundle.directory / "capture-inventory.json"
    path.write_bytes(path.read_bytes() + b" ")
    with (
        pytest.raises(IntakeRefusal, match="input_digest_mismatch"),
        synthetic_capture_authority(capture),
    ):
        read_bundle(bundle.directory, repin(bundle.directory))
