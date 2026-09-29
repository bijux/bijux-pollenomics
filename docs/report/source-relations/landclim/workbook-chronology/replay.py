"""Audit source-native age columns in four retained Rootsi workbooks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import xlrd


REPOSITORY = Path(__file__).resolve().parents[5]
LEDGER = REPOSITORY / "docs/report/source-relations/rootsi-landclim-overlap/overlap.csv"
SEQUENCES = ("FLINK", "HOLK", "RANV", "STAV")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(source_root: Path) -> dict[str, object]:
    """Bind each finding to the exact private workbook named by the overlap ledger."""
    with LEDGER.open(newline="") as stream:
        candidates = {
            row["publication_sequence"]: row for row in csv.DictReader(stream)
        }
    findings: list[dict[str, object]] = []
    for sequence in SEQUENCES:
        candidate = candidates[sequence]
        member = candidate["typed_workbook_member"]
        path = source_root / member
        if _sha256(path) != candidate["typed_workbook_sha256"]:
            raise ValueError(f"Workbook custody changed: {sequence}")
        sheet = xlrd.open_workbook(str(path)).sheet_by_index(0)
        header_row = 2 if sequence == "STAV" else 0
        data_start = 4 if sequence == "STAV" else 1
        header = [
            str(sheet.cell_value(header_row, column)).strip() for column in range(2)
        ]
        expected = "Sample age (cal AD/BC)" if sequence in {"FLINK", "HOLK"} else None
        if header[0] != "Sample" or (expected and header[1] != expected):
            raise ValueError(f"Workbook header changed: {sequence}")
        if not expected and header[1] == "Sample age (cal AD/BC)":
            raise ValueError(f"Unexpected age column: {sequence}")
        samples = int(candidate["site_samples"])
        if sequence == "STAV" and any(sheet.row_values(3)):
            raise ValueError("STAV separator row changed")
        if sheet.nrows - data_start != samples:
            raise ValueError(f"Workbook sample denominator changed: {sequence}")
        ages: list[tuple[int, float]] = []
        if expected:
            for row_index in range(data_start, sheet.nrows):
                cell = sheet.cell(row_index, 1)
                if cell.ctype != xlrd.XL_CELL_NUMBER:
                    raise ValueError(
                        f"Non-numeric source age: {sequence}:{row_index + 1}"
                    )
                ages.append((row_index + 1, float(cell.value)))
        reversals = [
            {
                "preceding_sheet_row": previous[0],
                "preceding_age": previous[1],
                "following_sheet_row": current[0],
                "following_age": current[1],
            }
            for previous, current in zip(ages, ages[1:], strict=False)
            if current[1] > previous[1]
        ]
        duplicates = len(ages) - len({age for _, age in ages})
        findings.append(
            {
                "sequence": sequence,
                "workbook_member": member,
                "workbook_sha256": candidate["typed_workbook_sha256"],
                "sheet": sheet.name,
                "sample_rows": samples,
                "second_column_header": header[1],
                "source_age_basis": expected,
                "numeric_source_ages": len(ages),
                "source_age_min": min((age for _, age in ages), default=None),
                "source_age_max": max((age for _, age in ages), default=None),
                "strict_age_reversals_in_sheet_order": reversals if expected else None,
                "exact_duplicate_source_ages": duplicates if expected else None,
                "dated_event_admitted": False,
            }
        )
    return {
        "schema_version": "rootsi-workbook-chronology-audit.v1",
        "overlap_ledger_sha256": _sha256(LEDGER),
        "sequence_count": len(findings),
        "source_age_column_sequences": ["FLINK", "HOLK"],
        "no_source_age_column_sequences": ["RANV", "STAV"],
        "findings": findings,
        "interpretation": "Source-native age cells are point labels, not verified age-model intervals. Reversals are preserved; no AD/BC-to-BP conversion, correction, interpolation, uncertainty, event date, or historical-input identity is inferred.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
