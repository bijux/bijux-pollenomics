"""Exact retained-product capture and deterministic joint downloads."""

from __future__ import annotations

import csv
import io
from pathlib import Path, PurePosixPath
from typing import Any
import zipfile

from ....analysis.lra.uncertainty.api import read_joint_lra_ensemble
from ..contracts import bound_bytes, canonical, digest


def capture_joint_product(
    directory: Path, expected: str
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Capture every reader-admitted byte, then recheck the source closure."""
    bound_bytes(directory / "manifest.json", expected)
    verified = read_joint_lra_ensemble(directory, expected_manifest_sha256=expected)
    manifest = verified.manifest()
    inventory = {**manifest["files"], "manifest.json": expected}
    contents: dict[str, bytes] = {}
    for member, sha256 in sorted(inventory.items()):
        relative = PurePosixPath(member)
        if relative.is_absolute() or ".." in relative.parts or "\\" in member:
            raise ValueError("Unsafe joint-product member")
        contents[member] = bound_bytes(directory / member, sha256)
    read_joint_lra_ensemble(directory, expected_manifest_sha256=expected)
    return manifest, contents


def _cell(value: object) -> object:
    if isinstance(value, (dict, list)):
        return canonical(value).decode("utf-8").rstrip("\n")
    if value is None:
        return ""
    return value


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(fields)
    for row in rows:
        writer.writerow([_cell(row[field]) for field in fields])
    path.write_text(stream.getvalue(), encoding="utf-8", newline="")


def write_joint_downloads(
    stage: Path, product: dict[str, bytes], projection: dict[str, Any]
) -> None:
    """Write exact originals plus lossless long-form generated projections."""
    for member, value in sorted(product.items()):
        path = stage / "product" / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    archive = stage / "product.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as stream:
        for member, value in sorted(product.items()):
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            stream.writestr(info, value)
    with zipfile.ZipFile(archive) as stream:
        if stream.namelist() != sorted(product) or any(
            stream.read(member) != value for member, value in product.items()
        ):
            raise ValueError("Joint-product archive identity differs")
    (stage / "joint-summary.json").write_bytes(canonical(projection))
    _write_csv(
        stage / "means.csv",
        (
            "bin_id",
            "coordinate_index",
            "role",
            "taxon",
            "ring_mean_m",
            "source_unit",
            "conversion",
            "unit",
            "value",
            "source_pointer",
            "source_member_sha256",
        ),
        [
            {
                **row,
                "role": row["coordinate"]["role"],
                "taxon": row["coordinate"]["taxon"],
                "ring_mean_m": row["coordinate"]["ring_mean_m"],
                "source_unit": row["coordinate"]["source_unit"],
                "conversion": row["coordinate"]["conversion"],
            }
            for row in projection["means"]
        ],
    )
    _write_csv(
        stage / "covariance.csv",
        (
            "bin_id",
            "row_index",
            "column_index",
            "row_role",
            "row_taxon",
            "row_ring_mean_m",
            "column_role",
            "column_taxon",
            "column_ring_mean_m",
            "value",
            "unit",
            "source_pointer",
            "source_member_sha256",
        ),
        [
            {
                **row,
                "row_role": row["row_coordinate"]["role"],
                "row_taxon": row["row_coordinate"]["taxon"],
                "row_ring_mean_m": row["row_coordinate"]["ring_mean_m"],
                "column_role": row["column_coordinate"]["role"],
                "column_taxon": row["column_coordinate"]["taxon"],
                "column_ring_mean_m": row["column_coordinate"]["ring_mean_m"],
            }
            for row in projection["covariance"]
        ],
    )
    _write_csv(
        stage / "draw-bin-ledger.csv",
        (
            "row_index",
            "row_id",
            "draw_id",
            "bin_id",
            "mass_numerator",
            "mass_denominator",
            "selected_samples",
            "status",
            "reason_code",
            "diagnostic",
            "child",
            "child_request_sha256",
            "child_manifest_sha256",
            "child_scientific_content_sha256",
            "source_pointer",
            "source_member_sha256",
            "source_row_sha256",
        ),
        [
            {
                **row,
                "mass_numerator": row["mass"]["numerator"],
                "mass_denominator": row["mass"]["denominator"],
            }
            for row in projection["draw_bin_ledger"]
        ],
    )
    accounting_rows: list[dict[str, Any]] = []
    for row in projection["bins"]:
        accounting_rows.append(
            {
                **row,
                **{
                    f"{status}_count": row["counts"][status]
                    for status in ("requested", "successful", "refused", "not_run")
                },
                **{
                    f"{status}_mass_numerator": row["masses"][status]["numerator"]
                    for status in (
                        "requested",
                        "successful",
                        "refused",
                        "not_run",
                        "combined_unsuccessful",
                    )
                },
                **{
                    f"{status}_mass_denominator": row["masses"][status]["denominator"]
                    for status in (
                        "requested",
                        "successful",
                        "refused",
                        "not_run",
                        "combined_unsuccessful",
                    )
                },
            }
        )
    _write_csv(
        stage / "bin-accounting.csv",
        (
            "bin_index",
            "bin_id",
            "younger_bp",
            "older_bp",
            "membership",
            "stationarity",
            "complete",
            "requested_count",
            "successful_count",
            "refused_count",
            "not_run_count",
            "requested_mass_numerator",
            "requested_mass_denominator",
            "successful_mass_numerator",
            "successful_mass_denominator",
            "refused_mass_numerator",
            "refused_mass_denominator",
            "not_run_mass_numerator",
            "not_run_mass_denominator",
            "combined_unsuccessful_mass_numerator",
            "combined_unsuccessful_mass_denominator",
            "source_pointer",
            "plan_source_pointer",
            "source_member_sha256",
            "plan_sha256",
        ),
        accounting_rows,
    )


def generated_hashes(stage: Path) -> dict[str, str]:
    return {
        path.relative_to(stage).as_posix(): digest(path.read_bytes())
        for path in sorted(stage.rglob("*"))
        if path.is_file()
    }


__all__ = ["capture_joint_product", "generated_hashes", "write_joint_downloads"]
