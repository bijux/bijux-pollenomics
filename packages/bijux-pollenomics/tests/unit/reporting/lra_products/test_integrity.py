"""Publication races, changed inputs and untrusted labels cannot corrupt reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.core.owned_tree import publish_new_output_tree
from bijux_pollenomics.reporting.lra_products import workflow
from bijux_pollenomics.reporting.lra_products.api import (
    LRAPresentationRefusal,
    TemporalProfile,
    render_lra_report,
)

from .support import encoded, geometry_fixture, product_fixture, rebind, sha


def test_noncooperating_output_writer_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, request = product_fixture(tmp_path)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    original = publish_new_output_tree
    destination = tmp_path / "report"

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "competing.txt").write_text("other writer")
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(workflow, "publish_new_output_tree", race)
    with pytest.raises(LRAPresentationRefusal, match="presentation_output_exists"):
        render_lra_report(
            product,
            expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
            geometry_path=geometry,
            expected_geometry_sha256=sha(geometry.read_bytes()),
            destination=destination,
        )
    assert (destination / "competing.txt").read_text() == "other writer"
    assert list(tmp_path.glob(".report.pending-*"))


@pytest.mark.parametrize(
    "change", ["geometry", "product", "duplicate_geometry", "wrong_expected"]
)
def test_changed_or_ambiguous_inputs_cannot_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    product, request = product_fixture(tmp_path)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    expected = sha(geometry.read_bytes())
    mutation_executed = False
    if change == "duplicate_geometry":
        geometry.write_bytes(
            geometry.read_bytes().rstrip()[:-1] + b',"crs":"OGC:CRS84"}\n'
        )
        expected = sha(geometry.read_bytes())
    elif change == "wrong_expected":
        expected = "0" * 64
    else:
        original = workflow._map

        def mutate(
            stage: Path,
            layers: list[dict[str, object]],
            native_view: dict[str, object],
            *,
            temporal_profile: TemporalProfile | None = None,
        ) -> str | None:
            nonlocal mutation_executed
            result = original(
                stage, layers, native_view, temporal_profile=temporal_profile
            )
            mutation_executed = True
            if change == "geometry":
                geometry.write_bytes(geometry.read_bytes() + b" ")
            else:
                (product / "request.json").write_bytes(
                    (product / "request.json").read_bytes() + b" "
                )
            return result

        monkeypatch.setattr(workflow, "_map", mutate)
    with pytest.raises(LRAPresentationRefusal):
        render_lra_report(
            product,
            expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
            geometry_path=geometry,
            expected_geometry_sha256=expected,
            destination=tmp_path / "report",
        )
    assert not (tmp_path / "report").exists()
    if change in {"geometry", "product"}:
        assert mutation_executed


def test_download_and_html_keep_source_text_without_script_execution(
    tmp_path: Path,
) -> None:
    product, request = product_fixture(tmp_path)
    geometry = tmp_path / "geometry.json"
    attack = '<script>alert("not executed")</script>'
    request["regional"]["samples"][0]["site_id"] = attack
    rebind(product, request)
    declared = geometry_fixture(product, request)
    declared["sites"][0]["source_locator"] = attack
    geometry.write_bytes(encoded(declared))
    result = render_lra_report(
        product,
        expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        geometry_path=geometry,
        expected_geometry_sha256=sha(geometry.read_bytes()),
        destination=tmp_path / "report",
    )
    assert (
        json.loads((result.directory / "display-geometry.json").read_bytes())
        == declared
    )
    assert (
        '<script>alert("not executed")</script>'
        not in (result.directory / "index.html").read_text()
    )


def test_saved_request_boolean_time_cannot_become_a_display_zero(
    tmp_path: Path,
) -> None:
    product, request = product_fixture(tmp_path)
    request["temporal_matching"]["bins"][0]["younger_bp"] = False
    rebind(product, request)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    with pytest.raises(LRAPresentationRefusal, match="invalid_lra_presentation"):
        render_lra_report(
            product,
            expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
            geometry_path=geometry,
            expected_geometry_sha256=sha(geometry.read_bytes()),
            destination=tmp_path / "report",
        )
    assert not (tmp_path / "report").exists()


@pytest.mark.parametrize("member", ["cover_unrecognized.csv", "unowned/cover_mean.csv"])
def test_unrecognized_cover_tables_remain_untyped(tmp_path: Path, member: str) -> None:
    product, request = product_fixture(tmp_path)
    extra = product / "numerical/local_love" / member
    extra.parent.mkdir(exist_ok=True)
    extra.write_text("index,Alnus,Betula\n100,25,75\n")
    rebind(product, request)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    result = render_lra_report(
        product,
        expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        geometry_path=geometry,
        expected_geometry_sha256=sha(geometry.read_bytes()),
        destination=tmp_path / "report",
    )
    rows = json.loads((result.directory / "model-estimates.json").read_bytes())
    tables = json.loads((result.directory / "numerical-tables.json").read_bytes())
    assert len(rows) == 18
    assert any(table["member"] == "numerical/local_love/" + member for table in tables)
    assert (
        result.directory / "product/numerical/local_love" / member
    ).read_bytes() == extra.read_bytes()


@pytest.mark.parametrize("alias", [False, True])
def test_dot_segments_cannot_contaminate_product(tmp_path: Path, alias: bool) -> None:
    product, request = product_fixture(tmp_path)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    bridge = tmp_path / "bridge"
    if alias:
        bridge.symlink_to(product, target_is_directory=True)
    else:
        bridge.mkdir()
    before = {
        p.relative_to(product): p.read_bytes()
        for p in product.rglob("*")
        if p.is_file()
    }
    with pytest.raises(LRAPresentationRefusal, match="invalid_presentation_output"):
        render_lra_report(
            product,
            expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
            geometry_path=geometry,
            expected_geometry_sha256=sha(geometry.read_bytes()),
            destination=bridge / ".." / "product" / "nested",
        )
    after = {
        p.relative_to(product): p.read_bytes()
        for p in product.rglob("*")
        if p.is_file()
    }
    assert before == after
    assert not list(product.glob(".*pending*"))


def test_signed_csv_preserves_support_objects_and_legacy_columns(
    tmp_path: Path,
) -> None:
    import csv

    from bijux_pollenomics.reporting.lra_products.downloads import write_downloads
    from bijux_pollenomics.reporting.lra_products.tables import (
        model_rows,
        numerical_tables,
    )

    product, request = product_fixture(tmp_path)
    for role in ("regional", "local"):
        request[role]["samples"][0]["age_support_bp"] = [[-0.5, 0.5]]
    request["temporal_matching"]["bins"][0].update(younger_bp=-1, older_bp=1)
    files = {
        p.relative_to(product).as_posix(): p.read_bytes()
        for p in product.rglob("*")
        if p.is_file()
    }
    tables = numerical_tables(files)
    legacy_rows = model_rows(tables, request, request_sha256="0" * 64)
    signed_rows = model_rows(
        tables,
        request,
        request_sha256="0" * 64,
        temporal_profile="calendar-bp1950-signed.v1",
    )
    for name, rows in (
        ("legacy-download", legacy_rows),
        ("signed-download", signed_rows),
    ):
        stage = tmp_path / name
        stage.mkdir()
        write_downloads(stage, files, rows, tables, [])
    with (tmp_path / "legacy-download/model-estimates.csv").open(newline="") as stream:
        legacy = list(csv.DictReader(stream))
    with (tmp_path / "signed-download/model-estimates.csv").open(newline="") as stream:
        signed = list(csv.DictReader(stream))
    for original, extended in zip(legacy, signed, strict=True):
        assert {k: v for k, v in extended.items() if k in original} == original
        source = json.loads(extended["source_calendar_support"])
        declared = json.loads(extended["declared_calendar_support"])
        assert source["younger_bp"] == -0.5 and declared["younger_bp"] == -1
        assert source["profile"] == declared["profile"] == "calendar-bp1950-signed.v1"
        assert source["axis"] == declared["axis"] == "BP1950"
