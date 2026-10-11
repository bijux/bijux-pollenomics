"""Real publication, raw replay and no-overwrite output boundaries."""

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.raa.materialization import (
    audit_raa_geopackage,
    inspect_raa_ownership_audit,
    service,
)
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .support import A, identity


def test_actual_files_repeat_replay_and_selected_nested_lineage(
    database: Path, tmp_path: Path
) -> None:
    digest, size = identity(database)
    for name in ("first", "second"):
        audit_raa_geopackage(
            database,
            expected_sha256=digest,
            expected_byte_count=size,
            output_directory=tmp_path / name,
        )
    for member in ("manifest.json", "rows.ndjson"):
        assert (tmp_path / "first" / member).read_bytes() == (
            tmp_path / "second" / member
        ).read_bytes()
    manifest_sha = sha256((tmp_path / "first/manifest.json").read_bytes()).hexdigest()
    result = inspect_raa_ownership_audit(
        tmp_path / "first",
        expected_manifest_sha256=manifest_sha,
        source_path=database,
        expected_source_sha256=digest,
        expected_source_byte_count=size,
        native_uuid=A,
    )
    selected = json.loads(canonical_bytes(result))
    assert selected["raw_replay_verified"] is True
    assert any(
        row["table"] == "egenskap" and row["fid"] == 2
        for row in selected["selected_source_rows"]
    )
    assert identity(database) == (digest, size)


def test_rehashed_saved_source_change_refuses_raw_replay(
    database: Path, tmp_path: Path
) -> None:
    digest, size = identity(database)
    out = tmp_path / "audit"
    audit_raa_geopackage(
        database, expected_sha256=digest, expected_byte_count=size, output_directory=out
    )
    docs = [
        json.loads(line) for line in (out / "rows.ndjson").read_bytes().splitlines()
    ]
    next(row for row in docs if row.get("table") == "lamning")["source_values"][
        "uuid"
    ] = "forged"
    content = b"".join(canonical_bytes(row) for row in docs)
    (out / "rows.ndjson").write_bytes(content)
    manifest = json.loads((out / "manifest.json").read_bytes())
    manifest["files"]["rows.ndjson"].update(
        sha256=sha256(content).hexdigest(), byte_count=len(content)
    )
    payload = canonical_bytes(manifest)
    (out / "manifest.json").write_bytes(payload)
    with pytest.raises(ValueError, match="raw replay"):
        inspect_raa_ownership_audit(
            out,
            expected_manifest_sha256=sha256(payload).hexdigest(),
            source_path=database,
            expected_source_sha256=digest,
            expected_source_byte_count=size,
        )


def test_output_overlap_and_no_replace_race(
    database: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digest, size = identity(database)
    with pytest.raises(ValueError, match="overlap"):
        audit_raa_geopackage(
            database,
            expected_sha256=digest,
            expected_byte_count=size,
            output_directory=tmp_path / "bridge/../raw/inside",
        )
    assert not (tmp_path / "bridge").exists()
    assert set(database.parent.iterdir()) == {database}
    original = publish_new_output_tree

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "other-owner").write_text("preserve")
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(service, "publish_new_output_tree", race)
    with pytest.raises(FileExistsError):
        audit_raa_geopackage(
            database,
            expected_sha256=digest,
            expected_byte_count=size,
            output_directory=tmp_path / "race",
        )
    assert (tmp_path / "race/other-owner").read_text() == "preserve"
    assert not (tmp_path / "race/manifest.json").exists()
