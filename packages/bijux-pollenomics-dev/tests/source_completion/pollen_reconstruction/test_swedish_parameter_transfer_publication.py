"""Verify aggregate-only publication without an expensive scientific replay."""

import hashlib
import json
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_parameter_transfer import (
    producer as scientific_producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_parameter_transfer.publication import (
    producer,
)


def _path(value: object) -> Path:
    """Require the physical fixture support/output path before touching bytes."""
    assert isinstance(value, Path)
    return value


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Provide repository for the retained source contract."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
    (tmp_path / "artifacts").mkdir()
    return tmp_path


@pytest.fixture
def source_root() -> Path:
    """Provide source root for the retained source contract."""
    path = Path(producer.__file__).absolute()
    return next(
        parent for parent in path.parents if (parent / "pyproject.toml").is_file()
    )


@pytest.fixture
def science(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Provide science for the retained source contract."""
    observed: dict[str, object] = {}

    def produce(arguments: list[str]) -> int:
        output = Path(arguments[arguments.index("--output") + 1])
        output.mkdir()
        capsule = output.parent / ".swedish-parameter-transfer-evidence-fixture"
        capsule.mkdir()
        support = capsule / "local-source-support.json"
        support.write_bytes(b'{"fixture_actual_presence": [true, false]}\n')
        report = {
            "producer_source_candidate": "a" * 40,
            "local_actual_source_support_file_sha256": hashlib.sha256(
                support.read_bytes()
            ).hexdigest(),
        }
        body = (json.dumps(report, sort_keys=True) + "\n").encode()
        (output / "report.json").write_bytes(body)
        observed.update(output=output, support=support, report_bytes=body)
        return 0

    monkeypatch.setattr(scientific_producer, "main", produce)
    return observed


def test_publishes_only_aggregate_and_retains_exact_private_support(
    repository: Path, source_root: Path, science: dict[str, object]
) -> None:
    """Verify publishes only aggregate and retains exact private support."""
    output, retained = (
        repository / "artifacts/source-products",
        repository / "artifacts/retained",
    )
    producer.publish(repository, source_root, output, retained)
    assert [path.name for path in output.iterdir()] == ["report.json"]
    assert (output / "report.json").read_bytes() == science["report_bytes"]
    assert _path(science["support"]).is_relative_to(retained)
    capture = json.loads((retained / "publication-capture.json").read_bytes())
    assert (
        capture["retained_source_support_sha256"]
        == hashlib.sha256(_path(science["support"]).read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("nested_root", ["output", "retained", "equal"])
def test_refuses_ancestry_overlap_before_science(
    repository: Path, source_root: Path, science: dict[str, object], nested_root: str
) -> None:
    """Verify refuses ancestry overlap before science."""
    parent = repository / "artifacts/overlap"
    parent.mkdir()
    output, retained = parent / "report", parent / "retained"
    if nested_root == "output":
        output.mkdir()
        retained = output / "evidence"
    elif nested_root == "retained":
        retained.mkdir()
        output = retained / "report"
    else:
        retained = output
    with pytest.raises(ValueError, match="must not overlap"):
        producer.publish(repository, source_root, output, retained)
    assert not science


def test_retained_evidence_symlink_ancestor_refuses(
    repository: Path, source_root: Path, science: dict[str, object]
) -> None:
    """Verify retained evidence symlink ancestor refuses."""
    real = repository / "artifacts/real"
    real.mkdir()
    link = repository / "artifacts/linked"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        producer.publish(
            repository, source_root, repository / "artifacts/report", link / "retained"
        )
    assert not science


def test_existing_output_is_not_overwritten(
    repository: Path, source_root: Path, science: dict[str, object]
) -> None:
    """Verify existing output is not overwritten."""
    output, retained = (
        repository / "artifacts/source-products",
        repository / "artifacts/retained",
    )
    output.mkdir()
    (output / "user.txt").write_text("preserve")
    with pytest.raises(ReportRebuildError, match="absent"):
        producer.publish(repository, source_root, output, retained)
    assert (output / "user.txt").read_text() == "preserve"
    assert not science


def test_failed_science_retains_local_failure_without_report(
    repository: Path, source_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify failed science retains local failure without report."""
    output, retained = (
        repository / "artifacts/source-products",
        repository / "artifacts/retained",
    )

    def fail(arguments: list[str]) -> int:
        (retained / "failure.log").write_text("fixture scientific refusal")
        raise ValueError("fixture scientific refusal")

    monkeypatch.setattr(scientific_producer, "main", fail)
    with pytest.raises(ValueError, match="scientific refusal"):
        producer.publish(repository, source_root, output, retained)
    assert not output.exists()
    assert (retained / "failure.log").read_text() == "fixture scientific refusal"


def test_actual_support_hash_mismatch_refuses_publication(
    repository: Path,
    source_root: Path,
    science: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify actual support hash mismatch refuses publication."""
    original = scientific_producer.main

    def tamper(arguments: list[str]) -> int:
        code = original(arguments)
        _path(science["support"]).write_text("changed support")
        return code

    monkeypatch.setattr(scientific_producer, "main", tamper)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="does not match"):
        producer.publish(
            repository, source_root, output, repository / "artifacts/retained"
        )
    assert not output.exists()


def test_raw_file_inside_aggregate_tree_refuses_publication(
    repository: Path,
    source_root: Path,
    science: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify raw file inside aggregate tree refuses publication."""
    original = scientific_producer.main

    def leak(arguments: list[str]) -> int:
        code = original(arguments)
        (_path(science["output"]) / "raw-source.json").write_text("fixture raw bytes")
        return code

    monkeypatch.setattr(scientific_producer, "main", leak)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="coverage is not exact"):
        producer.publish(
            repository, source_root, output, repository / "artifacts/retained"
        )
    assert not output.exists()


def test_atomic_publication_failure_does_not_expose_partial_report(
    repository: Path,
    source_root: Path,
    science: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify atomic publication failure does not expose partial report."""

    def fail(source: Path, target: Path) -> int:
        raise OSError("fixture publication denied")

    monkeypatch.setattr(os, "replace", fail)
    output = repository / "artifacts/source-products"
    with pytest.raises(OSError, match="publication denied"):
        producer.publish(
            repository, source_root, output, repository / "artifacts/retained"
        )
    assert not output.exists()
    assert (_path(science["output"]) / "report.json").read_bytes() == science[
        "report_bytes"
    ]
    assert _path(science["support"]).is_file()


def test_support_tamper_during_copy_refuses_publication(
    repository: Path,
    source_root: Path,
    science: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify support tamper during copy refuses publication."""
    original = shutil.copy2

    def tamper(source: Path, target: Path) -> Path | str:
        value = original(source, target)
        _path(science["support"]).write_text("late changed support")
        return value

    monkeypatch.setattr(shutil, "copy2", tamper)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="changed before publication"):
        producer.publish(
            repository, source_root, output, repository / "artifacts/retained"
        )
    assert not output.exists()
