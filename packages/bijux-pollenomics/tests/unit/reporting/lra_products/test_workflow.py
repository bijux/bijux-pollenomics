"""Report/download identities remain exact and unsupported map rows are accounted."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.reporting.lra_products.api import (
    LRAPresentation,
    LRAPresentationRefusal,
    TemporalProfile,
    render_lra_report,
)

from .support import encoded, geometry_fixture, product_fixture, rebind, sha


def _render(
    root: Path,
    product: Path,
    geometry: dict[str, object],
    name: str = "report",
    *,
    temporal_profile: TemporalProfile | None = None,
) -> LRAPresentation:
    path = root / f"{name}-geometry.json"
    path.write_bytes(encoded(geometry))
    return render_lra_report(
        product,
        expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        geometry_path=path,
        expected_geometry_sha256=sha(path.read_bytes()),
        destination=root / name,
        temporal_profile=temporal_profile,
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
    assert "linked map offers native" in html
    assert "are unavailable in this report profile" not in html
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


@pytest.mark.parametrize(
    "case",
    [
        "calibrated",
        "radiocarbon",
        "source",
        "multimodal",
        "multiple_bins",
        "outside",
        "missing",
        "unsafe_integer",
    ],
)
def test_signed_opt_in_refuses_unsupported_chronology_before_staging(
    tmp_path: Path, case: str
) -> None:
    product, request = product_fixture(tmp_path)
    sample = request["local"]["samples"][0]
    if case in ("calibrated", "radiocarbon"):
        sample["age_type"] = case + "_bp"
    elif case == "source":
        request["data_kind"] = "source_observations"
    elif case == "multimodal":
        sample["age_support_bp"] = [[5400, 5450], [5500, 5550]]
    elif case == "multiple_bins":
        request["temporal_matching"]["bins"].append(
            {"bin_id": "other", "younger_bp": 5000, "older_bp": 5300}
        )
    elif case == "outside":
        sample["age_support_bp"] = [[0, 1]]
    elif case == "missing":
        sample["age_support_bp"] = [[None, None]]
    elif case == "unsafe_integer":
        sample["age_support_bp"] = [[2**53, 2**53]]
    rebind(product, request)
    with pytest.raises(LRAPresentationRefusal):
        _render(
            tmp_path,
            product,
            geometry_fixture(product, request),
            temporal_profile="calendar-bp1950-signed.v1",
        )
    assert not (tmp_path / "report").exists()
    assert not list(tmp_path.glob(".report.pending-*"))


def test_signed_rows_preserve_fractional_source_and_separate_declared_support(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.lra_products.contracts import calendar_supports
    from bijux_pollenomics.reporting.lra_products.tables import (
        model_rows,
        numerical_tables,
    )

    product, request = product_fixture(tmp_path)
    for role in ("regional", "local"):
        request[role]["samples"][0]["age_support_bp"] = [[-50.5, -49.5]]
    request["temporal_matching"]["bins"][0].update(younger_bp=-50.75, older_bp=-49.25)
    files = {
        p.relative_to(product).as_posix(): p.read_bytes()
        for p in product.rglob("*")
        if p.is_file()
    }
    tables = numerical_tables(files)
    legacy = model_rows(tables, request, request_sha256="0" * 64)
    rows = model_rows(
        tables,
        request,
        request_sha256="0" * 64,
        temporal_profile="calendar-bp1950-signed.v1",
    )
    assert len(rows) == len(legacy) == 18
    for row, original in zip(rows, legacy, strict=True):
        assert {
            k: v
            for k, v in row.items()
            if k not in {"source_calendar_support", "declared_calendar_support"}
        } == original
        source, declared = calendar_supports(request)[row["role"]]
        assert row["source_calendar_support"] == source
        assert row["declared_calendar_support"] == declared
        assert source["younger_bp"] == -50.5 and declared["younger_bp"] == -50.75
        assert source["native_calendar_label"] is None
        assert source["calibration_evidence"] is None


@pytest.mark.parametrize("endpoints", [(-50.5, -49.5), (-0.5, 0.5), (0, 0)])
def test_signed_report_uses_complete_static_transport_and_bound_support(
    tmp_path: Path, endpoints: tuple[float, float]
) -> None:
    product, request = product_fixture(tmp_path)
    for role in ("regional", "local"):
        request[role]["samples"][0]["age_support_bp"] = [list(endpoints)]
    request["temporal_matching"]["bins"][0].update(
        younger_bp=endpoints[0], older_bp=endpoints[1]
    )
    rebind(product, request)
    report = _render(
        tmp_path,
        product,
        geometry_fixture(product, request),
        temporal_profile="calendar-bp1950-signed.v1",
    )
    manifest = json.loads((report.directory / "manifest.json").read_bytes())
    view = json.loads((report.directory / "native-view.json").read_bytes())
    assert manifest["schema_version"] == "lra-presentation.v2"
    assert view["schema_version"] == "lra-atlas-view.v2"
    assert (
        manifest["temporal_profile"]
        == view["temporal_profile"]
        == "calendar-bp1950-signed.v1"
    )
    assert view["temporal_axis"] == "BP1950"
    assert report.mapped_site_count == 2
    assert manifest["map_build_id"]
    html = (report.directory / "map.html").read_text()
    bootstrap = json.loads(
        html.split('<script id="atlas-static-bootstrap" type="application/json">', 1)[
            1
        ].split("</script>", 1)[0]
    )
    assert bootstrap["schema_version"] == "atlas-static-bootstrap.v3"
    assert bootstrap["load_strategy"] == "selection_aware_static_scripts"
    assert bootstrap["assets"]["schema_version"] == "atlas-static-asset-table.v4"
    assert bootstrap["native_view_sha256"] == manifest["native_view_sha256"]
    assert all(
        row["source_calendar_support"]["younger_bp"] == endpoints[0]
        for row in view["rows"]
    )
    assert sum(row["native_value"] is None for row in view["rows"]) == 3


@pytest.mark.parametrize("profile", [True, {}, [], 123, "unknown"])
def test_unknown_profile_refuses_before_any_missing_input_read(
    tmp_path: Path, profile: object
) -> None:
    from typing import cast

    with pytest.raises(LRAPresentationRefusal, match="unsupported_temporal_profile"):
        render_lra_report(
            tmp_path / "missing-product",
            expected_manifest_sha256="0" * 64,
            geometry_path=tmp_path / "missing-geometry.json",
            expected_geometry_sha256="0" * 64,
            destination=tmp_path / "report",
            temporal_profile=cast(TemporalProfile, profile),
        )
    assert not (tmp_path / "report").exists()
