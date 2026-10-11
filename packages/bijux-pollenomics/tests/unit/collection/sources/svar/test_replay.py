"""Offline normalization, raw identity and publication refusal contracts."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from pyproj import CRS
import pytest

from bijux_pollenomics.collection.sources.svar.collection import (
    _parse_pos_list,
    replay_svar_data,
)
from bijux_pollenomics.collection.sources.svar.replay import replay_svar_capture

from .test_capture import fixture_capture, page


def test_offline_replay_is_exact_and_preserves_zero_null(tmp_path: Path) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source)
    with patch("socket.socket.connect", side_effect=AssertionError("offline")):
        first = replay_svar_data(source, tmp_path / "one", expected_sha256=digest)
        second = replay_svar_data(source, tmp_path / "two", expected_sha256=digest)
    assert first.lake_count == 2
    assert (
        first.normalized_lake_geojson_path.read_bytes()
        == second.normalized_lake_geojson_path.read_bytes()
    )
    feature = json.loads(first.normalized_lake_geojson_path.read_text())["features"][0]
    assert feature["properties"]["area_km2"] == 0
    assert feature["properties"]["water_surface_elevation_m"] is None
    native = feature["properties"]["source_native_properties"]
    assert native["AREA"] == [{"text": "0", "attributes": {}}]
    assert native["VYHOJD"] == []
    assert native["COUNTRY"] == []
    assert feature["properties"]["country"] == "SE"
    assert (tmp_path / "one/raw/wfs-capture/capture.json").read_bytes() == (
        source / "capture.json"
    ).read_bytes()


@pytest.mark.parametrize(
    "change", ["missing", "extra", "tamper", "receipt", "symlink", "wrong_digest"]
)
def test_capture_forgery_or_incomplete_inventory_refuses(
    tmp_path: Path, change: str
) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source)
    path = source / "page-000000000.xml"
    if change == "missing":
        path.unlink()
    elif change == "extra":
        (source / "extra.xml").write_bytes(b"unused")
    elif change == "tamper":
        path.write_bytes(page(("forged", "two")))
    elif change == "receipt":
        (source / "hits.xml.json").write_text("{}")
    elif change == "symlink":
        path.unlink()
        path.symlink_to(source / "hits.xml")
    else:
        digest = "0" * 64
    with pytest.raises((ValueError, FileNotFoundError)):
        list(replay_svar_capture(source, expected_sha256=digest))


def test_output_collision_preserves_owner(tmp_path: Path) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source)
    output = tmp_path / "owned"
    output.mkdir()
    (output / "owner").write_text("retained")
    with pytest.raises(FileExistsError):
        replay_svar_data(source, output, expected_sha256=digest)
    assert (output / "owner").read_text() == "retained"


def test_nested_dot_segment_output_refuses_before_capture_write(tmp_path: Path) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    with pytest.raises(ValueError, match="overlapping"):
        replay_svar_data(
            source, tmp_path / "bridge/../capture/nested", expected_sha256=digest
        )
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}


def test_native_crs_axis_order_is_explicit() -> None:
    assert [axis.direction for axis in CRS.from_epsg(3786).axis_info] == [
        "east",
        "north",
    ]
    assert [axis.direction for axis in CRS.from_epsg(3006).axis_info] == [
        "north",
        "east",
    ]
    a = _parse_pos_list("579976 7364709 579953 7364730")
    b = _parse_pos_list("7364709 579976 7364730 579953", source_crs="EPSG:3006")
    for legacy, exact in zip(a, b, strict=True):
        assert legacy == pytest.approx(exact, abs=5e-7)
    assert a[0] == pytest.approx([16.789, 66.390], abs=0.01)


def test_world_cylindrical_is_not_sweref_and_is_refused() -> None:
    assert CRS.from_epsg(3786).name == "World Equidistant Cylindrical (Sphere)"
    with pytest.raises(ValueError, match="unsupported_or_missing_crs"):
        _parse_pos_list("579976 7364709 579953 7364730", source_crs="EPSG:3786")


def test_mutation_of_already_yielded_page_is_not_silently_accepted(
    tmp_path: Path,
) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source, tuple(str(i) for i in range(251)))
    pages = replay_svar_capture(source, expected_sha256=digest)
    next(pages)
    (source / "page-000000000.xml").write_bytes(b"changed after consumption")
    with pytest.raises(ValueError, match="changed_during_replay"):
        list(pages)


def test_zero_capture_normalizes_without_scientific_admission(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.contracts.families.authority import (
        _svar_authority_state,
    )

    source = tmp_path / "capture"
    digest = fixture_capture(source, ())
    report = replay_svar_data(source, tmp_path / "data/svar", expected_sha256=digest)
    assert report.lake_count == 0
    assert json.loads(report.normalized_lake_geojson_path.read_text())["features"] == []
    assert _svar_authority_state(tmp_path / "data").status == "refused"


def test_actual_no_replace_race_retains_competing_directory(tmp_path: Path) -> None:
    from bijux_pollenomics.core.owned_tree import publish_new_output_tree

    source = tmp_path / "capture"
    digest = fixture_capture(source)
    final = tmp_path / "output"

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        if final_output_root == final:
            final.mkdir()
            (final / "owner").write_text("competing writer")
        publish_new_output_tree(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    with (
        patch(
            "bijux_pollenomics.collection.sources.svar.collection.publish_new_output_tree",
            side_effect=race,
        ),
        pytest.raises(FileExistsError),
    ):
        replay_svar_data(source, final, expected_sha256=digest)
    assert [p.name for p in final.iterdir()] == ["owner"]
    assert (final / "owner").read_text() == "competing writer"
    assert list(tmp_path.glob(".svar-replay-*"))


def test_public_collector_binds_captured_raw_and_replay(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.svar.collection import collect_svar_data

    with (
        patch(
            "bijux_pollenomics.collection.sources.svar.collection.capture_svar_wfs",
            side_effect=fixture_capture,
        ),
        patch("socket.socket.connect", side_effect=AssertionError("offline fixture")),
    ):
        report = collect_svar_data(tmp_path / "collected", {})
    manifest = json.loads(report.raw_manifest_path.read_text())
    repeated = replay_svar_data(
        tmp_path / "collected/raw/wfs-capture",
        tmp_path / "repeated",
        expected_sha256=manifest["capture_sha256"],
    )
    assert (
        report.normalized_lake_geojson_path.read_bytes()
        == repeated.normalized_lake_geojson_path.read_bytes()
    )
    assert report.summary_path.read_bytes() == repeated.summary_path.read_bytes()


def test_nonfinite_native_property_refuses_normalized_publication(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.svar.capture import capture_svar_wfs

    from .test_capture import hits

    source = tmp_path / "capture"

    def fetch(params: dict[str, str]) -> bytes:
        return (
            hits(1)
            if params.get("RESULTTYPE") == "hits"
            else page(("one",)).replace(b"<ms:AREA>0", b"<ms:AREA>NaN")
        )

    digest = capture_svar_wfs(source, fetch=fetch)
    with pytest.raises(ValueError):
        replay_svar_data(source, tmp_path / "output", expected_sha256=digest)
    assert not (tmp_path / "output").exists()
    assert (source / "capture.json").exists()


def test_collector_refuses_existing_family_before_acquisition(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.svar.collection import collect_svar_data

    output = tmp_path / "owned"
    output.mkdir()
    (output / "owner").write_text("prior source")
    with (
        patch("socket.socket.connect", side_effect=AssertionError("must not acquire")),
        pytest.raises(FileExistsError),
    ):
        collect_svar_data(output, {})
    assert (output / "owner").read_text() == "prior source"
    assert not (output / "raw").exists()


def test_normalized_dot_segments_do_not_bypass_symlink_refusal(tmp_path: Path) -> None:
    source = tmp_path / "capture"
    digest = fixture_capture(source)
    external = tmp_path / "other-owner"
    external.mkdir()
    (tmp_path / "link").symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        replay_svar_data(
            source, tmp_path / "absent/../link/output", expected_sha256=digest
        )
    assert not list(external.iterdir())


def test_huge_declared_count_refuses_before_count_sized_allocation(
    tmp_path: Path,
) -> None:
    from hashlib import sha256

    source = tmp_path / "capture"
    fixture_capture(source)
    manifest = json.loads((source / "capture.json").read_text())
    manifest["matched_count"] = 10**100
    content = json.dumps(manifest).encode()
    (source / "capture.json").write_bytes(content)
    with pytest.raises(ValueError, match="inventory_mismatch"):
        list(replay_svar_capture(source, expected_sha256=sha256(content).hexdigest()))


def test_admitted_normalized_coordinates_retain_full_transform_precision(
    tmp_path: Path,
) -> None:
    from pyproj import Transformer

    source = tmp_path / "capture"
    digest = fixture_capture(source)
    result = replay_svar_data(source, tmp_path / "output", expected_sha256=digest)
    feature = json.loads(result.normalized_lake_geojson_path.read_text())["features"][0]
    expected = Transformer.from_crs(
        "EPSG:3006", "OGC:CRS84", always_xy=False
    ).transform(7364709, 579976)
    assert feature["geometry"]["coordinates"][0][0] == list(expected)
    assert list(expected) != [round(v, 6) for v in expected]
    assert (
        json.loads(result.summary_path.read_text())["coordinate_precision"]
        == "unrounded_binary64"
    )


def test_xml_declared_encoding_survives_capture_and_replay(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.svar.capture import capture_svar_wfs

    from .test_capture import hits

    outputs = []
    for encoding in ("UTF-8", "ISO-8859-1"):
        content = (
            page(("lake-Å",))
            .decode("utf-8")
            .replace('encoding="UTF-8"', f'encoding="{encoding}"')
            .encode(encoding)
        )

        def fetch(params: dict[str, str], response: bytes = content) -> bytes:
            return hits(1) if params.get("RESULTTYPE") == "hits" else response

        capture = tmp_path / encoding
        digest = capture_svar_wfs(capture, fetch=fetch)
        result = replay_svar_data(
            capture, tmp_path / (encoding + "-normalized"), expected_sha256=digest
        )
        outputs.append(result.normalized_lake_geojson_path.read_bytes())
        assert (capture / "page-000000000.xml").read_bytes() == content
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0])["features"][0]["properties"]["record_id"] == "lake-Å"
