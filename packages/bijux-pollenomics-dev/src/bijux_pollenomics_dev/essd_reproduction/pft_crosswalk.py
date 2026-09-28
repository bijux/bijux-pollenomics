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
AUTHOR_CUSTODY = Path("docs/report/pollen-reconstruction/author-source-custody.json")
AUTHOR_TAXON_CROSSWALK = Path("reference/taxon-name-crosswalk.csv")
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
# The source table places all nine rows under TBS. These pairs disclose the
# taxon-name translation being tested; arithmetic alone cannot establish why
# the published output split them into two columns.
TBS_SOURCE_TO_OUTPUT = (
    ("Carpinus betulus", "Carpinus.betulus"),
    ("Carpinus orientalis", "Carpinus.orientalis"),
    ("Castanea sativa", "Castanea"),
    ("Corylus avellana", "Corylus.avellana"),
    ("Fagus sylvatica", "Fagus.sylvatica"),
    ("Fraxinus", "Fraxinus"),
    ("Quercus deciduous t.", "Quercus.deciduous"),
    ("Tilia", "Tilia"),
    ("Ulmus", "Ulmus"),
)
ISTS_OUTPUT_TAXA = ("Corylus.avellana", "Fraxinus", "Quercus.deciduous")
TBS_OUTPUT_TAXA = (
    "Carpinus.betulus",
    "Carpinus.orientalis",
    "Castanea",
    "Fagus.sylvatica",
    "Tilia",
    "Ulmus",
)
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


def _source_tbs_taxa(content: bytes) -> list[str]:
    """Read the nine TBS taxon rows from the pinned parameter table."""
    rows = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    current_pft = ""
    taxa: list[str] = []
    for row in rows:
        current_pft = row["PFT"] or current_pft
        if current_pft == "TBS":
            taxa.append(row["Plant taxa/Pollen-morphological types"])
    if taxa != [source for source, _ in TBS_SOURCE_TO_OUTPUT]:
        raise ValueError("PANGAEA parameter TBS taxon rows changed")
    return taxa


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


def _verified_sources(repository: Path) -> tuple[bytes, list[dict[str, object]]]:
    """Verify exact local source assets and their PANGAEA acquisition receipt."""
    inputs: list[dict[str, object]] = []
    mapping_content = b""
    for relative, expected in PINNED.items():
        path = repository / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"PANGAEA source input missing or linked: {relative}")
        data = path.read_bytes()
        if _sha(data) != expected:
            raise ValueError(f"PANGAEA source input changed: {relative}")
        if relative == MAPPING:
            mapping_content = data
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
    return mapping_content, inputs


def build_taxon_arithmetic(repository: Path, output: Path) -> dict[str, object]:
    """Check the archived ISTS/TBS mean split against nine source TBS rows."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    mapping_content, inputs = _verified_sources(repository)
    _source_mapping(mapping_content)
    source_taxa = _source_tbs_taxa(mapping_content)
    expected_output_taxa = {name for _, name in TBS_SOURCE_TO_OUTPUT}
    if set(ISTS_OUTPUT_TAXA) | set(TBS_OUTPUT_TAXA) != expected_output_taxa:
        raise ValueError("Published TBS split omits source taxon mapping")
    if set(ISTS_OUTPUT_TAXA) & set(TBS_OUTPUT_TAXA):
        raise ValueError("Published TBS split repeats an output taxon")
    maximum_residual = {"ISTS": 0.0, "TBS": 0.0, "ISTS_plus_TBS": 0.0}
    nonzero_rows = {"ISTS": 0, "TBS": 0}
    rows_checked = 0
    with zipfile.ZipFile(repository / ARCHIVE) as archive:
        members = _members(archive)
        header: list[str] | None = None
        for window in range(1, 26):
            header, rows = _records(archive, members["mean"][window], header)
            if not expected_output_taxa.issubset(header) or not {
                "ISTS",
                "TBS",
            }.issubset(header):
                raise ValueError("PANGAEA ISTS/TBS or taxon output columns changed")
            for row in rows:
                observed_ists, observed_tbs = _finite(row, "ISTS"), _finite(row, "TBS")
                calculated_ists = sum(_finite(row, name) for name in ISTS_OUTPUT_TAXA)
                calculated_tbs = sum(_finite(row, name) for name in TBS_OUTPUT_TAXA)
                residuals = {
                    "ISTS": abs(observed_ists - calculated_ists),
                    "TBS": abs(observed_tbs - calculated_tbs),
                    "ISTS_plus_TBS": abs(
                        observed_ists + observed_tbs - calculated_ists - calculated_tbs
                    ),
                }
                for code, residual in residuals.items():
                    maximum_residual[code] = max(maximum_residual[code], residual)
                    if residual > MEAN_SUM_ABS_TOLERANCE:
                        raise ValueError(
                            f"PANGAEA {code} taxon mean arithmetic differs"
                        )
                nonzero_rows["ISTS"] += observed_ists != 0.0
                nonzero_rows["TBS"] += observed_tbs != 0.0
                rows_checked += 1
    report: dict[str, object] = {
        "schema_version": "landclim-tbs-taxon-arithmetic.v1",
        "dataset_doi": "10.1594/PANGAEA.937075",
        "inputs": inputs,
        "parameter_table_tbs_taxa": source_taxa,
        "declared_source_to_output_taxa": [
            {"parameter_taxon": source, "output_column": output_name}
            for source, output_name in TBS_SOURCE_TO_OUTPUT
        ],
        "published_mean_addends": {
            "ISTS": list(ISTS_OUTPUT_TAXA),
            "TBS": list(TBS_OUTPUT_TAXA),
        },
        "mean_grid_window_rows_checked": rows_checked,
        "nonzero_mean_rows": nonzero_rows,
        "absolute_tolerance": MEAN_SUM_ABS_TOLERANCE,
        "maximum_absolute_mean_residual": maximum_residual,
        "standard_error_aggregation_admitted": False,
        "source_taxon_name_translation_authenticated": False,
        "ists_biological_definition_admitted": False,
        "paper_dataset_pft_count_reconciled": False,
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_author_name_review(
    repository: Path, author_source_root: Path, output: Path
) -> dict[str, object]:
    """Test exact parameter names against the custody-bound author crosswalk."""
    repository, author_source_root, output = (
        repository.resolve(),
        author_source_root.resolve(),
        output.resolve(),
    )
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    mapping_content, inputs = _verified_sources(repository)
    _source_tbs_taxa(mapping_content)
    custody_path = repository / AUTHOR_CUSTODY
    custody_content = custody_path.read_bytes()
    custody = json.loads(custody_content)
    manifest_path = author_source_root / custody["original_manifest_filename"]
    manifest_content = manifest_path.read_bytes()
    if _sha(manifest_content) != custody["original_manifest_sha256"]:
        raise ValueError("Private author source manifest digest mismatch")
    source_manifest = json.loads(manifest_content)
    crosswalk_path = author_source_root / AUTHOR_TAXON_CROSSWALK
    if crosswalk_path.is_symlink() or not crosswalk_path.is_file():
        raise ValueError("Private author taxon crosswalk missing or linked")
    crosswalk_content = crosswalk_path.read_bytes()
    expected = source_manifest["files"][AUTHOR_TAXON_CROSSWALK.as_posix()]
    if _sha(crosswalk_content) != expected:
        raise ValueError("Private author taxon crosswalk digest mismatch")
    author_rows = list(
        csv.DictReader(io.StringIO(crosswalk_content.decode("utf-8-sig")))
    )
    if len(author_rows) != 31 or any(
        set(row) != {"source", "prepared"} for row in author_rows
    ):
        raise ValueError("Private author taxon crosswalk shape changed")
    author_mapping = {row["source"]: row["prepared"] for row in author_rows}
    if (
        len(author_mapping) != len(author_rows)
        or len(set(author_mapping.values())) != 31
    ):
        raise ValueError("Private author taxon crosswalk identities are not unique")
    with zipfile.ZipFile(repository / ARCHIVE) as archive:
        members = _members(archive)
        header, _ = _records(archive, members["mean"][1], None)
    decisions = []
    for source_name, output_name in TBS_SOURCE_TO_OUTPUT:
        match = author_mapping.get(source_name) == output_name
        alternatives = sorted(
            name for name, prepared in author_mapping.items() if prepared == output_name
        )
        if output_name not in header:
            raise ValueError(f"Published taxon output absent: {output_name}")
        decisions.append(
            {
                "parameter_taxon": source_name,
                "published_output_column": output_name,
                "author_crosswalk_source_names_for_output": alternatives,
                "decision": (
                    "exact_author_source_name_and_output_match"
                    if match
                    else "parameter_name_absent_from_author_crosswalk"
                ),
            }
        )
    counts = Counter(row["decision"] for row in decisions)
    report: dict[str, object] = {
        "schema_version": "landclim-author-tbs-name-review.v1",
        "inputs": inputs
        + [
            {"path": AUTHOR_CUSTODY.as_posix(), "sha256": _sha(custody_content)},
            {
                "path": "private-author-snapshot-manifest",
                "sha256": _sha(manifest_content),
            },
            {
                "path": AUTHOR_TAXON_CROSSWALK.as_posix(),
                "bytes": len(crosswalk_content),
                "sha256": _sha(crosswalk_content),
                "custody": "private",
            },
        ],
        "author_crosswalk_rows": len(author_rows),
        "parameter_tbs_taxa_reviewed": len(decisions),
        "decision_counts": dict(sorted(counts.items())),
        "decisions": decisions,
        "historical_published_taxon_translation_admitted": False,
        "ists_biological_definition_admitted": False,
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


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
    mapping_content, inputs = _verified_sources(repository)
    columns, groups, windows, summary = reconcile(mapping_content, repository / ARCHIVE)
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
    parser.add_argument(
        "--taxon-arithmetic",
        action="store_true",
        help="check the published ISTS/TBS mean split",
    )
    parser.add_argument(
        "--author-name-review",
        action="store_true",
        help="compare source taxon names against the private author crosswalk",
    )
    parser.add_argument("--author-source-root", type=Path)
    args = parser.parse_args()
    if args.author_name_review:
        if args.taxon_arithmetic or args.author_source_root is None:
            parser.error("author name review requires only --author-source-root")
        build_author_name_review(args.repository, args.author_source_root, args.output)
    elif args.taxon_arithmetic:
        build_taxon_arithmetic(args.repository, args.output)
    else:
        build(args.repository, args.output)


if __name__ == "__main__":
    main()
