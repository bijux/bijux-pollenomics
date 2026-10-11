"""Private source-to-member publication and independent raw replay refusals."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.contracts import (
    canonical_bytes,
)
from bijux_pollenomics.collection.sources.aadr.materialization.members import (
    inspect_aadr_member_bundle,
    materialize_aadr_evidence_members,
)

from ..accountability.test_service import _write_release


def test_materialization_has_real_non_admitting_inspection_consumer(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    _write_release(data)
    first = materialize_aadr_evidence_members(
        data_root=data, version="v66", output_root=tmp_path / "one"
    )
    second = materialize_aadr_evidence_members(
        data_root=data, version="v66", output_root=tmp_path / "two"
    )
    assert first.manifest_bytes == second.manifest_bytes
    assert len(first.member_ids()) == 2
    evidence = first.member_evidence(first.member_ids()[0])
    member = evidence["member"]
    assert isinstance(member, dict)
    assert member["genetic_id"] == "ID-DK"
    assert evidence["source_rows"]
    assert evidence["coordinate_claims"]
    assert evidence["chronology_claims"]
    manifest = json.loads(first.manifest_bytes)
    assert manifest["denominators"]["source_row_count"] == 2
    assert manifest["admission_boundary"]["scientifically_admitted"] is False
    assert len(list(first.directory.iterdir())) == 7
    assert not (data / "adna/species/homo_sapiens/normalized").exists()


def test_rehashed_raw_token_forgery_is_rejected_by_actual_raw_replay(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    _write_release(data)
    bundle = materialize_aadr_evidence_members(
        data_root=data, version="v66", output_root=tmp_path / "bundle"
    )
    path = bundle.directory / "source_rows.ndjson"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["raw_tokens"][-1] = "not from raw source"
    changed = b"".join(canonical_bytes(row) for row in rows)
    path.write_bytes(changed)
    manifest = json.loads(bundle.manifest_bytes)
    manifest["files"][path.name].update(
        byte_count=len(changed), sha256=sha256(changed).hexdigest()
    )
    content = canonical_bytes(manifest)
    (bundle.directory / "manifest.json").write_bytes(content)
    with pytest.raises(ValueError, match="raw replay/member projection mismatch"):
        inspect_aadr_member_bundle(
            bundle.directory,
            expected_sha256=sha256(content).hexdigest(),
            data_root=data,
        )


def test_existing_output_and_source_overlap_refuse(tmp_path: Path) -> None:
    data = tmp_path / "data"
    _write_release(data)
    with pytest.raises(ValueError, match="overlap"):
        materialize_aadr_evidence_members(
            data_root=data, version="v66", output_root=data / "nested"
        )
    output = tmp_path / "owned"
    output.mkdir()
    (output / "owner").write_text("retained")
    with pytest.raises(FileExistsError):
        materialize_aadr_evidence_members(
            data_root=data, version="v66", output_root=output
        )
    assert (output / "owner").read_text() == "retained"


def test_source_mutation_after_verified_inspection_does_not_relabel_saved_bytes(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    _write_release(data)
    bundle = materialize_aadr_evidence_members(
        data_root=data, version="v66", output_root=tmp_path / "bundle"
    )
    panel = data / "aadr/v66/ho/v66.HO.aadr.PUB.anno"
    panel.write_bytes(panel.read_bytes().replace(b"ID-SE", b"ID-XX"))
    with pytest.raises(ValueError, match="md5 mismatch"):
        inspect_aadr_member_bundle(
            bundle.directory, expected_sha256=bundle.manifest_sha256, data_root=data
        )


def test_atomic_race_preserves_competing_owner_and_staging(tmp_path: Path) -> None:
    from bijux_pollenomics.core.owned_tree import publish_new_output_tree

    data = tmp_path / "data"
    _write_release(data)
    output = tmp_path / "owned"

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        output.mkdir()
        (output / "owner").write_text("competitor")
        publish_new_output_tree(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    with (
        patch(
            "bijux_pollenomics.collection.sources.aadr.materialization.members.service.publish_new_output_tree",
            side_effect=race,
        ),
        pytest.raises(FileExistsError),
    ):
        materialize_aadr_evidence_members(
            data_root=data, version="v66", output_root=output
        )
    assert (output / "owner").read_text() == "competitor"
    assert list(tmp_path.glob(".aadr-members-*"))


def test_inspection_cannot_be_constructed_without_raw_replay() -> None:
    from bijux_pollenomics.collection.sources.aadr.materialization.members import (
        AadrMemberInspection,
    )

    with pytest.raises(TypeError, match="raw-replayed inspection"):
        AadrMemberInspection()
