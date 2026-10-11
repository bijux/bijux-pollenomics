"""Exact retained bytes and deterministic long-form downloads."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import zipfile

from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan
from bijux_pollenomics.reporting.lra_products.joint.downloads import (
    capture_joint_product,
    write_joint_downloads,
)
from bijux_pollenomics.reporting.lra_products.joint.projection import (
    project_joint_product,
)

from .support import joint_fixture


def test_downloads_preserve_product_and_full_ordered_tables(tmp_path: Path) -> None:
    product, checksum = joint_fixture(tmp_path / "fixture")
    manifest, files = capture_joint_product(product, checksum)
    projection = project_joint_product(
        manifest,
        JointLRAPlan(files["plan.json"].decode("utf-8")).payload(),
        product_manifest_sha256=checksum,
    )
    stage = tmp_path / "downloads"
    stage.mkdir()
    write_joint_downloads(stage, files, projection)
    assert {
        path.relative_to(stage / "product").as_posix(): path.read_bytes()
        for path in (stage / "product").rglob("*")
        if path.is_file()
    } == files
    with zipfile.ZipFile(stage / "product.zip") as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == files
    summary = json.loads((stage / "joint-summary.json").read_bytes())
    assert summary["product_manifest_sha256"] == checksum
    with (stage / "means.csv").open(encoding="utf-8", newline="") as stream:
        means = list(csv.DictReader(stream))
    with (stage / "covariance.csv").open(encoding="utf-8", newline="") as stream:
        covariance = list(csv.DictReader(stream))
    with (stage / "draw-bin-ledger.csv").open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(means) == 4 and len(covariance) == 16 and len(ledger) == 4
    assert {(row["row_index"], row["column_index"]) for row in covariance} == {
        (str(row), str(column)) for row in range(4) for column in range(4)
    }
    assert any(float(row["value"]) < 0 for row in covariance)
    assert all(row["mass_numerator"] == "1" for row in ledger)
    assert all(row["mass_denominator"] == "4" for row in ledger)


def test_incomplete_downloads_keep_empty_moments_and_partitioned_mass(
    tmp_path: Path,
) -> None:
    product, checksum = joint_fixture(tmp_path / "fixture", state="refused")
    manifest, files = capture_joint_product(product, checksum)
    projection = project_joint_product(
        manifest,
        JointLRAPlan(files["plan.json"].decode("utf-8")).payload(),
        product_manifest_sha256=checksum,
    )
    stage = tmp_path / "downloads"
    stage.mkdir()
    write_joint_downloads(stage, files, projection)
    assert len((stage / "means.csv").read_text().splitlines()) == 1
    assert len((stage / "covariance.csv").read_text().splitlines()) == 1
    with (stage / "bin-accounting.csv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["requested_count"] == "4" and row["refused_count"] == "1"
    assert row["refused_mass_numerator"] == "1"
    assert row["refused_mass_denominator"] == "4"
