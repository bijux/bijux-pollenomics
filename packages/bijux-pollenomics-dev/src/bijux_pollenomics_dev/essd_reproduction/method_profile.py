"""Bind the LandClim author method and example inputs to a native profile."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any
import zipfile

SNAPSHOT_SHA = "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
REVISION = "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
PROFILE = "landclimii-2016-release-source-v1"
PARITY = Path("docs/report/publication-replay/landclim-method-profile/reference")
PARITY_HASHES = {
    "report.json": "56f3dc776aa0a3405338fba62ae51a8b383b0c64787bd6fa4364677ac7ae24c5",
    "512/run-manifest.json": "c6b82fcc1cc916b060f9723cc760fbbfa79fe990741057ac71524fca4ac8bc6f",
    "562/run-manifest.json": "137881d83a1f861924a14a4d1f1490b7c9a201f0d51ffef3bb5f5f128d91b5ee",
}
CUSTODY = Path("docs/report/pollen-reconstruction/author-source-custody.json")
MAPPING = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")
ARCHIVE = Path("data/landclim/raw/landclim_ii_reveals_results.zip")
SOURCE_RECEIPT = Path("data/landclim/raw/landclim_sources.json")
NATIVE = (
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/publication.py"
    ),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py"
    ),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py"
    ),
)
METHOD_FIELDS = (
    "domain",
    "original_evidence",
    "native_evidence",
    "comparison_status",
    "source_locator",
    "native_locator",
    "limitation",
)
EXAMPLE_FIELDS = (
    "grid_id",
    "site_id",
    "raw_input_member",
    "raw_input_sha256",
    "prepared_input_member",
    "prepared_input_sha256",
    "source_model_code",
    "source_radius_m",
    "native_grid_sites",
    "native_grid_bins",
    "native_grid_taxa",
    "identity_status",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _rows(content: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))


def _identity(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": _sha(data),
    }


def _checked_private(root: Path) -> dict[str, str]:
    manifest_path = root / "snapshot-manifest.json"
    if manifest_path.is_symlink() or _sha(manifest_path.read_bytes()) != SNAPSHOT_SHA:
        raise ValueError("Author snapshot manifest identity changed")
    manifest = json.loads(manifest_path.read_text())
    files: dict[str, str] = manifest["files"]
    if manifest["file_count"] != 193 or len(files) != 193:
        raise ValueError("Author source closure changed")
    for relative, expected in files.items():
        path = root / relative
        if (
            path.is_symlink()
            or not path.is_file()
            or _sha(path.read_bytes()) != expected
        ):
            raise ValueError(f"Author source member changed: {relative}")
    return files


def _checked_parity(repository: Path) -> None:
    for name, expected in PARITY_HASHES.items():
        path = repository / PARITY / name
        if (
            path.is_symlink()
            or not path.is_file()
            or _sha(path.read_bytes()) != expected
        ):
            raise ValueError(f"Tracked native comparison receipt changed: {name}")


def _example_inputs(
    private_root: Path,
    hashes: dict[str, str],
    grid_reports: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    author = private_root / "author"
    group_files = _rows((author / "run.REVEALS.files/GC.list.csv").read_bytes())
    if group_files != [["site.list.512.csv"], ["site.list.562.csv"]]:
        raise ValueError("Author grid example list changed")
    metadata_rows = list(
        csv.DictReader((author / "site.metadata.csv").open(newline=""))
    )
    metadata = {row["filename"]: row for row in metadata_rows}
    if len(metadata_rows) != 17 or len(metadata) != 17:
        raise ValueError("Author example metadata denominator changed")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for grid_id, expected_sites in (("512", 9), ("562", 8)):
        names = [
            item[0]
            for item in _rows(
                (author / f"run.REVEALS.files/site.list.{grid_id}.csv").read_bytes()
            )
        ]
        if len(names) != expected_sites or len(set(names)) != expected_sites:
            raise ValueError("Author example grid membership changed")
        native = grid_reports[grid_id]
        if (
            native["sites"] != expected_sites
            or native["bins"] != 25
            or native["taxa"] != 31
            or not native["passed"]
        ):
            raise ValueError("Retained native example coverage changed")
        for filename in names:
            if not filename.startswith("LRAready_") or not filename.endswith(".csv"):
                raise ValueError("Author prepared member name changed")
            site = filename.removeprefix("LRAready_").removesuffix(".csv")
            if (
                site in seen
                or site not in metadata
                or metadata[site]["LCGRID_ID"] != grid_id
            ):
                raise ValueError("Author example site ownership changed")
            seen.add(site)
            raw = f"author/input/{site}.csv"
            prepared = f"author/run.REVEALS.files/{filename}"
            if raw not in hashes or prepared not in hashes:
                raise ValueError("Author raw/prepared example member missing")
            if metadata[site]["model"] != "2" or float(metadata[site]["radius"]) <= 0:
                raise ValueError("Author example lake/radius claim changed")
            prepared_rows = _rows((private_root / prepared).read_bytes())
            if (
                len(prepared_rows) != 34
                or [row[0].strip('"') for row in prepared_rows[:3]]
                != ["TW", "radius", "model"]
                or len(prepared_rows[0]) != 26
            ):
                raise ValueError("Author prepared example axes changed")
            rows.append(
                {
                    "grid_id": grid_id,
                    "site_id": site,
                    "raw_input_member": raw,
                    "raw_input_sha256": hashes[raw],
                    "prepared_input_member": prepared,
                    "prepared_input_sha256": hashes[prepared],
                    "source_model_code": metadata[site]["model"],
                    "source_radius_m": metadata[site]["radius"],
                    "native_grid_sites": expected_sites,
                    "native_grid_bins": native["bins"],
                    "native_grid_taxa": native["taxa"],
                    "identity_status": "source_members_verified_native_grid_axes_matched",
                }
            )
    if seen != set(metadata):
        raise ValueError("Author metadata contains sites outside example grids")
    return rows


def _pft_evidence(repository: Path) -> dict[str, object]:
    rows = list(csv.DictReader((repository / MAPPING).open(encoding="utf-8-sig")))
    labels = [row["PFT"] for row in rows if row["PFT"]]
    if len(rows) != 31 or len(labels) != 12 or len(set(labels)) != 12:
        raise ValueError("PANGAEA mapping table PFT labels changed")
    headers: set[tuple[str, ...]] = set()
    with zipfile.ZipFile(repository / ARCHIVE) as archive:
        names = archive.namelist()
        if len(names) != 50:
            raise ValueError("PANGAEA mean/SE member count changed")
        for name in names:
            with archive.open(name) as stream:
                headers.add(tuple(next(csv.reader(io.TextIOWrapper(stream)))))
    if len(headers) != 1:
        raise ValueError("PANGAEA mean/SE schemas diverge")
    header = next(iter(headers))
    if (
        len(header) != 50
        or header[:3] != ("LCGRID_ID", "lonDD", "latDD")
        or header[-3:] != ("ET", "ST", "OL")
    ):
        raise ValueError("PANGAEA output axis changed")
    pft_columns = header[34:-3]
    if len(pft_columns) != 13 or set(pft_columns) - set(labels) != {"ISTS"}:
        raise ValueError("PANGAEA PFT table/output conflict changed")
    return {
        "paper_prose_claim": 12,
        "dataset_description_claim": 11,
        "parameter_table_nonblank_codes": len(labels),
        "parameter_table_codes": labels,
        "mean_se_output_pft_position_columns": len(pft_columns),
        "mean_se_output_codes": list(pft_columns),
        "output_code_missing_from_parameter_table": ["ISTS"],
        "mean_se_output_files_checked": 50,
        "classification_admission": "blocked_conflicting_source_versions_and_no_column_crosswalk",
    }


def _method_rows() -> list[dict[str, str]]:
    source_script = "author/run.REVEALS.files/LRA-REVEALS-release.R"
    wrapper = "author/Kunes_REVEALS_iterate_across_sitelists.R"
    prep = "author/RV.file.format.LANDCLIMII.r"
    native_profile = NATIVE[0].as_posix()
    native_algorithm = NATIVE[1].as_posix()
    values = (
        (
            "executable",
            "2016-10-30 release REVEALS function via author wrapper",
            PROFILE,
            "named_source_profile",
            source_script,
            native_profile,
            "Current native code is compared to a retained historical run, not executed here.",
        ),
        (
            "taxonomy",
            "31 RPP taxa after source synonym lookup",
            "31 named taxon input axis",
            "example_axis_matched",
            prep,
            native_profile,
            "Full 1128-record historical taxonomy is not authenticated.",
        ),
        (
            "pollen_sums_missing_zero",
            "NA replaced with zero; positive named-taxon sum",
            "available cells require integral counts; unavailable site/bin masked",
            "documented_missing_support_difference",
            source_script,
            native_profile,
            "Absent site/bin is not silently treated as measured zero in native input.",
        ),
        (
            "chronology_bins",
            "26 author boundaries and 25 midpoint labels",
            "explicit author-archive BP bin profile and 25 bins",
            "example_axis_matched",
            "author/bins.csv;author/TWlookup.csv",
            native_profile,
            "Example bins do not authenticate all publication chronologies.",
        ),
        (
            "basin_geometry",
            "source radius and model code 2 lake in 17 example sites",
            "explicit radius metres and basin type per available site/bin",
            "example_geometry_mapped",
            "author/site.metadata.csv",
            native_profile,
            "Example has no bog site.",
        ),
        (
            "dispersal_deposition",
            "gpm neutral; 3 m/s wind; Zmax 100000 m",
            "same named publication profile parameters",
            "parameter_matched",
            wrapper,
            native_profile,
            "Historical lake gamma expression retains an unresolved author comment.",
        ),
        (
            "ppe_covariance",
            "31 taxa mean/fall speed and 31x31 covariance",
            "31-taxon ordered PPE/covariance input",
            "example_axis_matched",
            "author/run.REVEALS.files/av-RPP.all.landclimII.csv;author/run.REVEALS.files/avar-RPP.all.landclimII.csv",
            native_profile,
            "Multisite source bootstrap does not propagate PPE covariance.",
        ),
        (
            "aggregation_uncertainty",
            "1000 site-resampling draws; mean and SE",
            "1000 explicit site-index draws in retained profile",
            "bounded_retained_parity",
            source_script,
            native_algorithm,
            "Retained run covers two example grids, not the full study.",
        ),
        (
            "units_rounding",
            "source wrapper multiplies cover and SE by 100 for CSV",
            "native run stores fractional cover and SE",
            "conversion_required",
            wrapper,
            native_profile,
            "Output percent and native fraction cannot be compared without scaling.",
        ),
        (
            "pft_lct",
            "paper 12 PFT; dataset prose 11; output header 13 PFT-position codes",
            "no native PFT aggregation certified here",
            "classification_blocked",
            "PANGAEA.937075 mapping and output archive",
            native_profile,
            "Source table has 12 nonblank codes; output adds ISTS without resolved version crosswalk.",
        ),
    )
    return [dict(zip(METHOD_FIELDS, row, strict=True)) for row in values]


def build(repository: Path, private_root: Path, output: Path) -> dict[str, Any]:
    """Publish a deterministic source-bound comparison without copying private input."""
    repository, private_root, output = (
        repository.resolve(),
        private_root.resolve(),
        output.resolve(),
    )
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    hashes = _checked_private(private_root)
    _checked_parity(repository)
    custody = json.loads((repository / CUSTODY).read_text())
    if (
        custody["source_revision"] != REVISION
        or custody["original_manifest_sha256"] != SNAPSHOT_SHA
        or custody["redistribution_status"]
        != "not_cleared; source and independent reference files remain private in the external source-data store"
    ):
        raise ValueError("Author source revision or rights boundary changed")
    author = private_root / "author"
    source = (author / "run.REVEALS.files/LRA-REVEALS-release.R").read_text()
    wrapper = (author / "Kunes_REVEALS_iterate_across_sitelists.R").read_text()
    preparation = (author / "RV.file.format.LANDCLIMII.r").read_text()
    if (
        not all(
            fragment in source
            for fragment in (
                "Release version: 1 (30 October 2016)",
                "polcount[is.na(polcount)] <- 0",
                "sample(st, replace = TRUE)",
                "nrow = 1000",
            )
        )
        or 'REVEALS(largesites, avg, alvc, 3, 100000, dwm = "gpm neutral")'
        not in wrapper
        or "findInterval(age, bins)" not in preparation
    ):
        raise ValueError("Author method profile changed")
    parameter = _rows(
        (author / "run.REVEALS.files/av-RPP.all.landclimII.csv").read_bytes()
    )
    covariance = _rows(
        (author / "run.REVEALS.files/avar-RPP.all.landclimII.csv").read_bytes()
    )
    if (
        len(parameter) != 32
        or len(covariance) != 32
        or any(len(row) != 32 for row in covariance)
        or [row[0] for row in parameter[1:]] != covariance[0][1:]
    ):
        raise ValueError("Author PPE and covariance axes changed")
    if (
        len(_rows((author / "bins.csv").read_bytes())) != 26
        or len(_rows((author / "TWlookup.csv").read_bytes())) != 26
    ):
        raise ValueError("Author window axes changed")
    receipt = json.loads((private_root / "reference/receipt.json").read_text())
    if (
        receipt["exit_code"] != 0
        or receipt["input_files_unchanged"] is not True
        or receipt["source_sha256"]
        != hashes["author/run.REVEALS.files/LRA-REVEALS-release.R"]
    ):
        raise ValueError("Retained original R evidence changed")
    parity = json.loads((repository / PARITY / "report.json").read_text())
    if (
        parity["profile"] != PROFILE
        or parity["reference_receipt_sha256"] != hashes["reference/receipt.json"]
        or parity["coverage"]
        != "two_author_example_grids_only_not_full_1128_record_study"
    ):
        raise ValueError("Retained native comparison scope changed")
    grids = {row["grid_id"]: row for row in parity["grids"]}
    if set(grids) != {"512", "562"}:
        raise ValueError("Retained native example grids changed")
    for grid in grids:
        manifest = json.loads(
            (repository / PARITY / grid / "run-manifest.json").read_text()
        )
        config = manifest["parameters"]
        if (
            config["profile"] != PROFILE
            or config["source_revision"] != REVISION
            or config["source_file_sha256"] != receipt["source_sha256"]
            or config["wind_speed_m_s"] != 3.0
            or config["regional_extent_m"] != 100000.0
            or config["bootstrap_replicates"] != 1000
            or config["time_bin_profile"] != "landclimii-author-archive-bins-v1"
            or config["units"]["cover"] != "fraction"
            or config["units"]["standard_error"] != "fraction"
        ):
            raise ValueError("Native method profile differs from author source")
    methods = _method_rows()
    examples = _example_inputs(private_root, hashes, grids)
    pft = _pft_evidence(repository)
    dataset_receipt = json.loads((repository / SOURCE_RECEIPT).read_text())
    if not any(
        dataset["dataset_id"] == "937075"
        and dataset["doi"] == "https://doi.org/10.1594/PANGAEA.937075"
        and MAPPING.name in dataset["files"]
        and ARCHIVE.name in dataset["files"]
        for dataset in dataset_receipt["datasets"]
    ):
        raise ValueError("PANGAEA source asset receipt changed")
    output.mkdir(parents=True)
    for name, fields, records in (
        ("method_crosswalk.csv", METHOD_FIELDS, methods),
        ("example_inputs.csv", EXAMPLE_FIELDS, examples),
    ):
        with (output / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    report: dict[str, Any] = {
        "schema_version": "landclim-method-profile.v1",
        "scope": "two_retained_author_example_grids_method_and_input_identity",
        "paper_doi": "10.5194/essd-14-1581-2022",
        "dataset_doi": "10.1594/PANGAEA.937075",
        "author_source_revision": REVISION,
        "author_snapshot_manifest_sha256": SNAPSHOT_SHA,
        "author_snapshot_members_verified": len(hashes),
        "original_r_replay": "retained_receipt_passed_not_rerun_here",
        "native_numerical_comparison": "retained_two_grid_result_not_rerun_here",
        "native_profile": PROFILE,
        "example_grid_sites": {grid: grids[grid]["sites"] for grid in sorted(grids)},
        "example_input_rows": len(examples),
        "pft_evidence": pft,
        "publisher_prose_sources": [
            {
                "url": "https://essd.copernicus.org/articles/14/1581/2022/",
                "claim": "12 PFTs",
                "local_content_hash": None,
            },
            {
                "url": "https://doi.org/10.1594/PANGAEA.937075",
                "claim": "11 PFTs",
                "local_content_hash": None,
            },
        ],
        "admission": {
            "historical_full_study_input_identity": False,
            "pft_classification_resolved": False,
            "private_input_redistribution_rights_cleared": False,
            "whole_paper_reproduction": False,
            "independent_vegetation_accuracy": False,
        },
        "inputs": [
            {
                "owner": "private_author_store",
                "path": "snapshot-manifest.json",
                "sha256": SNAPSHOT_SHA,
            },
            *[
                _identity(repository / path, repository)
                for path in (
                    CUSTODY,
                    MAPPING,
                    ARCHIVE,
                    SOURCE_RECEIPT,
                    PARITY / "report.json",
                    PARITY / "512/run-manifest.json",
                    PARITY / "562/run-manifest.json",
                    *NATIVE,
                )
            ],
        ],
        "outputs": {
            name: {
                "bytes": (output / name).stat().st_size,
                "sha256": _sha((output / name).read_bytes()),
            }
            for name in ("method_crosswalk.csv", "example_inputs.csv")
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.private_root, args.output)


if __name__ == "__main__":
    main()
