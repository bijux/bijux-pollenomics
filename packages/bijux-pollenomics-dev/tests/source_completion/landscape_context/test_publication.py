"""Public geographic evidence excludes raw feature/claim/coordinate populations."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.landscape_context import publication
from bijux_pollenomics_dev.source_completion.landscape_context.report import (
    geodesic_metadata,
)


def test_public_writer_excludes_private_feature_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    output = repository / "artifacts" / "public"
    monkeypatch.setattr(
        sys,
        "argv",
        ["publication", "--repository", str(repository), "--output", str(output)],
    )
    monkeypatch.setattr(publication, "load", lambda root: ([], {}, {}))
    summary: dict[str, Any] = {"ecological_event_admission": False}
    cells = [{"centre": "BUS", "feature_count": 2}]
    monkeypatch.setattr(
        publication,
        "evaluate",
        lambda *args: (
            summary,
            [{"record_id": "private-record", "latitude": 55.0}],
            cells,
            [{"site_uuid": "private-uuid"}],
        ),
    )
    assert publication.main() == 0
    assert {path.name for path in output.iterdir()} == {
        "geodesic-sensitivity.json",
        "geodesic-window-cells.csv",
    }
    encoded = b"".join(path.read_bytes() for path in output.iterdir())
    assert b"private-record" not in encoded and b"private-uuid" not in encoded
    assert json.loads((output / "geodesic-sensitivity.json").read_bytes()) == {
        "ecological_event_admission": False,
        "geodesic": geodesic_metadata(),
    }


def test_public_writer_refuses_existing_output_before_reading_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "artifacts" / "public"
    output.mkdir(parents=True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["publication", "--repository", str(tmp_path), "--output", str(output)],
    )

    def unread(root: Path) -> Any:
        raise AssertionError("Refused output must be checked before source access")

    monkeypatch.setattr(publication, "load", unread)
    with pytest.raises(ReportRebuildError, match="must be absent"):
        publication.main()
