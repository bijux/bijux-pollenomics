"""Source and result boundaries for the constrained author LOVE owner."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    constrained_author_lra as subject,
)

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "docs/report/pollen-reconstruction/author-lra-constrained").is_dir()
)
GOVERNED = ROOT / "docs/report/pollen-reconstruction/author-lra-constrained"


def _complete_fixture(stage: Path) -> None:
    for original, destination in subject.STAGE_PRODUCTS.items():
        path = stage / original
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(GOVERNED / destination, path)


def test_all_eleven_retained_outputs_keep_declared_denominators(tmp_path: Path) -> None:
    stage = tmp_path / "retained-work"
    _complete_fixture(stage)
    products = subject._check_products(stage)
    assert set(products) == set(subject.STAGE_PRODUCTS.values())
    assert len(products) == 11


def test_changed_refusal_is_not_published(tmp_path: Path) -> None:
    stage = tmp_path / "retained-work"
    _complete_fixture(stage)
    report = stage / "report/report.json"
    payload = json.loads(report.read_text())
    payload["refused_site"] = "author:WHH05"
    report.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="denominator or refusal"):
        subject._check_products(stage)


def test_symlinked_stage_product_is_refused(tmp_path: Path) -> None:
    stage = tmp_path / "retained-work"
    _complete_fixture(stage)
    product = stage / "report/folds.csv"
    product.unlink()
    product.symlink_to(GOVERNED / "folds.csv")
    with pytest.raises(ReportRebuildError, match="real regular path"):
        subject._check_products(stage)


def test_original_stage_order_and_manifest_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    stage = tmp_path / "retained-work"
    stage.mkdir()

    def fake_run(_repository: Path, argv: list[str]) -> None:
        calls.append(argv)
        if "bijux_pollenomics_dev.essd_reproduction.author_lra_run" in argv:
            destination = stage / "predictions"
        elif "score.py" in argv[2]:
            destination = stage / "scores"
        elif "predict" in argv and "direct_comparison.py" in argv[2]:
            destination = stage / "direct-predictions"
        else:
            return
        destination.mkdir()
        (destination / "manifest.json").write_text("manifest identity\n")

    monkeypatch.setattr(subject, "_run", fake_run)
    monkeypatch.setattr(subject, "_require_experiment", lambda *_args: None)
    subject._run_pipeline(tmp_path, tmp_path / "qualified-source", stage)
    assert len(calls) == 10
    assert ["--author-source-root", str(tmp_path / "qualified-source")] == calls[0][4:6]
    assert "--prediction-manifest-sha256" in calls[3]
    assert "--score-manifest-sha256" in calls[4]
    assert "--prediction-manifest-sha256" in calls[6]
    assert all(
        str(stage / "source-products") not in call for argv in calls for call in argv
    )


def test_source_experiment_identity_refusal(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment.json"
    experiment.write_text('{"source":"original"}\n')
    subject._require_experiment(tmp_path, subject._sha(experiment))
    experiment.write_text('{"source":"changed"}\n')
    with pytest.raises(ValueError, match="experiment identity"):
        subject._require_experiment(tmp_path, "0" * 64)


def test_child_module_path_uses_only_candidate_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[dict[str, object]] = []

    def fake_subprocess(_argv: list[str], **kwargs: object) -> None:
        seen.append(kwargs)

    monkeypatch.setenv("PYTHONPATH", "/foreign/package/root")
    monkeypatch.setattr(subprocess, "run", fake_subprocess)
    subject._run(tmp_path, ["python", "-B", "-m", "verified.module"])
    assert len(seen) == 1
    assert seen[0]["check"] is True
    env = seen[0]["env"]
    assert isinstance(env, dict)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(tmp_path / "packages/bijux-pollenomics-dev/src"),
        str(tmp_path / "packages/bijux-pollenomics/src"),
        str(tmp_path / "packages/bijux-pollenomics-lra/src"),
    ]


def test_route_refuses_foreign_descriptor_before_source_or_study(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    owner = repository / "artifacts/owner/producer-output"
    owner.mkdir(parents=True)

    def fail_qualifier(*_args: object) -> None:
        raise AssertionError("qualifier should not run")

    monkeypatch.setattr(subject, "validated_external_report_sources", fail_qualifier)
    with pytest.raises(ValueError, match="route or descriptor"):
        subject.run(
            repository,
            tmp_path / "sources",
            Path("configs/ci/qualified-report-sources/other.json"),
            owner / "source-products",
        )


def test_retained_stage_cannot_be_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    owner = repository / "artifacts/owner"
    (owner / "producer-output").mkdir(parents=True)
    (owner / "retained-work").mkdir()

    def fail_qualifier(*_args: object) -> None:
        raise AssertionError("qualifier should not run")

    monkeypatch.setattr(subject, "validated_external_report_sources", fail_qualifier)
    with pytest.raises(ValueError, match="work destination must be absent"):
        subject.run(
            repository,
            tmp_path / "sources",
            subject.DESCRIPTOR,
            owner / "producer-output/source-products",
        )


def test_source_mutation_after_original_stages_blocks_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    owner = repository / "artifacts/owner"
    (owner / "producer-output").mkdir(parents=True)
    source = tmp_path / "qualified-source"
    source.mkdir()
    manifest = source / "snapshot-manifest.json"
    manifest.write_text("qualified snapshot\n")
    for relative in subject.ORIGINAL_SCRIPTS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source\n")
    for module in subject.ORIGINAL_MODULES:
        path = (
            repository
            / "packages/bijux-pollenomics-dev/src"
            / (module.replace(".", "/") + ".py")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source\n")
    monkeypatch.setattr(subject, "SOURCE_MANIFEST_SHA256", subject._sha(manifest))
    monkeypatch.setattr(
        subject,
        "validated_external_report_sources",
        lambda *_args: SimpleNamespace(
            directory=source,
            inputs={f"external/source-{index}": manifest for index in range(195)},
        ),
    )
    identities = iter(({"source": "before"}, {"source": "after"}))
    monkeypatch.setattr(
        subject, "producer_input_identity", lambda *_args: next(identities)
    )
    monkeypatch.setattr(subject, "_run_pipeline", lambda *_args: None)
    destination = owner / "producer-output/source-products"
    with pytest.raises(ValueError, match="source changed"):
        subject.run(repository, tmp_path, subject.DESCRIPTOR, destination)
    assert not destination.exists()
    assert (owner / "retained-work").is_dir()
