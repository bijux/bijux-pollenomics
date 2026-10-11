"""Refuse unbound English training inputs before compact publication."""

from __future__ import annotations

from collections.abc import Sequence
import copy
import csv
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    english_shared_ppe as subject,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, rows: Sequence[Sequence[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows(rows)


def _source_case(root: Path) -> tuple[Path, dict[str, object]]:
    directory = root / "author"
    names = [f"Taxon{index}" for index in range(31)]
    names[15] = "Filipendula"
    keep = [index for index in range(31) if index != 15]
    parameters = [
        {"taxon": f"Prepared{index}", "ppe": float(index + 1), "ppe_sd": 0.1}
        for index in keep
    ]
    _csv(
        directory / "run.REVEALS.files/av-RPP.all.landclimII.csv",
        [["Taxon", "PPE"], *[[name, index + 1] for index, name in enumerate(names)]],
    )
    _csv(
        directory / "run.REVEALS.files/avar-RPP.all.landclimII.csv",
        [
            ["Taxon", *names],
            *[
                [name, *[0.01 if index == column else 0 for column in range(31)]]
                for index, name in enumerate(names)
            ],
        ],
    )
    _csv(
        root / "reference/taxon-name-crosswalk.csv",
        [
            ["source", "prepared"],
            *[[name, f"Prepared{index}"] for index, name in enumerate(names)],
        ],
    )
    return root, {
        "taxa": [f"Prepared{index}" for index in keep],
        "parameters": parameters,
    }


def test_source_moments_match_exact_axis_and_diagonal(tmp_path: Path) -> None:
    root, payload = _source_case(tmp_path)
    means, sd, covariance = subject._source_moments(root, payload)
    assert means.shape == (30,)
    np.testing.assert_array_equal(sd, [0.1] * 30)
    np.testing.assert_array_equal(covariance, np.eye(30) * 0.01)


def test_source_off_diagonal_and_axis_refused(tmp_path: Path) -> None:
    root, payload = _source_case(tmp_path)
    bad_axis = copy.deepcopy(payload)
    taxa = bad_axis["taxa"]
    assert isinstance(taxa, list)
    taxa[0] = "Other"
    with pytest.raises(ValueError, match="taxon mapping"):
        subject._source_moments(root, bad_axis)
    covariance = root / "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
    rows = subject._rows(covariance)
    rows[1][2] = rows[2][1] = "0.005"
    _csv(covariance, rows)
    with pytest.raises(ValueError, match="covariance"):
        subject._source_moments(root, payload)


def test_prepared_evidence_refuses_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preparation = tmp_path / "private-preparation"
    source = preparation / "source-inputs/source-report.json"
    source.parent.mkdir(parents=True)
    source.write_text("{}")
    input_root = preparation / "extended/inputs"
    input_root.mkdir(parents=True)
    evidence = []
    for name in sorted(subject.EVIDENCE_NAMES):
        path = input_root / name
        path.write_text(name)
        evidence.append({"path": name, "sha256": _sha(path)})
    request_path = input_root / "request.json"
    request_path.write_text(json.dumps({"evidence": evidence}))
    monkeypatch.setattr(subject, "SOURCE_REPORT_SHA256", _sha(source))
    monkeypatch.setattr(subject, "REQUEST_SHA256", _sha(request_path))
    summary = {
        "source_manifest_sha256": subject.MANIFEST_SHA256,
        "prepared": [
            {"label": "initial"},
            {"label": "extended", "request_sha256": subject.REQUEST_SHA256},
        ],
    }
    _, request, actual = subject._prepared_request(preparation, summary)
    assert request["evidence"] == evidence
    assert set(actual) == set(subject.EVIDENCE_NAMES)
    (input_root / "decision.json").write_text("changed")
    with pytest.raises(ValueError, match="prepared evidence differs"):
        subject._prepared_request(preparation, summary)


def test_output_escape_refused_before_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    (repository / "artifacts").mkdir(parents=True)
    monkeypatch.setattr(
        subject,
        "validated_external_report_sources",
        lambda *args: pytest.fail("source accessed before output confinement"),
    )
    with pytest.raises(ReportRebuildError):
        subject.run(
            repository,
            tmp_path / "source",
            subject.DESCRIPTOR,
            repository / "artifacts/../escaped",
        )
    assert not (repository / "escaped").exists()


def test_compact_report_omits_private_rows() -> None:
    fit = SimpleNamespace(
        converged=True,
        optimality_gap=1e-8,
        mean_negative_log_likelihood=1.0,
        steps=2,
        stop_reason="gap_tolerance",
        vertex_condition_number=3.0,
        profile="homogeneous-fixed-input-likelihood-v1",
    )
    cover = np.broadcast_to(np.ones(30) / 30, (64, 30)).copy()
    result = SimpleNamespace(
        local_cover=cover,
        fits=[fit] * 64,
        forward_max_abs=np.zeros(64),
    )
    report, diagnostics = subject._compact_products(
        {"taxa": [f"Taxon{index}" for index in range(30)]},
        result,
        "a" * 64,
        {"decision.json": "b" * 64},
    )
    assert len(report["cover_by_taxon"]) == 30
    assert len(diagnostics) == 64
    assert "ppe_draws" not in report
    assert "regional_cover" not in report
    assert "source_request" not in report
    assert report["prepared_evidence_sha256"] == {"decision.json": "b" * 64}


def test_postread_request_mutation_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    (repository / "artifacts").mkdir(parents=True)
    output = repository / "artifacts/source-products"
    prepare = tmp_path / "prepare.py"
    prepare.write_text("original")
    inputs = tmp_path / "private-preparation/extended/inputs"
    inputs.mkdir(parents=True)
    request = inputs / "request.json"
    request.write_text("original request")
    evidence = inputs / "decision.json"
    evidence.write_text("original evidence")
    monkeypatch.setattr(subject, "PREPARE_SHA256", _sha(prepare))
    monkeypatch.setattr(subject, "REQUEST_SHA256", _sha(request))
    qualified = QualifiedReportSources(tmp_path, {}, "descriptor")
    monkeypatch.setattr(
        subject, "validated_external_report_sources", lambda *args: qualified
    )
    subject._require_unchanged_before_publication(
        repository,
        tmp_path,
        subject.DESCRIPTOR,
        qualified,
        prepare,
        inputs,
        {"decision.json": _sha(evidence)},
        output,
    )
    evidence.write_text("changed after read")
    with pytest.raises(ValueError, match="changed before publication"):
        subject._require_unchanged_before_publication(
            repository,
            tmp_path,
            subject.DESCRIPTOR,
            qualified,
            prepare,
            inputs,
            {"decision.json": hashlib.sha256(b"original evidence").hexdigest()},
            output,
        )
    assert not output.exists()


def test_postread_source_change_removes_stage_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    (repository / "artifacts").mkdir(parents=True)
    descriptor = repository / subject.DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps(
            {
                "schema_version": "qualified-author-snapshot.v1",
                "source_id": subject.SOURCE_ID,
            }
        )
    )
    source = tmp_path / "source"
    source.mkdir()
    manifest = source / "snapshot-manifest.json"
    manifest.write_text("snapshot")
    covariance = source / "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
    covariance.parent.mkdir(parents=True)
    covariance.write_text("synthetic covariance")
    prepare = repository / subject.PREPARE
    prepare.parent.mkdir(parents=True)
    prepare.write_text("maintained preparation")
    monkeypatch.setattr(subject, "MANIFEST_SHA256", _sha(manifest))
    monkeypatch.setattr(subject, "PREPARE_SHA256", _sha(prepare))
    qualified = QualifiedReportSources(
        source,
        {
            subject.DESCRIPTOR.as_posix(): descriptor,
            **{f"external/{index}": manifest for index in range(194)},
        },
        "first",
    )
    changed = QualifiedReportSources(source, qualified.inputs, "changed")
    calls = iter((qualified, changed))
    monkeypatch.setattr(
        subject,
        "validated_external_report_sources",
        lambda *args: next(calls),
    )
    monkeypatch.setattr(
        runpy, "run_path", lambda *args, **kwargs: {"prepare": lambda *args: {}}
    )
    monkeypatch.setattr(
        subject,
        "_prepared_request",
        lambda preparation, summary: (preparation, {}, {}),
    )
    taxa = [f"Taxon{index}" for index in range(30)]
    monkeypatch.setattr(
        subject,
        "_training_payload",
        lambda request, input_root: {
            "taxa": taxa,
            "regional": {"samples": [{"counts": [1] * 30}]},
            "local": {"samples": [{"counts": [1] * 30}]},
        },
    )
    monkeypatch.setattr(
        subject,
        "_source_moments",
        lambda *args: (np.ones(30), np.zeros(30), np.zeros((30, 30))),
    )
    monkeypatch.setattr(
        subject,
        "_kernels",
        lambda *args: (np.ones(30), np.ones((3, 30)), np.ones(3)),
    )
    # The exact nominal check is tested elsewhere; this fixture reaches the
    # publication boundary without solving any likelihood problem.
    taxa[:6] = list(subject.NOMINAL_COVER)
    nominal = np.array([subject.NOMINAL_COVER.get(taxon, 0.0) for taxon in taxa])
    fit = SimpleNamespace(
        converged=True,
        optimality_gap=0.0,
        mean_negative_log_likelihood=subject.NOMINAL_NEGATIVE_LOG_LIKELIHOOD,
    )
    result = SimpleNamespace(
        ppe_draws=np.ones((64, 30)),
        local_cover=np.broadcast_to(nominal, (64, 30)).copy(),
        fits=[fit] * 64,
    )
    monkeypatch.setattr(
        subject, "fit_shared_ppe_likelihood", lambda *args, **kwargs: result
    )
    monkeypatch.setattr(subject, "_compact_products", lambda *args: ({}, []))
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="source/request changed"):
        subject.run(repository, tmp_path, subject.DESCRIPTOR, output)
    assert not output.exists()
    assert not any(repository.joinpath("artifacts").glob(".english-shared-ppe-*"))
