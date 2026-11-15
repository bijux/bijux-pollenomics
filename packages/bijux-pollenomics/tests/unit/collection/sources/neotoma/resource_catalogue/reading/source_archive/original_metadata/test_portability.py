"""A portable archive owns only the exact original dataset metadata witness."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive


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
