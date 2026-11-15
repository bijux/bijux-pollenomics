"""Forensic downloads authenticate bytes without admitting numerical source shapes."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import reader


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
@pytest.mark.parametrize("kind", ["pollen", "unregistered native proxy"])
def test_source_entity_preserves_bytes_and_original_qualification(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    version: str,
    kind: str,
) -> None:
    inputs = catalogue_sources(auxiliary_type=kind)
    output, digest, sources = publish_catalogue(inputs)
    result = reader.read_neotoma_catalogue_source_entity(
        output,
        expected_manifest_sha256=digest,
        dataset_id=202,
        version=version,
        capture_sources=sources,
    )
    capture = next(iter(inputs["resource_captures"].values()))
    expected = (capture / f"dataset-202-{version}-attempt-1.body").read_bytes()
    assert result["native_body"] == expected
    assert result["source"]["body_sha256"] == sha256(expected).hexdigest()
    assert result["use_scope"] == "source_entity_download_only"
    assert result["scientific_admission"] == "not_asserted"
    assert result["units_interpreted"] is False
    assert "native_payload" not in result
    assert result["acquisition_status"] == (
        "unresolved_frozen_schema"
        if version == "doi_frozen"
        else "parsed_native"
        if kind == "pollen"
        else "unsupported_dataset_type"
    )


@pytest.mark.parametrize("dataset_id", [203, 204, 999])
def test_source_entity_refuses_roles_or_unknown_ids_before_external_access(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
    dataset_id: int,
) -> None:
    output, digest, _ = publish_catalogue(catalogue_sources())
    with pytest.raises(ValueError, match="exposure role|outside"):
        reader.read_neotoma_catalogue_source_entity(
            output,
            expected_manifest_sha256=digest,
            dataset_id=dataset_id,
            version="current",
            capture_sources=no_outcome_resolver,
        )


@pytest.mark.parametrize("dataset_id", [True, 0, -1, "201", 201.0])
def test_invalid_source_entity_identity_fails_before_catalogue_io(
    tmp_path: Path, dataset_id: Any
) -> None:
    with pytest.raises(ValueError):
        reader.read_neotoma_catalogue_source_entity(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=dataset_id,
            version="current",
            capture_sources={},
        )


@pytest.mark.parametrize("mutation", ["body", "receipt"])
def test_source_entity_refuses_changed_source_bytes(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    mutation: str,
) -> None:
    inputs = catalogue_sources(auxiliary_type="unregistered native proxy")
    output, digest, sources = publish_catalogue(inputs)
    if mutation == "body":
        root = next(iter(inputs["resource_captures"].values()))
        (root / "dataset-202-current-attempt-1.body").write_bytes(b"foreign")
    else:
        digest_source = next(iter(inputs["resource_captures"]))
        root = output / "captures" / digest_source
        (root / "dataset-202-current-attempt-1.receipt.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity|digest"):
        reader.read_neotoma_catalogue_source_entity(
            output,
            expected_manifest_sha256=digest,
            dataset_id=202,
            version="current",
            capture_sources=sources,
        )


def test_missing_source_entity_is_an_explicit_failure(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    output, digest, _ = publish_catalogue(catalogue_sources(capture_resources=False))
    with pytest.raises(ValueError, match="no complete successful source entity"):
        reader.read_neotoma_catalogue_source_entity(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version="current",
            capture_sources=no_outcome_resolver,
        )


def test_source_entity_authenticates_attribution_against_native_metadata(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
) -> None:
    output, _, sources = publish_catalogue(catalogue_sources())
    catalogue_path = output / "catalogue.json"
    catalogue = json.loads(catalogue_path.read_bytes())
    row = next(row for row in catalogue["resources"] if row["dataset_id"] == 201)
    invented = [{"contactname": "Invented forensic contributor"}]
    row["metadata"]["native_dataset"]["datasetpi"] = invented
    row["rights"]["investigator_metadata"] = invented
    catalogue_path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(
        catalogue_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metadata.*witness"):
        reader.read_neotoma_catalogue_source_entity(
            output,
            expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
            dataset_id=201,
            version="current",
            capture_sources=sources,
        )


def test_metadata_witness_rejects_another_dataset_in_the_same_native_unit(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.metadata import (
        validate_metadata_witness,
    )

    output, _, sources = publish_catalogue(catalogue_sources())
    catalogue = json.loads((output / "catalogue.json").read_bytes())
    row = deepcopy(
        next(row for row in catalogue["resources"] if row["dataset_id"] == 201)
    )
    donor = next(row for row in catalogue["resources"] if row["dataset_id"] == 202)
    row["metadata"] = deepcopy(donor["metadata"])
    with pytest.raises(ValueError, match="metadata.*owner"):
        validate_metadata_witness(output, catalogue, row, sources, None)
