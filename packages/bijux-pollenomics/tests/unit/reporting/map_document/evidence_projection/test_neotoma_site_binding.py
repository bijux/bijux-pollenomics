"""Opt-in Neotoma site joins require a pinned, geographically matching source."""

import copy
import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma_site_binding import (
    read_bound_neotoma_manifest,
    validate_neotoma_site_binding,
)
from tests.support.neotoma import country_decisions, download_row


def fixture(tmp_path: Path) -> tuple[Path, str, dict[str, Any]]:
    row = download_row()
    snapshot = build_neotoma_relational_snapshot(
        [row],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([row]),
    )
    root = tmp_path / "relational"
    materialize_neotoma_relational_snapshot(root, snapshot, rows_per_part=1)
    pin = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    return root, pin, cast(list[dict[str, Any]], snapshot["sites"])[0]


def test_validated_site_matches_geo_country_and_name(tmp_path: Path) -> None:
    root, pin, site = fixture(tmp_path)
    assert read_bound_neotoma_manifest(root, pin)["source_family"] == "neotoma"
    point = {
        "evidence_row_id": "20",
        "longitude": 1.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    validate_neotoma_site_binding(point, site)
    for key, value in [
        ("longitude", 2.0),
        ("latitude", 2.0),
        ("country", "Norway"),
        ("title", "wrong"),
        ("latitude", True),
        ("evidence_row_id", "21"),
    ]:
        altered = {**point, key: value}
        with pytest.raises(ValueError):
            validate_neotoma_site_binding(altered, site)
    invalid = copy.deepcopy(site)
    invalid["source_payload"]["geography"] = "bad"
    with pytest.raises(ValueError):
        validate_neotoma_site_binding(point, invalid)
    with pytest.raises(ValueError):
        read_bound_neotoma_manifest(root, "0" * 64)


def test_polygon_geometry_uses_source_representative_point(tmp_path: Path) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.country.site_geometry import (
        neotoma_site_representative_point,
    )

    _, _, site = fixture(tmp_path)
    site = copy.deepcopy(site)
    site["source_payload"]["geography"] = json.dumps(
        {"type": "Polygon", "coordinates": [[[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]}
    )
    xy = neotoma_site_representative_point(site["source_payload"])
    assert xy is not None
    point = {
        "evidence_row_id": "20",
        "longitude": xy[0],
        "latitude": xy[1],
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    validate_neotoma_site_binding(point, site)
    for bad in [None, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            validate_neotoma_site_binding({**point, "latitude": bad}, site)


def test_pinned_manifest_cannot_be_paired_with_a_different_validated_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        neotoma_site_binding as binding,
    )

    root, pin, _ = fixture(tmp_path)
    from bijux_pollenomics.evidence.sources.neotoma import (
        read_validated_neotoma_relational_manifest,
    )

    actual = read_validated_neotoma_relational_manifest(root)
    monkeypatch.setattr(
        binding,
        "read_validated_neotoma_relational_manifest",
        lambda _: {**actual, "build_id": "sha256:" + "d" * 64},
    )
    with pytest.raises(ValueError, match="validated manifest"):
        binding.read_bound_neotoma_manifest(root, pin)


def test_actual_projection_enforces_bound_site_with_legacy_compatibility(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
        _project_neotoma,
    )

    (tmp_path / "neotoma").mkdir()
    _, pin, _ = fixture(tmp_path / "neotoma")
    good = {
        "evidence_row_id": "20",
        "longitude": 1.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    records, _, _ = _project_neotoma(
        tmp_path, {"features": [dict(good)]}, expected_manifest_sha256=pin
    )
    assert records[0]["record_id"] == "neotoma:site:20"
    altered = {**good, "longitude": 2.0}
    with pytest.raises(ValueError, match="coordinates"):
        _project_neotoma(
            tmp_path, {"features": [altered]}, expected_manifest_sha256=pin
        )
    records, _, _ = _project_neotoma(tmp_path, {"features": [dict(altered)]})
    assert records[0]["record_id"] == "neotoma:site:20"
    with pytest.raises(ValueError, match="duplicate"):
        _project_neotoma(
            tmp_path,
            {"features": [dict(good), dict(good)]},
            expected_manifest_sha256=pin,
        )
    with pytest.raises(ValueError, match="governed-country"):
        _project_neotoma(
            tmp_path,
            {"features": [{**good, "evidence_row_id": "99"}]},
            expected_manifest_sha256=pin,
        )


def test_projection_refuses_site_part_substitution_after_manifest_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    from bijux_pollenomics.reporting.map_document.evidence_projection import neotoma

    (tmp_path / "neotoma").mkdir()
    root, pin, _ = fixture(tmp_path / "neotoma")
    manifest = json.loads((root / "manifest.json").read_bytes())
    part = root / manifest["surfaces"]["sites"]["parts"][0]["path"]
    original = part.read_bytes()
    read = read_bound_neotoma_manifest

    def swap_after_validation(path: Path, digest: str) -> dict[str, object]:
        result = read(path, digest)
        data = json.loads(original)
        data["rows"][0]["derived_country"] = "Norway"
        part.write_bytes(json.dumps(data).encode())
        return result

    monkeypatch.setattr(neotoma, "read_bound_neotoma_manifest", swap_after_validation)
    good = {
        "evidence_row_id": "20",
        "longitude": 1.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    with pytest.raises(ValueError, match="surface digest changed"):
        neotoma._project_neotoma(
            tmp_path, {"features": [good]}, expected_manifest_sha256=pin
        )
    part.write_bytes(original)


def test_bound_projection_does_not_mutate_any_feature_when_later_site_is_invalid(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
        _project_neotoma,
    )
    from tests.support.neotoma import set_row_identity

    first = download_row()
    second = copy.deepcopy(first)
    set_row_identity(second, 40)
    snapshot = build_neotoma_relational_snapshot(
        [first, second],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([first, second]),
    )
    root = tmp_path / "neotoma/relational"
    root.parent.mkdir()
    materialize_neotoma_relational_snapshot(root, snapshot, rows_per_part=1)
    pin = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    a = {
        "evidence_row_id": "20",
        "longitude": 1.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    b = {
        "evidence_row_id": "40",
        "longitude": 2.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    layer: dict[str, object] = {"features": [a, b]}
    original = copy.deepcopy(layer)
    with pytest.raises(ValueError):
        _project_neotoma(tmp_path, layer, expected_manifest_sha256=pin)
    assert layer == original


def test_public_projection_opt_in_and_missing_selected_layer(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        build_map_evidence_projection,
    )

    (tmp_path / "neotoma").mkdir()
    _, pin, _ = fixture(tmp_path / "neotoma")
    point = {
        "evidence_row_id": "20",
        "longitude": 1.0,
        "latitude": 1.0,
        "country": "Sweden",
        "title": "Ageröds Mosse",
    }
    result = build_map_evidence_projection(
        tmp_path,
        [{"key": "neotoma-pollen", "features": [point]}],
        neotoma_manifest_sha256=pin,
    )
    assert (
        cast(dict[str, Any], result.reconciliation["sources"])["neotoma"][
            "site_binding"
        ]["manifest_sha256"]
        == pin
    )
    with pytest.raises(ValueError, match="requires.*Neotoma"):
        build_map_evidence_projection(tmp_path, [], neotoma_manifest_sha256=pin)


def test_public_map_requires_held_point_capture_for_neotoma_binding(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.service import generate_multi_country_map

    output = tmp_path / "map"
    output.mkdir()
    (output / "prior").write_text("untouched")
    with pytest.raises(ValueError, match="point capture"):
        generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            output,
            "Nordic",
            "nordic",
            context_root=tmp_path,
            neotoma_manifest_sha256="0" * 64,
        )
    assert (output / "prior").read_text() == "untouched"


def test_bound_map_refuses_projection_owner_substitution(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers
    from bijux_pollenomics.reporting.context.nordic_point_inputs import (
        capture_nordic_point_inputs,
    )
    from tests.unit.reporting.context.test_nordic_point_inputs import source_inputs

    root = tmp_path / "source"
    point = capture_nordic_point_inputs(root, source_inputs(root))
    with pytest.raises(ValueError, match="maintained source projection"):
        prepare_layers(
            tmp_path / "stage",
            report=SimpleNamespace(),
            version="v66",
            all_samples=(),
            context_root=root,
            geography_scope=None,
            build_atlas_bundle_paths_fn=lambda **_: None,
            build_context_layers_fn=lambda **_: ([], [], []),
            build_samples_geojson_fn=lambda _: {},
            atlas_detail_records=None,
            atlas_scientific_signals=None,
            atlas_edge_records=None,
            atlas_sequence_records=None,
            surface=SimpleNamespace(
                build_map_evidence_projection=lambda *_args, **_kwargs: None
            ),
            nordic_point_inputs=point,
            neotoma_manifest_sha256="0" * 64,
        )
    assert not (tmp_path / "stage").exists()


@pytest.mark.parametrize("wrong_point", [False, True])
def test_full_map_uses_bound_neotoma_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, wrong_point: bool
) -> None:
    import json
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.context.nordic_point_inputs import (
        capture_nordic_point_inputs,
    )
    from bijux_pollenomics.reporting.map_document.evidence import DETAIL_TAB_KEYS
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        service as projection,
    )
    from tests.unit.reporting.context.test_nordic_point_inputs import (
        POINTS,
        source_inputs,
    )

    root = tmp_path / "data"
    pins = source_inputs(root)
    for role, member in POINTS.items():
        native = "20" if role == "neotoma-pollen" else "synthetic"
        lon = 2.0 if wrong_point and role == "neotoma-pollen" else 1.0
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, 1.0]},
            "properties": {
                "layer_key": role,
                "layer_label": role,
                "record_id": native,
                "name": "Ageröds Mosse" if role == "neotoma-pollen" else "synthetic",
                "country": "Sweden",
            },
        }
        body = json.dumps({"type": "FeatureCollection", "features": [feature]}).encode()
        (root / member).write_bytes(body)
        pins[role] = hashlib.sha256(body).hexdigest()
    held = capture_nordic_point_inputs(root, pins)
    if not wrong_point:
        (root / POINTS["neotoma-pollen"]).write_bytes(b"source replaced after capture")
    (root / "neotoma").mkdir(exist_ok=True)
    _, pin, _ = fixture(root / "neotoma")

    def fake_sead(
        _root: Path, layers: Any
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        for layer in layers:
            for feature in layer["features"]:
                feature["record_id"] = "sead:site:synthetic"
        return (
            [
                {
                    "record_id": "sead:site:synthetic",
                    "tabs": {key: {"status": "unavailable"} for key in DETAIL_TAB_KEYS},
                }
            ],
            {},
        )

    monkeypatch.setattr(projection, "_project_sead", fake_sead)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(
        atlas_bundle,
        "build_tracked_animal_atlas_bundle",
        lambda **_: SimpleNamespace(
            point_layers=(),
            extra_artifacts=(),
            localities=(),
            coordinate_review=SimpleNamespace(
                direct_coordinate_feature_count=0,
                named_site_geocoded_feature_count=0,
                weaker_geography_feature_count=0,
            ),
        ),
    )
    monkeypatch.setattr(
        atlas_bundle, "animal_sample_chronology_context_available", lambda _: False
    )
    out = tmp_path / "map"
    out.mkdir()
    (out / "prior").write_text("preserved")
    kwargs: dict[str, Any] = {
        "context_root": root,
        "lake_inputs": SwedenLakeInputs(),
        "nordic_point_inputs": held,
        "neotoma_manifest_sha256": pin,
    }
    if wrong_point:
        with pytest.raises(ValueError, match="coordinates"):
            service.generate_multi_country_map(
                tmp_path / "v66", ("Sweden",), out, "Nordic", "nordic", **kwargs
            )
        assert (out / "prior").read_text() == "preserved"
    else:
        service.generate_multi_country_map(
            tmp_path / "v66", ("Sweden",), out, "Nordic", "nordic", **kwargs
        )
        contract = json.loads(
            (out / "nordic_map_publication_contract.json").read_bytes()
        )
        assert (
            contract["detail_projection"]["sources"]["neotoma"]["site_binding"][
                "manifest_sha256"
            ]
            == pin
        )
        assert contract["nordic_selected_point_inputs"] == held.identity()
        import re

        from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
            normalize_asset_inventory,
        )
        from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
            decode_chunk_script,
        )

        match = re.search(
            r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
            (out / "nordic_map.html").read_text(),
            re.S,
        )
        assert match is not None
        inventory = cast(
            list[dict[str, Any]],
            normalize_asset_inventory(json.loads(match.group(1))["assets"]),
        )
        asset = next(
            x
            for x in inventory
            if x["domain"] == "nodes" and x.get("layer_key") == "neotoma-pollen"
        )
        node = cast(
            dict[str, Any],
            decode_chunk_script(
                (out / asset["path"]).read_bytes(),
                expected_asset_key=asset["asset_key"],
                expected_payload_sha256=asset["payload_sha256"],
                expected_payload_encoding=asset["payload_encoding"],
                expected_decoded_byte_count=asset.get("decoded_byte_count"),
            ),
        )
        assert len(node["features"]) == 1
        feature = node["features"][0]
        assert (
            feature["record_id"],
            feature["longitude"],
            feature["latitude"],
            feature["country"],
            feature["title"],
        ) == ("neotoma:site:20", 1.0, 1.0, "Sweden", "Ageröds Mosse")
