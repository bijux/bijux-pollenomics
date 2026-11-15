"""Selected native resource access guards controls."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize("dataset_id", [203, 204])
@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_reserved_and_heldout_refuse_before_external_source_access(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    dataset_id: int,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    output, digest, _ = publish_catalogue(catalogue_sources())
    with pytest.raises(ValueError, match="exposure role"):
        read(
            output,
            expected_manifest_sha256=digest,
            dataset_id=dataset_id,
            version=version,
            capture_sources=no_outcome_resolver,
        )


@pytest.mark.parametrize("dataset_id", [True, 0, -1, 201.5, "201"])
def test_invalid_requested_native_identity_refuses_before_catalogue_or_body_access(
    tmp_path: Path,
    dataset_id: object,
    resource_reader: Callable[..., dict[str, Any]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    with pytest.raises(ValueError, match="positive integer"):
        read(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=dataset_id,
            version="current",
            capture_sources=no_outcome_resolver,
        )


@pytest.mark.parametrize("version", ["original", None, True, [], {}])
def test_invalid_version_refuses_before_catalogue_or_source_access(
    tmp_path: Path,
    version: object,
    resource_reader: Callable[..., dict[str, Any]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    with pytest.raises(ValueError, match="version"):
        read(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version=version,
            capture_sources=no_outcome_resolver,
        )


def test_reader_requires_trusted_manifest_anchor(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    read = resource_reader
    output, _, sources = publish_catalogue(catalogue_sources())
    with pytest.raises(ValueError, match="manifest identity"):
        read(
            output,
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version="current",
            capture_sources=sources,
        )
    with pytest.raises(TypeError):
        read(output, dataset_id=201, version="current", capture_sources=sources)


def test_pending_and_unqualified_resources_refuse_before_body_access(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    inputs = catalogue_sources(capture_resources=False)
    output, digest, _ = publish_catalogue(inputs)
    with pytest.raises(ValueError, match="not.*qualified|not_attempted"):
        read(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version="current",
            capture_sources=no_outcome_resolver,
        )


def test_stale_unqualified_catalogue_cannot_open_frozen_outcomes(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    output, _, _ = publish_catalogue(catalogue_sources())
    path = output / "catalogue.json"
    catalogue = json.loads(path.read_bytes())
    del catalogue["resources"][0]["versions"]["doi_frozen"][
        "snapshot_qualification_status"
    ]
    path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="not qualified"):
        read(
            output,
            expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
            dataset_id=201,
            version="doi_frozen",
            capture_sources=no_outcome_resolver,
        )


def test_rehashed_qualification_cannot_promote_original_unsupported_current_ledger(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    read = resource_reader
    inputs = catalogue_sources(auxiliary_type="unqualified native type")
    output, _, _ = publish_catalogue(inputs)
    path = output / "catalogue.json"
    catalogue = json.loads(path.read_bytes())
    selected = catalogue["resources"][1]["versions"]["current"]
    assert selected["source_terminal_status"] == "unsupported_dataset_type"
    selected["qualification_status"] = "parsed_native"
    path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="not qualified|terminal|qualification"):
        read(
            output,
            expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
            dataset_id=202,
            version="current",
            capture_sources=no_outcome_resolver,
        )
