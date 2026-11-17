"""Bind public provenance dates to retained metadata without native-age inference."""

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from .test_archive import Retained, encoded, publish, retained  # noqa: F401


def rehash(directory: Path, change: Callable[[dict[str, Any]], None]) -> str:
    """Create an internally hashed generated contradiction at the public reader."""
    provenance_path = directory / "provenance.json"
    provenance = json.loads(provenance_path.read_bytes())
    change(provenance)
    raw = encoded(provenance)
    provenance_path.write_bytes(raw)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["provenance.json"] = {
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    manifest_path.write_bytes(encoded(manifest))
    return sha256(manifest_path.read_bytes()).hexdigest()


@pytest.mark.parametrize("reader", ["inventory", "taxa"])
def test_rehashed_commit_date_must_match_retained_commit(
    retained: Retained,  # noqa: F811
    tmp_path: Path,
    reader: str,
) -> None:
    owner, directory, _, _ = publish(retained, tmp_path)
    pin = rehash(
        directory, lambda value: value.__setitem__("commit_utc", "1999-01-01T00:00:00Z")
    )
    commit = json.loads((directory / "evidence/commit.json").read_bytes())
    assert commit["committer"]["date"] == "2026-11-02T08:54:59Z"
    with pytest.raises(ValueError):
        if reader == "inventory":
            owner.read_neotoma_taxonomy_reference_inventory(
                directory, expected_manifest_sha256=pin
            )
        else:
            owner.read_neotoma_taxonomy_reference_taxa(
                directory, expected_manifest_sha256=pin, taxon_ids=(1,)
            )


def test_rehashed_intake_interval_must_not_run_backwards(
    retained: Retained,  # noqa: F811
    tmp_path: Path,
) -> None:
    owner, directory, _, _ = publish(retained, tmp_path)

    def reverse(value: dict[str, Any]) -> None:
        row = value["transport"]["taxa_snapshot.json"]
        row["intake_start"], row["intake_end"] = row["intake_end"], row["intake_start"]

    pin = rehash(directory, reverse)
    with pytest.raises(ValueError):
        owner.read_neotoma_taxonomy_reference_inventory(
            directory, expected_manifest_sha256=pin
        )
