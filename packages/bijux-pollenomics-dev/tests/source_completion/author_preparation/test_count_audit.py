"""Verify source custody and atomic publication for the original count audit."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.author_preparation import (
    count_audit as subject,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditCase(TypedDict):
    repository: Path
    source_root: Path
    output: Path
    descriptor: Path
    reference: Path
    source_file: Path
    report: dict[str, Any]
    builder: Callable[[Path, Path, Path], dict[str, Any]]


def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AuditCase:
    repository = tmp_path / "repository"
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
    reference = repository / subject.REFERENCE
    reference.parent.mkdir(parents=True)
    reference.write_text("independent 17-site reference\n")
    source_root = tmp_path / "source-store"
    source = source_root / subject.SOURCE_ID
    source.mkdir(parents=True)
    manifest = source / "snapshot-manifest.json"
    manifest.write_text("original manifest\n")
    source_file = source / "author-input.csv"
    source_file.write_text("original source\n")
    original = tmp_path / "original-producer.py"
    original.write_text("original producer\n")
    original_reference_digest = sha(reference)
    original_source_digest = sha(source_file)
    monkeypatch.setattr(subject, "MANIFEST_SHA256", sha(manifest))
    monkeypatch.setattr(subject, "REFERENCE_SHA256", original_reference_digest)
    monkeypatch.setattr(subject, "_original_code", lambda: original)

    def qualify(repo: Path, root: Path, chosen: Path) -> QualifiedReportSources:
        assert repo == repository
        assert root == source_root
        assert chosen == subject.DESCRIPTOR
        if sha(source_file) != original_source_digest:
            raise ValueError("Qualified source changed")
        inputs = {chosen.as_posix(): descriptor, "external/manifest": manifest}
        inputs.update({f"external/source-{i}": source_file for i in range(193)})
        return QualifiedReportSources(source, inputs, sha(descriptor))

    monkeypatch.setattr(subject, "validated_external_report_sources", qualify)
    report = {
        "schema_version": "landclim-author-preparation-audit.v3",
        "totals": {"sites": 17, "raw_count": 501713},
        "input_sha256": {
            "author_snapshot_manifest": sha(manifest),
            "independent_counts": original_reference_digest,
        },
    }

    def build(_repo: Path, _source: Path, output: Path) -> dict[str, Any]:
        assert _repo == repository
        assert _source == source
        output.mkdir()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        return report

    monkeypatch.setattr(subject, "build_original_audit", build)
    return {
        "repository": repository,
        "source_root": source_root,
        "output": repository / "artifacts/source-products",
        "descriptor": descriptor,
        "reference": reference,
        "source_file": source_file,
        "report": report,
        "builder": build,
    }


def invoke(values: AuditCase) -> dict[str, Any]:
    return subject.run(
        values["repository"],
        values["source_root"],
        subject.DESCRIPTOR,
        values["output"],
    )


def assert_clean(values: AuditCase) -> None:
    assert not values["output"].exists()
    assert not list(
        (values["repository"] / "artifacts").glob(".author-preparation-audit-*")
    )


def test_exact_single_report_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    assert invoke(values) == values["report"]
    assert sorted(path.name for path in values["output"].iterdir()) == ["report.json"]
    assert (
        json.loads((values["output"] / "report.json").read_bytes()) == values["report"]
    )
    assert not list(
        (values["repository"] / "artifacts").glob(".author-preparation-audit-*")
    )


def test_source_change_after_original_read_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    original = values["builder"]

    def changed(*args: Any) -> dict[str, Any]:
        report = original(*args)
        values["source_file"].write_text("changed source after read\n")
        return report

    monkeypatch.setattr(subject, "build_original_audit", changed)
    with pytest.raises(ValueError, match="Qualified source changed"):
        invoke(values)
    assert_clean(values)


def test_independent_reference_change_after_read_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    original = values["builder"]

    def changed(*args: Any) -> dict[str, Any]:
        report = original(*args)
        values["reference"].write_text("changed reference after read\n")
        return report

    monkeypatch.setattr(subject, "build_original_audit", changed)
    with pytest.raises(ValueError, match="changed before publication"):
        invoke(values)
    assert_clean(values)


def test_original_code_change_after_read_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    original = values["builder"]

    def changed(*args: Any) -> dict[str, Any]:
        report = original(*args)
        (tmp_path / "original-producer.py").write_text("changed producer\n")
        return report

    monkeypatch.setattr(subject, "build_original_audit", changed)
    with pytest.raises(ValueError, match="changed before publication"):
        invoke(values)
    assert_clean(values)


def test_extra_original_output_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    original = values["builder"]

    def extra(*args: Any) -> dict[str, Any]:
        report = original(*args)
        (args[2] / "private.csv").write_text("private\n")
        return report

    monkeypatch.setattr(subject, "build_original_audit", extra)
    with pytest.raises(ValueError, match="output population"):
        invoke(values)
    assert_clean(values)


def test_output_escape_refused_before_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    monkeypatch.setattr(
        subject,
        "validated_external_report_sources",
        lambda *_args: pytest.fail("source accessed before output guard"),
    )
    with pytest.raises(ReportRebuildError):
        subject.run(
            values["repository"],
            values["source_root"],
            subject.DESCRIPTOR,
            values["repository"] / "artifacts/../outside",
        )
    assert not (values["repository"] / "outside").exists()


def test_wrong_descriptor_identity_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = case(tmp_path, monkeypatch)
    values["descriptor"].write_text(
        json.dumps(
            {"schema_version": "qualified-author-snapshot.v1", "source_id": "other"}
        )
    )
    with pytest.raises(ValueError, match="Qualified author preparation source differs"):
        invoke(values)
    assert_clean(values)
