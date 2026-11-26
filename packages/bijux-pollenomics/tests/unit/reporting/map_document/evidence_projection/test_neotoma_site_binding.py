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
