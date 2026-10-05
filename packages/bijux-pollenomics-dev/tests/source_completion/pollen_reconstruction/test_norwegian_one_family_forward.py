"""Refuse authority, support, scope and output drift in the retained account."""

from __future__ import annotations

from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.norwegian_one_family_forward import (
    producer,
    sources,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.norwegian_one_family_forward.account import (
    products,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.norwegian_one_family_forward.authority import (
    CAPTURE,
    DESCRIPTOR,
    SOURCE_ID,
    SOURCE_SHA256,
)

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    selected = os.environ.get("BIJUX_NORWEGIAN_FORWARD_SOURCE_ROOT")
    if not selected:
        pytest.skip("qualified private Norwegian forward sources are not provisioned")
    base = tmp_path_factory.mktemp("norwegian-forward-source")
    repository = base / "repository"
    repository.mkdir()
    for relative in (DESCRIPTOR, CAPTURE):
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (repository / "artifacts").mkdir()
    store = base / "source-store"
    shutil.copytree(Path(selected) / SOURCE_ID, store / SOURCE_ID)
    values = sources.load_inputs(repository, store)
    return repository, store, values


@contextmanager
def mutated(path: Path, body: bytes):
    original = path.read_bytes()
    path.write_bytes(body)
    try:
        yield
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("body", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'])
def test_duplicate_or_nonfinite_json_refused(body):
    with pytest.raises(ValueError):
        sources.read_json(body)


@pytest.mark.parametrize("name", sorted(SOURCE_SHA256))
def test_every_retained_source_byte_is_independently_pinned(fixture, name):
    repository, store, _ = fixture
    path = store / SOURCE_ID / name
    with mutated(path, path.read_bytes() + b" "):
        with pytest.raises((ValueError, ReportRebuildError)):
            sources.load_inputs(repository, store)


@pytest.mark.parametrize("relative", [DESCRIPTOR, CAPTURE])
def test_descriptor_and_capture_byte_pins(fixture, relative):
    repository, store, _ = fixture
    path = repository / relative
    with mutated(path, path.read_bytes() + b" "):
        with pytest.raises(ValueError):
            sources.load_inputs(repository, store)


SEMANTIC_MUTATIONS = [
    ("native-terminal.json", ["native_exit_code"], True),
    ("native-terminal.json", ["custody_after_unchanged"], False),
    ("native-terminal.json", ["resource_failure"], "actual-bound-failure"),
    ("native-terminal.json", ["plan_sha256"], "0" * 64),
    ("protocol.json", ["context_mask"], [1486]),
    ("protocol.json", ["grouping", "independent_training_family_count"], 2),
    ("protocol.json", ["cores", 0, "chronology_id"], 30603),
    ("protocol.json", ["panel", 1, "native_taxon_id"], 125),
    (
        "model-report.json",
        ["new252physical_and_independent_scalar_qualification_pending"],
        False,
    ),
    ("model-report.json", ["empirical_accuracy_or_untouched_claim"], True),
    ("model-report.json", ["prediction_ledger_written_before_current_scoring"], False),
    ("model-report.json", ["core_sample_populations", "4286", "accepted"], 56),
    ("model-report.json", ["paired_contrasts"], []),
    (
        "prediction-ledger.json",
        [0, "predictions", "physical_inverse_forward"],
        [1.1, -0.1],
    ),
    ("prediction-ledger.json", [0, "forward_predictive_uncertainty_emitted"], True),
    ("score-ledger.json", [0, "prediction_ledger_sha256"], "0" * 64),
    ("score-ledger.json", [0, "target_panel_N"], 1),
    ("outcome-ledger.json", [19, "target_counts"], [0, 0]),
    ("independent-scalar-review.json", ["actual_scalar_cell_comparisons"], 631),
    ("independent-scalar-review.json", ["source_model_report_sha256"], "0" * 64),
    ("independent-physical-review.json", ["actual_new_tuples"], 300),
    (
        "independent-physical-review.json",
        ["results", 0, "parameters", "receiver_radius_m"],
        80,
    ),
    ("source-guards.json", ["actual_controls"], 14),
    ("stages.json", [2, "native_exit_code"], 1),
    ("independent-output-review.json", ["accepted_for_scoped_retention"], False),
]


@pytest.mark.parametrize("name,route,changed", SEMANTIC_MUTATIONS)
def test_actual_shaped_source_and_scope_refusals(fixture, name, route, changed):
    values = copy.deepcopy(fixture[2])
    target = values[name]
    for part in route[:-1]:
        target = target[part]
    target[route[-1]] = changed
    with pytest.raises(ValueError):
        sources.validate(values)


def test_compact_account_preserves_scope_and_poorer_windows(fixture):
    rendered = products(fixture[2])
    assert set(rendered) == {
        "report.json",
        "comparisons.json",
        "assumptions.json",
        "source-account.json",
    }
    report = rendered["report.json"]
    assert report["population"]["predicted_windows"] == 20
    assert report["population"]["paired_target_windows"] == 18
    assert report["qualification"]["original_model_report_pending_flag"] is True
    assert report["qualification"]["independent_Decimal50_cells"] == 632
    assert report["shared_PPE_identified_by_pollen_predictions"] is False
    assert rendered["comparisons.json"][
        "physical_poorer_than_baseline_window_indices"
    ] == {"count_pooled_pollen": [], "equal_source_pollen_mean": [17, 19, 21]}
    assert len(json.dumps(rendered).encode()) < 128 * 1024
    forbidden = {
        "training_counts",
        "training_sample_ids",
        "target_counts",
        "target_sample_ids",
        "native_ages",
        "counts",
        "windows_by_sample",
    }

    def check(value: Any) -> None:
        if isinstance(value, dict):
            assert not set(value) & forbidden
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    check(rendered)


def test_existing_user_output_is_preserved(fixture):
    repository, store, _ = fixture
    output = repository / "artifacts/user-output"
    output.mkdir()
    (output / "user.txt").write_text("preserve")
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, output)
    assert (output / "user.txt").read_text() == "preserve"


def test_lexical_and_symlink_writer_ownership(fixture):
    repository, store, _ = fixture
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, repository / "artifacts/../outside")
    target = repository / "artifacts/real-parent"
    target.mkdir()
    alias = repository / "artifacts/alias-parent"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, alias / "output")


def test_atomic_promotion_failure_leaves_no_report(fixture, monkeypatch):
    repository, store, _ = fixture
    output = repository / "artifacts/refused-account"

    def refuse(*_):
        raise OSError("actual atomic promotion refusal")

    monkeypatch.setattr(producer.os, "rename", refuse)
    with pytest.raises(OSError, match="promotion refusal"):
        producer.publish(repository, store, output)
    assert not output.exists()
    assert not list(output.parent.glob("norwegian-forward-*"))


@pytest.mark.parametrize("explicit", [False, True])
def test_cli_accepts_only_default_or_exact_descriptor(tmp_path, monkeypatch, explicit):
    calls = []

    def capture(repository, source_root, output):
        calls.append((repository, source_root, output))
        return {}

    monkeypatch.setattr(producer, "publish", capture)
    argv = [
        "--repository",
        str(tmp_path / "repository"),
        "--source-root",
        str(tmp_path / "source"),
        "--output",
        str(tmp_path / "output"),
    ]
    if explicit:
        argv += ["--source-descriptor", DESCRIPTOR.as_posix()]
    assert producer.main(argv) == 0
    assert len(calls) == 1


@pytest.mark.parametrize(
    "descriptor",
    [
        "wrong.json",
        "/absolute.json",
        "configs/../qualified-report-sources/norwegian-one-family-forward.json",
    ],
)
def test_cli_refuses_descriptor_before_writer(tmp_path, monkeypatch, descriptor):
    def refuse(*_):
        raise AssertionError("source writer must not be reached")

    monkeypatch.setattr(producer, "publish", refuse)
    with pytest.raises(SystemExit):
        producer.main(
            [
                "--repository",
                str(tmp_path / "repository"),
                "--source-root",
                str(tmp_path / "source"),
                "--output",
                str(tmp_path / "output"),
                "--source-descriptor",
                descriptor,
            ]
        )
