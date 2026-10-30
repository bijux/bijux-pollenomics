"""Reconcile archived LegacyAge run inputs without selecting or fitting ages."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
import csv
from decimal import ROUND_FLOOR, Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

ARCHIVE_SHA256 = "f3b326c67572896ba08bebaabb55bf921e4f34a8a304b9a88ed9d74e867f467f"
SCRIPT_SHA256 = "6059a0b23199c3a86e7d9ab2b8fcd7bc5a28404cf6078392551ad11df8276e21"
S4_SHA256 = "943d6151d05cfc47df65b5a3ccedc683393fe6e8e24d14733ba7c58dcd071bb2"
PANGAEA_TABLES = {
    "S1": (
        "table-s1-chronological-controls.csv",
        "b35b8e3d4110efcb24714d7ccecf025ccd96c31de1b94bb279c9cb7ec0c40b08",
    ),
    "S3": (
        "table-s3-bacon-parameters.csv",
        "ae87f1cd145eddf630b84fc4e77b3b4f62508a6bea869faccadb19911faa8c41",
    ),
}
MEMBERS = {
    "S1": "Table S1_Chronological control points metadata.csv",
    "S3": "Table S3_Bacon parameter settings.csv",
    "S4": "Table S4_Original chronology metadata by pollen records.csv",
}
CORES = {
    "19913": "ABBO",
    "20034": "DALMUT",
    "4445": "SOLSOE81",
    "4446": "SOLSOE83",
    "52082": "LAIH",
    "53995": "BUS",
    "54001": "BOKE",
}
Row = dict[str, str]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selected_rows(rows: Iterable[Row]) -> tuple[int, dict[str, list[Row]]]:
    selected: dict[str, list[Row]] = {key: [] for key in CORES}
    count = 0
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("LegacyAge row has a different field population")
        if "Dataset_ID" not in row:
            raise ValueError("LegacyAge table has no native dataset identity")
        count += 1
        if row["Dataset_ID"] in selected:
            selected[row["Dataset_ID"]].append(row)
    return count, selected


def _depth_rows(rows: list[Row]) -> dict[Decimal, Row]:
    keyed: dict[Decimal, Row] = {}
    for row in rows:
        depth = Decimal(row["Depth_Pollen"])
        if not depth.is_finite() or depth in keyed:
            raise ValueError("LegacyAge pollen depth is nonfinite or repeated")
        keyed[depth] = row
    return keyed


def compare_original_rows(archived: list[Row], retained: list[Row]) -> dict[str, Any]:
    """Compare native tokens and exact numeric cells on an identical depth axis."""
    left, right = _depth_rows(archived), _depth_rows(retained)
    if left.keys() != right.keys():
        raise ValueError("LegacyAge S4 versions have different pollen depth axes")
    changes: Counter[str] = Counter()
    numeric: Counter[str] = Counter()
    gaps: dict[str, Decimal] = {}
    examples: dict[str, dict[str, str]] = {}
    memberships: list[dict[str, object]] = []
    for depth, row in left.items():
        other = right[depth]
        if row.keys() != other.keys():
            raise ValueError("LegacyAge S4 versions have different field axes")
        for name, value in row.items():
            if value == other[name]:
                continue
            changes[name] += 1
            examples.setdefault(
                name,
                {
                    "depth_token": row["Depth_Pollen"],
                    "archived": value,
                    "retained": other[name],
                },
            )
            if name.startswith(("Estimated_Age_", "Estimated.age_Error_")):
                if value in {"NA", ""} or other[name] in {"NA", ""}:
                    raise ValueError(
                        "LegacyAge S4 age missingness differs between versions"
                    )
                try:
                    difference = abs(Decimal(value) - Decimal(other[name]))
                except InvalidOperation as error:
                    raise ValueError("LegacyAge S4 age value is not numeric") from error
                if not difference.is_finite():
                    raise ValueError("LegacyAge S4 age value is nonfinite")
                if difference:
                    numeric[name] += 1
                gaps[name] = max(gaps.get(name, Decimal(0)), difference)
                type_field = name.replace("Estimated_Age_", "Original_Age.type_")
                if (
                    name.startswith("Estimated_Age_")
                    and row.get(type_field) == "Calibrated radiocarbon years BP"
                    and other.get(type_field) == row[type_field]
                ):
                    # Follow the original R's x1000 transform and the existing
                    # half-open 500-year bins; signed source ages stay signed.
                    a_bin = int(
                        (Decimal(value) * 2).to_integral_value(rounding=ROUND_FLOOR)
                    )
                    b_bin = int(
                        (Decimal(other[name]) * 2).to_integral_value(
                            rounding=ROUND_FLOOR
                        )
                    )
                    if a_bin != b_bin:
                        memberships.append(
                            {
                                "depth_token": row["Depth_Pollen"],
                                "age_field": name,
                                "age_type": row[type_field],
                                "archived_token": value,
                                "retained_token": other[name],
                                "archived_bin_index": a_bin,
                                "retained_bin_index": b_bin,
                            }
                        )
    return {
        "matched_depths": len(left),
        "literal_different_cells_by_field": dict(sorted(changes.items())),
        "numerically_different_age_cells_by_field": dict(sorted(numeric.items())),
        "maximum_absolute_age_difference_native_units": {
            key: str(value) for key, value in sorted(gaps.items())
        },
        "first_different_cell_by_field": dict(sorted(examples.items())),
        "calibrated_source_token_500_year_bin_changes": memberships,
        "age_types": sorted(
            {
                row[key]
                for row in archived
                for key in row
                if key.startswith("Original_Age.type_") and row[key] not in {"NA", ""}
            }
        ),
    }


def _control_rows(rows: list[Row]) -> dict[tuple[str, Decimal], Row]:
    keyed: dict[tuple[str, Decimal], Row] = {}
    for row in rows:
        try:
            depth = Decimal(row["Depth (cm)"])
        except InvalidOperation as error:
            raise ValueError("LegacyAge control depth is not numeric") from error
        key = row["Laboratory_Label"], depth
        if not depth.is_finite() or key in keyed:
            raise ValueError(
                "LegacyAge control lab/depth identity is nonfinite or repeated"
            )
        keyed[key] = row
    return keyed


def _r_control_numbers(row: Row) -> tuple[Decimal, Decimal]:
    try:
        age = Decimal(row["Age_Uncalibrated (kyr BP)"])
        older = Decimal(row["Dating Error_Older (kyr)"])
        younger = Decimal(row["Dating Error_Younger (kyr)"])
    except InvalidOperation as error:
        raise ValueError("missing_or_nonnumeric_control_age_or_error") from error
    if not all(value.is_finite() for value in (age, older, younger)):
        raise ValueError("nonfinite_control_age_or_error")
    if older < 0 or younger < 0:
        raise ValueError("negative_control_error")
    return age * 1000, (older + younger) * 500


def compare_control_rows(archived: list[Row], pangaea: list[Row]) -> dict[str, Any]:
    """Retain unmatched controls and compare the R's literal pre-calibration numbers."""
    left, right = _control_rows(archived), _control_rows(pangaea)
    changes: Counter[str] = Counter()
    compared: list[dict[str, Any]] = []
    for key in sorted(left.keys() & right.keys()):
        a, b = left[key], right[key]
        if a.keys() != b.keys():
            raise ValueError("LegacyAge S1 versions have different field axes")
        changes.update(name for name in a if a[name] != b[name])
        record: dict[str, Any] = {
            "laboratory_label": key[0],
            "depth_cm_token": a["Depth (cm)"],
        }
        if (
            a["Dating_Method"] != "Carbon-14"
            or b["Dating_Method"] != a["Dating_Method"]
        ):
            record.update(
                status="not_compared",
                reason="outside_matched_radiocarbon_type",
                archived_method=a["Dating_Method"],
                pangaea_method=b["Dating_Method"],
            )
        else:
            try:
                a_age, a_error = _r_control_numbers(a)
                b_age, b_error = _r_control_numbers(b)
            except ValueError as error:
                record.update(status="refused", reason=str(error))
            else:
                record.update(
                    status="compared",
                    archived_age_years=str(a_age),
                    pangaea_age_years=str(b_age),
                    archived_error_argument_years=str(a_error),
                    pangaea_error_argument_years=str(b_error),
                    age_difference_years=str(b_age - a_age),
                    error_argument_difference_years=str(b_error - a_error),
                )
        compared.append(record)
    return {
        "archived_controls": len(left),
        "pangaea_controls": len(right),
        "matched_controls": len(compared),
        "archived_only_identities": [
            {"laboratory_label": lab, "depth_cm": str(depth)}
            for lab, depth in sorted(left.keys() - right.keys())
        ],
        "pangaea_only_identities": [
            {"laboratory_label": lab, "depth_cm": str(depth)}
            for lab, depth in sorted(right.keys() - left.keys())
        ],
        "literal_different_cells_by_field": dict(sorted(changes.items())),
        "numeric_population": dict(
            sorted(Counter(row["status"] for row in compared).items())
        ),
        "precalibration_numeric_comparisons": compared,
    }


def _parameter_comparison(archived: list[Row], pangaea: list[Row]) -> dict[str, Any]:
    if len(archived) > 1 or len(pangaea) > 1:
        raise ValueError("LegacyAge core has competing parameter rows")
    if not archived or not pangaea:
        return {
            "archived_rows": len(archived),
            "pangaea_rows": len(pangaea),
            "nonmissing_tokens_equal": None,
            "literal_differences": None,
        }
    a, b = archived[0], pangaea[0]
    if a.keys() != b.keys():
        raise ValueError("LegacyAge S3 versions have different field axes")
    return {
        "archived_rows": 1,
        "pangaea_rows": 1,
        "nonmissing_tokens_equal": {k: v for k, v in a.items() if v not in {"NA", ""}}
        == {k: v for k, v in b.items() if v not in {"NA", ""}},
        "literal_differences": {
            k: {"archived": a[k], "pangaea": b[k]} for k in a if a[k] != b[k]
        },
    }


def inspect_inputs(source: Path, retained_s4: Path) -> dict[str, Any]:
    """Bind the exact published archive, script and already retained S4 release."""
    archive = source / "input-metadata-tables.zip"
    script = source / "R-script_bacon_age-depth_modelling_LegacyAge1_0.R"
    pins = {
        "zenodo_input_archive": (archive, ARCHIVE_SHA256),
        "zenodo_r_script": (script, SCRIPT_SHA256),
        "pangaea_s4": (retained_s4, S4_SHA256),
        **{
            f"pangaea_{name.lower()}": (retained_s4.parent / filename, digest)
            for name, (filename, digest) in PANGAEA_TABLES.items()
        },
    }
    for name, (path, expected) in pins.items():
        if _digest(path) != expected:
            raise ValueError(f"LegacyAge {name} bytes differ from source identity")
    tables: dict[str, dict[str, list[Row]]] = {}
    population: dict[str, int] = {}
    with ZipFile(archive) as zipped:
        infos = zipped.infolist()
        if len(infos) != len(MEMBERS) or {item.filename for item in infos} != set(
            MEMBERS.values()
        ):
            raise ValueError("LegacyAge archive member population differs")
        if any(item.flag_bits & 1 or item.file_size > 70_000_000 for item in infos):
            raise ValueError(
                "LegacyAge archive member is encrypted or exceeds its bound"
            )
        for table, member in MEMBERS.items():
            # The pinned Windows CSV bytes contain characters invalid in UTF-8.
            with (
                zipped.open(member) as stream,
                io.TextIOWrapper(stream, encoding="cp1252", newline="") as text,
            ):
                population[table], tables[table] = _selected_rows(
                    csv.DictReader(text, delimiter=";")
                )
    with retained_s4.open(encoding="utf-8", newline="") as retained_stream:
        retained_count, retained = _selected_rows(
            csv.DictReader(retained_stream, delimiter="\t")
        )
    pangaea_tables: dict[str, dict[str, list[Row]]] = {}
    pangaea_population: dict[str, int] = {}
    for table, (filename, _) in PANGAEA_TABLES.items():
        with (retained_s4.parent / filename).open(
            encoding="utf-8", newline=""
        ) as pangaea_stream:
            pangaea_population[table], pangaea_tables[table] = _selected_rows(
                csv.DictReader(pangaea_stream, delimiter="\t")
            )
    cores: dict[str, Any] = {}
    for dataset, core in CORES.items():
        parameters = tables["S3"][dataset]
        if len(parameters) > 1:
            raise ValueError("LegacyAge core has competing parameter rows")
        controls = tables["S1"][dataset]
        cores[core] = {
            "dataset_id": int(dataset),
            "source_control_rows": len(controls),
            "source_control_methods": dict(
                sorted(Counter(row["Dating_Method"] for row in controls).items())
            ),
            "native_nonmissing_parameter_tokens": {
                key: value
                for key, value in parameters[0].items()
                if value not in {"NA", ""}
            }
            if parameters
            else None,
            "s4_comparison": compare_original_rows(
                tables["S4"][dataset], retained[dataset]
            ),
            "s1_comparison": compare_control_rows(
                controls, pangaea_tables["S1"][dataset]
            ),
            "s3_comparison": _parameter_comparison(
                parameters, pangaea_tables["S3"][dataset]
            ),
            "run_input_state": "retained_source_metadata"
            if parameters
            else "not_in_these_source_tables",
        }
    return {
        "schema_version": "legacyage-run-input-reconciliation.v1",
        "source_doi": "10.5281/zenodo.5815192",
        "license": "CC-BY-4.0",
        "input_sha256": {name: expected for name, (_, expected) in pins.items()},
        "archive_rows_by_table": population,
        "retained_pangaea_s4_rows": retained_count,
        "pangaea_rows_by_table": pangaea_population,
        "cores": cores,
        "producer_scope": {
            "control_numeric_sensitivity": "For matched literal Carbon-14 controls only, preserve age*1000 and (older_error+younger_error)*500 from the R script before curve selection, missing-error defaults or calibration. This arithmetic does not infer a sampling law, chronology posterior or realized Bacon model.",
            "source_token_sensitivity": "Use the source R's x1000 age transformation and existing half-open [500*k, 500*(k+1)) BP bins; preserve negative indices. This compares original-source tokens without selecting a chronology or admitting a study sample.",
            "archived_script_default_dataset_ids": [47502, 4320],
            "script_input_route": "Live tab-delimited PANGAEA URLs for S1, S3 and S4; not the archived semicolon-delimited members.",
            "script_version_limit": "Pinned R source, no pinned rbacon/IntCal dependency versions or random seed; not an authenticated historical executable or realized chronology.",
        },
        "limits": {
            "age_model_calls": 0,
            "posterior_draws_acquired": 0,
            "lra_samples_admitted": 0,
            "interpretation": "Source inputs and literal precision differences only. No chronology selection, calibration, posterior, historical LandClim production identity, dated basin, taxon/PPE decision or independent scientific acceptance follows.",
        },
    }


def main() -> int:
    """Write one bounded source-input reconciliation from retained originals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--retained-s4", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = inspect_inputs(args.source, args.retained_s4)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
