"""A linked current API source must fail before any historical source read."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_site_evaluations as author,
)


def test_hardlinked_spatial_source_is_refused_before_historical_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = tmp_path / "spatial-source.py"
    current.write_bytes(b"own current API source fixture\n")
    (tmp_path / "linked-current-source.py").hardlink_to(current)
    assert current.stat().st_nlink == 2
    source_row = {
        "path": author.SPATIAL_EXPORT_SOURCE,
        "sha256": author.SPATIAL_HISTORICAL_SHA256,
        "bytes": author.SPATIAL_HISTORICAL_BYTES,
    }
    members = [
        {"path": f"own/{index}.json", "sha256": "a" * 64, "bytes": 1}
        for index in range(author.EXPECTED_MEMBERS - 1)
    ]
    members.append(
        {
            **source_row,
            "path": "executions/uncertainty/first-party-inputs/"
            + author.SPATIAL_EXPORT_SOURCE,
        }
    )
    document = {
        "schema_version": "retained-author-site-evaluation-source-capture.v1",
        "member_count": author.EXPECTED_MEMBERS,
        "members": members,
        "current_scientific_source_projection": [source_row]
        + [{"path": f"own-current/{index}.py"} for index in range(177)],
    }
    captured = tmp_path / "capture.json"
    raw = json.dumps(document, sort_keys=True).encode()
    captured.write_bytes(raw)
    monkeypatch.setattr(author, "CAPTURE_SHA256", hashlib.sha256(raw).hexdigest())

    def confined_file(_repository: Path, name: str) -> Path:
        return captured if name == author.CAPTURE else current

    def forbidden_source_read(_member: str) -> bytes:
        pytest.fail("Linked current source must fail before source transport")

    def no_native_reference(*_args: object) -> None:
        pass

    buffer = SimpleNamespace(read_source=forbidden_source_read)
    monkeypatch.setattr(author, "_file", confined_file)
    monkeypatch.setattr(author, "_native_references", no_native_reference)
    monkeypatch.setattr(
        author, "_validate_author_owner_partition", lambda _owners: None
    )
    monkeypatch.setattr(author, "validated_descriptor", lambda *_args: buffer)
    owners = [{"owner_id": sorted(author.OWNERS)[0], "role": "retained_source"}]
    with pytest.raises(ReportRebuildError, match="scientific implementation changed"):
        author.validated_author_site_evaluation_captures(tmp_path, {}, owners)
