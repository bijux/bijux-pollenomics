"""Compare the author example's BP bins with the published archive's TW labels."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from bijux_pollenomics.collection.sources.landclim.catalog import (
    time_window_from_tw_filename,
)

from .published_window_correspondence import (
    ARCHIVE_SHA256,
    SOURCE_REVISION,
)


_WINDOW = re.compile(r"(?P<start>-?\d+)-(?P<end>-?\d+) BP")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _archive_bounds(index: int) -> tuple[int, int, str]:
    mean = time_window_from_tw_filename(f"TW{index}.RV.estimates.jun21.csv")
    error = time_window_from_tw_filename(f"TW{index}.RV.standarderrors.jun21.csv")
    match = _WINDOW.fullmatch(mean)
    if mean != error or match is None:
        raise ValueError("Published mean and SE window labels differ")
    start, end = int(match["start"]), int(match["end"])
    if end <= start:
        raise ValueError("Published window bounds are not increasing")
    return start, end, mean


def window_rows(
    edges: list[Decimal], lookup: list[tuple[str, str]]
) -> list[dict[str, str]]:
    """Join window indices only; label an estimate comparison exact by both bounds."""
    if (
        len(edges) != 26
        or len(lookup) != 25
        or [index for index, _ in lookup] != [str(i) for i in range(1, 26)]
        or len({label for _, label in lookup}) != 25
        or any(not value.is_finite() for value in edges)
        or any(right <= left for left, right in zip(edges, edges[1:], strict=False))
    ):
        raise ValueError("Author BP bin or lookup axis differs")
    rows = []
    previous_end = None
    for position, (index, label) in enumerate(lookup):
        archive_start, archive_end, archive_label = _archive_bounds(position + 1)
        if previous_end is not None and archive_start != previous_end:
            raise ValueError("Published windows are not contiguous")
        previous_end = archive_end
        author_start, author_end = edges[position : position + 2]
        lower_delta = Decimal(archive_start) - author_start
        upper_delta = Decimal(archive_end) - author_end
        rows.append(
            {
                "tw_index": index,
                "author_bin_label_bp": label,
                "author_start_bp": str(author_start),
                "author_end_bp": str(author_end),
                "published_window": archive_label,
                "published_start_bp": str(archive_start),
                "published_end_bp": str(archive_end),
                "published_minus_author_start_bp": str(lower_delta),
                "published_minus_author_end_bp": str(upper_delta),
                "exact_bounds": str(lower_delta == 0 and upper_delta == 0),
            }
        )
    return rows


def align_windows(
    bins_path: Path,
    lookup_path: Path,
    author_report_path: Path,
    published_report_path: Path,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    """Bind source axes and retained numerical receipts before reporting alignment."""
    author = json.loads(author_report_path.read_text())
    published = json.loads(published_report_path.read_text())
    if (
        author["profile"] != "landclimii-2016-release-source-v1"
        or {row["grid_id"] for row in author["grids"]} != {"512", "562"}
        or not all(row["passed"] for row in author["grids"])
        or published["schema_version"]
        != "landclimii-published-window-correspondence.v1"
        or published["source_revision"] != SOURCE_REVISION
        or published["published_archive_sha256"] != ARCHIVE_SHA256
        or published["author_bin_bounds_bp"] != [100, 350]
        or published["published_window"] != "100-350 BP"
    ):
        raise ValueError("Retained author/archive numerical scope differs")
    for grid in author["grids"]:
        sources = grid["source_files"]
        if sources["bins.csv"] != _digest(bins_path) or sources[
            "TWlookup.csv"
        ] != _digest(lookup_path):
            raise ValueError("Author BP axes differ from retained numerical receipts")
    edges = [Decimal(value) for value in bins_path.read_text().splitlines()]
    with lookup_path.open(newline="") as stream:
        reader = csv.reader(stream)
        if next(reader) != ["TW", "class"]:
            raise ValueError("Author time-window lookup header differs")
        raw_lookup = list(reader)
    if any(len(row) != 2 for row in raw_lookup):
        raise ValueError("Author time-window lookup width differs")
    lookup = [(row[0], row[1]) for row in raw_lookup]
    rows = window_rows(edges, lookup)
    exact = [row for row in rows if row["exact_bounds"] == "True"]
    if not any(
        row["tw_index"] == "2"
        and row["author_bin_label_bp"] == "225"
        and row["exact_bounds"] == "True"
        for row in rows
    ):
        raise ValueError("Retained numerical TW2 anchor is no longer exact")
    report: dict[str, object] = {
        "schema_version": "landclimii-author-published-window-alignment.v1",
        "source_revision": SOURCE_REVISION,
        "published_archive_sha256": ARCHIVE_SHA256,
        "author_report_sha256": _digest(author_report_path),
        "published_report_sha256": _digest(published_report_path),
        "author_bins_sha256": _digest(bins_path),
        "author_lookup_sha256": _digest(lookup_path),
        "published_axis": "documented TW filename mapping; archived TW2 numerical receipt",
        "compared_windows": len(rows),
        "exact_windows": len(exact),
        "exact_tw_indices": [row["tw_index"] for row in exact],
        "nonexact_windows": len(rows) - len(exact),
        "historical_raw_input_closure": "not_established",
        "measured_vegetation_accuracy": "not_evaluated",
    }
    return rows, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", type=Path, required=True)
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--author-report", type=Path, required=True)
    parser.add_argument("--published-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = align_windows(
        args.bins, args.lookup, args.author_report, args.published_report
    )
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "window-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# LandClim II author/archive time-window correspondence",
        "",
        "The 25 BP intervals in the retained 2016 author example are compared by "
        "TW index with the documented PANGAEA 937075 mean and SE filename labels. "
        "Both author axis files match the retained numerical replay receipts; "
        "the published archive identity and exact TW2 numerical receipt are "
        "bound by the retained published-window report. No archive payload or "
        "historical raw cohort is recomputed here.",
        "",
        f"{report['exact_windows']} of {report['compared_windows']} windows match both "
        "BP bounds exactly. A shared TW index alone does not establish the same "
        "time support for a numerical cover/SE comparison.",
        "",
        "| TW | Author BP interval | Published BP interval | Published minus author start/end (years) | Exact |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['tw_index']} | {row['author_start_bp']}–{row['author_end_bp']} | "
            f"{row['published_window']} | "
            f"{row['published_minus_author_start_bp']} / "
            f"{row['published_minus_author_end_bp']} | {row['exact_bounds']} |"
        )
    lines.extend(
        [
            "",
            "Only exact time-window support permits a direct same-window numeric "
            "comparison. This axis result does not resolve the 2016 author versus "
            "2021 archive input-cohort difference or measure vegetation accuracy.",
        ]
    )
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("compared_windows", "exact_windows", "exact_tw_indices")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
