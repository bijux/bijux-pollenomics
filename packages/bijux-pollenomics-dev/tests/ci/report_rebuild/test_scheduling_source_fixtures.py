"""Keep declared external table shapes explicit in scheduling-only fixtures."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)

from ... import test_scientific_change_impact as IMPACT

configured_owner_rows = IMPACT.configured_owner_rows


def _fixture_sources(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    loader = cast(
        Callable[[Path, Path, Path], QualifiedReportSources],
        configured_owner.__dict__["validated_external_report_sources"],
    )
    return loader(repository, source_root, descriptor_path)


@pytest.mark.parametrize(
    ("descriptor", "identity", "table", "owner"),
    [
        (
            "solsoe-primary-age-controls.json",
            "landclim/pangaea/solsoe",
            "solsoe81-age-740759.txt",
            "countries/denmark/solsoe-source-lineage/pangaea-core-controls/report-products",
        ),
        (
            "solsoe-published-epd-ages.json",
            "epd/pangaea",
            "epd-age-cut-pangaea-804596.tsv",
            "countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/report-products",
        ),
    ],
)
def test_age_table_fixture_preserves_exact_descriptor_and_one_external_input(
    tmp_path: Path,
    configured_owner_rows: list[dict[str, str]],
    descriptor: str,
    identity: str,
    table: str,
    owner: str,
) -> None:
    relative = Path("configs/ci/qualified-report-sources") / descriptor
    store = tmp_path / "source-store"
    result = _fixture_sources(IMPACT.REPO_ROOT, store, relative)
    assert {row["id"] for row in configured_owner_rows} >= {owner}
    external = f"external/{identity}/{table}"
    assert set(result.inputs) == {relative.as_posix(), external}
    assert result.inputs[relative.as_posix()] == IMPACT.REPO_ROOT / relative
    assert result.inputs[external] == store / identity / table
    assert result.inputs[external].read_text() == "synthetic archive-layout fixture\n"
    assert result.directory == store / identity
    assert result.descriptor_sha256 == "a" * 64


def test_unknown_external_schema_remains_an_explicit_fixture_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    repository = tmp_path / "repository"
    relative = Path("configs/ci/qualified-report-sources/unreviewed.json")
    descriptor = repository / relative
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps({"source_id": "unreviewed", "schema_version": "unreviewed.v1"})
    )
    monkeypatch.setattr(IMPACT, "REPO_ROOT", repository)

    def schedule(root: Path, *, source_root: Path) -> dict[str, list[dict[str, str]]]:
        _fixture_sources(root, source_root, relative)
        return {"owners": []}

    monkeypatch.setattr(IMPACT, "configured_owner_schedule", schedule)
    with pytest.raises(AssertionError, match="Unreviewed synthetic source schema"):
        request.getfixturevalue("configured_owner_rows")
