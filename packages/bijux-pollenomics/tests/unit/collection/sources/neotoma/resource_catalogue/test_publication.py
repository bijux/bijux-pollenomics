"""Compact catalogue publication owns a new portable tree and explicit raw resolvers."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    load_neotoma_resource_catalogue,
    publication,
    write_neotoma_resource_catalogue,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree


@pytest.mark.parametrize(
    "mutation", ["stage_tree", "catalogue_leaf", "native_leaf", "manifest_leaf"]
)
def test_publication_refuses_late_source_swaps_and_preserves_published_evidence(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    output = tmp_path / "published-catalogue"
    preserved_stage = tmp_path / "validated-stage-evidence"
    native = next(iter(inputs["resource_captures"].values()))
    native_leaf = native / "dataset-201-current-attempt-1.body"
    foreign = b'{"foreign_source":true}'

    def publish_with_late_swap(
        *, final_output_root: Path, staging_output_root: Path
    ) -> None:
        if mutation == "stage_tree":
            staging_output_root.rename(preserved_stage)
            shutil.copytree(preserved_stage, staging_output_root)
        if mutation in {"stage_tree", "catalogue_leaf"}:
            (staging_output_root / "catalogue.json").write_bytes(foreign)
        elif mutation == "native_leaf":
            native_leaf.write_bytes(foreign)
        else:
            (staging_output_root / "manifest.json").write_bytes(foreign)
        publish_new_output_tree(
            final_output_root=final_output_root,
            staging_output_root=staging_output_root,
        )

    monkeypatch.setattr(publication, "publish_new_output_tree", publish_with_late_swap)
    with pytest.raises(ValueError, match="identity|digest|source|population"):
        write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=sources,
        )
    assert output.is_dir()
    if mutation == "native_leaf":
        assert native_leaf.read_bytes() == foreign
        assert (output / "catalogue.json").is_file()
    elif mutation == "manifest_leaf":
        assert (output / "manifest.json").read_bytes() == foreign
    else:
        assert (output / "catalogue.json").read_bytes() == foreign
    if mutation == "stage_tree":
        assert (preserved_stage / "catalogue.json").read_bytes() != foreign


def test_compact_publication_has_portable_sources_and_required_raw_replay(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "public-catalogue"
    all_sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    written = write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=all_sources,
    )
    assert written["resource_count"] == 4 and written["version_status_count"] == 8
    assert (
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
        )["resources"]
        == catalogue["resources"]
    )
    assert (
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            capture_sources=all_sources,
            require_source_bodies=True,
        )["resources"]
        == catalogue["resources"]
    )
    with pytest.raises(ValueError, match="resolver|source"):
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            require_source_bodies=True,
        )
    text = "\n".join(path.read_text() for path in output.rglob("*.json"))
    assert str(tmp_path) not in text and "artifacts/" not in text
    assert not list(output.rglob("*.body"))
    assert list(output.glob("captures/*/descriptor.json"))


def test_catalogue_publication_refuses_existing_foreign_tree(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "foreign"
    output.mkdir()
    (output / "user-work").write_text("keep")
    with pytest.raises(FileExistsError):
        write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={},
        )
    assert (output / "user-work").read_text() == "keep"


def test_catalogue_publication_readback_authenticates_compact_bytes(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "public-catalogue"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources={**inputs["metadata_captures"], **inputs["resource_captures"]},
    )
    path = output / "catalogue.json"
    document = json.loads(path.read_bytes())
    document["resources"][0]["versions"]["current"]["native_counts"][
        "raw_sample_rows"
    ] = 999
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="identity|digest"):
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
        )


def test_descriptor_identity_cannot_escape_owned_publication_tree(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    digest, descriptor = next(iter(catalogue["capture_descriptors"].items()))
    catalogue["capture_descriptors"] = {"../../escaped-source": descriptor}
    all_sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    with pytest.raises(ValueError):
        write_neotoma_resource_catalogue(
            tmp_path / "publication",
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={"../../escaped-source": all_sources[digest]},
        )
    assert not (tmp_path / "escaped-source").exists()


def test_self_consistent_compact_republication_cannot_change_native_counts(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:

    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "public-catalogue"
    sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=sources,
    )
    catalogue_path = output / "catalogue.json"
    modified = json.loads(catalogue_path.read_bytes())
    modified["resources"][0]["versions"]["current"]["native_counts"][
        "raw_sample_rows"
    ] = 999
    catalogue_path.write_text(json.dumps(modified))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(
        catalogue_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="projection|counts|source"):
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            capture_sources=sources,
            require_source_bodies=True,
        )


def test_descriptor_entity_hash_cannot_be_invented_even_with_valid_raw_resolver(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    descriptor = next(iter(catalogue["capture_descriptors"].values()))
    entity = next(member for member in descriptor["files"] if member["source_entity"])
    entity["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="descriptor|source"):
        write_neotoma_resource_catalogue(
            tmp_path / "publication",
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={
                **inputs["metadata_captures"],
                **inputs["resource_captures"],
            },
        )


def test_public_metadata_load_requires_a_caller_supplied_manifest_anchor(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "public-catalogue"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources={**inputs["metadata_captures"], **inputs["resource_captures"]},
    )
    with pytest.raises(TypeError):
        load_neotoma_resource_catalogue(output)  # type: ignore[call-arg]


@pytest.mark.parametrize("surface", ["country", "role", "rights"])
def test_rehashed_public_metadata_refuses_against_original_anchor(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, surface: str
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "catalogue"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources={**inputs["metadata_captures"], **inputs["resource_captures"]},
    )
    manifest_path = output / "manifest.json"
    trusted = sha256(manifest_path.read_bytes()).hexdigest()
    path = output / "catalogue.json"
    content = json.loads(path.read_bytes())
    if surface == "country":
        content["resources"][0]["country"]["final_country_code"] = "NO"
    elif surface == "role":
        content["resources"][2]["exposure_role"] = "development_resource_discovery"
    else:
        content["resources"][0]["rights"]["available_public_data_license"] = "CC0"
    path.write_text(json.dumps(content))
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest identity"):
        load_neotoma_resource_catalogue(output, expected_manifest_sha256=trusted)


@pytest.mark.parametrize("surface", ["role", "rights", "native_metadata"])
def test_writer_cannot_certify_tampered_source_facts(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, surface: str
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    if surface == "role":
        catalogue["resources"][2]["exposure_role"] = "development_resource_discovery"
    elif surface == "rights":
        catalogue["resources"][0]["rights"]["available_public_data_license"] = "CC0"
    else:
        catalogue["resources"][0]["metadata"]["native_dataset"]["datasetpi"] = [
            {"contactname": "Invented"}
        ]
        catalogue["resources"][0]["rights"]["investigator_metadata"] = [
            {"contactname": "Invented"}
        ]
    output = tmp_path / "catalogue"
    with pytest.raises(ValueError, match="role|rights|metadata"):
        write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={
                **inputs["metadata_captures"],
                **inputs["resource_captures"],
            },
        )
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "receipt_file",
        "receipt_sha256",
        "omit_receipt",
        "source_kind",
        "capture_digest",
        "body_file",
        "lookup_branch",
    ],
)
def test_complete_metadata_source_tuple_must_match_original_receipt(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, mutation: str
) -> None:
    inputs = catalogue_sources()
    catalogue = build_neotoma_resource_catalogue(**inputs)
    source = catalogue["resources"][0]["metadata"]["source"]
    if mutation == "receipt_file":
        source["receipt_file"] = "not-a-real-source-receipt.json"
    elif mutation == "receipt_sha256":
        source["receipt_sha256"] = "0" * 64
    elif mutation == "omit_receipt":
        del source["receipt_file"]
    elif mutation == "source_kind":
        source["source_kind"] = "original_relational_metadata"
    elif mutation == "capture_digest":
        source["capture_manifest_sha256"] = "0" * 64
    elif mutation == "body_file":
        source["body_file"] = "not-a-real-source.body"
    else:
        source["current_metadata_lookup"] = {
            "manifest_sha256": "0" * 64,
            "successful_empty": True,
        }
    with pytest.raises(ValueError, match="metadata|source|resolver|identity"):
        write_neotoma_resource_catalogue(
            tmp_path / "publication",
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources={
                **inputs["metadata_captures"],
                **inputs["resource_captures"],
            },
        )
