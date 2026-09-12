"""Report/download identities remain exact and unsupported map rows are accounted."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.reporting.lra_products.api import (
    LRAPresentation,
    LRAPresentationRefusal,
    render_lra_report,
)

from .support import encoded, geometry_fixture, product_fixture, rebind, sha


def _render(
    root: Path, product: Path, geometry: dict[str, object], name: str = "report"
) -> LRAPresentation:
    path = root / f"{name}-geometry.json"
    path.write_bytes(encoded(geometry))
    return render_lra_report(
        product,
        expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        geometry_path=path,
        expected_geometry_sha256=sha(path.read_bytes()),
        destination=root / name,
    )


def test_report_preserves_native_values_nulls_source_locators_and_archive(
    tmp_path: Path,
) -> None:
    product, request = product_fixture(tmp_path)
    report = _render(tmp_path, product, geometry_fixture(product, request))
    manifest = json.loads((report.directory / "manifest.json").read_bytes())
    assert (
        sha((report.directory / "manifest.json").read_bytes()) == report.manifest_sha256
    )
    assert report.mapped_site_count == 2 and report.refused_site_count == 0
    assert manifest["counts"]["requested_sites"] == 2
    assert manifest["counts"]["missing_model_values"] == 3
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert manifest["capabilities"]["browser_acceptance"] is False
    assert all(
        sha((report.directory / p).read_bytes()) == h
        for p, h in manifest["files"].items()
    )
    rows = json.loads((report.directory / "model-estimates.json").read_bytes())
    assert len(rows) == 18
    regional = next(
        row
        for row in rows
        if row["role"] == "regional"
        and row["taxon"] == "Alnus"
        and row["statistic"] == "mean"
    )
    local = next(
        row
        for row in rows
        if row["role"] == "local"
        and row["taxon"] == "Alnus"
        and row["statistic"] == "mean"
    )
    assert (regional["native_value"], regional["native_unit"]) == ("0", "percent")
    assert (local["native_value"], local["native_unit"]) == ("0.25", "fraction")
    assert local["spatial_support"]["ring"] == request["rings"][0]
    assert (
        local["raw_evidence_id"] == "raw_snapshot" and local["sample_id"] == "local-1"
    )
    assert regional["source_locator"]["csv_row"] == 2
    layers = json.loads((report.directory / "model-layers.json").read_bytes())
    assert layers[0]["features"][0]["latitude"] == 0
    assert layers[0]["features"][0]["longitude"] == 0
    assert all(
        not layer["scientific_selection_enabled"] and not layer["circle_enabled"]
        for layer in layers
    )
    with zipfile.ZipFile(report.directory / "product.zip") as archive:
        expected = {
            p.relative_to(product).as_posix(): p.read_bytes()
            for p in product.rglob("*")
            if p.is_file()
        }
        assert {name: archive.read(name) for name in archive.namelist()} == expected
    html = (report.directory / "index.html").read_text()
    assert (
        html.startswith("<!doctype html>") and "not evaluated" in html and "N/A" in html
    )
    again = _render(tmp_path, product, geometry_fixture(product, request), "again")
    assert again.manifest_sha256 == report.manifest_sha256


@pytest.mark.parametrize(
    "case,reason",
    [
        ("missing", "missing_display_geometry"),
        ("unresolved", "unresolved_display_geometry"),
        ("source", "source_geography_not_admitted"),
        ("mixed_age", "mixed_age_types_not_comparable_in_map"),
        ("signed", "unsupported_signed_bp_map_chronology"),
        ("multimodal", "unsupported_multimodal_map_chronology"),
        ("outside_bin", "source_support_outside_declared_map_bin"),
        ("reversed", "invalid_map_chronology_bounds"),
    ],
)
def test_unsupported_map_rows_keep_all_estimates_and_input_lineage(
    tmp_path: Path, case: str, reason: str
) -> None:
    product, request = product_fixture(tmp_path)
    if case == "source":
        request["data_kind"] = "source_observations"
    if case == "mixed_age":
        request["local"]["samples"][0]["age_type"] = "calibrated_bp"
    if case in ("signed", "multimodal"):
        for role in ("regional", "local"):
            request[role]["samples"][0]["age_support_bp"] = (
                [[-50, -10]] if case == "signed" else [[5400, 5450], [5500, 5600]]
            )
        if case == "signed":
            request["temporal_matching"]["bins"][0].update(younger_bp=-50, older_bp=-10)
    if case in ("outside_bin", "reversed"):
        for role in ("regional", "local"):
            request[role]["samples"][0]["age_support_bp"] = (
                [[5300, 5600]] if case == "outside_bin" else [[5600, 5400]]
            )
    rebind(product, request)
    geometry = geometry_fixture(product, request)
    if case == "missing":
        geometry["sites"] = []
    if case == "unresolved":
        for site in geometry["sites"]:
            site.update(disposition="unresolved", position=None, basis="unresolved")
    result = _render(tmp_path, product, geometry)
    assert result.mapped_site_count == 0 and result.refused_site_count == 2
    assert not (result.directory / "map.html").exists()
    rows = json.loads((result.directory / "model-estimates.json").read_bytes())
    assert len(rows) == 18
    sites = json.loads((result.directory / "site-accounting.json").read_bytes())
    assert all(reason in row["reason_codes"] for row in sites)
    assert sum(len(row["model_row_ids"]) for row in sites) == len(rows)
    assert (result.directory / "product/request.json").read_bytes() == (
        product / "request.json"
    ).read_bytes()


def test_other_operation_keeps_every_numerical_csv_cell_with_profile_refusal(
    tmp_path: Path,
) -> None:
    product, request = product_fixture(tmp_path, operation="reveals")
    result = _render(tmp_path, product, geometry_fixture(product, request))
    assert result.mapped_site_count == 0 and result.refused_site_count == 1
    manifest = json.loads((result.directory / "manifest.json").read_bytes())
    assert (
        manifest["table_projection_status"]
        == "unsupported_operation_original_tables_retained"
    )
    assert manifest["counts"]["numerical_csv_files"] == 2
    assert manifest["counts"]["numerical_csv_data_rows"] == 3
    assert "100" in (result.directory / "index.html").read_text()


def test_existing_output_and_product_nested_destination_are_refused(
    tmp_path: Path,
) -> None:
    product, request = product_fixture(tmp_path)
    geometry = geometry_fixture(product, request)
    result = _render(tmp_path, product, geometry)
    before = (result.directory / "manifest.json").read_bytes()
    with pytest.raises(LRAPresentationRefusal, match="presentation_output_exists"):
        _render(tmp_path, product, geometry)
    assert (result.directory / "manifest.json").read_bytes() == before
    with pytest.raises(LRAPresentationRefusal, match="invalid_presentation_output"):
        render_lra_report(
            product,
            expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
            geometry_path=tmp_path / "report-geometry.json",
            expected_geometry_sha256=sha(encoded(geometry)),
            destination=product / "nested",
        )
