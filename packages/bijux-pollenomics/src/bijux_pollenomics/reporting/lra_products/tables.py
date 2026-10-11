"""Lossless CSV inventory and native-unit paired reconstruction row projection."""

from __future__ import annotations

import csv
import io
from pathlib import PurePosixPath
from typing import Any

from .contracts import (
    TemporalProfile,
    calendar_supports,
    canonical,
    digest,
    validate_temporal_profile,
)


def numerical_tables(files: dict[str, bytes]) -> list[dict[str, Any]]:
    """Retain all numerical CSV cells, including auxiliary/unsupported profiles."""
    tables = []
    for member, encoded in sorted(files.items()):
        if not member.startswith("numerical/") or not member.endswith(".csv"):
            continue
        rows = list(csv.reader(io.StringIO(encoded.decode("utf-8")), strict=True))
        if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows[1:]):
            raise ValueError(f"Malformed numerical CSV: {member}")
        tables.append(
            {
                "member": member,
                "sha256": digest(encoded),
                "header": rows[0],
                "rows": rows[1:],
                "data_row_count": len(rows) - 1,
                "cell_count": sum(len(row) for row in rows[1:]),
                "unit_posture": "source table; units require its result contract",
            }
        )
    return tables


def model_rows(
    tables: list[dict[str, Any]],
    request: dict[str, Any],
    *,
    request_sha256: str,
    temporal_profile: TemporalProfile | None = None,
) -> list[dict[str, Any]]:
    """Project paired estimates without rounding, imputing or converting units.

    Other operations retain complete numerical tables and the original product;
    their typed presentation and map profile have an explicit refusal.
    """
    validate_temporal_profile(temporal_profile)
    supports = calendar_supports(request) if temporal_profile is not None else {}
    if request["operation"] != "lra":
        return []
    bins = {row["bin_id"]: row for row in request["temporal_matching"]["bins"]}
    projected = []
    for table in tables:
        member = table["member"]
        name = PurePosixPath(member).name
        regional = member == "numerical/regional_reveals/reconstruction.csv"
        local = member in {
            f"numerical/local_love/cover_{statistic}.csv"
            for statistic in ("mean", "sd", "q10", "q90")
        }
        if not regional and not local:
            continue
        role = "regional" if regional else "local"
        samples = request[role]["samples"]
        if len(samples) != 1:
            raise ValueError("Paired presentation requires one request sample per role")
        sample = samples[0]
        for index, cells in enumerate(table["rows"]):
            support = {
                "basin": request[role]["basin"],
                "kind": "regional_basin_context",
            }
            if local:
                support = {
                    "kind": "local_radial_support_not_geographic_tessellation",
                    "basin": request[role]["basin"],
                    "ring_index": index,
                    "ring": request["rings"][index],
                }
            for taxon in request["taxa"]:
                statistics = (
                    ("mean", "median", "q90", "q10", "sd")
                    if regional
                    else (name.removeprefix("cover_").removesuffix(".csv"),)
                )
                for statistic in statistics:
                    column = f"{taxon}.{statistic}" if regional else taxon
                    position = table["header"].index(column)
                    text = cells[position]
                    locator = {"member": member, "csv_row": index + 2, "column": column}
                    row = {
                        "row_id": "lra-estimate:"
                        + digest(
                            canonical(
                                {
                                    "request_sha256": request_sha256,
                                    "source_member_sha256": table["sha256"],
                                    **locator,
                                }
                            )
                        ),
                        "role": role,
                        "site_id": sample["site_id"],
                        "sample_id": sample["sample_id"],
                        "bin_id": sample["bin_id"],
                        "pairing_coordinate": sample["coordinate"],
                        "age_type": sample["age_type"],
                        "age_support_bp": sample["age_support_bp"],
                        "declared_bin": bins[sample["bin_id"]],
                        "taxon": taxon,
                        "statistic": statistic,
                        "native_value": text if text != "" else None,
                        "value_encoding": "original_csv_decimal_text_or_null",
                        "native_unit": "percent" if regional else "fraction",
                        "missing_reason": "source_statistic_unavailable"
                        if text == ""
                        else None,
                        "source_locator": locator,
                        "source_member_sha256": table["sha256"],
                        "raw_evidence_id": sample["raw_evidence_id"],
                        "chronology_evidence_id": sample["chronology_evidence_id"],
                        "spatial_support": support,
                    }
                    if temporal_profile is not None:
                        source, declared = supports[role]
                        row["source_calendar_support"] = dict(source)
                        row["declared_calendar_support"] = dict(declared)
                    projected.append(row)
    return sorted(projected, key=lambda row: row["row_id"])


def input_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Retain each input count with exact sample/taxon/source identities."""
    return [
        {
            "role": role,
            **{key: value for key, value in sample.items() if key != "counts"},
            "taxon": taxon,
            "native_count": count,
            "native_unit": request["pollen_unit"],
            "data_kind": request["data_kind"],
            "evidence_role": "input_pollen",
        }
        for role in ("regional", "local")
        if role in request
        for sample in request[role]["samples"]
        for taxon, count in zip(request["taxa"], sample["counts"], strict=True)
    ]
