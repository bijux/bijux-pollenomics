"""Reject source attribution/refusal corruption without retained producers or decoding."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    pangaea_abbo_profile as profile_contract,
)
from bijux_pollenomics_dev.source_completion.neotoma import abbo_profile
from bijux_pollenomics_dev.source_completion.neotoma import (
    native_correspondence as native,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("descriptor", list(native.CASES))
@pytest.mark.parametrize(
    "mutation",
    ["valid", "raw-hash", "workbook-hash", "extra-hash", "basin", "false-lra"],
)
def test_native_source_identity_and_refusal_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor: Path, mutation: str
) -> None:
    repository, store = tmp_path / "repository", tmp_path / "external"
    case = native.CASES[descriptor]
    raw = repository / case.raw
    workbook = store / native.SOURCE_ID / case.workbook
    for path in (raw, workbook):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic identity only; never decode")
    report: dict[str, Any] = {
        "schema_version": case.schema,
        "neotoma_dataset_id": case.dataset,
        "neotoma_site_id": case.site,
        "rootsi_archive_member": case.workbook,
        "lra_admitted_samples": 0,
        "basin_radius_transfer": "refused",
        "input_sha256": {
            "neotoma_raw_part": digest(raw),
            "rootsi_workbook": digest(workbook),
        },
    }
    before = copy.deepcopy(report)
    if mutation == "raw-hash":
        report["input_sha256"]["neotoma_raw_part"] = "0" * 64
    if mutation == "workbook-hash":
        report["input_sha256"]["rootsi_workbook"] = "0" * 64
    if mutation == "extra-hash":
        report["input_sha256"]["unqualified_source"] = "0" * 64
    if mutation == "basin":
        report["basin_radius_transfer"] = "admitted"
    if mutation == "false-lra":
        report["lra_admitted_samples"] = False

    def publication(*args: Any) -> dict[str, Any]:
        args[-1](report)
        return report

    monkeypatch.setattr(native, "publish", publication)
    if mutation == "valid":
        assert native.run(repository, store, descriptor, tmp_path / "output") == before
    else:
        with pytest.raises(ReportRebuildError):
            native.run(repository, store, descriptor, tmp_path / "output")


@pytest.mark.parametrize(
    "mutation",
    [
        "valid",
        "doi",
        "url",
        "license",
        "source-hash",
        "sequence-hash",
        "support",
        "handle",
        "unit",
        "unknown-unit",
        "absent-unit",
        "zero-geometry",
        "zero-lra",
    ],
)
def test_profile_attribution_and_nonadmission_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    repository, store = tmp_path / "repository", tmp_path / "external"
    table = store / profile_contract.SOURCE_ID / profile_contract.TABLE
    manifest = repository / abbo_profile.SEQUENCE / "manifest.json"
    for path in (table, manifest):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic metadata identity; no source interpretation")
    report: dict[str, Any] = {
        "schema_version": "neotoma-abbo-pangaea-lineage.v1",
        "dataset_id": "19913",
        "site_id": "13338",
        "historical_basin_geometry_admitted": False,
        "lra_input_admitted": False,
        "source_profile_doi": profile_contract.DOI,
        "source_profile_url": "https://doi.pangaea.de/" + profile_contract.DOI,
        "source_profile_license": "CC-BY-NC-3.0",
        "source_profile_sha256": digest(table),
        "governed_sequence_manifest_sha256": digest(manifest),
        "pangaea_area_temporal_support": "source_event_metadata_only",
        "source_core_handle": "ABBO",
        "source_depth_unit": "m",
        "neotoma_depth_source_unit": None,
    }
    before = copy.deepcopy(report)
    changes = {
        "doi": ("source_profile_doi", "10.1594/PANGAEA.other"),
        "url": ("source_profile_url", "https://unrelated.invalid/"),
        "license": ("source_profile_license", "CC0"),
        "source-hash": ("source_profile_sha256", "0" * 64),
        "sequence-hash": ("governed_sequence_manifest_sha256", "0" * 64),
        "support": ("pangaea_area_temporal_support", "historical_basin_geometry"),
        "handle": ("source_core_handle", "OTHER"),
        "unit": ("source_depth_unit", "cm"),
        "unknown-unit": ("neotoma_depth_source_unit", "cm"),
        "zero-geometry": ("historical_basin_geometry_admitted", 0),
        "zero-lra": ("lra_input_admitted", 0),
    }
    if mutation in changes:
        name, value = changes[mutation]
        report[name] = value
    if mutation == "absent-unit":
        report.pop("neotoma_depth_source_unit")

    def publication(*args: Any) -> dict[str, Any]:
        args[-1](report)
        return report

    monkeypatch.setattr(abbo_profile, "publish", publication)
    if mutation == "valid":
        assert (
            abbo_profile.run(
                repository, store, abbo_profile.DESCRIPTOR, tmp_path / "output"
            )
            == before
        )
    else:
        with pytest.raises(ReportRebuildError):
            abbo_profile.run(
                repository, store, abbo_profile.DESCRIPTOR, tmp_path / "output"
            )
