from __future__ import annotations

import hashlib
from pathlib import Path
from typing import IO

import pytest
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi import normalization


def test_intake_posture_does_not_extend_pangaea_rights() -> None:
    posture = normalization.rootsi_intake_posture()

    assert posture.lifecycle_state == "quarantined"
    assert posture.source_identity_status == "candidate"
    assert posture.candidate_dataset_license == "CC-BY-4.0"
    assert not posture.candidate_license_applies_to_archive
    assert posture.licence_id is None
    assert not posture.public_release_allowed
    assert not posture.propagation_use_allowed
    assert "per_sequence_rights_unresolved" in posture.blockers
    assert "time_basis_mixed" in posture.blockers
    assert "unit_denominator_unresolved" in posture.blockers


def test_observation_values_are_refused_with_all_scientific_blockers() -> None:
    with pytest.raises(IntakeRefusal) as caught:
        normalization.refuse_rootsi_observations()

    assert caught.value.reason_code == "rootsi_observations_not_admitted"
    message = str(caught.value)
    for concept in ("rights", "coordinates", "chronology", "taxonomy", "units"):
        assert concept in message


def test_archive_identity_is_byte_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "rootsi.7z"
    path.write_bytes(b"exact receipt")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(normalization, "ARCHIVE_SHA256", digest)
    monkeypatch.setattr(normalization, "ARCHIVE_SIZE_BYTES", len(path.read_bytes()))

    identity = normalization.identify_rootsi_archive(path)

    assert identity.sha256 == digest
    assert identity.media_type == "application/x-7z-compressed"
    path.write_bytes(b"changed receipt")
    with pytest.raises(IntakeRefusal, match="archive_digest_mismatch"):
        normalization.identify_rootsi_archive(path)


def test_archive_identity_keeps_hash_and_size_on_one_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "rootsi.7z"
    original = b"original-receipt"
    replacement = b"replaced-receipt"
    assert len(original) == len(replacement)
    path.write_bytes(original)
    replacement_path = tmp_path / "replacement.7z"
    replacement_path.write_bytes(replacement)
    expected_digest = hashlib.sha256(original).hexdigest()
    real_sha256_stream = normalization.sha256_stream

    def replace_path_after_descriptor_open(stream: IO[bytes]) -> str:
        replacement_path.replace(path)
        return real_sha256_stream(stream)

    monkeypatch.setattr(normalization, "ARCHIVE_SHA256", expected_digest)
    monkeypatch.setattr(normalization, "ARCHIVE_SIZE_BYTES", len(original))
    monkeypatch.setattr(
        normalization, "sha256_stream", replace_path_after_descriptor_open
    )

    identity = normalization.identify_rootsi_archive(path)

    assert identity.sha256 == expected_digest
    assert identity.size_bytes == len(original)
    assert path.read_bytes() == replacement
