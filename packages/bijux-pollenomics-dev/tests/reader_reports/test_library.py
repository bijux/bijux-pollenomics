import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TypedDict

import pytest


class _PaperManifest(TypedDict):
    schema_version: str
    repository_revision: str
    producer_revision: str
    inventory: str
    inventory_sha256: str
    build_receipt_sha256: str
    papers: list[dict[str, object]]
    producer_sha256: dict[str, str]


class _VisualReview(TypedDict):
    overall_status: str
    defects: list[str]
    input_receipt_sha256: str
    repository_revision: str
    papers: list[dict[str, object]]


ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    "corruption",
    ["inventory", "duplicate_paper", "pdf", "review", "page_coverage"],
)
def test_library_refuses_a_corrupted_source_pdf_or_review(
    corruption: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = ROOT / "reports/exports/papers/verify.py"
    spec = importlib.util.spec_from_file_location("paper_library", path)
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest = json.loads(path.with_name("manifest.json").read_text())
    review = json.loads(path.with_name("visual-review.json").read_text())
    if corruption == "inventory":
        manifest["inventory_sha256"] = "0" * 64
    elif corruption == "duplicate_paper":
        manifest["papers"].append(copy.deepcopy(manifest["papers"][0]))
    elif corruption == "pdf":
        manifest["papers"][0]["pdf_sha256"] = "0" * 64
    elif corruption == "review":
        review["input_receipt_sha256"] = "0" * 64
    else:
        review["papers"][0]["pages"].pop()
    inputs = iter([manifest, review])
    monkeypatch.setattr(verifier, "json", SimpleNamespace(loads=lambda _: next(inputs)))
    with pytest.raises(ValueError):
        verifier.main()


def _source_revision_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, _PaperManifest, _VisualReview, Path, str]:
    """Use real Git blobs to distinguish retained and independently exported sources."""
    import hashlib
    import subprocess

    root = tmp_path / "repository"
    source = root / "reports/science/paper.md"
    library = root / "reports/exports/papers"
    source.parent.mkdir(parents=True)
    library.mkdir(parents=True)
    inventory = source.with_name("paper-accounts.csv")
    inventory.write_text("paper_id,canonical_report\npaper,reports/science/paper.md\n")
    source.write_text("# Retained account\n")
    producer_relative = (
        "packages/bijux-pollenomics-dev/src/"
        "bijux_pollenomics_dev/reader_reports/render.py"
    )
    producer = root / producer_relative
    producer.parent.mkdir(parents=True)
    producer.write_text('"""Stable renderer identity fixture."""\n')
    for args in (
        ["init", "--quiet"],
        ["add", "reports/science", producer_relative],
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def commit() -> str:
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Bijux",
                "-c",
                "user.email=checks@bijux.io",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "-am",
                "docs(science): bind paper source",
            ],
            cwd=root,
            check=True,
            capture_output=True,
        )
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()

    retained_revision = commit()
    source.write_text("# Separately exported account\n")
    export_revision = commit()
    path = ROOT / "reports/exports/papers/verify.py"
    spec = importlib.util.spec_from_file_location("paper_library_source_binding", path)
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    monkeypatch.setattr(verifier, "ROOT", root)
    monkeypatch.setattr(verifier, "HERE", library)
    pdf = library / "paper.pdf"
    pdf.write_bytes(b"PDF identity fixture, without a layout acceptance claim")

    def digest(value: Path) -> str:
        return hashlib.sha256(value.read_bytes()).hexdigest()

    row: dict[str, object] = {
        "paper_id": "paper",
        "canonical_report": "reports/science/paper.md",
        "source_sha256": digest(source),
        "source_revision": export_revision,
        "build_receipt_sha256": "b" * 64,
        "pdf": "paper.pdf",
        "pdf_sha256": digest(pdf),
        "pdf_bytes": pdf.stat().st_size,
    }
    manifest: _PaperManifest = {
        "schema_version": "canonical-paper-pdf-library.v1",
        "repository_revision": retained_revision,
        "producer_revision": retained_revision,
        "inventory": "reports/science/paper-accounts.csv",
        "inventory_sha256": digest(inventory),
        "build_receipt_sha256": "a" * 64,
        "papers": [row],
        "producer_sha256": {producer_relative: digest(producer)},
    }
    visual: dict[str, object] = {
        "paper_id": "paper",
        "input_pdf_sha256": digest(pdf),
        "source_sha256": digest(source),
        "source_revision": export_revision,
        "input_receipt_sha256": "b" * 64,
        "review_status": "layout_pass",
        "all_fonts_embedded": True,
        "page_count": 1,
        "pages": [{"page": 1, "visual_status": "readable"}],
    }
    review: _VisualReview = {
        "overall_status": "layout_pass",
        "defects": [],
        "input_receipt_sha256": "a" * 64,
        "repository_revision": retained_revision,
        "papers": [visual],
    }
    (library / "manifest.json").write_text(json.dumps(manifest))
    (library / "visual-review.json").write_text(json.dumps(review))
    return verifier, manifest, review, source, retained_revision


def test_library_accepts_a_separate_paper_revision_with_actual_git_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier, *_ = _source_revision_library(tmp_path, monkeypatch)
    verifier.main()


def test_library_preserves_legacy_global_source_and_build_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier, manifest, review, source, _ = _source_revision_library(
        tmp_path, monkeypatch
    )
    source.write_text("# Retained account\n")
    row, visual = manifest["papers"][0], review["papers"][0]
    row["source_sha256"] = visual["source_sha256"] = verifier.digest(source)
    del row["source_revision"], row["build_receipt_sha256"]
    del visual["source_revision"], visual["input_receipt_sha256"]
    (verifier.HERE / "manifest.json").write_text(json.dumps(manifest))
    (verifier.HERE / "visual-review.json").write_text(json.dumps(review))
    verifier.main()


@pytest.mark.parametrize(
    "corruption",
    [
        "malformed_revision",
        "wrong_blob_revision",
        "changed_source",
        "mismatched_receipt",
        "missing_receipt",
        "wrong_review_revision",
    ],
)
def test_library_refuses_separate_source_or_build_identity_drift(
    corruption: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier, manifest, review, source, retained_revision = _source_revision_library(
        tmp_path, monkeypatch
    )
    row, visual = manifest["papers"][0], review["papers"][0]
    if corruption == "malformed_revision":
        row["source_revision"] = visual["source_revision"] = "HEAD"
    elif corruption == "wrong_blob_revision":
        row["source_revision"] = visual["source_revision"] = retained_revision
    elif corruption == "changed_source":
        source.write_text("# Source changed after export\n")
    elif corruption == "mismatched_receipt":
        visual["input_receipt_sha256"] = "c" * 64
    elif corruption == "missing_receipt":
        del row["build_receipt_sha256"]
    else:
        visual["source_revision"] = retained_revision
    (verifier.HERE / "manifest.json").write_text(json.dumps(manifest))
    (verifier.HERE / "visual-review.json").write_text(json.dumps(review))
    with pytest.raises(ValueError):
        verifier.main()
