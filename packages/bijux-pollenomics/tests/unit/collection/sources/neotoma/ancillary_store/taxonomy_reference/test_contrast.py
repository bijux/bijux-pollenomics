"""Contrast explicitly stored frontier metadata without reopening native sources."""

from hashlib import sha1, sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.chain.native_products import (
    capture_parent,
    retain_chain,
)

from .test_archive import Retained, encoded, git_tree, publish


def frontier(tmp_path: Path, rows: list[dict[str, Any]]) -> tuple[Path, str]:
    """Use the maintained content-addressed chain transport for generated rows."""
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        storage,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        COLLECTIONS,
        SCHEMA,
    )

    document = {
        "schema_version": SCHEMA,
        "parent_chain_manifest_sha256": None,
        "new_capture_manifest_sha256s": ["b" * 64],
        "scientific_admission": "not_asserted",
        **dict.fromkeys(COLLECTIONS, []),
        "frontier": rows,
    }
    manifest, parts = storage._pack(document, collections=COLLECTIONS, schema=SCHEMA)
    root = tmp_path / "chain"
    root.mkdir()
    for name, raw in {**parts, "manifest.json": encoded(manifest)}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return root, sha256((root / "manifest.json").read_bytes()).hexdigest()


def target(kind: str, identity: int) -> dict[str, Any]:
    """Keep recorded scope statements separate from current verification."""
    return {
        "target_key": f"{kind}-{identity}",
        "target_kind": kind,
        "native_id": identity,
        "current_root_dataset_ids": [44, 439],
        "current_use_role": "development_only",
        "status": "not_attempted_capture_not_authorized",
        "GET_authorized": False,
        "scientific_admission": "not_asserted",
    }


def change_metadata(retained: Retained, changes: dict[str, dict[str, Any]]) -> None:
    """Rebuild consistent generated Git evidence after a source-field variation."""
    directory, files, evidence, _, _ = retained
    path = directory / "taxon_metadata.json"
    metadata = json.loads(path.read_bytes())
    for key, change in changes.items():
        metadata[key].update(change)
    path.write_bytes(encoded(metadata))
    for name in files:
        raw = (directory / name).read_bytes()
        files[name] = {
            "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(),
            "git_blob": sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest(),
        }
    data = git_tree(
        [
            {
                "path": name,
                "mode": "100644",
                "type": "blob",
                "sha": row["git_blob"],
                "size": row["bytes"],
            }
            for name, row in files.items()
        ]
    )
    root = git_tree(
        [{"path": "data", "mode": "040000", "type": "tree", "sha": data["sha"]}]
    )
    commit = json.loads(evidence["commit"].read_bytes())
    commit["tree"] = {"sha": root["sha"], "url": root["url"]}
    for name, value in [("commit", commit), ("root_tree", root), ("data_tree", data)]:
        evidence[name].write_bytes(encoded(value))
    # Retained transport size must describe the newly generated metadata bytes.
    transport_path = retained[3]["taxon_metadata.json"]
    transport = json.loads(transport_path.read_bytes())
    transport["size_download"] = files["taxon_metadata.json"]["bytes"]
    transport_path.write_bytes(encoded(transport))


def test_frozen_frontier_contrast_preserves_every_outcome_and_epoch(
    retained: Retained, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, directory, _, pin = publish(retained, tmp_path)
    rows = [
        target("taxon", 1),
        target("taxon", 999),
        target("publication", 99),
        target("publication", 100),
    ]
    chain, chain_pin = frontier(tmp_path, rows)
    function = getattr(owner, "contrast_neotoma_taxonomy_reference_frontier", None)
    assert callable(function), "Metadata-only frontier reference consumer is missing"
    real_open = os.open

    def no_body(path: Any, *args: Any, **kwargs: Any) -> int:
        assert not str(path).endswith(".body"), (
            "Contrast attempted a native source body"
        )
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", no_body)
    result = function(
        directory,
        expected_manifest_sha256=pin,
        chain_directory=chain,
        expected_chain_manifest_sha256=chain_pin,
    )
    assert [row["target_key"] for row in result.rows] == [
        row["target_key"] for row in rows
    ]
    assert [row["outcome"] for row in result.rows] == [
        "dated_taxon_lookup_available",
        "not_observed_in_reference_projection",
        "classification_publication_fallback_only",
        "not_observed_in_reference_projection",
    ]
    assert (
        result.rows[2]["classification_references"][0]["publication"]
        == "fallback reference"
    )
    assert result.rows[2]["classification_references"][0]["citation"] is None
    assert result.rows[2]["classification_references"][0]["source_taxon_ids"] == (1,)
    assert result.source_generated_at == "2026-11-02T08:54:54+00:00"
    assert result.reference_commit_utc == "2026-11-02T08:54:59Z"
    assert result.reference_intake_intervals["taxa_snapshot.json"] == (
        "2026-11-17T18:54:03+00:00",
        "2026-11-17T18:54:07+00:00",
    )
    assert result.chain_manifest_sha256 == chain_pin
    assert result.current_roles_revalidated is False and result.GET_authorized is False
    assert result.summary["frozen_frontier_rows"] == 4
    assert result.summary["unmatched_targets"] == 2
    with pytest.raises(TypeError):
        result.rows[0]["native_id"] = 999


@pytest.mark.parametrize(
    "fault", ["duplicate", "foreign", "authorized", "no_explicit_frontier"]
)
def test_contrast_refuses_ambiguous_or_upgraded_frontier(
    retained: Retained, tmp_path: Path, fault: str
) -> None:
    owner, directory, _, pin = publish(retained, tmp_path)
    rows = [target("taxon", 1)]
    if fault == "duplicate":
        rows.append(dict(rows[0]))
    elif fault == "foreign":
        rows[0]["native_id"] = 2
    elif fault == "authorized":
        rows[0]["GET_authorized"] = True
    else:
        rows.clear()
    chain, chain_pin = frontier(tmp_path, rows)
    function = getattr(owner, "contrast_neotoma_taxonomy_reference_frontier", None)
    assert callable(function), "Metadata-only frontier reference consumer is missing"
    with pytest.raises(ValueError):
        function(
            directory,
            expected_manifest_sha256=pin,
            chain_directory=chain,
            expected_chain_manifest_sha256=chain_pin,
        )


def test_real_generated_sdk_chain_needs_no_baseline_or_body_for_contrast(
    retained: Retained,
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner, directory, _, reference_pin = publish(retained, tmp_path)
    sources, capture_pin = capture_parent(
        chain_products, tmp_path / "generated-capture"
    )
    chain = tmp_path / "sdk-chain"
    _, chain_pin, document = retain_chain(
        chain, sources=sources, parent=None, captures=(capture_pin,)
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )

    def no_baseline(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(
            "Recorded reference contrast attempted source qualification"
        )

    real_open = os.open

    def no_body(path: Any, *args: Any, **kwargs: Any) -> int:
        assert not str(path).endswith(".body")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(ChainOperation, "__enter__", no_baseline)
    monkeypatch.setattr(os, "open", no_body)
    result = owner.contrast_neotoma_taxonomy_reference_frontier(
        directory,
        expected_manifest_sha256=reference_pin,
        chain_directory=chain,
        expected_chain_manifest_sha256=chain_pin,
    )
    assert [row["target_key"] for row in result.rows] == [
        row["target_key"] for row in document["frontier"]
    ]
    assert result.recorded_new_capture_manifest_sha256s == (capture_pin,)
    assert result.current_roles_revalidated is False


def test_publication_pointer_without_text_stays_id_only(
    retained: Retained, tmp_path: Path
) -> None:
    change_metadata(retained, {"1": {"publication": None, "citation": None}})
    owner, directory, _, pin = publish(retained, tmp_path)
    chain, chain_pin = frontier(tmp_path, [target("publication", 99)])
    result = owner.contrast_neotoma_taxonomy_reference_frontier(
        directory,
        expected_manifest_sha256=pin,
        chain_directory=chain,
        expected_chain_manifest_sha256=chain_pin,
    )
    assert result.rows[0]["outcome"] == "observed_publication_id_only"
    assert result.summary["publication_id_only_targets"] == 1
    assert result.summary["citation_text_available_targets"] == 0
    assert result.rows[0]["classification_references"][0]["citation"] is None


def test_all_publication_variants_keep_their_native_taxon_links(
    retained: Retained, tmp_path: Path
) -> None:
    change_metadata(
        retained,
        {
            "3": {
                "publicationid": 99,
                "publication": "different source text",
                "citation": "literal citation",
                "publicationYear": "2000",
            }
        },
    )
    owner, directory, _, pin = publish(retained, tmp_path)
    chain, chain_pin = frontier(tmp_path, [target("publication", 99)])
    result = owner.contrast_neotoma_taxonomy_reference_frontier(
        directory,
        expected_manifest_sha256=pin,
        chain_directory=chain,
        expected_chain_manifest_sha256=chain_pin,
    )
    variants = result.rows[0]["classification_references"]
    assert result.rows[0]["outcome"] == "classification_citation_text_available"
    assert {
        (row["publication"], row["citation"], row["source_taxon_ids"])
        for row in variants
    } == {
        ("fallback reference", None, (1,)),
        ("different source text", "literal citation", (3,)),
    }
