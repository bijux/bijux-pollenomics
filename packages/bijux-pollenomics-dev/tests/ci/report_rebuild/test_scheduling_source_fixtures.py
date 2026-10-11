"""Keep declared external table shapes explicit in scheduling-only fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)

from ... import test_scientific_change_impact as IMPACT

configured_owner_rows = IMPACT.configured_owner_rows


def _fixture_sources(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    return IMPACT.synthetic_scheduling_sources(repository, source_root, descriptor_path)


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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    relative = Path("configs/ci/qualified-report-sources/unreviewed.json")
    descriptor = repository / relative
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps({"source_id": "unreviewed", "schema_version": "unreviewed.v1"})
    )
    monkeypatch.setattr(IMPACT, "REPO_ROOT", repository)

    with pytest.raises(AssertionError, match="Unreviewed synthetic source schema"):
        _fixture_sources(repository, tmp_path / "source-store", relative)


@pytest.mark.parametrize(
    ("descriptor_name", "identity", "expected_external"),
    [
        (
            "rootsi-bokesjon-workbook.json",
            "landclim/rootsi-workbooks",
            {"manifest.json", "rootsi/BOKE.xls"},
        ),
        (
            "rootsi-abborrtjarne-workbook.json",
            "landclim/rootsi-workbooks",
            {"manifest.json", "rootsi/BOKE.xls", "rootsi/ABB.xls"},
        ),
        (
            "rootsi-bussjosjon-workbook.json",
            "landclim/rootsi-workbooks",
            {"manifest.json", "rootsi/BOKE.xls", "rootsi/BUS.xls"},
        ),
        (
            "abbo-pollen-profile.json",
            "epd/pangaea",
            {"abbo-pollen-profile-pangaea-738429.tsv"},
        ),
    ],
)
def test_retained_source_fixture_preserves_exact_descriptor_dependency_population(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    descriptor_name: str,
    identity: str,
    expected_external: set[str],
) -> None:
    repository = tmp_path / "repository"
    folder = Path("configs/ci/qualified-report-sources")
    relative = folder / descriptor_name
    files = [relative]
    if descriptor_name in {
        "rootsi-abborrtjarne-workbook.json",
        "rootsi-bussjosjon-workbook.json",
    }:
        files.append(folder / "rootsi-bokesjon-workbook.json")
    expected_bytes = {}
    for name in files:
        payload = (IMPACT.REPO_ROOT / name).read_bytes()
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        expected_bytes[name] = payload
    monkeypatch.setattr(IMPACT, "REPO_ROOT", repository)
    result = _fixture_sources(repository, tmp_path / "source-store", relative)
    external = {f"external/{identity}/{name}" for name in expected_external}
    assert set(result.inputs) == {name.as_posix() for name in files} | external
    assert result.directory == tmp_path / "source-store" / identity
    assert result.descriptor_sha256 == "a" * 64
    for name in files:
        assert result.inputs[name.as_posix()] == repository / name
        assert (repository / name).read_bytes() == expected_bytes[name]
    for external_name in expected_external:
        path = tmp_path / "source-store" / identity / external_name
        assert result.inputs[f"external/{identity}/{external_name}"] == path
        assert path.read_text() == "synthetic archive-layout fixture\n"


@pytest.mark.parametrize(
    "refusal",
    ["unknown_without_identity", "base_schema", "base_escape", "foreign_member"],
)
def test_retained_source_fixture_refuses_unreviewed_schema_or_native_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refusal: str,
) -> None:
    repository = tmp_path / "repository"
    folder = Path("configs/ci/qualified-report-sources")
    relative = folder / "rootsi-abborrtjarne-workbook.json"
    base_path = folder / "rootsi-bokesjon-workbook.json"
    descriptor = json.loads((IMPACT.REPO_ROOT / relative).read_bytes())
    base = json.loads((IMPACT.REPO_ROOT / base_path).read_bytes())
    if refusal == "unknown_without_identity":
        descriptor["schema_version"] = "qualified-rootsi-native-workbook.v2"
    elif refusal == "base_schema":
        base["schema_version"] = "unreviewed.v1"
    elif refusal == "base_escape":
        descriptor["base_descriptor"] = "../foreign.json"
    else:
        descriptor["workbook"]["path"] = "rootsi/FOREIGN.xls"
    for name, value in [(relative, descriptor), (base_path, base)]:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
    monkeypatch.setattr(IMPACT, "REPO_ROOT", repository)

    with pytest.raises(AssertionError):
        _fixture_sources(repository, tmp_path / "source-store", relative)
    assert not (tmp_path / "source-store").exists()
