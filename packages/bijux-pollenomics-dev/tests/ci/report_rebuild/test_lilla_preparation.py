"""Bind the qualified Lilla preparation owner without promoting later stages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import check_report_ownership
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)

REPOSITORY = Path(__file__).resolve().parents[5]
OWNER = "regions/nordic/lilla-gloppsjon-direct-pollen/prepared-products"
PROTOCOL_OWNER = "regions/nordic/lilla-gloppsjon-direct-pollen/report-products"
DESCRIPTOR = "configs/ci/qualified-report-sources/lilla-gloppsjon-publication-link.json"
PREPARED = {
    "docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/inputs/input-manifest.json",
    "docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/inputs/metadata.json",
}


def _owners() -> dict[str, dict[str, object]]:
    inventory = json.loads(
        (REPOSITORY / "configs/ci/report-ownership.json").read_text(encoding="utf-8")
    )
    return {row["owner_id"]: row for row in inventory["owners"]}


def test_preparation_has_exact_source_and_output_boundary() -> None:
    owners = _owners()
    prepared = owners[OWNER]
    protocols = owners[PROTOCOL_OWNER]
    prepared_paths = prepared["paths"]
    code_paths = prepared["producer_paths"]
    source_paths = prepared["producer_inputs"]
    protocol_paths = protocols["paths"]
    assert isinstance(prepared_paths, list)
    assert isinstance(code_paths, list)
    assert isinstance(source_paths, list)
    assert isinstance(protocol_paths, list)
    assert prepared["role"] == "generated_owner"
    assert set(prepared_paths) == PREPARED
    assert len(code_paths) == 1019
    assert len(source_paths) == 12
    assert DESCRIPTOR in source_paths
    assert protocols["role"] == "unresolved"
    assert set(protocol_paths) == {
        "docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/protocol.json",
        "docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scoring-protocol.json",
    }
    assert not set(protocol_paths) & PREPARED
    result = check_report_ownership(REPOSITORY)
    assert PROTOCOL_OWNER in result.unresolved_owner_ids
    assert OWNER not in result.unresolved_owner_ids


def test_configured_preparation_requires_qualified_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        configured_owner.resolve_configured_owner(REPOSITORY, OWNER)

    response = tmp_path / "response.json"
    response.write_text('{"capture": true}\n', encoding="utf-8")
    descriptor = REPOSITORY / DESCRIPTOR
    invoked: list[tuple[Path, Path, Path]] = []

    def qualified(
        repository: Path, source_root: Path, source_descriptor: Path
    ) -> QualifiedReportSources:
        invoked.append((repository, source_root, source_descriptor))
        return QualifiedReportSources(
            source_root,
            {DESCRIPTOR: descriptor, "external/lilla/publication-response": response},
            hashlib.sha256(descriptor.read_bytes()).hexdigest(),
        )

    monkeypatch.setattr(
        configured_owner, "validated_external_report_sources", qualified
    )
    selected = configured_owner.resolve_configured_owner(
        REPOSITORY, OWNER, source_root=tmp_path
    )
    assert invoked == [(REPOSITORY, tmp_path, Path(DESCRIPTOR))]
    assert set(selected.expected_outputs) == PREPARED
    assert set(selected.source_paths) == {
        "source-products/input-manifest.json",
        "source-products/metadata.json",
    }
    assert selected.command[-2:] == ("--output", "{output_root}/source-products")
    assert selected.command.count("--source-descriptor") == 1
    assert selected.command.count("--source-root") == 1


@pytest.mark.parametrize("change", ["partial_mapping", "role_change"])
def test_configured_preparation_refuses_mapping_or_role_drift(
    tmp_path: Path, change: str
) -> None:
    config = json.loads(
        (REPOSITORY / "configs/ci/report-owner-execution.json").read_text(
            encoding="utf-8"
        )
    )
    inventory = json.loads(
        (REPOSITORY / "configs/ci/report-ownership.json").read_text(encoding="utf-8")
    )
    if change == "partial_mapping":
        row = next(item for item in config["owners"] if item["owner_id"] == OWNER)
        row["source_paths"].pop("source-products/metadata.json")
    else:
        row = next(item for item in inventory["owners"] if item["owner_id"] == OWNER)
        row["role"] = "unresolved"
    configurations = REPOSITORY / "artifacts/owner-registration"
    configurations.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="lilla-preparation-", dir=configurations
    ) as directory:
        configuration_root = Path(directory)
        config_path = configuration_root / "configuration.json"
        inventory_path = configuration_root / "inventory.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        with pytest.raises(
            ReportRebuildError,
            match="output map differs|not declared generated",
        ):
            configured_owner.resolve_configured_owner(
                REPOSITORY,
                OWNER,
                configuration_path=config_path.relative_to(REPOSITORY),
                inventory_path=inventory_path.relative_to(REPOSITORY),
                source_root=tmp_path,
            )
