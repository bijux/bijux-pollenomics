"""Historical country coverage requires a source-bound retrieval report."""

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest
from bijux_pollenomics_dev.source_completion import sead_country_coverage as owner


@pytest.mark.parametrize("excluded_id", ["3447", "3457", "3528", "3652"])
def test_historical_retrieval_rejects_identity_and_refusal_changes(
    monkeypatch: pytest.MonkeyPatch, excluded_id: str
) -> None:
    root = Path(__file__).resolve().parents[4]
    sites = (
        root / "docs/report/source-relations/sead-country-retrieval/sites.csv"
    ).read_bytes()
    site_sha, lineage_sha = "a" * 64, "b" * 64
    report = {
        "schema_version": "sead-country-retrieval.v2",
        "run_id": owner.RUN,
        "admission": {
            "qualified_review_of_126_coordinates": "pending",
            "source_release_status": "refused",
        },
        "inputs": [
            {
                "path": "data/boundaries/review/country-decisions/sead.json",
                "sha256": "5f74c5b8eeb02e28e0ff0b5abdb96a8fb0dc7fa32427055dce0c1967e07ad643",
                "custody": "historical_retained_ledger",
            },
            {
                "path": "data/sead/normalized/nordic_environmental_sites.csv",
                "sha256": site_sha,
            },
            {"path": "data/sead/normalized/source_lineage.json", "sha256": lineage_sha},
        ],
        "outputs": {"sites.csv": {"sha256": hashlib.sha256(sites).hexdigest()}},
    }
    owner.validate_historical_retrieval(report, sites, site_sha, lineage_sha)
    for mutation in ("ledger", "site", "lineage", "release", "excluded"):
        altered = deepcopy(report)
        if mutation == "ledger":
            altered["inputs"][0]["sha256"] = "0" * 64
        if mutation == "site":
            altered["inputs"][1]["sha256"] = "0" * 64
        if mutation == "lineage":
            altered["inputs"][2]["sha256"] = "0" * 64
        if mutation == "release":
            altered["admission"]["source_release_status"] = "accepted"
        altered_sites = (
            sites.replace(f"{excluded_id},".encode(), b"9999,", 1)
            if mutation == "excluded"
            else sites
        )
        if mutation == "excluded":
            altered_digest = hashlib.sha256(altered_sites).hexdigest()
            monkeypatch.setattr(owner, "HISTORICAL_SITES_SHA256", altered_digest)
            altered["outputs"]["sites.csv"]["sha256"] = altered_digest
        with pytest.raises(ValueError, match="historical retrieval"):
            owner.validate_historical_retrieval(
                altered, altered_sites, site_sha, lineage_sha
            )


def test_historical_inputs_are_all_required(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="supplied together"):
        owner.run(
            tmp_path,
            tmp_path / "artifacts/out",
            historical_retrieval_report=tmp_path / "report.json",
        )


def test_default_retrieval_report_pin_rejects_replacement(tmp_path: Path) -> None:
    relative = owner.RETRIEVAL / "report.json"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"replacement")
    with pytest.raises(ValueError, match="Pinned SEAD input changed"):
        owner._read_pinned(tmp_path, relative)


@pytest.mark.parametrize("changed", ["report", "site", "lineage"])
def test_selected_input_digest_refusal_is_before_output(
    tmp_path: Path, changed: str
) -> None:
    root = Path(__file__).resolve().parents[4]
    repository = tmp_path / "repository"
    for relative in owner.PINNED:
        if relative == owner.RETRIEVAL / "report.json":
            continue
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    admission = owner.RAW / "admission.json"
    shutil.copyfile(root / admission, repository / admission)
    report = tmp_path / "selected/report.json"
    report.parent.mkdir()
    report.write_bytes(b"{}")
    (report.parent / "sites.csv").write_bytes(b"sites")
    site = repository / owner.HISTORICAL_SITE_CSV
    lineage = repository / owner.HISTORICAL_LINEAGE
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_bytes(b"site")
    lineage.write_bytes(b"lineage")
    digests = {
        "report": hashlib.sha256(b"{}").hexdigest(),
        "site": hashlib.sha256(b"site").hexdigest(),
        "lineage": hashlib.sha256(b"lineage").hexdigest(),
    }
    digests[changed] = "0" * 64
    output = repository / "artifacts/out"
    with pytest.raises(ValueError, match="selected input digest differs"):
        owner.run(
            repository,
            output,
            historical_retrieval_report=report,
            historical_retrieval_sha256=digests["report"],
            historical_site_sha256=digests["site"],
            historical_lineage_sha256=digests["lineage"],
        )
    assert not output.exists()


def test_historical_site_lineage_requires_original_authority_and_admission() -> None:
    admission = {
        "run_id": owner.RUN,
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
    }
    site_sha = "a" * 64
    lineage = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": owner.RUN,
        **{k: v for k, v in admission.items() if k != "run_id"},
        "country_membership": {
            "purpose": "historical_admission_cohort",
            "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
            "artifact_digest": "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
        },
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.csv": site_sha
        },
    }
    lineage["refresh_input_sha256"] = {
        "boundary/normalized/nordic_country_boundaries.geojson": "bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
        "evidence/evidence_materialization_manifest.json": "383151443d04da5a6e127ea2e4344b4b10bb210137dd1d13b77e50dbfae93508",
    }
    owner.validate_historical_site_lineage(lineage, admission, site_sha)
    for kind in ("authority", "admission", "site", "evidence"):
        altered = deepcopy(lineage)
        if kind == "authority":
            altered["country_membership"]["authority_id"] = "sha256:" + "0" * 64
        if kind == "admission":
            altered["parent_admission_sha256"] = "0" * 64
        if kind == "site":
            altered["normalized_surface_sha256"][
                "normalized/nordic_environmental_sites.csv"
            ] = "0" * 64
        if kind == "evidence":
            altered["refresh_input_sha256"][
                "evidence/evidence_materialization_manifest.json"
            ] = "0" * 64
        with pytest.raises(ValueError, match="historical site lineage"):
            owner.validate_historical_site_lineage(altered, admission, site_sha)


def test_historical_coverage_records_admission_input(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    repository = tmp_path / "repository"
    for relative in owner.PINNED:
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    admission_path = owner.RAW / "admission.json"
    shutil.copyfile(root / admission_path, repository / admission_path)
    shutil.copytree(root / owner.RAW / "receipts", repository / owner.RAW / "receipts")
    site_path = repository / owner.HISTORICAL_SITE_CSV
    site_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / owner.HISTORICAL_SITE_CSV, site_path)
    site_sha = hashlib.sha256(site_path.read_bytes()).hexdigest()
    admission = json.loads((repository / admission_path).read_bytes())
    lineage = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": admission["run_id"],
        **{
            key: admission[key]
            for key in (
                "build_id",
                "acquisition_manifest_sha256",
                "parent_admission_sha256",
                "acquisition_bundle_sha256",
            )
        },
        "country_membership": {
            "purpose": "historical_admission_cohort",
            "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
            "artifact_digest": "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
        },
        "refresh_input_sha256": {
            "boundary/normalized/nordic_country_boundaries.geojson": "bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
            "evidence/evidence_materialization_manifest.json": owner.PINNED[
                owner.NORMALIZED / "evidence_materialization_manifest.json"
            ],
        },
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.csv": site_sha
        },
    }
    lineage_path = repository / owner.HISTORICAL_LINEAGE
    lineage_bytes = json.dumps(lineage).encode()
    lineage_path.write_bytes(lineage_bytes)
    lineage_sha = hashlib.sha256(lineage_bytes).hexdigest()
    report = json.loads((root / owner.RETRIEVAL / "report.json").read_bytes())
    report["schema_version"] = "sead-country-retrieval.v2"
    for row in report["inputs"]:
        if row["path"] == owner.HISTORICAL_REVIEW:
            row["custody"] = "historical_retained_ledger"
    report["inputs"].append({"path": owner.HISTORICAL_LINEAGE, "sha256": lineage_sha})
    selected = tmp_path / "selected/report.json"
    selected.parent.mkdir()
    report_bytes = json.dumps(report).encode()
    selected.write_bytes(report_bytes)
    shutil.copyfile(root / owner.RETRIEVAL / "sites.csv", selected.parent / "sites.csv")
    result = owner.run(
        repository,
        repository / "artifacts/result",
        historical_retrieval_report=selected,
        historical_retrieval_sha256=hashlib.sha256(report_bytes).hexdigest(),
        historical_site_sha256=site_sha,
        historical_lineage_sha256=lineage_sha,
    )
    assert (
        result["historical_inputs_sha256"][admission_path.as_posix()]
        == hashlib.sha256((repository / admission_path).read_bytes()).hexdigest()
    )
