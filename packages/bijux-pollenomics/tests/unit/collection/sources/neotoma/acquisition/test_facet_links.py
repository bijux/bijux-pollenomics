"""Derived native ID links retain exact source pointers and inherited root roles."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest

from .test_facet_profiles import capture


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.facets.links"
    )


@pytest.mark.parametrize("higher", [False, True])
def test_every_discovered_id_is_bound_to_actual_source_buffer_and_pointer(
    tmp_path: Path,
    higher: bool,
) -> None:
    source = tmp_path / "capture"
    captured = capture(source)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    report = owner().discover_neotoma_facet_links(
        source,
        expected_manifest_sha256=captured.manifest_sha256,
        include_higher_taxa=higher,
    )
    assert len(report["links"]) == (282 if higher else 188)
    assert len(report["targets"]) == (203 if higher else 120)
    assert len(report["higher_taxon_leads"]) == 94
    assert report["HTTP_requests"] == 0 and report["recursive_expansion"] is False
    assert report["scientific_admission"] == "not_asserted"
    manifest = json.loads((source / "capture-manifest.json").read_bytes())
    entries = {r["facet_key"]: r for r in manifest["facets"]}
    for link in report["links"]:
        entry = entries[link["source_facet_key"]]
        reference = entry["attempts"][-1]
        content = (source / reference["body_file"]).read_bytes()
        assert link["source_body_sha256"] == sha256(content).hexdigest()
        assert link["source_receipt_sha256"] == reference["receipt_sha256"]
        assert link["source_capture_manifest_sha256"] == captured.manifest_sha256
        assert link["root_dataset_id"] == 19913
        assert link["inherited_exposure_role"] == "development_resource_discovery"
        value = json.loads(content)
        for token in link["json_pointer"].split("/")[1:]:
            value = value[int(token)] if isinstance(value, list) else value[token]
        assert type(value) is int and value == link["native_id"]
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}


def test_dataset_and_taxonomic_publications_are_separate_without_author_id_guess(
    tmp_path: Path,
) -> None:
    result = capture(tmp_path / "capture")
    report = owner().discover_neotoma_facet_links(
        tmp_path / "capture",
        expected_manifest_sha256=result.manifest_sha256,
    )
    contacts = [row for row in report["links"] if row["target_kind"] == "contact"]
    assert [row["native_id"] for row in contacts] == [8720]
    assert all("preparedby/contactid" in row["json_pointer"] for row in contacts)
    dataset = [
        row for row in report["links"] if row["relation"] == "dataset_publication"
    ]
    taxonomy = [
        row
        for row in report["links"]
        if row["relation"] == "taxonomic_reference_publication"
    ]
    assert [row["native_id"] for row in dataset] == [9435]
    assert len(taxonomy) == 92
    assert len({row["native_id"] for row in taxonomy}) == 24
    for target in report["targets"]:
        expected = [
            index
            for index, proof in enumerate(report["links"])
            if (
                proof["target_kind"],
                proof["native_id"],
                proof["root_dataset_id"],
                proof["inherited_exposure_role"],
            )
            == (
                target["target_kind"],
                target["native_id"],
                target["root_dataset_id"],
                target["inherited_exposure_role"],
            )
        ]
        assert target["proof_indices"] == expected
    nulls = [
        row
        for row in report["unavailable"]
        if row.get("relation") == "taxonomic_reference_publication"
    ]
    assert len(nulls) == 2
    assert all(row["reason"] == "source_null_native_id" for row in nulls)


def test_swapped_body_cannot_supply_ids_under_an_authentic_old_manifest(
    tmp_path: Path,
) -> None:
    result = capture(tmp_path / "capture")
    entry = next(row for row in result.facets if row["facet"] == "taxa")
    body = tmp_path / "capture" / entry["attempts"][-1]["body_file"]
    body.write_bytes(b'{"status":"success","data":[{"taxonid":999}]}')
    with pytest.raises(ValueError):
        owner().discover_neotoma_facet_links(
            tmp_path / "capture",
            expected_manifest_sha256=result.manifest_sha256,
        )
