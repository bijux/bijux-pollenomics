"""Draw-fed LOVE reports retain saved tables without inventing a regional site."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch
import zipfile

import pytest

from bijux_pollenomics.analysis.lra import publication_draws
from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.execution import regional_draw_love
from bijux_pollenomics.analysis.lra.outputs.contracts import request_metadata
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
from bijux_pollenomics.cli import main
from bijux_pollenomics.reporting.lra_products import workflow
from bijux_pollenomics.reporting.lra_products.api import LRAPresentationRefusal
from bijux_pollenomics_lra import api as engine_api

from ...analysis.lra.support import regional_draw_love_fixture
from ...analysis.lra.test_publication_draws import _bundle, _pin
from .support import encoded, geometry_fixture, sha


@pytest.fixture
def saved_product(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[Path, dict[str, Any]]:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path, bundle=bundle, checksums_sha256=_pin(bundle)
    )
    binding = EngineBinding(
        "bijux-pollenomics-lra", "0.2.0", "python-numpy-scipy", engine_api
    )
    for owner in (regional_draw_love, publication_draws):
        monkeypatch.setattr(owner, "load_engine", lambda **_: binding)
    request = tmp_path / "request.json"
    request.write_bytes(encoded(payload))
    product = tmp_path / "product"
    assert (
        main(
            [
                "run-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(product),
            ]
        )
        == 0
    )
    capsys.readouterr()
    return product, payload


def render_arguments(root: Path, product: Path, request: dict[str, Any]) -> list[str]:
    geometry = root / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    return [
        "render-lra-report",
        str(product),
        "--expected-manifest-sha256",
        sha((product / "manifest.json").read_bytes()),
        "--geometry",
        str(geometry),
        "--expected-geometry-sha256",
        sha(geometry.read_bytes()),
        "--output",
        str(root / "report"),
    ]


def test_actual_cli_product_renders_lossless_tables_downloads_and_explicit_map_refusal(
    tmp_path: Path,
    saved_product: tuple[Path, dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    product, request = saved_product
    original = {
        path.relative_to(product).as_posix(): path.read_bytes()
        for path in product.rglob("*")
        if path.is_file()
    }
    with (
        patch.object(engine_api, "run_love_from_regional_draws") as compute,
        patch.object(regional_draw_love, "load_engine") as engine,
        patch.object(publication_draws, "load_engine") as source_engine,
        patch.object(workflow, "write_static_map_document") as map_writer,
    ):
        assert main(render_arguments(tmp_path, product, request)) == 0
    for operation in (compute, engine, source_engine, map_writer):
        operation.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    report = tmp_path / "report"
    assert result["mapped_site_count"] == 0 and result["refused_site_count"] == 1
    manifest = json.loads((report / "manifest.json").read_bytes())
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert (
        manifest["table_projection_status"]
        == "unsupported_operation_original_tables_retained"
    )
    assert manifest["counts"]["model_rows"] == 0
    assert manifest["counts"]["input_pollen_rows"] == 3
    assert not (report / "map.html").exists()
    assert json.loads((report / "model-estimates.json").read_bytes()) == []
    assert json.loads((report / "model-layers.json").read_bytes()) == []
    with zipfile.ZipFile(report / "product.zip") as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == original
    assert {
        path.relative_to(report / "product").as_posix(): path.read_bytes()
        for path in (report / "product").rglob("*")
        if path.is_file()
    } == original
    reopened = read_lra_product(
        report / "product", expected_manifest_sha256=result["product_manifest_sha256"]
    ).manifest()
    assert reopened["units"]["regional_cover_draws"] == "fraction"
    assert "regional_cover" not in reopened["units"]
    assert reopened["uncertainty_omissions"] == request["uncertainty_omissions"]
    native = json.loads((report / "native-view.json").read_bytes())
    assert native["rows"] == []
    assert len(native["sites"]) == 1 and native["sites"][0]["role"] == "local"
    assert "unsupported_map_operation" in native["sites"][0]["reason_codes"]
    assert native["method"]["configuration"] == request["configuration"]
    assert native["method"]["configuration"]["love"]["seed"] == 7
    assert native["uncertainty_omissions"] == request["uncertainty_omissions"]
    pollen = json.loads((report / "input-pollen.json").read_bytes())
    assert {row["role"] for row in pollen} == {"local"}
    assert [row["native_count"] for row in pollen] == [40, 30, 30]
    for table in json.loads((report / "numerical-tables.json").read_bytes()):
        raw = list(csv.reader(io.StringIO(original[table["member"]].decode())))
        assert table["header"] == raw[0] and table["rows"] == raw[1:]
    html = (report / "index.html").read_text()
    assert "supplied regional-cover draws in fractions" in html
    assert "not measured regional pollen" in html
    assert "typed estimate rows and a geographic map are unavailable" in html
    assert "REVEALS cover: percent" not in html
    assert all(
        sha((report / name).read_bytes()) == value
        for name, value in manifest["files"].items()
    )


def test_signed_opt_in_refuses_before_staging_the_local_only_product(
    tmp_path: Path,
    saved_product: tuple[Path, dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    product, request = saved_product
    arguments = render_arguments(tmp_path, product, request)
    assert main([*arguments, "--temporal-profile", "calendar-bp1950-signed.v1"]) == 2
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "unsupported_signed_calendar_request"
    )
    assert not (tmp_path / "report").exists()
    assert not list(tmp_path.glob(".report.pending-*"))


@pytest.mark.parametrize(
    "change", ["unknown_schema", "missing_draw_binding", "regional_placeholder"]
)
def test_self_consistent_saved_request_still_requires_the_exact_supported_schema(
    tmp_path: Path,
    saved_product: tuple[Path, dict[str, Any]],
    change: str,
) -> None:
    product, request = saved_product
    if change == "unknown_schema":
        request["schema_version"] = "unknown.v1"
    elif change == "missing_draw_binding":
        del request["regional_draw_source"]
    else:
        request["regional"] = request["local"]
    # Rebind internal consistency deliberately; the report must still reject
    # a caller-pinned product whose request violates the supported schema.
    encoded_request = encoded(request)
    (product / "request.json").write_bytes(encoded_request)
    manifest = json.loads((product / "manifest.json").read_bytes())
    manifest.update(
        request_metadata(request), request_sha256=sha(encoded_request.rstrip(b"\n"))
    )
    manifest["files"]["request.json"] = sha(encoded_request)
    manifest["scientific_identity"]["request_sha256"] = manifest["request_sha256"]
    manifest["scientific_content_sha256"] = sha(
        encoded(manifest["scientific_identity"])
    )
    (product / "manifest.json").write_bytes(encoded(manifest))
    read_lra_product(product, expected_manifest_sha256=sha(encoded(manifest)))
    arguments = render_arguments(tmp_path, product, request)
    with pytest.raises(LRAPresentationRefusal, match="invalid_lra_presentation"):
        workflow.render_lra_report(
            product,
            expected_manifest_sha256=arguments[3],
            geometry_path=tmp_path / "geometry.json",
            expected_geometry_sha256=arguments[7],
            destination=tmp_path / "report",
        )
    assert not (tmp_path / "report").exists()
    assert not list(tmp_path.glob(".report.pending-*"))


def test_product_tamper_is_refused_without_reconstruction_or_report(
    tmp_path: Path,
    saved_product: tuple[Path, dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    product, request = saved_product
    arguments = render_arguments(tmp_path, product, request)
    member = product / "numerical/cover_mean.csv"
    member.write_bytes(member.read_bytes() + b"changed\n")
    assert main(arguments) == 2
    assert (
        json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_presentation"
    )
    assert not (tmp_path / "report").exists()
