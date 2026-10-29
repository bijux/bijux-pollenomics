"""Keep the old canonical publication witness without restoring its retired copy."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden import (
    metadata,
)


def _owned_body() -> bytes:
    """Return only controlled fixture text at the original bounded byte length."""
    return b"Own historical publication fixture.\n".ljust(6879, b" ")


def test_historical_reader_uses_exact_genuine_canonical_Git_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _owned_body()
    seen: list[tuple[Path, GitSourceMember]] = []

    def read(repository: Path, member: GitSourceMember) -> bytes:
        seen.append((repository, member))
        member.validate()
        return body

    monkeypatch.setattr(metadata, "read_blob", read)
    digest = hashlib.sha256(body).hexdigest()
    metadata.validate_historical_reader(tmp_path, digest)
    repository, member = seen[0]
    assert repository == tmp_path
    assert member.member == member.repository_path == metadata.HISTORICAL_READER_PATH
    assert member.source_revision == "d029760ddf2f6853d07e9ac14091df8f041ecbb4"
    assert member.git_blob == "508a1d3e260e1da95483f664485909a14f2533b4"
    assert member.bytes == 6879
    assert member.sha256 == digest
    assert not (
        tmp_path / "data/source-custody/country-reports/sweden/historical-reader.md"
    ).exists()


@pytest.mark.parametrize("damage", ["changed_sha", "wrong_length", "not_ancestor"])
def test_historical_body_or_Git_custody_failure_is_not_rescued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    body = _owned_body()
    digest = "0" * 64 if damage == "changed_sha" else hashlib.sha256(body).hexdigest()

    def read(repository: Path, member: GitSourceMember) -> bytes:
        if damage == "not_ancestor":
            raise ReportRebuildError("Controlled missing genuine ancestor")
        return body[:-1] if damage == "wrong_length" else body

    monkeypatch.setattr(metadata, "read_blob", read)
    with pytest.raises((ValueError, ReportRebuildError)):
        metadata.validate_historical_reader(tmp_path, digest)


def test_current_reader_prose_is_not_assigned_the_old_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _owned_body()
    current = tmp_path / metadata.HISTORICAL_READER_PATH
    current.parent.mkdir(parents=True)
    current.write_bytes(b"Different maintained current prose.\n")
    monkeypatch.setattr(metadata, "read_blob", lambda repository, member: body)
    metadata.validate_historical_reader(tmp_path, hashlib.sha256(body).hexdigest())
    assert current.read_bytes() == b"Different maintained current prose.\n"


@pytest.mark.parametrize(
    "path",
    [
        "docs/report/unreviewed/README.md",
        "data/source-custody/country-reports/sweden/historical-reader.md",
        "reports/needed/private-reader.md",
    ],
)
def test_one_canonical_publication_allowance_does_not_admit_other_paths(
    path: str,
) -> None:
    member = GitSourceMember(
        path,
        path,
        "d029760ddf2f6853d07e9ac14091df8f041ecbb4",
        "508a1d3e260e1da95483f664485909a14f2533b4",
        "1" * 64,
        6879,
    )
    with pytest.raises(ReportRebuildError):
        member.validate()
