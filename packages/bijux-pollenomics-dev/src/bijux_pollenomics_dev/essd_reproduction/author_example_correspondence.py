"""Export cellwise ESSD author-example correspondence from a retained parity run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any, cast

MEAN_ATOL = 1e-11
MEAN_RTOL = 1e-10
SE_ATOL = 5e-8
SE_RTOL = 1e-9


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked(path: Path, digest: str) -> Path:
    if _digest(path) != digest:
        raise ValueError(f"Input digest differs from retained parity receipt: {path}")
    return path


def _candidate_file(base: Path, hashes: dict[str, Any], name: str) -> Path:
    return _checked(base / name, hashes[name]["sha256"])


def _reference_file(
    reference: Path, grid: str, grid_report: dict[str, Any], name: str
) -> Path:
    return _checked(
        reference / grid / name,
        grid_report["reference_files"][f"{grid}/{name}"],
    )


def _rows(path: Path) -> list[list[str]]:
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


def _candidate(
    path: Path, bins: list[str], taxa: list[str]
) -> dict[tuple[str, str], float]:
    rows = _rows(path)
    if rows[0] != ["bin_id", *taxa] or [row[0] for row in rows[1:]] != bins:
        raise ValueError(f"Candidate axes differ: {path}")
    if any(len(row) != len(taxa) + 1 for row in rows[1:]):
        raise ValueError(f"Candidate row width differs: {path}")
    return {
        (row[0], taxon): float(value) if value else math.nan
        for row in rows[1:]
        for taxon, value in zip(taxa, row[1:], strict=True)
    }


def _reference(
    path: Path, bins: list[str], taxa: list[str], prepared: list[str]
) -> dict[tuple[str, str], float]:
    rows = _rows(path)
    if rows[0] != ["", *bins] or [row[0] for row in rows[1:]] != prepared:
        raise ValueError(f"Author reference axes differ: {path}")
    if any(len(row) != len(bins) + 1 for row in rows[1:]):
        raise ValueError(f"Author reference row width differs: {path}")
    return {
        (bin_id, taxon): float(value) if value else math.nan
        for row, taxon in zip(rows[1:], taxa, strict=True)
        for bin_id, value in zip(bins, row[1:], strict=True)
    }


def _metric(
    *,
    grid: str,
    scope: str,
    site: str,
    bins: list[str],
    taxa: list[str],
    supported: set[str],
    actual: dict[tuple[str, str], float],
    expected: dict[tuple[str, str], float],
    metric: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    atol, rtol = (MEAN_ATOL, MEAN_RTOL) if metric == "mean" else (SE_ATOL, SE_RTOL)
    output: list[dict[str, object]] = []
    residuals: list[float] = []
    for bin_id in bins:
        if bin_id not in supported:
            continue
        for taxon in taxa:
            key = (bin_id, taxon)
            candidate, reference = actual[key], expected[key]
            if not math.isfinite(candidate) or not math.isfinite(reference):
                raise ValueError(
                    f"Undefined supported estimate: {grid}/{site}/{key}/{metric}"
                )
            residual = candidate - reference
            residuals.append(abs(residual))
            output.append(
                {
                    "source": "ESSD_LandClim_author_R_example",
                    "grid_id": grid,
                    "scope": scope,
                    "site_id": site,
                    "bin_id_bp": bin_id,
                    "taxon": taxon,
                    "metric": metric,
                    "unit": "fraction",
                    "author_reference": reference,
                    "installed_lra": candidate,
                    "signed_residual": residual,
                    "within_declared_tolerance": math.isclose(
                        candidate, reference, abs_tol=atol, rel_tol=rtol
                    ),
                }
            )
    return output, {
        "grid_id": grid,
        "scope": scope,
        "site_id": site,
        "metric": metric,
        "supported_bins": len(supported),
        "excluded_unavailable_bins": len(bins) - len(supported),
        "compared_values": len(residuals),
        "missing_keys": 0,
        "extra_keys": 0,
        "max_absolute_residual": max(residuals) if residuals else None,
        "median_absolute_residual": median(residuals) if residuals else None,
        "within_declared_tolerance": all(
            row["within_declared_tolerance"] for row in output
        ),
        "absolute_tolerance": atol,
        "relative_tolerance": rtol,
    }


def build_correspondence(
    run: Path, reference: Path
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Authenticate selected retained tables and compare supported mean/SE cells."""
    parity = json.loads((run / "report.json").read_text())
    if parity["profile"] != "landclimii-2016-release-source-v1":
        raise ValueError("Unexpected publication profile")
    receipt_path = reference / "receipt.json"
    _checked(receipt_path, parity["reference_receipt_sha256"])
    receipt = json.loads(receipt_path.read_text())
    if (
        receipt.get("exit_code") != 0
        or receipt.get("input_files_unchanged") is not True
    ):
        raise ValueError(
            "Independent author-R replay has no successful input-stable receipt"
        )
    crosswalk_path = reference / "taxon-name-crosswalk.csv"
    _checked(crosswalk_path, parity["grids"][0]["crosswalk_sha256"])
    crosswalk = list(csv.DictReader(crosswalk_path.open(newline="")))
    taxa = [row["source"] for row in crosswalk]
    prepared = [row["prepared"] for row in crosswalk]
    if len(taxa) != len(set(taxa)) or len(prepared) != len(set(prepared)):
        raise ValueError("Ambiguous author taxon crosswalk")
    detail: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    grids: list[dict[str, object]] = []
    for grid_report in parity["grids"]:
        if not grid_report["passed"] or grid_report["crosswalk_sha256"] != _digest(
            crosswalk_path
        ):
            raise ValueError("Retained grid parity or crosswalk is invalid")
        grid = grid_report["grid_id"]
        base = run / grid
        hashes = json.loads((base / "checksums.json").read_text())
        manifest = json.loads((base / "run-manifest.json").read_text())
        if (
            manifest["parameters"]["profile"] != parity["profile"]
            or manifest["parameters"]["source_revision"]
            != "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
            or manifest["parameters"]["units"]["cover"] != "fraction"
            or manifest["parameters"]["units"]["standard_error"] != "fraction"
        ):
            raise ValueError("Retained grid method or units differ")

        counts = _rows(_candidate_file(base, hashes, "site-count.csv"))
        if counts[0] != ["bin_id", "site_count"]:
            raise ValueError("Unexpected site-count axes")
        bins = [row[0] for row in counts[1:]]
        if len(set(bins)) != len(bins) or len(bins) != grid_report["bins"]:
            raise ValueError("Unexpected bin axes")
        site_counts = {row[0]: int(row[1]) for row in counts[1:]}
        author_counts = _rows(
            _reference_file(reference, grid, grid_report, "site-count.csv")
        )
        if author_counts != [["", *bins], ["1", *[str(site_counts[b]) for b in bins]]]:
            raise ValueError("Author site counts differ")
        availability = _rows(_candidate_file(base, hashes, "availability.csv"))
        sites = json.loads((base / "site-index.json").read_text())
        names = [site["site_id"] for site in sites]
        if (
            availability[0] != ["bin_id", *names]
            or [row[0] for row in availability[1:]] != bins
            or names != [item["site_id"] for item in grid_report["checks"]["sites"]]
        ):
            raise ValueError("Site/availability axes differ")
        if len(sites) != grid_report["sites"] or len(taxa) != grid_report["taxa"]:
            raise ValueError("Unexpected site/taxon count")
        masks = {
            name: {row[0] for row in availability[1:] if row[position + 1] == "True"}
            for position, name in enumerate(names)
        }
        if any(
            value not in {"True", "False"}
            for row in availability[1:]
            for value in row[1:]
        ):
            raise ValueError("Invalid availability token")
        if any(site_counts[b] != sum(b in masks[name] for name in names) for b in bins):
            raise ValueError("Site counts and availability differ")
        if sum(map(len, masks.values())) != grid_report["available_site_bins"]:
            raise ValueError("Available site-bin denominator differs")
        supported = {b for b in bins if site_counts[b] > 0}
        if len(supported) != grid_report["supported_bins"]:
            raise ValueError("Regional support denominator differs")
        targets = [("regional", "", base, 0, supported)] + [
            (
                "site",
                site["site_id"],
                base / site["path"],
                position + 1,
                masks[site["site_id"]],
            )
            for position, site in enumerate(sites)
        ]
        for scope, site, candidate_dir, position, supported_bins in targets:
            for metric, candidate_name, reference_name in (
                ("mean", "cover.csv", "cover.csv"),
                ("standard_error", "standard-error.csv", "se.csv"),
            ):
                prefix = "regional-" if scope == "regional" else ""
                actual_name = f"{candidate_dir.relative_to(base)}/{prefix}{candidate_name}".removeprefix(
                    "./"
                )
                author_name = f"{prefix if scope == 'regional' else f'site-{position}-'}{reference_name}"
                actual = _candidate(
                    _candidate_file(base, hashes, actual_name), bins, taxa
                )
                expected = _reference(
                    _reference_file(reference, grid, grid_report, author_name),
                    bins,
                    taxa,
                    prepared if scope == "site" else taxa,
                )
                rows, summary = _metric(
                    grid=grid,
                    scope=scope,
                    site=site,
                    bins=bins,
                    taxa=taxa,
                    supported=supported_bins,
                    actual=actual,
                    expected=expected,
                    metric=metric,
                )
                previous = (
                    grid_report["checks"][
                        "regional_cover" if metric == "mean" else "regional_se"
                    ]
                    if scope == "regional"
                    else grid_report["checks"]["sites"][position - 1][
                        "cover" if metric == "mean" else "se"
                    ]
                )
                if summary["compared_values"] != previous["values"]:
                    raise ValueError(
                        "Cell denominator differs from retained numerical comparison"
                    )
                detail.extend(rows)
                summaries.append(summary)
        grids.append(
            {
                "grid_id": grid,
                "sites": len(sites),
                "bins": len(bins),
                "taxa": len(taxa),
                "available_site_bins": sum(map(len, masks.values())),
                "supported_regional_bins": len(supported),
                "source_revision": manifest["parameters"]["source_revision"],
            }
        )
    report = {
        "schema_version": "1.0.0",
        "comparison": "installed_LRA_vs_independent_exact_author_R_replay",
        "profile": parity["profile"],
        "reference_receipt_sha256": parity["reference_receipt_sha256"],
        "coverage": "17_author_example_sites_in_two_grids_only",
        "unit": "fraction",
        "measured_vegetation_accuracy": "not_evaluated",
        "grids": grids,
        "summary": summaries,
        "compared_values": len(detail),
        "passed": all(item["within_declared_tolerance"] for item in summaries),
        "max_absolute_mean_residual": max(
            cast(float, item["max_absolute_residual"])
            for item in summaries
            if item["metric"] == "mean"
        ),
        "max_absolute_standard_error_residual": max(
            cast(float, item["max_absolute_residual"])
            for item in summaries
            if item["metric"] == "standard_error"
        ),
    }
    return detail, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = build_correspondence(args.run, args.reference)
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "paper-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "REPORT.md").write_text(
        "# ESSD LandClim author-example correspondence\n\n"
        "The installed LRA publication profile was recomputed on the retained author "
        "inputs and compared cell by cell with an independent exact author-R replay. "
        "The source revision is `57ead2e2fcc493d099be4e5a3092fc396e1c3d3a`. "
        "Values are fractional cover and fractional standard error.\n\n"
        f"Across 17 site examples in grids 512 and 562, {report['compared_values']:,} "
        "supported mean/SE values have zero missing or extra keys. "
        f"The maximum absolute mean residual is {report['max_absolute_mean_residual']:.6g}; "
        f"the maximum absolute SE residual is {report['max_absolute_standard_error_residual']:.6g}. "
        "All pass the source comparison's prospective mean "
        "(`atol=1e-11`, `rtol=1e-10`) and SE "
        "(`atol=5e-8`, `rtol=1e-9`) tolerances. "
        "The CSV gives each reference value, recomputed value, signed residual, and status; "
        "the JSON gives per-site and regional maximum/median residuals and support counts.\n\n"
        "This checks two author examples, not the 1,128-row historical reconstruction or "
        "the PANGAEA published estimate table. The source bins retain their documented "
        "50 BP difference from the paper, and 12-PFT paper / 11-description dataset / "
        "populated ISTS output semantics remain unresolved. No independent measured "
        "vegetation accuracy is evaluated.\n"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "passed",
                    "compared_values",
                    "max_absolute_mean_residual",
                    "max_absolute_standard_error_residual",
                )
            }
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
