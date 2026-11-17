"""Distinguish commit-addressed API tree labels from canonical Git tree identity."""

import json
from pathlib import Path

import pytest

from .test_archive import Retained, api, encoded, publish, source


@pytest.mark.parametrize("address", ["tree", "commit"])
def test_root_tree_address_preserves_canonical_membership_and_original_evidence(
    retained: Retained, tmp_path: Path, address: str
) -> None:
    """A commit selector is accepted only with its independently bound tree bytes."""
    _, _, evidence, _, revision = retained
    root = json.loads(evidence["root_tree"].read_bytes())
    canonical_tree = root["sha"]
    if address == "commit":
        root["sha"] = revision
        root["url"] = root["url"].rsplit("/", 1)[0] + "/" + revision
        evidence["root_tree"].write_bytes(encoded(root))
    original = evidence["root_tree"].read_bytes()
    owner, archive, _, pin = publish(retained, tmp_path)
    inventory = owner.read_neotoma_taxonomy_reference_inventory(
        archive, expected_manifest_sha256=pin
    )
    record = owner.read_neotoma_taxonomy_reference_taxa(
        archive, expected_manifest_sha256=pin, taxon_ids=(1,)
    )
    assert record[0].native_id == 1
    assert (archive / "evidence/root_tree.json").read_bytes() == original
    commit = json.loads((archive / "evidence/commit.json").read_bytes())
    assert commit["tree"]["sha"] == canonical_tree
    assert inventory.provenance["source_revision"] == revision
    assert inventory.source_entity_bodies_verified is False


@pytest.mark.parametrize("mismatch", ["foreign_selector", "canonical_content"])
def test_commit_tree_address_cannot_lend_foreign_identity(
    retained: Retained, tmp_path: Path, mismatch: str
) -> None:
    """Neither a foreign selector nor a claimed tree hash replaces reconstruction."""
    _, _, evidence, _, revision = retained
    root = json.loads(evidence["root_tree"].read_bytes())
    root["sha"] = revision if mismatch == "canonical_content" else "b" * 40
    root["url"] = root["url"].rsplit("/", 1)[0] + "/" + root["sha"]
    evidence["root_tree"].write_bytes(encoded(root))
    if mismatch == "canonical_content":
        commit = json.loads(evidence["commit"].read_bytes())
        commit["tree"]["sha"] = "b" * 40
        commit["tree"]["url"] = root["url"].rsplit("/", 1)[0] + "/" + "b" * 40
        evidence["commit"].write_bytes(encoded(commit))
    owner = api()
    output = tmp_path / "refused-archive"
    with pytest.raises(ValueError, match="Git tree identity"):
        owner.write_neotoma_taxonomy_reference_archive(
            output, source_provenance=source(owner, retained)
        )
    assert not output.exists()
