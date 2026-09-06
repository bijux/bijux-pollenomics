from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from bijux_pollenomics.collection.sources.open_land import normalization, projection
from bijux_pollenomics.collection.sources.open_land.publication import (
    materialize_private_review,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _fixture_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "open-land.zip"
    member_path = "LandCover_OpenLand/Data/Land_Cover_50.csv"
    content = (
        "Lon,Lat,C_KK10LonLatElev,B_KK10LonLatElev,U_KK10LonLatElev\n1,1,0,0.25,0.75\n"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr(member_path, content)
    archive_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    coordinate_grid = hashlib.sha256(b"1\t1\n").hexdigest()
    monkeypatch.setattr(normalization, "ARCHIVE_SHA256", archive_sha256)
    monkeypatch.setattr(normalization, "ARCHIVE_MEMBER_COUNT", 1)
    monkeypatch.setattr(normalization, "ARCHIVE_EXPANDED_BYTES", len(content))
    monkeypatch.setattr(normalization, "MODELED_CELL_COUNT", 1)
    monkeypatch.setattr(normalization, "SOURCE_TIME_SLICES_BP", (50,))
    monkeypatch.setattr(normalization, "SOURCE_INTERVAL_BY_SLICE_BP", {50: (0, 100)})
    monkeypatch.setattr(normalization, "SOURCE_ROW_COUNT_BY_SLICE_BP", {50: 1})
    monkeypatch.setattr(
        normalization, "SOURCE_GRID_SHA256_BY_SLICE_BP", {50: coordinate_grid}
    )
    monkeypatch.setattr(normalization, "ADMITTED_CSV_MEMBERS", (member_path,))
    monkeypatch.setattr(projection, "ARCHIVE_SHA256", archive_sha256)
    monkeypatch.setattr(projection, "MODELED_CELL_COUNT", 1)
    monkeypatch.setattr(projection, "SOURCE_WINDOWS_BP", ((50, 0, 100),))
    monkeypatch.setattr(projection, "SOURCE_ROW_COUNT_BY_SLICE_BP", {50: 1})
    monkeypatch.setattr(
        projection, "SOURCE_GRID_SHA256_BY_SLICE_BP", {50: coordinate_grid}
    )
    return path


def _boundaries() -> dict[str, dict[str, object]]:
    return {
        country: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [west, 0],
                                [west + 2, 0],
                                [west + 2, 2],
                                [west, 2],
                                [west, 0],
                            ]
                        ],
                    },
                }
            ],
        }
        for country, west in (
            ("Sweden", 0),
            ("Denmark", 3),
            ("Norway", 6),
            ("Finland", 9),
        )
    }


def test_materializer_writes_only_immutable_private_review_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _fixture_archive(tmp_path, monkeypatch)
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()

    review = materialize_private_review(
        archive,
        repository_root=repository_root,
        country_boundaries=_boundaries(),
        boundary_artifact_digest="b" * 64,
        boundary_version="synthetic-boundaries",
    )

    assert review.output_root == (
        repository_root
        / "artifacts"
        / "execution-control"
        / "open-land"
        / archive_sha256
        / "private-review"
    )
    assert sorted(path.name for path in review.output_root.iterdir()) == [
        "country_decisions.json",
        "manifest.json",
        "nordic_spatial_land_cover_temporal_grid_cells.geojson",
        "reconciliation.json",
    ]
    manifest = json.loads(review.manifest_path.read_text(encoding="utf-8"))
    assert manifest["release_posture"] == "private_review_only"
    assert manifest["public_release_allowed"] is False
    assert manifest["propagation_use_allowed"] is False
    assert manifest["raw_archive_copied"] is False
    assert manifest["added_spatial_interpolation"] is False
    assert manifest["added_temporal_interpolation"] is False
    assert "Behnaz Pirzamanbein" in manifest["required_attribution"]
    canonical_config = json.dumps(
        manifest["projection_configuration"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert (
        manifest["projection_configuration_sha256"]
        == hashlib.sha256(canonical_config).hexdigest()
    )
    implementation_files = manifest["implementation_files"]
    for implementation_file in implementation_files:
        source = Path(projection.__file__).parent / implementation_file["path"]
        assert (
            implementation_file["sha256"]
            == hashlib.sha256(source.read_bytes()).hexdigest()
        )
    canonical_implementation = json.dumps(
        implementation_files,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert (
        manifest["implementation_sha256"]
        == hashlib.sha256(canonical_implementation).hexdigest()
    )
    for artifact in manifest["artifacts"]:
        content = (review.output_root / artifact["path"]).read_bytes()
        assert artifact["sha256"] == hashlib.sha256(content).hexdigest()
        assert artifact["size_bytes"] == len(content)
    feature_payload = json.loads(
        (
            review.output_root / "nordic_spatial_land_cover_temporal_grid_cells.geojson"
        ).read_text(encoding="utf-8")
    )
    properties = feature_payload["features"][0]["properties"]
    assert properties["coniferous_proportion"] == "0"
    assert properties["coniferous_proportion_numeric"] == 0.0
    assert properties["time_start_bp"] == 0
    assert properties["time_end_bp"] == 100
    assert not any(path.suffix == ".zip" for path in review.output_root.iterdir())

    with pytest.raises(IntakeRefusal, match="open_land_private_review_target_exists"):
        materialize_private_review(
            archive,
            repository_root=repository_root,
            country_boundaries=_boundaries(),
            boundary_artifact_digest="b" * 64,
            boundary_version="synthetic-boundaries",
        )


def test_materializer_refuses_symlinked_artifacts_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _fixture_archive(tmp_path, monkeypatch)
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (repository_root / "artifacts").symlink_to(external, target_is_directory=True)

    with pytest.raises(IntakeRefusal, match="open_land_artifact_directory_symlink"):
        materialize_private_review(
            archive,
            repository_root=repository_root,
            country_boundaries=_boundaries(),
            boundary_artifact_digest="b" * 64,
            boundary_version="synthetic-boundaries",
        )
