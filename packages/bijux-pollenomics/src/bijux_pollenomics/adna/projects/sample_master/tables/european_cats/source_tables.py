"""Archive and workbook-table parsing for the European cat panel."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from io import StringIO
from pathlib import Path


@dataclass(frozen=True)
class TableRow:
    """One normalized supplementary-workbook row."""

    row_number: int
    values: dict[str, str]


@dataclass(frozen=True)
class ArchiveRow:
    """One ENA archive sample and its submitted basenames."""

    sample_accession: str
    experiment_accession: str
    tax_id: str
    scientific_name: str
    submitted_basenames: tuple[str, ...]


def read_archive_rows(archive_text: str) -> tuple[ArchiveRow, ...]:
    """Parse archive rows while enforcing unique sample accessions."""
    reader = csv.DictReader(StringIO(archive_text), delimiter="\t")
    required = {
        "sample_accession",
        "experiment_accession",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
    }
    _require(
        reader.fieldnames is not None and required <= set(reader.fieldnames),
        "ENA archive columns required by the cat reconciliation are missing",
    )
    rows: list[ArchiveRow] = []
    for source in reader:
        accession = source["sample_accession"].strip()
        if not accession:
            continue
        basenames = tuple(
            Path(item.strip()).name
            for item in source["submitted_ftp"].split(";")
            if item.strip()
        )
        rows.append(
            ArchiveRow(
                sample_accession=accession,
                experiment_accession=source["experiment_accession"].strip(),
                tax_id=source["tax_id"].strip(),
                scientific_name=source["scientific_name"].strip(),
                submitted_basenames=basenames,
            )
        )
    _require(
        len({row.sample_accession for row in rows}) == len(rows),
        "duplicate ENA sample accession",
    )
    return tuple(rows)


def table_rows(
    rows: tuple[tuple[str, ...], ...],
    *,
    required_headers: tuple[str, ...],
    primary_key: str,
) -> tuple[TableRow, ...]:
    """Normalize a workbook table against required headers and its primary key."""
    _require(len(rows) >= 2, "supplementary table has no header row")
    header = {
        value.strip(): index for index, value in enumerate(rows[1]) if value.strip()
    }
    _require(
        set(required_headers) <= set(header),
        f"supplementary table headers missing for {primary_key}",
    )
    built: list[TableRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        values = {key: cell_value(row, header[key]) for key in required_headers}
        if not values[primary_key]:
            continue
        built.append(TableRow(row_number=row_number, values=values))
    return tuple(built)


def collapse_deep_sequence_rows(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, TableRow]:
    """Collapse identical repeated sequencing rows to one ancient individual."""
    required = ("Sample ID", "Cat ID", "Individual", "Country", "Site", "element")
    parsed = table_rows(rows, required_headers=required, primary_key="Sample ID")
    grouped: dict[str, list[TableRow]] = {}
    for row in parsed:
        sample_id = row.values["Sample ID"].removesuffix("*")
        grouped.setdefault(sample_id, []).append(row)
    collapsed: dict[str, TableRow] = {}
    for sample_id, group in grouped.items():
        signatures = {
            tuple(row.values[field] for field in required[1:]) for row in group
        }
        _require(
            len(signatures) == 1,
            f"repeated Table S3 rows disagree for {sample_id}",
        )
        first = group[0]
        collapsed[sample_id] = TableRow(
            row_number=first.row_number,
            values={**first.values, "Sample ID": sample_id},
        )
    return collapsed


def unique_index(
    rows: tuple[TableRow, ...], key: str, label: str
) -> dict[str, TableRow]:
    """Index workbook rows and reject duplicate identities."""
    index: dict[str, TableRow] = {}
    for row in rows:
        value = row.values[key]
        _require(value not in index, f"duplicate {label}: {value}")
        index[value] = row
    return index


def display_coordinate(value: str) -> str:
    """Render a source coordinate at its governed two-decimal precision."""
    number = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{number:.2f}"


def cell_value(row: tuple[str, ...], index: int) -> str:
    """Read one optional workbook cell as trimmed text."""
    return "" if index >= len(row) else str(row[index]).strip()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
