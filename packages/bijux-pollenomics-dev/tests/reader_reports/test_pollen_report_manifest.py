"""Keep retained scientific bytes strict while ordinary source edits use Git."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pollen_report_manifest",
        ROOT / "docs/report/pollen-reconstruction/verify_report.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def manifest(tmp_path: Path) -> dict[str, Any]:
    maintained = ["docs/report/pollen-reconstruction/README.md", "packages/analysis.py"]
    retained = [
        "configs/release_evidence_policy.json",
        "data/source/raw.bin",
        "data/source/source/packages/algorithm.py",
        "docs/report/reference-bundle/original.py",
        "docs/report/pollen-reconstruction/study/result.json",
        "reports/exports/study.pdf",
    ]
    files = []
    for relative in [*maintained, *retained]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"Fixture source for {relative}\n".encode()
        path.write_bytes(payload)
        if relative in retained:
            files.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                }
            )
    return {
        "schema_version": "pollen-reconstruction-report-manifest.v2",
        "status": "scoped_results_with_external_source_blockers",
        "repository": "bijux-pollenomics",
        "as_of": "2026-10-01",
        "files": files,
        "maintained_paths": maintained,
    }


def test_ordinary_source_edits_do_not_repin_retained_evidence(
    tmp_path: Path, manifest: dict[str, Any], verifier: ModuleType
) -> None:
    original = copy.deepcopy(manifest)
    assert verifier.verify_report_manifest(tmp_path, manifest) == (6, 2)
    for relative in manifest["maintained_paths"]:
        (tmp_path / relative).write_text("Edited ordinary maintained prose or code\n")
    assert verifier.verify_report_manifest(tmp_path, manifest) == (6, 2)
    assert manifest == original


@pytest.mark.parametrize(
    "relative",
    [
        "presentation/big-picture.tex",
        "presentation/developer.tex",
        "presentation/scientific-evidence.tex",
        "presentation/shared.tex",
        "presentation/build.py",
        "makes/pollenomics-verification.mk",
        "makes/packages/bijux-pollenomics-dev.mk",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
        "ci/atlas_browser/probe.mjs",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/"
        "map_document/assets/document.html",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/"
        "report_portal/scientific_accounts.json",
        "docs/report/report_surface_registry.json",
        "docs/report/report_narrative_quality_review.json",
    ],
)
def test_named_maintained_inputs_preserve_evidence_identities(
    tmp_path: Path, manifest: dict[str, Any], verifier: ModuleType, relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Reader bookkeeping\n")
    manifest["maintained_paths"] = sorted([*manifest["maintained_paths"], relative])
    original = copy.deepcopy(manifest)
    expected = (len(manifest["files"]), len(manifest["maintained_paths"]))
    assert verifier.verify_report_manifest(tmp_path, manifest) == expected
    path.write_text("Edited reader bookkeeping\n")
    assert verifier.verify_report_manifest(tmp_path, manifest) == expected
    assert manifest == original


def test_repository_make_entrypoint_has_no_evidence_byte_pin() -> None:
    manifest = json.loads(
        (ROOT / "docs/report/pollen-reconstruction/manifest.json").read_text()
    )
    relative = "makes/pollenomics-verification.mk"
    assert relative in manifest["maintained_paths"]
    assert relative not in {row["path"] for row in manifest["files"]}


@pytest.mark.parametrize(
    "relative",
    [
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R",
        "docs/report/method-certification/current-r-oracle/source-domains/"
        "run_source_domains.py",
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/source_domains.R",
    ],
)
def test_canonical_oracle_references_retain_exact_evidence_bytes(
    verifier: ModuleType, relative: str
) -> None:
    manifest = json.loads(
        (ROOT / "docs/report/pollen-reconstruction/manifest.json").read_text()
    )
    assert relative not in manifest["maintained_paths"]
    original = (
        "data/method-certification/native-r-count-domain/capture/source-domains/"
        + Path(relative).name
    )
    assert original not in {row["path"] for row in manifest["files"]}
    (row,) = [item for item in manifest["files"] if item["path"] == relative]
    manifest["files"] = [row.copy()]
    manifest["maintained_paths"] = []
    assert verifier.verify_report_manifest(ROOT, manifest) == (1, 0)
    manifest["files"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="report evidence digest mismatch"):
        verifier.verify_report_manifest(ROOT, manifest)


@pytest.mark.parametrize("index", range(6))
def test_raw_reference_numerical_release_and_pdf_bytes_remain_exact(
    tmp_path: Path, manifest: dict[str, Any], verifier: ModuleType, index: int
) -> None:
    original = copy.deepcopy(manifest)
    path = tmp_path / manifest["files"][index]["path"]
    payload = path.read_bytes()
    path.write_bytes(b"X" + payload[1:])
    with pytest.raises(ValueError, match="report evidence digest mismatch"):
        verifier.verify_report_manifest(tmp_path, manifest)
    assert manifest == original


@pytest.mark.parametrize("kind", ["retained", "maintained"])
@pytest.mark.parametrize(
    "defect", ["missing", "escape", "absolute", "symlink", "disposable"]
)
def test_paths_stay_available_and_confined(
    tmp_path: Path,
    manifest: dict[str, Any],
    verifier: ModuleType,
    kind: str,
    defect: str,
) -> None:
    relative = (
        manifest["files"][0]["path"]
        if kind == "retained"
        else manifest["maintained_paths"][0]
    )
    path = tmp_path / relative
    replacement = relative
    if defect == "missing":
        path.unlink()
    elif defect == "symlink":
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    elif defect == "absolute":
        replacement = str(path)
    elif defect == "escape":
        replacement = "../outside.py"
    else:
        replacement = "artifacts/disposable.py"
    if kind == "retained":
        manifest["files"][0]["path"] = replacement
    else:
        manifest["maintained_paths"] = sorted(
            replacement if p == relative else p for p in manifest["maintained_paths"]
        )
    with pytest.raises(
        ValueError, match="invalid report evidence path|depends on disposable"
    ):
        verifier.verify_report_manifest(tmp_path, manifest)


@pytest.mark.parametrize(
    "defect",
    [
        "retained_duplicate",
        "maintained_duplicate",
        "overlap",
        "schema",
        "hash",
        "bytes",
        "bool_bytes",
        "row_field",
        "inventory",
    ],
)
def test_manifest_roles_and_identities_are_unambiguous(
    tmp_path: Path, manifest: dict[str, Any], verifier: ModuleType, defect: str
) -> None:
    if defect == "retained_duplicate":
        manifest["files"].append(manifest["files"][0].copy())
    elif defect == "maintained_duplicate":
        manifest["maintained_paths"].append(manifest["maintained_paths"][-1])
    elif defect == "overlap":
        manifest["maintained_paths"] = sorted(
            [*manifest["maintained_paths"], manifest["files"][0]["path"]]
        )
    elif defect == "schema":
        manifest["schema_version"] = "pollen-reconstruction-report-manifest.v1"
    elif defect == "hash":
        manifest["files"][0]["sha256"] = "unbound"
    elif defect == "bytes":
        manifest["files"][0]["bytes"] = -1
    elif defect == "bool_bytes":
        manifest["files"][0]["bytes"] = True
    elif defect == "row_field":
        manifest["files"][0]["optional"] = True
    else:
        manifest["maintained_paths"] = "packages/analysis.py"
    with pytest.raises(ValueError):
        verifier.verify_report_manifest(tmp_path, manifest)


@pytest.mark.parametrize(
    "relative",
    [
        "data/source/account.md",
        "docs/report/reference/original.py",
        "docs/report/reference-bundle/original.py",
        "docs/report/study/result.json",
        "docs/report/study/result.csv",
        "reports/science/report-claims.csv",
        "reports/science/scientific_accounts.json",
        "makes/bijux-py/ci/test.mk",
        "makes/bijux-py/pollenomics-verification.mk",
        "makes/pollenomics-verification.py",
        "makes/other-verification.mk",
        "makes/packages/other.mk",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/"
        "map_document/assets/other.html",
        "docs/report/reference/document.html",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
        "ci/atlas_browser/other.mjs",
    ],
)
def test_source_evidence_cannot_be_relabelled_as_ordinary_maintained_content(
    tmp_path: Path, manifest: dict[str, Any], verifier: ModuleType, relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Source evidence\n")
    manifest["files"] = [row for row in manifest["files"] if row["path"] != relative]
    manifest["maintained_paths"] = sorted([*manifest["maintained_paths"], relative])
    with pytest.raises(ValueError, match="not maintained prose or code"):
        verifier.verify_report_manifest(tmp_path, manifest)


@pytest.mark.parametrize(
    "relative",
    [
        ".github/workflows/scientific-verification.yml",
        "mkdocs.yml",
        "packages/bijux-pollenomics-dev/pyproject.toml",
        "packages/bijux-pollenomics-lra/pyproject.toml",
        "presentation/source-lock.json",
        "pyproject.toml",
        "reports/exports/site-downloads.json",
        "uv.lock",
    ],
)
def test_current_repository_bookkeeping_keeps_exact_paths_without_body_pins(
    tmp_path: Path, verifier: ModuleType, manifest: dict[str, Any], relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Current repository bookkeeping")
    manifest["maintained_paths"] = sorted([*manifest["maintained_paths"], relative])
    before = verifier.verify_report_manifest(tmp_path, manifest)
    path.write_bytes(b"Changed ordinary current bookkeeping")
    assert verifier.verify_report_manifest(tmp_path, manifest) == before


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/other.yml", "other.toml", "configs/ci/report-ownership.json"],
)
def test_unlisted_metadata_and_scientific_ownership_cannot_be_unpinned(
    tmp_path: Path, verifier: ModuleType, manifest: dict[str, Any], relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Unlisted metadata or scientific custody")
    manifest["maintained_paths"] = sorted([*manifest["maintained_paths"], relative])
    with pytest.raises(ValueError):
        verifier.verify_report_manifest(tmp_path, manifest)
