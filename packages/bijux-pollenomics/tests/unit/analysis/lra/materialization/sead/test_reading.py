"""Source-owned normalization must match pinned raw data, beyond member hashes."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.sead.reading import (
    read_sead_evidence,
)

from .support import admitted_fixture


def test_full_fixture_uses_real_country_and_raw_validation(tmp_path: Path) -> None:
    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    evidence = read_sead_evidence(raw, normalized, expected_identity=expected)
    assert (
        len(list(evidence.rows("source_native_observations.json", "observations"))) == 4
    )
    assert evidence.manifest()["source_table_count"] == 61
    assert b"exact_source_replay_match" in evidence.replay_receipt_bytes
    evidence.assert_unchanged()
    member = normalized / "source_native_observations.json"
    member.write_bytes(member.read_bytes() + b" ")
    with pytest.raises(ValueError, match="changed"):
        evidence.document(member.name)


def test_rehashed_native_value_forgery_is_rejected_by_raw_replay(
    tmp_path: Path,
) -> None:
    import hashlib
    import json

    from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
    from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
        validate_sead_source_native_evidence_materialization,
    )
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _stable_id,
    )

    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    raw_before = {
        path.relative_to(raw).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in raw.rglob("*")
        if path.is_file()
    }
    member = normalized / "source_native_observations.json"
    document = json.loads(member.read_bytes())
    row = document["observations"][0]
    row["source_value"] = 2
    row["source_row"][row["source_value_field"]] = 2
    member.write_bytes(canonical_bytes(document))
    manifest_path = normalized / "evidence_materialization_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for record in manifest["files"]:
        data = (normalized / record["path"]).read_bytes()
        record.update(sha256=hashlib.sha256(data).hexdigest(), byte_count=len(data))
    manifest["file_set_sha256"] = _stable_id(
        "sead-evidence-files",
        *(
            f"{record['path']}:{record['sha256']}:{record['byte_count']}"
            for record in sorted(manifest["files"], key=lambda item: item["path"])
        ),
    ).removeprefix("sead-evidence-files:")
    manifest_path.write_bytes(canonical_bytes(manifest))
    validate_sead_source_native_evidence_materialization(normalized)
    with pytest.raises(ValueError, match="raw projection differs"):
        read_sead_evidence(raw, normalized, expected_identity=expected)
    assert raw_before == {
        path.relative_to(raw).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in raw.rglob("*")
        if path.is_file()
    }
