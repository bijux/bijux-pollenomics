"""Compact authenticated catalogue adaptation preserves source qualifications."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    load_neotoma_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.source_resources import (
    catalogue as adapter,
)

from .catalogue_inputs import pin_compact_extension


def test_all_resources_sites_roles_and_epochs_remain_metadata_only(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, digest, native = atlas_catalogue(auxiliary_type="future native type")
    actual_loader = load_neotoma_resource_catalogue
    calls = []

    def compact_loader(directory: Path, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        assert kwargs == {
            "expected_manifest_sha256": digest,
            "require_source_bodies": False,
        }
        return actual_loader(directory, **kwargs)

    monkeypatch.setattr(adapter, "load_neotoma_resource_catalogue", compact_loader)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    assert len(calls) == 1
    assert result.summary == native["summary"]
    assert result.source_descriptors == native["capture_descriptors"]
    assert len(result.site_records) == 3
    assert {row["country_code"] for row in result.site_records} == {"UNASSIGNED"}
    assert {row["dataset_id"] for row in result.resource_records} == {
        "201",
        "202",
        "203",
        "204",
    }
    for raw, projected in zip(
        native["resources"], result.resource_records, strict=True
    ):
        for key in ("versions", "rights", "original_epoch", "method_capability"):
            assert projected[key] == raw[key]
        assert (
            projected["metadata"]["native_dataset"] == raw["metadata"]["native_dataset"]
        )
        assert "native_site" not in projected["metadata"]
        assert "native_body" not in projected
    assert result.provenance["catalogue_manifest_sha256"] == digest
    assert result.provenance["scientific_admission"] == "not_asserted"
    assert result.legacy_site_references == ()


@pytest.mark.parametrize("digest", [None, "", "A" * 64, "0" * 63, True, 12])
def test_independent_manifest_anchor_is_required_before_io(
    tmp_path: Path, digest: Any
) -> None:
    with pytest.raises(ValueError, match="manifest SHA-256"):
        AtlasResourceCatalogueInput(tmp_path / "absent", digest)


def test_manifest_and_public_member_tampering_refuse(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> None:
    root, digest, _ = atlas_catalogue()
    with pytest.raises(ValueError, match="manifest identity"):
        load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, "0" * 64))
    path = root / "catalogue.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="file identity"):
        load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))


def test_future_version_fields_raw_rights_and_source_objects_are_preserved(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> None:
    root, _, native = atlas_catalogue()
    # Publish a finite, independently pinned future compact schema extension.
    resource = native["resources"][0]
    resource["versions"]["current"]["derived_current_qualification"] = {
        "status": "qualified_separate_interpreter",
        "original_status": None,
    }
    anchor = pin_compact_extension(root, native)
    before = deepcopy(native)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, anchor))
    assert result.resource_records[0]["versions"] == resource["versions"]
    assert result.resource_records[0]["rights"] == resource["rights"]
    assert result.resource_records[0]["rights"]["constituent_database"] is None
    assert result.resource_records[0]["rights"]["investigator_metadata"] == []
    assert result.resource_records[0]["versions"]["current"]["acquisition_status"] == (
        "not_attempted_pending_capture"
    )
    result.resource_records[0]["versions"]["current"]["absence_certified"] = True
    assert json.loads((root / "catalogue.json").read_bytes()) == before


@pytest.mark.parametrize("family", ["sead", None, "NEOTOMA"])
def test_foreign_catalogue_namespace_refuses_even_with_a_valid_manifest_pin(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], family: object
) -> None:
    root, _, native = atlas_catalogue()
    native["source_family"] = family
    anchor = pin_compact_extension(root, native)
    with pytest.raises(ValueError, match="source family"):
        load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, anchor))
