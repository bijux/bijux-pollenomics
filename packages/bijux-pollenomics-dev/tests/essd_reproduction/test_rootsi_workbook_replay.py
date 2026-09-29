"""Verify deterministic Rootsi workbook replay without scientific promotion."""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.rootsi import RootsiSiteMetadataClaim
from bijux_pollenomics.collection.sources.rootsi.authority import (
    ARCHIVE_SHA256,
    METADATA_MEMBER,
    METADATA_SHA256,
)
from bijux_pollenomics_dev.essd_reproduction import rootsi_workbook_replay
from bijux_pollenomics_dev.essd_reproduction.rootsi_workbook_replay import (
    RootsiWorkbookReplayError,
    RootsiWorkbookReplayInput,
    publish_rootsi_workbook_replay,
    read_rootsi_workbook_replay,
)

JsonObject = dict[str, Any]
_ACTUAL_LOAD_INPUTS = rootsi_workbook_replay._load_inputs


@dataclass(frozen=True)
class _Harness:
    source: RootsiWorkbookReplayInput
    inputs: rootsi_workbook_replay._Inputs
    roster: tuple[JsonObject, ...]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _objects(path: Path) -> list[JsonObject]:
    rows = []
    for line in path.read_bytes().splitlines():
        value = json.loads(line)
        assert isinstance(value, dict)
        rows.append(cast(JsonObject, value))
    return rows


def _tree_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def _cell(
    workbook: rootsi_workbook_replay._Workbook,
    sheet: rootsi_workbook_replay._Sheet,
    row: int,
    column: int,
    *,
    cell_type: int,
    value: object,
) -> JsonObject:
    numeric = cell_type in (2, 3)
    binary64_hex = None
    if numeric:
        assert isinstance(value, (int, float))
        binary64_hex = float(value).hex()
    return {
        "cell_id": rootsi_workbook_replay._source_id(
            workbook.workbook_id, sheet.ordinal, row, column
        ),
        "workbook_id": workbook.workbook_id,
        "sheet_ordinal": sheet.ordinal,
        "row": row,
        "column": column,
        "cell_type": cell_type,
        "decoded_value": value,
        "binary64_hex": binary64_hex,
        "xf_index": 0,
        "refusal_reason": None,
    }


def _claim(
    source_row: int,
    *,
    label: str,
    workbook: str | None,
    samples: int | None,
    site_name: str | None = None,
) -> RootsiSiteMetadataClaim:
    raw_samples = "" if samples is None else str(samples)
    return RootsiSiteMetadataClaim(
        source_row_number=source_row,
        country_native="SWE",
        site_name=site_name or f"Site {label}",
        site_id_native=f"site-{label}",
        record_id_native=f"record-{label}",
        sample_count_claim=samples,
        site_label=label,
        observation_workbook_claim=workbook,
        latitude_dms_claim=None,
        latitude_decimal_claim=None,
        longitude_dms_claim=None,
        longitude_decimal_claim=None,
        elevation_m_claim=None,
        site_area_ha_claim=None,
        site_radius_m_claim=None,
        date_count_claim=None,
        basin_type_claim=None,
        source_values=(("nr_samples", raw_samples),),
        unsupported_values=(),
    )


def _snapshot(label: str, path: Path) -> rootsi_workbook_replay._Snapshot:
    content = path.read_bytes()
    return rootsi_workbook_replay._Snapshot(
        label=label,
        path=path,
        sha256=_sha256(content),
        byte_count=len(content),
    )


def _repin_peer(directory: Path, name: str, content: bytes) -> str:
    (directory / name).write_bytes(content)
    manifest = _object(directory / "manifest.json")
    artifacts = cast(list[JsonObject], manifest["artifacts"])
    artifact = next(row for row in artifacts if row["path"] == name)
    artifact["sha256"] = _sha256(content)
    artifact["byte_count"] = len(content)
    manifest_bytes = _canonical(manifest)
    (directory / "manifest.json").write_bytes(manifest_bytes)
    return _sha256(manifest_bytes)


def _repin_manifest(directory: Path, manifest: JsonObject) -> str:
    content = _canonical(manifest)
    (directory / "manifest.json").write_bytes(content)
    return _sha256(content)


@pytest.fixture
def replay_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Harness:
    review = tmp_path / "typed-review"
    closure = tmp_path / "candidate-closure"
    workbook_directory = tmp_path / "workbooks"
    review.mkdir()
    closure.mkdir()
    workbook_directory.mkdir()

    names = ["EKE.xls", "GIL.xls", "RASH.xls"] + [
        f"SITE{index:03d}.xls" for index in range(76)
    ]
    names.sort()
    layout_zero = {"EKE.xls", "GIL.xls", *[f"SITE{i:03d}.xls" for i in range(39)]}
    three_sheet = set(names[:14])
    workbooks: list[rootsi_workbook_replay._Workbook] = []
    sheets: list[rootsi_workbook_replay._Sheet] = []
    cells: list[JsonObject] = []
    metadata: list[RootsiSiteMetadataClaim] = []

    for position, name in enumerate(names):
        member = f"rootsi/{name}"
        payload = f"retained workbook {name}\n".encode()
        path = workbook_directory / name
        path.write_bytes(payload)
        workbook_sha = _sha256(payload)
        sheet_count = 3 if name in three_sheet else 1
        workbook = rootsi_workbook_replay._Workbook(
            archive_member=member,
            path=path,
            sha256=workbook_sha,
            byte_count=len(payload),
            workbook_id=rootsi_workbook_replay._source_id(
                ARCHIVE_SHA256, member, workbook_sha
            ),
            excel_date_mode=0,
            sheet_count=sheet_count,
        )
        workbooks.append(workbook)

        if name == "RASH.xls":
            header_row, first_data, last_data, columns = 2, 4, 11, 54
        elif name == "EKE.xls":
            header_row, first_data, last_data, columns = 0, 1, 42, 2
        elif name in layout_zero:
            header_row, first_data, last_data, columns = 0, 1, 1, 2
        else:
            header_row, first_data, last_data, columns = 2, 4, 4, 2
        rows = last_data + 1
        active = rootsi_workbook_replay._Sheet(
            workbook_id=workbook.workbook_id,
            ordinal=0,
            name="LC_GILLT" if name == "GIL.xls" else "Sheet1",
            rows=rows,
            columns=columns,
            rectangle_positions=rows * columns,
            merged_ranges=(),
        )
        sheets.append(active)

        for row in range(rows):
            for column in range(columns):
                value: str | float
                if row == header_row:
                    if name == "GIL.xls" and column == 0:
                        cell_type, value = 0, ""
                    else:
                        cell_type, value = 1, f"field-{column}"
                elif first_data <= row <= last_data:
                    if name == "GIL.xls" and column == 0:
                        cell_type, value = 0, ""
                    elif name == "RASH.xls" and row == 11 and column == 53:
                        cell_type, value = 1, "  "
                    elif name == "GIL.xls" and column == 1:
                        cell_type, value = 2, 0.0
                    elif name == "SITE000.xls" and column == 0:
                        cell_type, value = 2, -2.0
                    else:
                        cell_type, value = 2, float(row + column + 1)
                elif header_row == 2 and row == 0 and column == 0:
                    cell_type, value = 2, 1.0
                else:
                    cell_type, value = 0, ""
                cells.append(
                    _cell(
                        workbook,
                        active,
                        row,
                        column,
                        cell_type=cell_type,
                        value=value,
                    )
                )
        for ordinal in range(1, sheet_count):
            sheets.append(
                rootsi_workbook_replay._Sheet(
                    workbook_id=workbook.workbook_id,
                    ordinal=ordinal,
                    name=f"Empty{ordinal}",
                    rows=0,
                    columns=0,
                    rectangle_positions=0,
                    merged_ranges=(),
                )
            )

        samples = 25 if name == "EKE.xls" else last_data - first_data + 1
        workbook_claim = "site000.xls" if name == "SITE000.xls" else name
        metadata.append(
            _claim(
                14 if name == "EKE.xls" else 100 + position,
                label=name.removesuffix(".xls"),
                workbook=workbook_claim,
                samples=samples,
            )
        )

    metadata.extend(
        (
            _claim(
                3,
                label="ABO",
                workbook=None,
                samples=None,
                site_name="Åbodasjön",
            ),
            _claim(
                46,
                label="LIND",
                workbook=None,
                samples=None,
                site_name="Lindhultsgöl",
            ),
        )
    )

    inventory_path = tmp_path / "capture-inventory.json"
    inventory_content = _canonical({"portable": "native inventory"})
    inventory_path.write_bytes(inventory_content)
    metadata_path = tmp_path / "metadata.xlsx"
    metadata_prefix = b"portable Rootsi metadata\n"
    metadata_path.write_bytes(metadata_prefix + b"\0" * (54_688 - len(metadata_prefix)))
    review_files = {
        "manifest.json": _canonical({"schema": "quarantined-rootsi-cell-review.v1"}),
        "workbooks.json": _canonical([]),
        "sheets.jsonl": b"{}\n",
        "cells.jsonl": b"".join(_canonical(cell) for cell in cells),
        "accounting.json": _canonical({"portable": True}),
        "capture-inventory.json": inventory_content,
    }
    for name, content in review_files.items():
        (review / name).write_bytes(content)
    closure_crosswalk = closure / "rootsi-crosswalk.csv"
    archive_members_by_casefold = {
        Path(workbook.archive_member).name.casefold(): workbook.archive_member
        for workbook in workbooks
    }
    with closure_crosswalk.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "rootsi_source_row",
                "rootsi_observation_workbook_claim",
                "typed_workbook_member",
                "publication_candidate_status",
            )
        )
        for claim in metadata:
            member = (
                archive_members_by_casefold.get(
                    claim.observation_workbook_claim.casefold(), ""
                )
                if claim.observation_workbook_claim is not None
                else ""
            )
            writer.writerow(
                (
                    claim.source_row_number,
                    claim.observation_workbook_claim or "",
                    member,
                    "unique_rootsi_metadata_candidate"
                    if member
                    else "no_rootsi_metadata_candidate",
                )
            )
    closure_files = {
        "manifest.json": _canonical(
            {"schema_version": "essd-rootsi-input-closure-manifest.v1"}
        ),
        "publication-candidates.jsonl": b"{}\n",
        "rootsi-crosswalk.csv": closure_crosswalk.read_bytes(),
        "requirement-status.csv": b"portable\n",
        "report.json": _canonical({"portable": True}),
    }
    for name, content in closure_files.items():
        (closure / name).write_bytes(content)

    review_hash = _sha256(review_files["manifest.json"])
    inventory_hash = _sha256(inventory_content)
    metadata_hash = _sha256(metadata_path.read_bytes())
    closure_hash = _sha256(closure_files["manifest.json"])
    roster = tuple(workbook.source_dict() for workbook in workbooks)
    source = RootsiWorkbookReplayInput(
        typed_cell_review_dir=review,
        expected_cell_review_manifest_sha256=review_hash,
        native_inventory_path=inventory_path,
        expected_native_inventory_sha256=inventory_hash,
        workbook_directory=workbook_directory,
        rootsi_metadata_path=metadata_path,
        expected_rootsi_metadata_sha256=metadata_hash,
        candidate_closure_dir=closure,
        expected_candidate_closure_manifest_sha256=closure_hash,
    )
    snapshots = tuple(
        sorted(
            (
                _snapshot("native_inventory", inventory_path),
                _snapshot("rootsi_metadata", metadata_path),
                *(
                    _snapshot(f"workbook:{workbook.archive_member}", workbook.path)
                    for workbook in workbooks
                ),
                *(
                    _snapshot(f"typed_cell_review:{name}", review / name)
                    for name in sorted(review_files)
                ),
                *(
                    _snapshot(f"candidate_closure:{name}", closure / name)
                    for name in sorted(closure_files)
                ),
            ),
            key=lambda item: item.label,
        )
    )
    inputs = rootsi_workbook_replay._Inputs(
        source=source,
        snapshots=snapshots,
        review_manifest={"schema": "quarantined-rootsi-cell-review.v1"},
        review_accounting={"portable": True},
        workbooks=tuple(workbooks),
        sheets=tuple(sheets),
        metadata=tuple(metadata),
        candidate_manifest={"schema_version": "essd-rootsi-input-closure-manifest.v1"},
        candidate_report={"portable": True},
    )
    review_identity = {
        snapshot.path.name: snapshot.as_dict()
        for snapshot in snapshots
        if snapshot.label.startswith("typed_cell_review:")
    }
    closure_identity = {
        snapshot.path.name: snapshot.as_dict()
        for snapshot in snapshots
        if snapshot.label.startswith("candidate_closure:")
    }
    metadata_by_workbook = {
        claim.observation_workbook_claim.casefold(): claim
        for claim in metadata
        if claim.observation_workbook_claim is not None
    }
    metadata_bindings = []
    for workbook in workbooks:
        basename = Path(workbook.archive_member).name
        claim = metadata_by_workbook[basename.casefold()]
        metadata_bindings.append(
            {
                "archive_member": workbook.archive_member,
                "workbook_sha256": workbook.sha256,
                "rootsi_source_row": claim.source_row_number,
                "rootsi_source_locator": (
                    f"{METADATA_MEMBER}!{claim.source_row_number}"
                ),
                "rootsi_site_name_raw": claim.site_name,
                "rootsi_sequence_label_raw": claim.site_label,
                "rootsi_observation_workbook_claim_raw": (
                    claim.observation_workbook_claim or ""
                ),
                "rootsi_sample_count_raw": dict(claim.source_values)["nr_samples"],
                "rootsi_sample_count_claim": claim.sample_count_claim,
            }
        )

    constants: dict[str, object] = {
        "TYPED_CELL_REVIEW_MANIFEST_SHA256": review_hash,
        "NATIVE_INVENTORY_SHA256": inventory_hash,
        "METADATA_SHA256": metadata_hash,
        "CANDIDATE_CLOSURE_MANIFEST_SHA256": closure_hash,
        "WORKBOOK_ROSTER_SHA256": _sha256(rootsi_workbook_replay._encode(list(roster))),
        "TYPED_CELL_REVIEW_FILES_SHA256": _sha256(
            rootsi_workbook_replay._encode(review_identity)
        ),
        "CANDIDATE_CLOSURE_FILES_SHA256": _sha256(
            rootsi_workbook_replay._encode(closure_identity)
        ),
        "METADATA_WORKBOOK_BINDINGS_SHA256": _sha256(
            rootsi_workbook_replay._encode(metadata_bindings)
        ),
        "SHEETS": 107,
        "RECTANGLE_POSITIONS": 1264,
        "HEADER_FIELDS": 210,
        "DATA_ROW_CANDIDATES": 127,
        "DATA_ROW_POSITIONS": 670,
        "DATA_ROW_NUMERIC_POSITIONS": 668,
        "DATA_ROW_EMPTY_POSITIONS": 1,
        "DATA_ROW_TEXT_POSITIONS": 1,
        "HEADER_TEXT_POSITIONS": 209,
        "HEADER_EMPTY_POSITIONS": 1,
        "HEADER_NONEMPTY_TEXT_POSITIONS": 209,
    }
    for name, constant_value in constants.items():
        monkeypatch.setattr(rootsi_workbook_replay, name, constant_value)
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_producer_identity",
        lambda: {
            "essd_reproduction/rootsi_workbook_replay.py": {
                "sha256": "e" * 64,
                "bytes": 1,
            }
        },
    )
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_load_inputs",
        lambda candidate: (
            inputs
            if candidate == source
            else rootsi_workbook_replay._refuse("unexpected_test_input", candidate)
        ),
    )
    return _Harness(source=source, inputs=inputs, roster=roster)


def test_portable_replay_is_exact_deterministic_and_refusal_bounded(
    tmp_path: Path, replay_harness: _Harness
) -> None:
    first = publish_rootsi_workbook_replay(
        source=replay_harness.source, destination=tmp_path / "bundle-a"
    )
    second = publish_rootsi_workbook_replay(
        source=replay_harness.source, destination=tmp_path / "bundle-b"
    )

    expected_files = {
        "manifest.json",
        "workbook-profiles.jsonl",
        "header-fields.jsonl",
        "data-row-candidates.jsonl",
        "sample-denominator-review.csv",
        "report.json",
    }
    assert _tree_files(first.directory) == expected_files
    assert first.manifest_sha256 == second.manifest_sha256
    assert {name: (first.directory / name).read_bytes() for name in expected_files} == {
        name: (second.directory / name).read_bytes() for name in expected_files
    }
    assert (
        first.workbook_profiles,
        first.header_fields,
        first.data_row_candidates,
        first.sample_denominator_records,
    ) == (79, 210, 127, 79)
    assert (
        read_rootsi_workbook_replay(
            first.directory, expected_manifest_sha256=first.manifest_sha256
        )
        == first
    )

    profiles = _objects(first.directory / "workbook-profiles.jsonl")
    rows = _objects(first.directory / "data-row-candidates.jsonl")
    report = _object(first.directory / "report.json")
    by_member = {cast(str, row["archive_member"]): row for row in profiles}
    assert sum(row["sheet_count"] == 1 for row in profiles) == 65
    assert sum(row["sheet_count"] == 3 for row in profiles) == 14
    assert sum(row["empty_auxiliary_sheets"] == 2 for row in profiles) == 14
    assert sum(row["header_row_index"] == 0 for row in profiles) == 41
    assert sum(row["header_row_index"] == 2 for row in profiles) == 38
    assert sum(row["data_row_first_index"] == 1 for row in profiles) == 41
    assert sum(row["data_row_first_index"] == 4 for row in profiles) == 38
    assert by_member["rootsi/GIL.xls"]["header_first_field_empty"] is True
    assert by_member["rootsi/GIL.xls"]["nonempty_sheet_name"] == "LC_GILLT"
    sample_rows = list(
        csv.DictReader((first.directory / "sample-denominator-review.csv").open())
    )
    site000 = next(
        row for row in sample_rows if row["archive_member"] == "rootsi/SITE000.xls"
    )
    assert site000["rootsi_observation_workbook_claim_raw"] == "site000.xls"
    assert by_member["rootsi/EKE.xls"]["data_row_candidates"] == 42
    for member, profile in by_member.items():
        indices = [
            cast(int, row["row_index"])
            for row in rows
            if row["archive_member"] == member
        ]
        assert indices == list(
            range(
                cast(int, profile["data_row_first_index"]),
                cast(int, profile["data_row_last_index"]) + 1,
            )
        )

    gil_row = next(row for row in rows if row["archive_member"] == "rootsi/GIL.xls")
    gil_cells = cast(list[JsonObject], gil_row["cells"])
    assert (gil_cells[0]["cell_type"], gil_cells[0]["decoded_value"]) == (0, "")

    decoded = [
        cell["decoded_value"]
        for row in rows
        for cell in cast(list[JsonObject], row["cells"])
    ]
    assert 0.0 in decoded
    assert -2.0 in decoded
    assert "  " in decoded
    numeric_edges = [
        cell
        for row in rows
        for cell in cast(list[JsonObject], row["cells"])
        if cell["decoded_value"] in {0.0, -2.0}
    ]
    assert {(cell["cell_type"], cell["binary64_hex"]) for cell in numeric_edges} == {
        (2, (0.0).hex()),
        (2, (-2.0).hex()),
    }
    denominators = report["observed_denominators"]
    assert denominators["data_row_candidate_positions"] == 670
    assert denominators["data_row_numeric_positions"] == 668
    assert denominators["data_row_empty_positions"] == 1
    assert denominators["data_row_text_positions"] == 1
    assert report["preserved_variants"]["sample_denominator_mismatch"] == {
        "archive_member": "rootsi/EKE.xls",
        "metadata_sample_count_raw": "25",
        "metadata_sample_count_claim": 25,
        "mechanical_data_row_candidates": 42,
        "status": "mismatch_preserved",
        "landclim_candidate_publication_rows": [981],
        "landclim_candidate_reported_sample_count": 42,
        "candidate_count_coincidence_resolves_revision_identity": False,
    }
    assert [
        row["rootsi_sequence_label_raw"]
        for row in report["preserved_variants"]["metadata_without_workbook_claim"]
    ] == ["ABO", "LIND"]
    claims = report["claims"]
    assert claims["zeros_interpreted"] is False
    assert claims["negatives_interpreted"] is False
    assert claims["scientifically_accepted"] is False
    assert claims["public_release_allowed"] is False


def test_real_header_type_partition_is_frozen() -> None:
    assert (
        rootsi_workbook_replay.HEADER_TEXT_POSITIONS,
        rootsi_workbook_replay.HEADER_EMPTY_POSITIONS,
        rootsi_workbook_replay.HEADER_NONEMPTY_TEXT_POSITIONS,
    ) == (7458, 1, 7434)


def test_replay_uses_complete_capture_scope(
    replay_harness: _Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}
    review_snapshots = tuple(
        snapshot
        for snapshot in replay_harness.inputs.snapshots
        if snapshot.label.startswith("typed_cell_review:")
    )
    closure_snapshots = tuple(
        snapshot
        for snapshot in replay_harness.inputs.snapshots
        if snapshot.label.startswith("candidate_closure:")
    )

    def replay(*args: object, **kwargs: object) -> None:
        observed["args"] = args
        observed["kwargs"] = kwargs

    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_native_inventory",
        lambda _: replay_harness.roster,
    )
    monkeypatch.setattr(rootsi_workbook_replay, "_replay_cell_review", replay)
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_review_manifest",
        lambda *_: (
            replay_harness.inputs.review_manifest,
            replay_harness.inputs.review_accounting,
            review_snapshots,
        ),
    )
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_candidate_closure",
        lambda *_: (
            replay_harness.inputs.candidate_manifest,
            replay_harness.inputs.candidate_report,
            closure_snapshots,
        ),
    )
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "_review_structure",
        lambda *_: (replay_harness.inputs.workbooks, replay_harness.inputs.sheets),
    )
    monkeypatch.setattr(
        rootsi_workbook_replay,
        "normalize_rootsi_site_metadata",
        lambda _: replay_harness.inputs.metadata,
    )

    loaded = _ACTUAL_LOAD_INPUTS(replay_harness.source)

    assert loaded.workbooks == replay_harness.inputs.workbooks
    assert cast(dict[str, object], observed["kwargs"])["scope"] == (
        "complete_retained_capture"
    )


def test_header_and_sheet_ambiguity_and_row_gaps_are_refused(
    replay_harness: _Harness,
) -> None:
    source_workbook = replay_harness.inputs.workbooks[0]
    workbook = replace(source_workbook, sheet_count=2)

    tied = rootsi_workbook_replay._Sheet(workbook.workbook_id, 0, "Sheet1", 2, 2, 4, ())
    tied_cells = iter(
        _cell(workbook, tied, row, column, cell_type=1, value=f"t{row}{column}")
        for row in range(2)
        for column in range(2)
    )
    with pytest.raises(RootsiWorkbookReplayError, match="ambiguous_header"):
        rootsi_workbook_replay._analyze_sheet(tied_cells, workbook, tied)

    analyses = []
    for ordinal in range(2):
        sheet = rootsi_workbook_replay._Sheet(
            workbook.workbook_id, ordinal, f"Sheet{ordinal + 1}", 2, 2, 4, ()
        )
        cells = iter(
            [
                _cell(workbook, sheet, 0, 0, cell_type=1, value="a"),
                _cell(workbook, sheet, 0, 1, cell_type=1, value="b"),
                _cell(workbook, sheet, 1, 0, cell_type=2, value=1.0),
                _cell(workbook, sheet, 1, 1, cell_type=2, value=2.0),
            ]
        )
        analyses.append(rootsi_workbook_replay._analyze_sheet(cells, workbook, sheet))
    with pytest.raises(RootsiWorkbookReplayError, match="nonempty_sheet_count"):
        rootsi_workbook_replay._profile(workbook, tuple(analyses))

    gap = rootsi_workbook_replay._Sheet(workbook.workbook_id, 0, "Sheet1", 4, 2, 8, ())
    gap_cells = []
    for row in range(4):
        for column in range(2):
            if row == 0:
                gap_cells.append(
                    _cell(workbook, gap, row, column, cell_type=1, value="header")
                )
            elif row == 2:
                gap_cells.append(
                    _cell(workbook, gap, row, column, cell_type=0, value="")
                )
            else:
                gap_cells.append(
                    _cell(workbook, gap, row, column, cell_type=2, value=1.0)
                )
    analysis = rootsi_workbook_replay._analyze_sheet(iter(gap_cells), workbook, gap)
    with pytest.raises(RootsiWorkbookReplayError, match="noncontiguous_data_rows"):
        rootsi_workbook_replay._profile(workbook, (analysis,))


@pytest.mark.parametrize("variant", ["missing", "extra", "symlink"])
def test_workbook_inventory_is_exact_and_regular(
    tmp_path: Path, replay_harness: _Harness, variant: str
) -> None:
    directory = tmp_path / f"workbooks-{variant}"
    shutil.copytree(replay_harness.source.workbook_directory, directory)
    victim = directory / "EKE.xls"
    if variant == "missing":
        victim.unlink()
    elif variant == "extra":
        (directory / "EXTRA.xls").write_bytes(b"extra")
    else:
        victim.unlink()
        victim.symlink_to(directory / "GIL.xls")

    with pytest.raises(
        RootsiWorkbookReplayError,
        match=(
            "workbook_directory_inventory"
            if variant != "symlink"
            else "unsafe_workbook_file"
        ),
    ):
        rootsi_workbook_replay._workbook_files(directory, replay_harness.roster)


@pytest.mark.parametrize(
    "content,reason",
    [
        (b'{"broken":\n', "invalid_json"),
        (b'{"same":1,"same":2}\n', "duplicate_json_key"),
        (b'{"value":NaN}\n', "nonfinite_json"),
    ],
)
def test_rehashed_malformed_json_is_refused(
    tmp_path: Path,
    replay_harness: _Harness,
    content: bytes,
    reason: str,
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source, destination=tmp_path / "malformed"
    )
    manifest_sha = _repin_peer(bundle.directory, "report.json", content)

    with pytest.raises(RootsiWorkbookReplayError, match=reason):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


def test_outer_hash_is_checked_before_peer_content(
    tmp_path: Path, replay_harness: _Harness
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source, destination=tmp_path / "wrong-hash"
    )
    (bundle.directory / "report.json").write_bytes(b"not json")

    with pytest.raises(RootsiWorkbookReplayError, match="manifest_digest_mismatch"):
        read_rootsi_workbook_replay(bundle.directory, expected_manifest_sha256="f" * 64)
    with pytest.raises(RootsiWorkbookReplayError, match="artifact_identity"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=bundle.manifest_sha256
        )
    wrong_source = replace(
        replay_harness.source, expected_native_inventory_sha256="f" * 64
    )
    with pytest.raises(RootsiWorkbookReplayError, match="ungoverned_parent"):
        rootsi_workbook_replay._validate_governed_pins(wrong_source)


@pytest.mark.parametrize("surface", ["manifest", "report"])
def test_claim_promotion_is_refused_after_coordinated_rehash(
    tmp_path: Path, replay_harness: _Harness, surface: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"promoted-{surface}",
    )
    if surface == "manifest":
        manifest = _object(bundle.directory / "manifest.json")
        cast(JsonObject, manifest["claims"])["public_release_allowed"] = True
        manifest_sha = _repin_manifest(bundle.directory, manifest)
    else:
        report = _object(bundle.directory / "report.json")
        cast(JsonObject, report["claims"])["zeros_interpreted"] = True
        manifest_sha = _repin_peer(bundle.directory, "report.json", _canonical(report))

    with pytest.raises(
        RootsiWorkbookReplayError,
        match="manifest_posture" if surface == "manifest" else "report_contract",
    ):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


@pytest.mark.parametrize("variant", ["duplicate", "omit", "reorder"])
def test_rehashed_data_cell_partition_tamper_is_refused(
    tmp_path: Path, replay_harness: _Harness, variant: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"data-cell-{variant}",
    )
    path = bundle.directory / "data-row-candidates.jsonl"
    rows = _objects(path)
    record = next(row for row in rows if row["archive_member"] == "rootsi/SITE000.xls")
    cells = cast(list[JsonObject], record["cells"])
    if variant == "duplicate":
        cells[1] = dict(cells[0])
    elif variant == "omit":
        cells.pop()
    else:
        cells.reverse()
    digest = hashlib.sha256()
    for cell in cells:
        digest.update(rootsi_workbook_replay._encode(cell))
    record["decoded_cells_sha256"] = digest.hexdigest()
    manifest_sha = _repin_peer(
        bundle.directory,
        path.name,
        b"".join(_canonical(row) for row in rows),
    )

    with pytest.raises(RootsiWorkbookReplayError, match="rootsi_workbook_replay_"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


@pytest.mark.parametrize("field", ["column_index", "cell_id", "workbook_id"])
def test_rehashed_header_binding_tamper_is_refused(
    tmp_path: Path, replay_harness: _Harness, field: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"header-{field}",
    )
    path = bundle.directory / "header-fields.jsonl"
    rows = _objects(path)
    record = rows[0]
    record[field] = 1 if field == "column_index" else "f" * 64
    manifest_sha = _repin_peer(
        bundle.directory,
        path.name,
        b"".join(_canonical(row) for row in rows),
    )

    with pytest.raises(RootsiWorkbookReplayError, match="rootsi_workbook_replay_"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


@pytest.mark.parametrize("variant", ["duplicate", "reorder"])
def test_rehashed_sample_roster_tamper_is_refused(
    tmp_path: Path, replay_harness: _Harness, variant: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"sample-{variant}",
    )
    path = bundle.directory / "sample-denominator-review.csv"
    lines = path.read_bytes().splitlines(keepends=True)
    if variant == "duplicate":
        lines[3] = lines[2]
    else:
        lines[2], lines[3] = lines[3], lines[2]
    manifest_sha = _repin_peer(bundle.directory, path.name, b"".join(lines))

    with pytest.raises(RootsiWorkbookReplayError, match="rootsi_workbook_replay_"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


@pytest.mark.parametrize(
    "surface",
    ["source_hashes", "mechanical_rules", "preserved_variants", "pair", "blockers"],
)
def test_rehashed_report_contract_tamper_is_refused(
    tmp_path: Path, replay_harness: _Harness, surface: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"report-{surface}",
    )
    report = _object(bundle.directory / "report.json")
    if surface == "source_hashes":
        cast(JsonObject, report["source_hashes"])["native_inventory_sha256"] = "f" * 64
    elif surface == "mechanical_rules":
        cast(JsonObject, report["mechanical_rules"])["header"] = "promoted"
    elif surface == "preserved_variants":
        variants = cast(JsonObject, report["preserved_variants"])
        cast(JsonObject, variants["blank_first_header_field"])["preserved"] = False
    elif surface == "pair":
        cast(JsonObject, report["candidate_pair"])["interpretation"] = "authenticated"
    else:
        report["blocking_dependencies"] = []
    manifest_sha = _repin_peer(bundle.directory, "report.json", _canonical(report))

    with pytest.raises(RootsiWorkbookReplayError, match="rootsi_workbook_replay_"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


@pytest.mark.parametrize("parent", ["typed_cell_review", "candidate_closure"])
def test_rehashed_embedded_parent_file_map_tamper_is_refused(
    tmp_path: Path, replay_harness: _Harness, parent: str
) -> None:
    bundle = publish_rootsi_workbook_replay(
        source=replay_harness.source,
        destination=tmp_path / f"parent-map-{parent}",
    )
    manifest = _object(bundle.directory / "manifest.json")
    sources = cast(JsonObject, manifest["sources"])
    parent_record = cast(JsonObject, sources[parent])
    files = cast(JsonObject, parent_record["files"])
    first = cast(JsonObject, files[sorted(files)[0]])
    first["bytes"] = cast(int, first["bytes"]) + 1
    parent_record["files_sha256"] = _sha256(rootsi_workbook_replay._encode(files))
    manifest_sha = _repin_manifest(bundle.directory, manifest)

    with pytest.raises(RootsiWorkbookReplayError, match="source_manifest"):
        read_rootsi_workbook_replay(
            bundle.directory, expected_manifest_sha256=manifest_sha
        )


def test_source_mutation_prevents_publication(
    tmp_path: Path,
    replay_harness: _Harness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = rootsi_workbook_replay._write_stage

    def mutate_after_stage(
        inputs: rootsi_workbook_replay._Inputs,
        stage: Path,
        producer: JsonObject,
    ) -> str:
        manifest_sha = original(inputs, stage, producer)
        replay_harness.source.native_inventory_path.write_bytes(b"changed")
        return manifest_sha

    monkeypatch.setattr(rootsi_workbook_replay, "_write_stage", mutate_after_stage)
    destination = tmp_path / "source-mutated"
    with pytest.raises(RootsiWorkbookReplayError, match="input_changed"):
        publish_rootsi_workbook_replay(
            source=replay_harness.source, destination=destination
        )
    assert not destination.exists()


def test_preexisting_and_racing_targets_are_never_replaced(
    tmp_path: Path,
    replay_harness: _Harness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "sentinel"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(RootsiWorkbookReplayError, match="destination_exists"):
        publish_rootsi_workbook_replay(
            source=replay_harness.source, destination=existing
        )
    assert sentinel.read_text(encoding="utf-8") == "preserve"

    original = rootsi_workbook_replay._publish_new_output_tree
    racing = tmp_path / "racing"

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "sentinel").write_text("race winner", encoding="utf-8")
        original(
            final_output_root=final_output_root,
            staging_output_root=staging_output_root,
        )

    monkeypatch.setattr(rootsi_workbook_replay, "_publish_new_output_tree", race)
    with pytest.raises(RootsiWorkbookReplayError, match="publish_failed"):
        publish_rootsi_workbook_replay(source=replay_harness.source, destination=racing)
    assert (racing / "sentinel").read_text(encoding="utf-8") == "race winner"
    assert list(tmp_path.glob(".racing.pending-*"))


@pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_ROOTSI_WORKBOOK_REPLAY_REAL") != "1",
    reason="real retained Rootsi replay is explicitly opt-in",
)
def test_real_retained_workbook_replay_is_opt_in(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[4]
    review = repository / (
        "artifacts/v2/sources/rootsi-cell-preparation/actual-002/all-79"
    )
    closure = repository / (
        "artifacts/v3/landclim/rootsi-input-closure-841cf13b/"
        "real-generation003/candidate-a"
    )
    source = RootsiWorkbookReplayInput(
        typed_cell_review_dir=review,
        expected_cell_review_manifest_sha256=(
            rootsi_workbook_replay.TYPED_CELL_REVIEW_MANIFEST_SHA256
        ),
        native_inventory_path=review / "capture-inventory.json",
        expected_native_inventory_sha256=rootsi_workbook_replay.NATIVE_INVENTORY_SHA256,
        workbook_directory=repository
        / (
            "artifacts/v2/sources/remaining-frontier/rootsi-lineage/"
            "workbooks-001/private-workbooks"
        ),
        rootsi_metadata_path=repository
        / (
            "artifacts/v2/sources/remaining-frontier/rootsi-lineage/"
            "intake-001/metadata.xlsx"
        ),
        expected_rootsi_metadata_sha256=METADATA_SHA256,
        candidate_closure_dir=closure,
        expected_candidate_closure_manifest_sha256=(
            rootsi_workbook_replay.CANDIDATE_CLOSURE_MANIFEST_SHA256
        ),
    )

    bundle = publish_rootsi_workbook_replay(
        source=source, destination=tmp_path / "real-rootsi-workbook-replay"
    )

    assert bundle.workbook_profiles == 79
    assert bundle.header_fields == 7459
    assert bundle.data_row_candidates == 5170
