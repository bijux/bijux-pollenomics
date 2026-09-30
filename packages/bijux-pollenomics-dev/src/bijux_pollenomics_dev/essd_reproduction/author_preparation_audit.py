"""Recount the 17 author raw and prepared pollen examples from private sources."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

INDEPENDENT_COUNTS = Path(
    "docs/report/source-relations/landclim/author-preparation-audit/independent-counts.json"
)
INDEPENDENT_SOURCE_SHA256 = (
    "4046de43b9674d67ea57537d3556d62359e941def478af60314c48bc08e3e049"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.reader(stream))


def _integer(value: Decimal) -> int:
    if value != int(value):
        raise ValueError("Nonintegral pollen count")
    return int(value)


def _raw_total(path: Path) -> tuple[int, int]:
    rows = _rows(path)
    included = [
        index
        for index, name in enumerate(rows[0])
        if name.strip().lower() not in {"depth", "sum", "age.cal.bp"}
    ]
    total = Decimal(0)
    nonblank = 0
    for row in rows[1:]:
        if any(cell.strip() for cell in row):
            nonblank += 1
        for index in included:
            value = row[index].strip()
            if value and value.upper() != "NA":
                total += Decimal(value)
    return _integer(total), nonblank


def _prepared_total(path: Path) -> int:
    rows = _rows(path)
    if (
        len(rows) != 34
        or any(len(row) != 26 for row in rows)
        or [row[0] for row in rows[:3]] != ["TW", "radius", "model"]
    ):
        raise ValueError("Author prepared shape changed")
    return _integer(
        sum(
            (Decimal(cell) for row in rows[3:] for cell in row[1:] if cell),
            Decimal(0),
        )
    )


def _site_categories(
    author: Path, site: str
) -> tuple[dict[str, int], list[dict[str, str | int]]]:
    """Follow the author's first exact lookup match and right-trimmed R headers."""
    with (author / "LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv").open(
        newline="", encoding="latin-1"
    ) as stream:
        lookup = list(csv.DictReader(stream))
    first_match: dict[str, str] = {}
    for row in lookup:
        first_match.setdefault(row["oldvar"], row["RPP.LANDCLIMII"])
    ppe = {row[0] for row in _rows(author / "run.all.taxa.100219.csv")}
    bins = [Decimal(row[0]) for row in _rows(author / "bins.csv")]
    raw = _rows(author / "input" / f"{site}.csv")
    header = raw[0]
    age_index = next(
        index for index, name in enumerate(header) if name.lower() == "age.cal.bp"
    )
    counts = dict.fromkeys(
        (
            "raw",
            "retained",
            "excluded_zz",
            "excluded_not_ppe",
            "unmapped",
            "outside_window",
        ),
        Decimal(0),
    )
    unmapped_by_column: dict[int, Decimal] = {}
    for record in raw[1:]:
        if not any(cell.strip() for cell in record):
            continue
        if len(record) != len(header) or not record[age_index].strip():
            raise ValueError(f"Incomplete author raw record: {site}")
        window = bisect_right(bins, Decimal(record[age_index])) - 1
        for index, native in enumerate(header):
            if index == age_index or native.strip().lower() in {"depth", "sum"}:
                continue
            if not record[index].strip() or record[index].strip().upper() == "NA":
                continue
            amount = Decimal(record[index])
            counts["raw"] += amount
            target = first_match.get(native.rstrip())
            if not 0 <= window < 25:
                counts["outside_window"] += amount
            elif target == "zz.do not use":
                counts["excluded_zz"] += amount
            elif target is None:
                counts["unmapped"] += amount
                unmapped_by_column[index] = (
                    unmapped_by_column.get(index, Decimal(0)) + amount
                )
            elif target not in ppe:
                counts["excluded_not_ppe"] += amount
            else:
                counts["retained"] += amount
    unmapped: list[dict[str, str | int]] = [
        {
            "source_column_index_zero_based": index,
            "native_header": header[index],
            "count": _integer(value),
        }
        for index, value in sorted(unmapped_by_column.items())
        if value
    ]
    categories = {key: _integer(value) for key, value in counts.items()}
    if sum(int(row["count"]) for row in unmapped) != categories["unmapped"]:
        raise ValueError(f"Unmapped source count closure changed: {site}")
    return categories, unmapped


def build(repository: Path, author_source_root: Path, output: Path) -> dict[str, Any]:
    """Recount source rows against the independent 17-site count reference."""
    repository = repository.resolve()
    author_source_root = author_source_root.resolve()
    independent = json.loads((repository / INDEPENDENT_COUNTS).read_text())
    if (
        independent["schema_version"] != "landclim-author-example-independent-counts.v1"
        or independent["source_report_sha256"] != INDEPENDENT_SOURCE_SHA256
        or independent["checked_sites"] != 17
        or independent["full_partition_sites"] != 17
        or len(independent["sites"]) != 17
    ):
        raise ValueError("Independent author count reference changed")

    manifest = json.loads((author_source_root / "snapshot-manifest.json").read_text())
    if manifest["file_count"] != 193:
        raise ValueError("Author source snapshot file set changed")
    author = author_source_root / "author"

    def source_path(relative: str) -> Path:
        path = author_source_root / relative
        if _sha(path) != manifest["files"][relative]:
            raise ValueError(f"Author source changed: {relative}")
        return path

    metadata_path = source_path("author/site.metadata.csv")
    with metadata_path.open(newline="", encoding="utf-8-sig") as stream:
        metadata = list(csv.DictReader(stream))
    names = [row["filename"] for row in metadata]
    if len(names) != len(set(names)) or len(names) != 17:
        raise ValueError("Author site cohort changed")
    for name in (
        "LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv",
        "run.all.taxa.100219.csv",
        "bins.csv",
    ):
        source_path(f"author/{name}")
    independent_by_site = {row["site"]: row for row in independent["sites"]}
    if set(independent_by_site) != set(names):
        raise ValueError("Independent count site set changed")

    sites = []
    category_totals: dict[str, int] = {}
    for row in metadata:
        name = row["filename"]
        raw_path = source_path(f"author/input/{name}.csv")
        prepared_path = source_path(f"author/run.REVEALS.files/LRAready_{name}.csv")
        raw, nonblank = _raw_total(raw_path)
        prepared = _prepared_total(prepared_path)
        categories, unmapped_labels = _site_categories(author, name)
        independent_site = independent_by_site[name]
        if (
            Decimal(independent_site["raw_total"]) != raw
            or Decimal(independent_site["prepared_total"]) != prepared
            or Decimal(independent_site["audited_excluded_total"]) != raw - prepared
            or independent_site["prepared_sha256"] != _sha(prepared_path)
            or independent_site["grid"] != row["LCGRID_ID"]
            or independent_site["raw_nonblank_rows"] != nonblank
            or categories["raw"] != raw
            or categories["retained"] != prepared
            or sum(
                value
                for key, value in categories.items()
                if key not in {"raw", "retained"}
            )
            != raw - prepared
        ):
            raise ValueError(f"Independent author counts disagree with source: {name}")
        for key, value in categories.items():
            category_totals[key] = category_totals.get(key, 0) + value
        sites.append(
            {
                "site": name,
                "grid": row["LCGRID_ID"],
                "raw_count": raw,
                "prepared_count": prepared,
                "raw_minus_prepared": raw - prepared,
                "raw_nonblank_rows": nonblank,
                "source_raw_sha256": _sha(raw_path),
                "source_prepared_sha256": _sha(prepared_path),
                "source_categories": categories,
                "unmapped_source_labels": unmapped_labels,
                "independent_partition_status": independent_site["partition_status"],
            }
        )
    whh05 = next(site["source_categories"] for site in sites if site["site"] == "WHH05")
    if {key: str(value) for key, value in whh05.items()} != independent[
        "whh05_categories"
    ]:
        raise ValueError("WHH05 source count partition changed")
    if whh05["raw"] != 2482 or whh05["retained"] != 2448:
        raise ValueError("WHH05 source count denominator changed")
    totals = {
        "sites": len(sites),
        "grid_512_sites": sum(row["grid"] == "512" for row in sites),
        "grid_562_sites": sum(row["grid"] == "562" for row in sites),
        "raw_count": sum(row["raw_count"] for row in sites),
        "prepared_count": sum(row["prepared_count"] for row in sites),
        "raw_minus_prepared": sum(row["raw_minus_prepared"] for row in sites),
    }
    if (
        (totals["grid_512_sites"], totals["grid_562_sites"]) != (9, 8)
        or totals["raw_count"] != 501713
        or totals["prepared_count"] != 299660
        or totals["raw_minus_prepared"] != 202053
        or Decimal(independent["raw_total"]) != totals["raw_count"]
        or Decimal(independent["prepared_total"]) != totals["prepared_count"]
        or Decimal(independent["audited_excluded_total_17_sites"])
        != totals["raw_minus_prepared"]
        or category_totals["raw"] != totals["raw_count"]
        or category_totals["retained"] != totals["prepared_count"]
    ):
        raise ValueError("Author source count mass changed")
    report = {
        "schema_version": "landclim-author-preparation-audit.v3",
        "scope": "17 authenticated author examples, not 1128 historical study inputs",
        "totals": totals,
        "sites": sites,
        "category_totals": category_totals,
        "whh05_source_categories": whh05,
        "independent_count_correspondence": (
            "Fresh source replay classifies all 17 site count partitions by exact "
            "author lookup, PPE membership and time-window support; the "
            "independent count reference agrees on raw/prepared totals"
        ),
        "input_sha256": {
            "author_snapshot_manifest": _sha(
                author_source_root / "snapshot-manifest.json"
            ),
            "independent_counts": _sha(repository / INDEPENDENT_COUNTS),
        },
    }
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    return report


def main() -> None:
    """Run the CLI to recount the 17 author raw and prepared pollen examples from private sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.repository, args.author_source_root, args.output)


if __name__ == "__main__":
    main()
