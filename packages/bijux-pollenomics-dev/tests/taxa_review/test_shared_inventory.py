"""Shared private inventories retain confinement, snapshot identity and quarantine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.evidence import EvidenceReader
from bijux_pollenomics_dev.taxa_review import workflow
from bijux_pollenomics_dev.taxa_review.quarantine import rootsi_rows


def inventory_bytes(**changes: Any) -> bytes:
    payload = {
        "schema_version": "quarantined-rootsi-header-review.v1",
        "archive_sha256": "controlled-original-archive",
        "publication_allowed": False,
        "derived_analysis_allowed": False,
        "workbooks": [{}],
        "headers": [
            {
                "archive_member": "source.xls",
                "sheet": "sheet",
                "column_index": 1,
                "source_header_candidates": ["candidate", None],
            }
        ],
        **changes,
    }
    return json.dumps(payload).encode()


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path.resolve() / "repository"
    contract = root / workflow.CONTRACT_PATH
    contract.parent.mkdir(parents=True)
    contract.write_text("{}\n")
    for name in ("neotoma_rows", "sead_rows", "adna_rows"):
        monkeypatch.setattr(workflow, name, lambda reader: ([], {}))
    for name in ("landclim_rows", "parameter_rows"):
        monkeypatch.setattr(workflow, name, lambda reader: [])
    return root


@pytest.fixture
def shared_inventory(tmp_path: Path) -> Path:
    path = tmp_path.resolve() / "shared" / "inventory.json"
    path.parent.mkdir()
    path.write_bytes(inventory_bytes())
    return path


def test_explicit_shared_inventory_is_read_once_in_identity_and_stays_quarantined(
    repository: Path, shared_inventory: Path
) -> None:
    original = shared_inventory.read_bytes()
    result = workflow.build_review(repository, rootsi_inventory=str(shared_inventory))
    identities = [
        row for row in result["input_files"] if row["path"] == str(shared_inventory)
    ]
    assert identities == [
        {
            "path": str(shared_inventory),
            "presence": "present",
            "byte_count": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
        }
    ]
    assert len(result["input_files"]) == 2
    assert result["row_count"] == 1
    assert result["rows"][0]["supporting_evidence"]["inventory_path"] == str(
        shared_inventory
    )
    assert result["rows"][0]["derived_analysis_allowed"] is False
    assert result["scientific_admission_allowed"] is False
    assert result["publication_allowed"] is False
    assert result["source_summaries"]["rootsi"]["header_row_selection"].startswith(
        "unresolved"
    )
    assert shared_inventory.read_bytes() == original
    assert not (repository / "artifacts").exists()


def test_relative_and_absolute_in_repository_inventory_keep_original_reader(
    repository: Path, shared_inventory: Path
) -> None:
    path = repository / "inventory.json"
    path.write_bytes(inventory_bytes())
    relative = workflow.build_review(repository, rootsi_inventory="inventory.json")
    absolute = workflow.build_review(repository, rootsi_inventory=str(path))
    shared = workflow.build_review(repository, rootsi_inventory=str(shared_inventory))
    assert {row["path"] for row in relative["input_files"]} == {
        workflow.CONTRACT_PATH,
        "inventory.json",
    }
    assert relative["rows"][0]["review_row_id"] == absolute["rows"][0]["review_row_id"]
    assert relative["rows"][0]["review_row_id"] == shared["rows"][0]["review_row_id"]
    assert relative["bundle_sha256"] != absolute["bundle_sha256"]
    assert (
        relative["rows"][0]["source_identity_sha256"]
        != absolute["rows"][0]["source_identity_sha256"]
    )


def test_explicit_inventory_does_not_relax_generic_or_relative_confinement(
    repository: Path, shared_inventory: Path
) -> None:
    with pytest.raises(ValueError, match="escapes repository"):
        EvidenceReader(repository).json(str(shared_inventory))
    with pytest.raises(ValueError, match="escapes repository"):
        workflow.build_review(repository, rootsi_inventory="../shared/inventory.json")


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "parent_symlink"])
def test_external_inventory_requires_a_physical_file(
    repository: Path, shared_inventory: Path, kind: str
) -> None:
    if kind == "missing":
        path = shared_inventory.with_name("absent.json")
    elif kind == "directory":
        path = shared_inventory.parent
    elif kind == "symlink":
        path = shared_inventory.with_name("link.json")
        path.symlink_to(shared_inventory)
    else:
        parent = shared_inventory.parent.with_name("linked-store")
        parent.symlink_to(shared_inventory.parent, target_is_directory=True)
        path = parent / shared_inventory.name
    with pytest.raises(ValueError, match="physical file"):
        workflow.build_review(repository, rootsi_inventory=str(path))


@pytest.mark.parametrize("change", ["bytes", "missing", "symlink"])
def test_shared_inventory_is_rechecked_after_projection(
    repository: Path,
    shared_inventory: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    def changing_rows(
        reader: EvidenceReader, path: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        result = rootsi_rows(reader, path)
        if change == "bytes":
            shared_inventory.write_bytes(inventory_bytes(archive_sha256="changed"))
        elif change == "missing":
            shared_inventory.unlink()
        else:
            target = shared_inventory.with_name("replacement.json")
            target.write_bytes(shared_inventory.read_bytes())
            shared_inventory.unlink()
            shared_inventory.symlink_to(target)
        return result

    monkeypatch.setattr(workflow, "rootsi_rows", changing_rows)
    with pytest.raises(ValueError, match="changed during audit|physical file"):
        workflow.build_review(repository, rootsi_inventory=str(shared_inventory))


@pytest.mark.parametrize("field", ["publication_allowed", "derived_analysis_allowed"])
def test_shared_inventory_cannot_promote_quarantine(
    repository: Path, shared_inventory: Path, field: str
) -> None:
    shared_inventory.write_bytes(inventory_bytes(**{field: True}))
    with pytest.raises(ValueError, match="quarantine restrictions"):
        workflow.build_review(repository, rootsi_inventory=str(shared_inventory))
