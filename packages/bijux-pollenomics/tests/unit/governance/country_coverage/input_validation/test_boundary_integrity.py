"""Boundary artifact and governed-path integrity refusal tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.governance.country_coverage import (
    build_country_dimension_coverage_ledger,
)

from ..fixtures import (
    _CELL_SCHEMA_PATH,
    _READ_BYTES,
    _REPOSITORY_ROOT,
    _build,
    _document_bytes,
    _replace_input_document,
    _replace_input_documents,
)


def test_boundary_manifest_digest_must_match_artifact_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def change_boundary(document: dict[str, object]) -> None:
        document["falsification_marker"] = True

    _replace_input_document(
        monkeypatch,
        "data/boundaries/normalized/nordic_country_boundaries.geojson",
        change_boundary,
    )

    with pytest.raises(ValueError, match="boundary artifact digest does not match"):
        _build()


@pytest.mark.parametrize("symlink_part", ("file", "ancestor"))
def test_symlinked_governed_input_path_is_refused(
    monkeypatch: pytest.MonkeyPatch, symlink_part: str
) -> None:
    input_path = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    claimed_symlink = input_path if symlink_part == "file" else input_path.parent
    original_is_symlink = Path.is_symlink

    def is_symlink(path: Path) -> bool:
        return path == claimed_symlink or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)

    with pytest.raises(
        ValueError, match="governed input path must not contain symlinks"
    ):
        _build()


def test_symlinked_schema_path_is_refused(tmp_path: Path) -> None:
    schema_alias = tmp_path / "country-coverage.schema.json"
    schema_alias.symlink_to(_CELL_SCHEMA_PATH)

    with pytest.raises(ValueError, match="schema path must not contain symlinks"):
        build_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT, cell_schema_path=schema_alias
        )


def test_normalized_boundary_duplicate_alias_is_refused_before_indexing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_path = "data/boundaries/normalized/nordic_country_boundaries.geojson"
    manifest_path = "data/boundaries/raw/source_manifest.json"
    boundary = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / boundary_path))
    )
    features = cast(list[dict[str, object]], boundary["features"])
    properties = cast(dict[str, object], features[1]["properties"])
    properties["country"] = "SE"
    properties["name"] = "Sweden"
    boundary_bytes = _document_bytes(boundary)
    manifest = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / manifest_path))
    )
    normalized = cast(dict[str, object], manifest["normalized_artifact"])
    normalized["sha256"] = hashlib.sha256(boundary_bytes).hexdigest()
    _replace_input_documents(
        monkeypatch,
        {
            boundary_path: boundary_bytes,
            manifest_path: _document_bytes(manifest),
        },
    )

    with pytest.raises(ValueError, match="duplicate country alias"):
        _build()


def test_normalized_boundary_requires_exact_nordic_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_path = "data/boundaries/normalized/nordic_country_boundaries.geojson"
    manifest_path = "data/boundaries/raw/source_manifest.json"
    boundary = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / boundary_path))
    )
    features = cast(list[dict[str, object]], boundary["features"])
    boundary["features"] = [
        feature
        for feature in features
        if cast(dict[str, object], feature["properties"])["country"] != "Norway"
    ]
    boundary_bytes = _document_bytes(boundary)
    manifest = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / manifest_path))
    )
    normalized = cast(dict[str, object], manifest["normalized_artifact"])
    normalized["sha256"] = hashlib.sha256(boundary_bytes).hexdigest()
    normalized["feature_count"] = 3
    _replace_input_documents(
        monkeypatch,
        {
            boundary_path: boundary_bytes,
            manifest_path: _document_bytes(manifest),
        },
    )

    with pytest.raises(ValueError, match="exactly SE/DK/NO/FI"):
        _build()
