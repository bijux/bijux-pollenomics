"""Verify aggregate-only publication without an expensive scientific replay."""

import hashlib
import json
from pathlib import Path

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_parameter_transfer.publication import producer


@pytest.fixture
def repository(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
    (tmp_path / "artifacts").mkdir()
    return tmp_path


@pytest.fixture
def source_root():
    path = Path(producer.__file__).absolute()
    return next(parent for parent in path.parents if (parent / "pyproject.toml").is_file())


@pytest.fixture
def science(monkeypatch):
    observed = {}

    def produce(arguments):
        output = Path(arguments[arguments.index("--output") + 1])
        output.mkdir()
        capsule = output.parent / ".swedish-parameter-transfer-evidence-fixture"
        capsule.mkdir()
        support = capsule / "local-source-support.json"
        support.write_bytes(b'{"fixture_actual_presence": [true, false]}\n')
        report = {
            "producer_source_candidate": "a" * 40,
            "local_actual_source_support_file_sha256": hashlib.sha256(support.read_bytes()).hexdigest(),
        }
        body = (json.dumps(report, sort_keys=True) + "\n").encode()
        (output / "report.json").write_bytes(body)
        observed.update(output=output, support=support, report_bytes=body)
        return 0

    monkeypatch.setattr(producer.scientific_producer, "main", produce)
    return observed


def test_publishes_only_aggregate_and_retains_exact_private_support(repository, source_root, science):
    output, retained = repository / "artifacts/source-products", repository / "artifacts/retained"
    producer.publish(repository, source_root, output, retained)
    assert [path.name for path in output.iterdir()] == ["report.json"]
    assert (output / "report.json").read_bytes() == science["report_bytes"]
    assert science["support"].is_relative_to(retained)
    capture = json.loads((retained / "publication-capture.json").read_bytes())
    assert capture["retained_source_support_sha256"] == hashlib.sha256(science["support"].read_bytes()).hexdigest()


@pytest.mark.parametrize("nested_root", ["output", "retained", "equal"])
def test_refuses_ancestry_overlap_before_science(repository, source_root, science, nested_root):
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


def test_retained_evidence_symlink_ancestor_refuses(repository, source_root, science):
    real = repository / "artifacts/real"
    real.mkdir()
    link = repository / "artifacts/linked"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        producer.publish(repository, source_root, repository / "artifacts/report", link / "retained")
    assert not science


def test_existing_output_is_not_overwritten(repository, source_root, science):
    output, retained = repository / "artifacts/source-products", repository / "artifacts/retained"
    output.mkdir()
    (output / "user.txt").write_text("preserve")
    with pytest.raises(ReportRebuildError, match="absent"):
        producer.publish(repository, source_root, output, retained)
    assert (output / "user.txt").read_text() == "preserve"
    assert not science


def test_failed_science_retains_local_failure_without_report(repository, source_root, monkeypatch):
    output, retained = repository / "artifacts/source-products", repository / "artifacts/retained"
    def fail(arguments):
        (retained / "failure.log").write_text("fixture scientific refusal")
        raise ValueError("fixture scientific refusal")
    monkeypatch.setattr(producer.scientific_producer, "main", fail)
    with pytest.raises(ValueError, match="scientific refusal"):
        producer.publish(repository, source_root, output, retained)
    assert not output.exists()
    assert (retained / "failure.log").read_text() == "fixture scientific refusal"


def test_actual_support_hash_mismatch_refuses_publication(repository, source_root, science, monkeypatch):
    original = producer.scientific_producer.main
    def tamper(arguments):
        code = original(arguments)
        science["support"].write_text("changed support")
        return code
    monkeypatch.setattr(producer.scientific_producer, "main", tamper)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="does not match"):
        producer.publish(repository, source_root, output, repository / "artifacts/retained")
    assert not output.exists()


def test_raw_file_inside_aggregate_tree_refuses_publication(repository, source_root, science, monkeypatch):
    original = producer.scientific_producer.main
    def leak(arguments):
        code = original(arguments)
        (science["output"] / "raw-source.json").write_text("fixture raw bytes")
        return code
    monkeypatch.setattr(producer.scientific_producer, "main", leak)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="coverage is not exact"):
        producer.publish(repository, source_root, output, repository / "artifacts/retained")
    assert not output.exists()


def test_atomic_publication_failure_does_not_expose_partial_report(repository, source_root, science, monkeypatch):
    def fail(source, target):
        raise OSError("fixture publication denied")
    monkeypatch.setattr(producer.os, "replace", fail)
    output = repository / "artifacts/source-products"
    with pytest.raises(OSError, match="publication denied"):
        producer.publish(repository, source_root, output, repository / "artifacts/retained")
    assert not output.exists()
    assert (science["output"] / "report.json").read_bytes() == science["report_bytes"]
    assert science["support"].is_file()


def test_support_tamper_during_copy_refuses_publication(repository, source_root, science, monkeypatch):
    original = producer.shutil.copy2
    def tamper(source, target):
        value = original(source, target)
        science["support"].write_text("late changed support")
        return value
    monkeypatch.setattr(producer.shutil, "copy2", tamper)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="changed before publication"):
        producer.publish(repository, source_root, output, repository / "artifacts/retained")
    assert not output.exists()
