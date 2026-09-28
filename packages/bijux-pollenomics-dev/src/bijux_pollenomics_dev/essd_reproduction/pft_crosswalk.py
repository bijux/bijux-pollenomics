"""Retain PANGAEA 937075 column identities and bounded LCT arithmetic."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import cast
import zipfile

MAPPING = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")
ARCHIVE = Path("data/landclim/raw/landclim_ii_reveals_results.zip")
SOURCE_RECEIPT = Path("data/landclim/raw/landclim_sources.json")
PINNED = {
    MAPPING: "32eac151566b41c186745dd077fabcddde06f64f9a3a2056699e88dbabd76d4d",
    ARCHIVE: "c585f0691ad95342b8aba083b90fe91dc398f985b6b7fbc19561299389c4fb86",
    SOURCE_RECEIPT: "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677",
}
MEAN_SUM_ABS_TOLERANCE = 1e-9
SOURCE_GROUPS = {
    "ET": ("TBE1", "TBE2", "IBE", "MTBE", "TSE", "MTSE"),
    "ST": ("IBS", "TBS", "TSD"),
    "OL": ("LSE", "GL", "AL"),
}
OBSERVED_MEAN_GROUPS = {
    "ET": SOURCE_GROUPS["ET"],
    "ST": ("IBS", "ISTS", "TBS", "TSD"),
    "OL": SOURCE_GROUPS["OL"],
}
COLUMN_FIELDS = (
    "column_kind",
    "code",
    "output_position",
    "parameter_table_present",
    "parameter_definition",
    "parameter_lct_code",
    "mean_files_present",
    "se_files_present",
    "admission",
)
GROUP_FIELDS = (
    "lct_code",
    "parameter_table_pft_codes",
    "observed_mean_addends",
    "additional_output_code",
    "mean_rows_checked",
    "maximum_absolute_mean_residual",
    "se_naive_sum_disagreement_rows",
    "admission",
)
WINDOW_FIELDS = (
    "window",
    "grid_rows",
    "mean_se_grid_ids_equal",
    "et_max_absolute_residual",
    "st_max_absolute_residual",
    "ol_max_absolute_residual",
    "et_se_naive_sum_disagreement_rows",
    "st_se_naive_sum_disagreement_rows",
    "ol_se_naive_sum_disagreement_rows",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_mapping(
    content: bytes,
) -> tuple[list[str], dict[str, str], dict[str, tuple[str, ...]]]:
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    if len(rows) != 31:
        raise ValueError("PANGAEA parameter taxon count changed")
    current_lct = ""
    current_pft = ""
    codes: list[str] = []
    definitions: dict[str, str] = {}
    grouped: dict[str, list[str]] = {code: [] for code in SOURCE_GROUPS}
    for row in rows:
        if row["Land-cover types (LCTs)"]:
            match = re.search(r"\(([A-Z]{2})\)$", row["Land-cover types (LCTs)"])
            if match is None:
                raise ValueError("PANGAEA source LCT label changed")
            current_lct = match.group(1)
        if row["PFT"]:
            current_pft = row["PFT"]
            if current_pft in definitions:
                raise ValueError("Repeated PANGAEA parameter PFT code")
            codes.append(current_pft)
            definitions[current_pft] = row["PFT definition"]
            grouped[current_lct].append(current_pft)
        if not row["Plant taxa/Pollen-morphological types"] or not current_pft:
            raise ValueError("PANGAEA parameter taxon lacks a source PFT")
    groups = {code: tuple(members) for code, members in grouped.items()}
    if groups != SOURCE_GROUPS or len(codes) != 12 or len(set(codes)) != 12:
        raise ValueError("PANGAEA source PFT/LCT grouping changed")
    return codes, definitions, groups


def _members(archive: zipfile.ZipFile) -> dict[str, dict[int, str]]:
    result: dict[str, dict[int, str]] = {"mean": {}, "se": {}}
    for name in archive.namelist():
        match = re.fullmatch(
            r"LANDCLIMII\.RV\.(means|standarderrors)\.JUN2021/TW(\d+)\.RV\."
            r"(estimates|standarderrors)\.jun21\.csv",
            name,
        )
        if match is None:
            raise ValueError(f"Unexpected PANGAEA archive member: {name}")
        kind = "mean" if match.group(1) == "means" else "se"
        if (kind == "mean") != (match.group(3) == "estimates"):
            raise ValueError("PANGAEA mean/SE archive member roles conflict")
        number = int(match.group(2))
        if number in result[kind]:
            raise ValueError("Duplicate PANGAEA time window")
        result[kind][number] = name
    if any(set(members) != set(range(1, 26)) for members in result.values()):
        raise ValueError("PANGAEA 25-window mean/SE archive incomplete")
    return result


def _records(
    archive: zipfile.ZipFile, name: str, expected_header: list[str] | None
) -> tuple[list[str], list[dict[str, str]]]:
    with archive.open(name) as stream:
        reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
        header = list(reader.fieldnames or [])
        if len(header) != 50 or len(set(header)) != 50:
            raise ValueError("PANGAEA output header changed")
        if expected_header is not None and header != expected_header:
            raise ValueError("PANGAEA mean/SE output headers diverge")
        rows = cast(list[dict[str, str]], list(reader))
    if len(rows) != 420 or any(None in row for row in rows):
        raise ValueError("PANGAEA grid/window row width or denominator changed")
    ids = [row["LCGRID_ID"] for row in rows]
    if len(set(ids)) != 420 or any(not site_id for site_id in ids):
        raise ValueError("PANGAEA grid IDs are incomplete or duplicated")
    return header, rows


def _finite(row: dict[str, str], code: str) -> float:
    value = float(row[code])
    if not math.isfinite(value):
        raise ValueError(f"PANGAEA output has nonfinite {code}")
    return value


def reconcile(
    mapping_content: bytes, archive_path: Path
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    """Compare every source column and every published mean/SE grid row."""
    codes, definitions, source_groups = _source_mapping(mapping_content)
    windows: list[dict[str, object]] = []
    max_residual = {code: 0.0 for code in SOURCE_GROUPS}
    se_disagreements: Counter[str] = Counter()
    with zipfile.ZipFile(archive_path) as archive:
        members = _members(archive)
        header: list[str] | None = None
        for window in range(1, 26):
            header, means = _records(archive, members["mean"][window], header)
            _, errors = _records(archive, members["se"][window], header)
            mean_ids = {row["LCGRID_ID"] for row in means}
            error_ids = {row["LCGRID_ID"] for row in errors}
            if mean_ids != error_ids:
                raise ValueError("PANGAEA mean/SE grid identity mismatch")
            local_max = {code: 0.0 for code in SOURCE_GROUPS}
            local_disagreement: Counter[str] = Counter()
            for row in means:
                for lct, addends in OBSERVED_MEAN_GROUPS.items():
                    residual = abs(
                        _finite(row, lct) - sum(_finite(row, code) for code in addends)
                    )
                    local_max[lct] = max(local_max[lct], residual)
                    if residual > MEAN_SUM_ABS_TOLERANCE:
                        raise ValueError(f"PANGAEA {lct} mean arithmetic differs")
            for row in errors:
                for lct, addends in OBSERVED_MEAN_GROUPS.items():
                    difference = abs(
                        _finite(row, lct) - sum(_finite(row, code) for code in addends)
                    )
                    if difference > MEAN_SUM_ABS_TOLERANCE:
                        local_disagreement[lct] += 1
            for lct in SOURCE_GROUPS:
                max_residual[lct] = max(max_residual[lct], local_max[lct])
                se_disagreements[lct] += local_disagreement[lct]
            windows.append(
                {
                    "window": window,
                    "grid_rows": len(means),
                    "mean_se_grid_ids_equal": "true",
                    "et_max_absolute_residual": local_max["ET"],
                    "st_max_absolute_residual": local_max["ST"],
                    "ol_max_absolute_residual": local_max["OL"],
                    "et_se_naive_sum_disagreement_rows": local_disagreement["ET"],
                    "st_se_naive_sum_disagreement_rows": local_disagreement["ST"],
                    "ol_se_naive_sum_disagreement_rows": local_disagreement["OL"],
                }
            )
    if (
        header is None
        or header[:3] != ["LCGRID_ID", "lonDD", "latDD"]
        or header[-3:] != ["ET", "ST", "OL"]
    ):
        raise ValueError("PANGAEA source axes changed")
    output_pfts = header[34:-3]
    if (
        len(header[3:34]) != 31
        or len(output_pfts) != 13
        or set(output_pfts) - set(codes) != {"ISTS"}
    ):
        raise ValueError("PANGAEA PFT output/parameter mismatch changed")
    columns: list[dict[str, object]] = []
    for position, code in enumerate(output_pfts, start=35):
        lct = next(
            (key for key, members in source_groups.items() if code in members), ""
        )
        columns.append(
            {
                "column_kind": "PFT_position",
                "code": code,
                "output_position": position,
                "parameter_table_present": str(code in definitions).lower(),
                "parameter_definition": definitions.get(code, ""),
                "parameter_lct_code": lct,
                "mean_files_present": 25,
                "se_files_present": 25,
                "admission": "source_code_identity_only"
                if code in definitions
                else "unmapped_output_code_refused",
            }
        )
    for position, code in enumerate(header[-3:], start=48):
        columns.append(
            {
                "column_kind": "LCT_position",
                "code": code,
                "output_position": position,
                "parameter_table_present": "true",
                "parameter_definition": "",
                "parameter_lct_code": code,
                "mean_files_present": 25,
                "se_files_present": 25,
                "admission": "source_lct_code_and_observed_mean_arithmetic",
            }
        )
    groups: list[dict[str, object]] = [
        {
            "lct_code": lct,
            "parameter_table_pft_codes": ";".join(source_groups[lct]),
            "observed_mean_addends": ";".join(OBSERVED_MEAN_GROUPS[lct]),
            "additional_output_code": "ISTS" if lct == "ST" else "",
            "mean_rows_checked": 10500,
            "maximum_absolute_mean_residual": max_residual[lct],
            "se_naive_sum_disagreement_rows": se_disagreements[lct],
            "admission": "version_specific_output_mean_identity_only",
        }
        for lct in ("ET", "ST", "OL")
    ]
    summary: dict[str, object] = {
        "source_parameter_pft_codes": codes,
        "output_pft_position_codes": output_pfts,
        "unmapped_output_codes": ["ISTS"],
        "mean_files": 25,
        "se_files": 25,
        "rows_per_file": 420,
        "mean_grid_window_rows": 10500,
        "se_grid_window_rows": 10500,
        "declared_mean_sum_absolute_tolerance": MEAN_SUM_ABS_TOLERANCE,
        "maximum_mean_residual_by_lct": max_residual,
        "se_naive_sum_disagreement_rows_by_lct": dict(se_disagreements),
        "pft_taxon_definition_admitted_for_ists": False,
        "lct_standard_error_aggregation_admitted": False,
        "paper_dataset_pft_count_reconciled": False,
    }
    return columns, groups, windows, summary


def build(repository: Path, output: Path) -> dict[str, object]:
    """Write a deterministic, source-hash-bound column and arithmetic review."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    inputs: list[dict[str, object]] = []
    for relative, expected in PINNED.items():
        path = repository / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"PANGAEA source input missing or linked: {relative}")
        data = path.read_bytes()
        if _sha(data) != expected:
            raise ValueError(f"PANGAEA source input changed: {relative}")
        inputs.append(
            {"path": relative.as_posix(), "bytes": len(data), "sha256": expected}
        )
    receipt = json.loads((repository / SOURCE_RECEIPT).read_text())
    if not any(
        dataset["dataset_id"] == "937075"
        and dataset["doi"] == "https://doi.org/10.1594/PANGAEA.937075"
        and MAPPING.name in dataset["files"]
        and ARCHIVE.name in dataset["files"]
        for dataset in receipt["datasets"]
    ):
        raise ValueError("PANGAEA 937075 asset receipt changed")
    columns, groups, windows, summary = reconcile(
        (repository / MAPPING).read_bytes(), repository / ARCHIVE
    )
    output.mkdir(parents=True)
    for name, fields, records in (
        ("columns.csv", COLUMN_FIELDS, columns),
        ("lct_groups.csv", GROUP_FIELDS, groups),
        ("windows.csv", WINDOW_FIELDS, windows),
    ):
        with (output / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    report: dict[str, object] = {
        "schema_version": "landclim-pft-crosswalk.v1",
        "dataset_doi": "10.1594/PANGAEA.937075",
        "evidence_scope": "source_parameter_codes_and_complete_published_output_axes_and_mean_arithmetic",
        "inputs": inputs,
        "summary": summary,
        "publisher_prose_claims": {
            "paper_pft_count": 12,
            "pangaea_description_pft_count": 11,
            "prose_byte_identity": "not_retained_in_this_review",
        },
        "outputs": {
            name: {
                "bytes": (output / name).stat().st_size,
                "sha256": _sha((output / name).read_bytes()),
            }
            for name in ("columns.csv", "lct_groups.csv", "windows.csv")
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
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
