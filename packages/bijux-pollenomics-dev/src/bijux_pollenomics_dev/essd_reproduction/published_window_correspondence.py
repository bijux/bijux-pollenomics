"""Compare an exact author time window with pinned ESSD published estimates."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import cast
from zipfile import ZipFile

from bijux_pollenomics.collection.sources.landclim.catalog import (
    time_window_from_tw_filename,
)

from .comparison import (
    PublishedEstimateCandidate,
    PublishedEstimateKey,
    PublishedEstimateValue,
    _compare_rows,
)

ARCHIVE_SHA256 = "c585f0691ad95342b8aba083b90fe91dc398f985b6b7fbc19561299389c4fb86"
RECEIPT_SHA256 = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
SOURCE_REVISION = "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
WINDOW = "100-350 BP"
BIN_ID = "225"
GRIDS = ("512", "562")
MEAN_MEMBER = "LANDCLIMII.RV.means.JUN2021/TW2.RV.estimates.jun21.csv"
SE_MEMBER = "LANDCLIMII.RV.standarderrors.JUN2021/TW2.RV.standarderrors.jun21.csv"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked(path: Path, digest: str) -> Path:
    if _digest(path) != digest:
        raise ValueError(f"Retained input digest differs: {path}")
    return path


def _rows(path: Path) -> list[list[str]]:
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


def _exact_author_window(bins_path: Path, lookup_path: Path) -> list[str]:
    """Admit only the source bin whose bounds exactly match published TW2."""
    edges = [Decimal(value) for value in bins_path.read_text().splitlines()]
    lookup = _rows(lookup_path)
    if (
        len(edges) != 26
        or edges[1:3] != [Decimal(100), Decimal(350)]
        or lookup[0] != ["TW", "class"]
        or len(lookup) != 26
        or [row[0] for row in lookup[1:]] != [str(index) for index in range(1, 26)]
        or lookup[2] != ["2", BIN_ID]
        or time_window_from_tw_filename(MEAN_MEMBER) != WINDOW
        or time_window_from_tw_filename(SE_MEMBER) != WINDOW
    ):
        raise ValueError("Author and published time-window bounds do not match")
    return [row[1] for row in lookup[1:]]


def _published_rows(
    archive: ZipFile, prepared: list[str]
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, object]]:
    selected: list[dict[str, dict[str, str]]] = []
    headers: list[list[str]] = []
    source_rows: list[dict[str, int]] = []
    for name in (MEAN_MEMBER, SE_MEMBER):
        with archive.open(name) as stream:
            reader = csv.DictReader((line.decode("utf-8") for line in stream))
            header = reader.fieldnames
            if (
                header is None
                or header[:3] != ["LCGRID_ID", "lonDD", "latDD"]
                or header[3:34] != prepared
            ):
                raise ValueError(f"Published taxon or identity axes differ: {name}")
            headers.append(list(header))
            rows: dict[str, dict[str, str]] = {}
            positions: dict[str, int] = {}
            for position, row in enumerate(reader, start=2):
                grid = row["LCGRID_ID"]
                if grid in GRIDS:
                    if (
                        grid in rows
                        or set(row) != set(header)
                        or any(value is None for value in row.values())
                    ):
                        raise ValueError(
                            f"Published grid row is repeated or incomplete: {name}/{grid}"
                        )
                    rows[grid] = row
                    positions[grid] = position
            if set(rows) != set(GRIDS):
                raise ValueError(f"Published grid rows are missing: {name}")
            selected.append(rows)
            source_rows.append(positions)
    if headers[0] != headers[1] or any(
        (selected[0][grid]["lonDD"], selected[0][grid]["latDD"])
        != (selected[1][grid]["lonDD"], selected[1][grid]["latDD"])
        for grid in GRIDS
    ):
        raise ValueError("Published mean/SE identities differ")
    return (
        selected[0],
        selected[1],
        {
            grid: {
                "longitude": selected[0][grid]["lonDD"],
                "latitude": selected[0][grid]["latDD"],
                "mean_source_row": source_rows[0][grid],
                "standard_error_source_row": source_rows[1][grid],
            }
            for grid in GRIDS
        },
    )


def _candidate_values(
    path: Path, bins: list[str], taxa: list[str]
) -> dict[str, Decimal]:
    rows = _rows(path)
    if rows[0] != ["bin_id", *taxa] or [row[0] for row in rows[1:]] != bins:
        raise ValueError(f"Candidate axes differ: {path}")
    if any(len(row) != len(taxa) + 1 for row in rows[1:]):
        raise ValueError(f"Candidate row width differs: {path}")
    row = next(item for item in rows[1:] if item[0] == BIN_ID)
    return {
        taxon: Decimal(value) * Decimal(100)
        for taxon, value in zip(taxa, row[1:], strict=True)
    }


def build_correspondence(
    raw: Path, author: Path, run: Path, reference: Path
) -> tuple[list[dict[str, str]], dict[str, object]]:
    """Compare published and recomputed taxon values on the one exact bin."""
    archive_path = _checked(raw / "landclim_ii_reveals_results.zip", ARCHIVE_SHA256)
    _checked(raw / "landclim_sources.json", RECEIPT_SHA256)
    parity = json.loads((run / "report.json").read_text())
    if parity["profile"] != "landclimii-2016-release-source-v1" or {
        item["grid_id"] for item in parity["grids"]
    } != set(GRIDS):
        raise ValueError("Retained numerical run is outside the selected profile/grids")
    _checked(
        reference / "taxon-name-crosswalk.csv", parity["grids"][0]["crosswalk_sha256"]
    )
    with (reference / "taxon-name-crosswalk.csv").open(newline="") as stream:
        crosswalk = list(csv.DictReader(stream))
    taxa = [row["source"] for row in crosswalk]
    prepared = [row["prepared"] for row in crosswalk]
    if len(taxa) != 31 or len(set(taxa)) != 31 or len(set(prepared)) != 31:
        raise ValueError("Author taxon crosswalk is incomplete")
    sources = {row["source"]: row["prepared"] for row in crosswalk}
    first = parity["grids"][0]["source_files"]
    bins_path = _checked(author / "bins.csv", first["bins.csv"])
    lookup_path = _checked(author / "TWlookup.csv", first["TWlookup.csv"])
    expected_bins = _exact_author_window(bins_path, lookup_path)
    with ZipFile(archive_path) as archive:
        published_mean, published_se, locators = _published_rows(archive, prepared)
    reference_rows: list[PublishedEstimateValue] = []
    candidate_rows: list[PublishedEstimateValue] = []
    site_counts: dict[str, int] = {}
    for grid in GRIDS:
        grid_report = next(item for item in parity["grids"] if item["grid_id"] == grid)
        if not grid_report["passed"] or grid_report["crosswalk_sha256"] != _digest(
            reference / "taxon-name-crosswalk.csv"
        ):
            raise ValueError("Retained numerical grid did not pass author-R parity")
        base = run / grid
        hashes = json.loads((base / "checksums.json").read_text())
        manifest = json.loads((base / "run-manifest.json").read_text())
        if (
            manifest["parameters"]["source_revision"] != SOURCE_REVISION
            or manifest["parameters"]["units"]["cover"] != "fraction"
            or manifest["parameters"]["units"]["standard_error"] != "fraction"
        ):
            raise ValueError("Candidate revision or fraction units differ")
        count_rows = _rows(
            _checked(base / "site-count.csv", hashes["site-count.csv"]["sha256"])
        )
        bins = [row[0] for row in count_rows[1:]]
        if count_rows[0] != ["bin_id", "site_count"] or bins != expected_bins:
            raise ValueError("Candidate bin axis differs")
        site_counts[grid] = int(
            next(row[1] for row in count_rows[1:] if row[0] == BIN_ID)
        )
        if not 0 < site_counts[grid] <= grid_report["sites"]:
            raise ValueError("No supported author sites in the matched bin")
        mean_values = _candidate_values(
            _checked(
                base / "regional-cover.csv", hashes["regional-cover.csv"]["sha256"]
            ),
            bins,
            taxa,
        )
        se_values = _candidate_values(
            _checked(
                base / "regional-standard-error.csv",
                hashes["regional-standard-error.csv"]["sha256"],
            ),
            bins,
            taxa,
        )
        for source_taxon in taxa:
            feature = sources[source_taxon]
            key = PublishedEstimateKey(grid, WINDOW, feature)
            reference_mean = Decimal(published_mean[grid][feature])
            reference_se = Decimal(published_se[grid][feature])
            if (
                not reference_mean.is_finite()
                or not reference_se.is_finite()
                or reference_se < 0
            ):
                raise ValueError(f"Published mean/SE is invalid: {grid}/{feature}")
            reference_rows.append(
                PublishedEstimateValue(key, reference_mean, reference_se)
            )
            candidate_rows.append(
                PublishedEstimateValue(
                    key, mean_values[source_taxon], se_values[source_taxon]
                )
            )
    candidate = PublishedEstimateCandidate(
        "landclimii-author-example-publication-profile",
        "percentage_cover",
        tuple(candidate_rows),
    )
    comparison = _compare_rows(
        tuple(reference_rows), candidate, reference_input_sha256=ARCHIVE_SHA256
    )
    if (
        comparison.denominators.shared_keys != 62
        or comparison.denominators.reference_only_keys
        or comparison.denominators.candidate_only_keys
    ):
        raise ValueError("Exact published/candidate taxon keys do not close")
    rows = [
        {
            "grid_id": row.key.grid,
            "window": row.key.window,
            "author_bin_id_bp": BIN_ID,
            "taxon": row.key.feature,
            "unit": "percentage_cover",
            "published_mean": str(row.reference_mean),
            "recomputed_mean": str(row.candidate_mean),
            "mean_residual": str(row.mean_residual),
            "published_standard_error": str(row.reference_standard_error),
            "recomputed_standard_error": str(row.candidate_standard_error),
            "standard_error_residual": str(row.standard_error_residual),
        }
        for row in comparison.rows
    ]
    summaries = []
    for grid in GRIDS:
        subset = [row for row in comparison.rows if row.key.grid == grid]
        means = [
            abs(row.mean_residual) for row in subset if row.mean_residual is not None
        ]
        errors = [
            abs(row.standard_error_residual)
            for row in subset
            if row.standard_error_residual is not None
        ]
        if len(means) != 31 or len(errors) != 31:
            raise ValueError("Published mean/SE numerical denominator differs")
        largest_mean = max(
            subset,
            key=lambda row: (
                abs(row.mean_residual) if row.mean_residual is not None else Decimal(-1)
            ),
        )
        largest_se = max(
            subset,
            key=lambda row: (
                abs(row.standard_error_residual)
                if row.standard_error_residual is not None
                else Decimal(-1)
            ),
        )
        summaries.append(
            {
                "grid_id": grid,
                "author_sites_in_bin": site_counts[grid],
                "published_source": locators[grid],
                "taxa": 31,
                "max_absolute_mean_residual_percentage_points": str(max(means)),
                "median_absolute_mean_residual_percentage_points": str(median(means)),
                "max_absolute_standard_error_residual_percentage_points": str(
                    max(errors)
                ),
                "median_absolute_standard_error_residual_percentage_points": str(
                    median(errors)
                ),
                "largest_mean_residual_taxon": largest_mean.key.feature,
                "largest_mean_signed_residual_percentage_points": str(
                    largest_mean.mean_residual
                ),
                "largest_standard_error_residual_taxon": largest_se.key.feature,
                "largest_standard_error_signed_residual_percentage_points": str(
                    largest_se.standard_error_residual
                ),
            }
        )
    report: dict[str, object] = {
        "schema_version": "landclimii-published-window-correspondence.v1",
        "comparison": "retained_author_example_python_recomputation_minus_pangaea_937075_archive",
        "source_revision": SOURCE_REVISION,
        "published_archive_sha256": ARCHIVE_SHA256,
        "published_receipt_sha256": RECEIPT_SHA256,
        "candidate_parity_report_sha256": _digest(run / "report.json"),
        "author_bin_bounds_bp": [100, 350],
        "published_window": WINDOW,
        "unit": "percentage_cover",
        "taxon_keys": comparison.denominators.payload(),
        "grids": summaries,
        "tolerance": "none_descriptive_cross_revision_comparison",
        "historical_raw_input_closure": "not_established",
        "measured_vegetation_accuracy": "not_evaluated",
        "pft_correspondence": "excluded_unresolved_12_11_ISTS_mapping",
    }
    return rows, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = build_correspondence(args.raw, args.author, args.run, args.reference)
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "paper-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    grids = cast(list[dict[str, object]], report["grids"])
    (args.output / "REPORT.md").write_text(
        "# LandClim II published-window correspondence\n\n"
        "The retained Python REVEALS publication-profile output for author grids "
        "512 and 562 is compared with the pinned PANGAEA 937075 June 2021 mean "
        "and standard-error members. The author bin labeled 225 spans 100–350 BP, "
        "exactly the published TW2 window. The 31 taxon axes use the authenticated "
        "author crosswalk; recomputed fractions are explicitly multiplied by 100 "
        "to match published percentage cover. All 62 grid/taxon keys and all "
        "mean/SE values pair without missing or extra keys.\n\n"
        + "\n".join(
            f"- Grid {grid['grid_id']}: {grid['author_sites_in_bin']} author sites in "
            f"this bin; maximum/median absolute mean residual "
            f"{Decimal(str(grid['max_absolute_mean_residual_percentage_points'])):.4f}/"
            f"{Decimal(str(grid['median_absolute_mean_residual_percentage_points'])):.4f} "
            f"percentage points; maximum/median absolute SE residual "
            f"{Decimal(str(grid['max_absolute_standard_error_residual_percentage_points'])):.4f}/"
            f"{Decimal(str(grid['median_absolute_standard_error_residual_percentage_points'])):.4f} "
            f"percentage points. Largest mean discrepancy: {grid['largest_mean_residual_taxon']}; "
            f"largest SE discrepancy: {grid['largest_standard_error_residual_taxon']}."
            for grid in grids
        )
        + "\n\nThese are candidate-minus-archive residuals, with no fitted or declared "
        "pass tolerance. Matching keys, bin bounds and units do not establish matching "
        "historical raw-input cohorts: the local author example uses the pinned "
        "2016 source revision while the archive is a June 2021 published product. "
        "The other author bins differ from the published time bounds and are "
        "excluded. Functional-type columns, including the unresolved ISTS mapping, "
        "are excluded. This is a numerical published-product correspondence on one "
        "window, not whole-paper reproduction or measured vegetation accuracy.\n"
    )
    print(json.dumps({"keys": len(rows), "grids": report["grids"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
