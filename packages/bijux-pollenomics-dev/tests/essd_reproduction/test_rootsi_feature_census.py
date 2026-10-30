"""Source-value partitions without count, chronology or publication admission."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics.collection.sources.rootsi import authority
from bijux_pollenomics.collection.sources.rootsi.cells import decoding, inputs, models
from bijux_pollenomics_dev.essd_reproduction import rootsi_feature_census as census


@dataclass
class Cell:
    ctype: int
    value: object
    xf_index: int | None = 0


class Sheet:
    def __init__(self, rows: list[list[Cell]], name: str = "source") -> None:
        self.rows = rows
        self.name = name
        self.nrows = len(rows)
        self.ncols = len(rows[0])
        self.merged_cells: list[tuple[int, int, int, int]] = []

    def cell(self, rowx: int, colx: int) -> Cell:
        return self.rows[rowx][colx]


class Book:
    datemode = 0

    def __init__(self, sheets: list[Sheet]) -> None:
        self._sheets = sheets
        self.released = False

    def sheets(self) -> list[decoding.Sheet]:
        return list(self._sheets)

    def release_resources(self) -> None:
        self.released = True


def number(value: float) -> Cell:
    return Cell(2, value)


def book(features: list[list[Cell]]) -> Book:
    header = [Cell(1, value) for value in ["Sample", "Sample age", "A", "B"]]
    rows = [
        header,
        *[
            [number(float(i)), number(float(i * 10)), *row]
            for i, row in enumerate(features, start=1)
        ],
    ]
    return Book([Sheet(rows)])


def test_exclusive_partitions_and_overlapping_flags_preserve_typed_missingness() -> (
    None
):
    source = book(
        [
            [number(2), number(3)],
            [number(0), number(0)],
            [number(0.5), number(1)],
            [number(-1.5), number(2)],
            *[
                [cell, number(0)]
                for cell in [
                    Cell(0, ""),
                    Cell(1, "0"),
                    Cell(6, ""),
                    Cell(2, None),
                    Cell(3, 1.0),
                    Cell(4, 0),
                    Cell(5, 1),
                    Cell(9, "unknown"),
                    Cell(2, float("nan")),
                ]
            ],
        ]
    )
    result = census.summarize(source)
    assert result["row_partition"] == {
        "complete_finite_nonnegative_positive": 2,
        "complete_allzero": 1,
        "numeric_with_negative": 1,
        "incomplete_or_unsupported": 9,
    }
    assert sum(result["row_partition"].values()) == 13
    assert result["anomaly_row_numbers"]["noninteger"] == [4, 5]
    assert result["anomaly_row_numbers"]["negative"] == [5]
    assert result["anomaly_row_numbers"]["null"] == [9]
    assert result["orthogonal_flag_counts"]["missing"] == 3
    assert result["orthogonal_flag_counts"]["nonfinite"] == 1
    assert result["allzero_feature_rows_age_states"] == {"finite_nonzero": [3]}


def test_features_are_selected_by_explicit_header_roles_not_first_two_columns() -> None:
    header = [Cell(1, value) for value in ["Sample", "A", "Sample age (cal AD/BC)"]]
    source = Book([Sheet([header, [number(1), number(0), number(-500)]])])
    result = census.summarize(source)
    assert result["candidate_feature_columns"] == 1
    assert result["row_partition"]["complete_allzero"] == 1
    assert result["allzero_feature_rows_age_states"] == {"finite_nonzero": [2]}


@pytest.mark.parametrize("defect", ["tie", "two_sheets", "gap"])
def test_existing_header_and_row_ambiguities_are_refusals(defect: str) -> None:
    source = book([[number(1), number(2)]])
    if defect == "tie":
        source._sheets[0].rows.append([Cell(1, str(i)) for i in range(4)])
        source._sheets[0].nrows += 1
    elif defect == "two_sheets":
        source._sheets.append(Sheet([[number(1)]], "other"))
    else:
        source._sheets[0].rows.extend([[Cell(0, "")] * 4, [number(3)] * 4])
        source._sheets[0].nrows += 2
    with pytest.raises(census.CensusRefusal):
        census.summarize(source)


def test_missing_header_role_keeps_mechanical_rows_without_inventing_features() -> None:
    source = book([[number(0), number(0)]])
    source._sheets[0].rows[0][0] = Cell(0, "")
    result = census.summarize(source)
    assert result["status"] == "refused"
    assert result["mechanical_row_count"] == 1
    assert result["row_partition"] is None
    assert result["unresolved_header_columns"] == [1]


def test_empty_auxiliary_sheets_do_not_create_new_data_rows() -> None:
    source = book([[number(1), number(2)]])
    source._sheets.append(Sheet([[Cell(0, "")]], "empty"))
    assert census.summarize(source)["mechanical_row_count"] == 1


def fixture_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    repository, source = tmp_path / "repository", tmp_path / "source"
    path = repository / census.CROSSWALK
    path.parent.mkdir(parents=True)
    raw = b"typed_workbook_member,typed_workbook_sha256,typed_workbook_bytes,rootsi_source_locator,rootsi_sample_count_raw,rootsi_sample_count_claim,publication_candidate_status\n"
    digest = hashlib.sha256(b"xls").hexdigest()
    raw += f"rootsi/ONE.xls,{digest},3,metadata!2,1,1,unique_rootsi_metadata_candidate\n".encode()
    path.write_bytes(raw)
    source.mkdir()
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "archive_sha256": authority.ARCHIVE_SHA256,
                "workbook_count": 1,
                "total_workbook_bytes": 3,
                "members": [
                    {"archive_member": "rootsi/ONE.xls", "sha256": digest, "bytes": 3}
                ],
            }
        )
    )
    (source / "rootsi").mkdir()
    (source / "rootsi/ONE.xls").write_bytes(b"xls")
    for key, value in {
        "CROSSWALK_SHA256": hashlib.sha256(raw).hexdigest(),
        "CROSSWALK_BYTES": len(raw),
        "WORKBOOK_COUNT": 1,
        "WORKBOOK_BYTES": 3,
    }.items():
        monkeypatch.setattr(census, key, value)
    return repository, source


@pytest.mark.parametrize("defect", ["crosswalk", "member", "duplicate", "bytes"])
def test_canonical_candidate_identity_binds_the_external_workbook_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, source = fixture_roster(tmp_path, monkeypatch)
    assert len(census.roster(repository, source)) == 1
    path = source / "manifest.json"
    value = json.loads(path.read_text())
    if defect == "crosswalk":
        (repository / census.CROSSWALK).write_bytes(b"Changed canonical identity")
    elif defect == "member":
        value["members"][0]["archive_member"] = "rootsi/OTHER.xls"
    elif defect == "duplicate":
        value["members"].append(value["members"][0].copy())
    else:
        value["members"][0]["bytes"] = 4
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        census.roster(repository, source)


def test_source_workbooks_are_released_and_failures_preserve_remaining_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source = fixture_roster(tmp_path, monkeypatch)
    records = census.roster(repository, source)
    source_book = book([[number(1), number(2)]])

    class Parser:
        def open_workbook(self, *, file_contents: bytes, formatting_info: bool) -> Book:
            assert file_contents == b"xls" and formatting_info
            return source_book

    rows = census.census(source, records, Parser())
    assert rows[0]["status"] == "computed"
    assert source_book.released
    (source / "rootsi/ONE.xls").write_bytes(b"bad")
    rows = census.census(source, [*records, *records], Parser())
    assert [row["status"] for row in rows] == ["fatal", "not_run"]


def test_expected_header_refusal_does_not_stop_other_workbooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source = fixture_roster(tmp_path, monkeypatch)
    records = census.roster(repository, source)

    class Parser:
        def open_workbook(self, *, file_contents: bytes, formatting_info: bool) -> Book:
            source_book = book([[number(1), number(2)]])
            source_book._sheets[0].rows.append([Cell(1, str(i)) for i in range(4)])
            source_book._sheets[0].nrows += 1
            return source_book

    assert [
        row["status"] for row in census.census(source, [*records, *records], Parser())
    ] == ["refused", "refused"]


@pytest.mark.parametrize("defect", ["dirty", "untracked", "origin"])
def test_census_commit_requires_canonical_clean_tracked_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    prefix = (
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi"
    )
    modules = [
        (authority, f"{prefix}/authority.py"),
        (decoding, f"{prefix}/cells/decoding.py"),
        (inputs, f"{prefix}/cells/inputs.py"),
        (models, f"{prefix}/cells/models.py"),
        (
            census,
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/rootsi_feature_census.py",
        ),
    ]
    for module, relative in modules:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Synthetic revision fixture; no copied source\n")
        monkeypatch.setattr(module, "__file__", str(path))
    for arguments in (
        ["init", "--quiet"],
        ["add", "--", "packages"],
        [
            "-c",
            "user.name=Bijux",
            "-c",
            "user.email=checks@bijux.io",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "test(curation): bind synthetic source revision",
        ],
    ):
        subprocess.run(
            ["git", "-C", str(tmp_path), *arguments], check=True, capture_output=True
        )
    assert len(census.revision(tmp_path)) == 40
    path = tmp_path / modules[0][1]
    if defect == "dirty":
        path.write_text("# Changed source fixture\n")
    elif defect == "untracked":
        subprocess.run(
            ["git", "-C", str(tmp_path), "rm", "--cached", "--", modules[0][1]],
            check=True,
            capture_output=True,
        )
    else:
        foreign = tmp_path / "foreign.py"
        foreign.write_text("# Noncanonical origin\n")
        monkeypatch.setattr(authority, "__file__", str(foreign))
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        census.revision(tmp_path)
