"""A portable archive owns only the exact original dataset metadata witness."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    NeotomaResourceSpec,
    capture_neotoma_resources,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def test_historical_dataset_replays_without_external_original_metadata(
    original_catalogue: tuple[Path, str, dict[str, Path], Path], tmp_path: Path
) -> None:
    catalogue, digest, sources, original = original_catalogue
    expected = {
        p.relative_to(original).as_posix(): p.read_bytes()
        for p in original.rglob("*")
        if p.is_file()
    }
    output = tmp_path / "portable"
    archive.write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
        original_relational_root=original,
    )
    original.rename(tmp_path / "external-original-removed")
    manifest = archive.load_neotoma_source_archive(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
    )
    witness = manifest["original_metadata"]
    assert witness["scope"] == "original_relational_dataset_metadata_only"
    assert witness["dataset_row_count"] == 2
    assert witness["dataset_part_count"] == 2
    copied = {
        p.relative_to(output / "captures/original-metadata").as_posix(): p.read_bytes()
        for p in (output / "captures/original-metadata").rglob("*")
        if p.is_file()
    }
    assert copied == expected
    assert "numerical-not-supplied.json" not in " ".join(manifest["files"])
    compact = json.loads((output / "catalogue/catalogue.json").read_bytes())
    row = compact["resources"][0]
    assert row["metadata"]["source"]["source_kind"] == "original_relational_metadata"
    assert row["original_epoch"]["source_snapshot_id"] == "sha256:" + "a" * 64


def test_selected_empty_entity_authenticates_internal_historical_metadata(
    original_catalogue: tuple[Path, str, dict[str, Path], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalogue, _, metadata_sources, original = original_catalogue
    roster = catalogue / "source-inventory.json"
    roster_sha = sha256(roster.read_bytes()).hexdigest()
    part_sha = sha256(
        (original / "surfaces/datasets/201.json").read_bytes()
    ).hexdigest()
    empty = b'{"status":"success","data":[]}'
    capture_root = tmp_path / "empty-native-source"
    captured = capture_neotoma_resources(
        capture_root,
        plan=NeotomaResourcePlan(
            (
                NeotomaResourceSpec(
                    201,
                    12,
                    100,
                    "pollen",
                    None,
                    "development_resource_discovery",
                    part_sha,
                    "/rows/0/source_payload",
                    ("current",),
                ),
            ),
            roster_sha,
        ),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), empty),
    )
    logical = api.build_neotoma_resource_catalogue(
        roster_path=roster,
        expected_roster_sha256=roster_sha,
        metadata_captures=metadata_sources,
        resource_captures={captured.manifest_sha256: capture_root},
        original_relational_root=original,
    )
    public = tmp_path / "historical-public"
    sources = {**metadata_sources, captured.manifest_sha256: capture_root}
    api.write_neotoma_resource_catalogue(
        public,
        catalogue=logical,
        roster_path=roster,
        capture_sources=sources,
        original_relational_root=original,
    )
    output = tmp_path / "historical-archive"
    archive.write_neotoma_source_archive(
        output,
        catalogue_directory=public,
        expected_catalogue_manifest_sha256=sha256(
            (public / "manifest.json").read_bytes()
        ).hexdigest(),
        capture_sources=sources,
        original_relational_root=original,
    )
    original.rename(tmp_path / "detached-original")
    for index, path in enumerate(sources.values()):
        path.rename(tmp_path / f"detached-capture-{index}")
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    open_source = capture_opening()
    with monkeypatch.context() as guard:

        def forbidden(path: Path, *args: Any, **kwargs: Any) -> Any:
            if path.suffix == ".body" or path.parent.name == "datasets":
                pytest.fail(
                    "protected selection opened a source or original dataset buffer"
                )
            return open_source(path, *args, **kwargs)

        observe_opening(guard, forbidden)
        for read in (
            archive.read_neotoma_source_archive_resource,
            archive.read_neotoma_source_archive_entity,
        ):
            with pytest.raises(ValueError, match="exposure role"):
                read(
                    output,
                    expected_manifest_sha256=pin,
                    dataset_id=203,
                    version="current",
                )
    result = archive.read_neotoma_source_archive_entity(
        output, expected_manifest_sha256=pin, dataset_id=201, version="current"
    )
    assert result["native_body"] == empty
    assert result["scientific_admission"] == "not_asserted"
    assert result["archive"]["unselected_source_bodies_verified"] is False
    part = output / "captures/original-metadata/surfaces/datasets/201.json"
    document = json.loads(part.read_bytes())
    document["rows"][0]["source_payload"]["datasetid"] = 999
    part.write_text(json.dumps(document))
    native_open = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name == "dataset-201-current-attempt-1.body":
            pytest.fail("numerical entity opened before historical witness refusal")
        return native_open(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        archive.read_neotoma_source_archive_entity(
            output, expected_manifest_sha256=pin, dataset_id=201, version="current"
        )
