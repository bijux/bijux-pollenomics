"""Preserve exact original-product bytes and source-addressable table downloads."""

from __future__ import annotations

import csv
import io
from pathlib import Path, PurePosixPath
from typing import Any
import zipfile

from ...analysis.lra.api import read_lra_product
from .contracts import bound_bytes, canonical, digest


def capture_product(
    directory: Path, expected: str
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Bind every copied member to the verified inventory, then check it again."""
    bound_bytes(directory / "manifest.json", expected)
    verified = read_lra_product(directory, expected_manifest_sha256=expected)
    manifest = verified.manifest()
    inventory = {**manifest["files"], "manifest.json": expected}
    contents = {}
    for member, sha256 in sorted(inventory.items()):
        relative = PurePosixPath(member)
        if relative.is_absolute() or ".." in relative.parts or "\\" in member:
            raise ValueError("Unsafe product member")
        contents[member] = bound_bytes(directory / member, sha256)
    read_lra_product(directory, expected_manifest_sha256=expected)
    return manifest, contents


def write_downloads(
    stage: Path,
    product: dict[str, bytes],
    rows: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> dict[str, str]:
    """Write original product, deterministic archive and lossless JSON/CSV tables."""
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
            raise ValueError("Original-product archive identity differs")
    for filename, payload in (
        ("model-estimates.json", rows),
        ("numerical-tables.json", tables),
        ("input-pollen.json", observations),
    ):
        (stage / filename).write_bytes(canonical(payload))
    fields: tuple[str, ...] = (
        "row_id",
        "role",
        "site_id",
        "sample_id",
        "bin_id",
        "taxon",
        "statistic",
        "native_value",
        "native_unit",
        "missing_reason",
        "source_locator",
        "source_member_sha256",
        "age_type",
        "age_support_bp",
        "declared_bin",
        "spatial_support",
    )
    if rows and "source_calendar_support" in rows[0]:
        fields += ("source_calendar_support", "declared_calendar_support")
    csv_stream = io.StringIO(newline="")
    writer = csv.writer(csv_stream, lineterminator="\n")
    writer.writerow(fields)
    for row in rows:
        writer.writerow(
            [
                canonical(row[field]).decode().rstrip("\n")
                if isinstance(row[field], (dict, list))
                else row[field]
                for field in fields
            ]
        )
    (stage / "model-estimates.csv").write_text(csv_stream.getvalue(), newline="")
    return {
        path.relative_to(stage).as_posix(): digest(path.read_bytes())
        for path in sorted(stage.rglob("*"))
        if path.is_file()
    }
