"""Refuse authority, support, scope and output drift in the retained account."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.vegetation.namibia_grouped_mapped_area import (
    producer,
    sources,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_grouped_mapped_area.account import (
    products,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_grouped_mapped_area.authority import (
    CAPTURE,
    DESCRIPTOR,
    SOURCE_ID,
    SOURCE_SHA256,
)


def _object(value: object) -> dict[str, object]:
    """Require a retained JSON object while preserving its mutation identity."""
    assert isinstance(value, dict) and all(isinstance(key, str) for key in value)
    return value


def _array(value: object) -> list[object]:
    """Require a retained JSON array while preserving its mutation identity."""
    assert isinstance(value, list)
    return value


ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, object]]:
    """Provide fixture for the retained source contract."""
    selected = os.environ.get("BIJUX_NAMIBIA_MAPPED_AREA_SOURCE_ROOT")
    if not selected:
        pytest.skip("qualified private Namibia mapped-area sources are not provisioned")
    base = tmp_path_factory.mktemp("namibia-mapped-area-source")
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
    return repository, store, dict(values)


@contextmanager
def mutated(path: Path, body: bytes) -> Iterator[None]:
    """Provide mutated for the retained source contract."""
    original = path.read_bytes()
    path.write_bytes(body)
    try:
        yield
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("body", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'])
def test_duplicate_or_nonfinite_json_refused(body: bytes) -> None:
    """Verify duplicate or nonfinite json refused."""
    with pytest.raises(ValueError):
        sources.read_json(body)


@pytest.mark.parametrize("name", sorted(SOURCE_SHA256))
def test_every_retained_source_byte_is_independently_pinned(
    fixture: tuple[Path, Path, dict[str, object]], name: str
) -> None:
    """Verify every retained source byte is independently pinned."""
    repository, store, _ = fixture
    path = store / SOURCE_ID / name
    with (
        mutated(path, path.read_bytes() + b" "),
        pytest.raises((ValueError, ReportRebuildError)),
    ):
        sources.load_inputs(repository, store)


@pytest.mark.parametrize("relative", [DESCRIPTOR, CAPTURE])
def test_descriptor_and_capture_byte_pins(
    fixture: tuple[Path, Path, dict[str, object]], relative: Path
) -> None:
    """Verify descriptor and capture byte pins."""
    repository, store, _ = fixture
    path = repository / relative
    with mutated(path, path.read_bytes() + b" "), pytest.raises(ValueError):
        sources.load_inputs(repository, store)


SEMANTIC_MUTATIONS = [
    ("native-terminal.json", ["native_exit_code"], True),
    ("native-terminal.json", ["custody_after_unchanged"], False),
    ("native-terminal.json", ["resource_failure"], "actual-bound-failure"),
    ("native-terminal.json", ["status"], "PASS"),
    ("native-terminal.json", ["plan_sha256"], "0" * 64),
    ("native-terminal.json", ["native_files", "report.json", "sha256"], "0" * 64),
    ("study-plan.json", ["candidate"], "0" * 40),
    ("protocol.json", ["radius_selection_allowed"], True),
    ("protocol.json", ["target_data_already_exposed"], False),
    ("protocol.json", ["untouched_confirmation"], True),
    ("protocol.json", ["field_vegetation_accuracy"], True),
    ("protocol.json", ["PPE_or_ERV_estimation"], True),
    ("protocol.json", ["source_year_or_BP_conversion"], True),
    ("protocol.json", ["taxa", 0], "Senegalia"),
    ("protocol.json", ["expected_groups"], [["Namibia_T4"], ["Namibia_T5"]]),
    ("protocol.json", ["group_intersection_threshold_m"], 1500),
    ("native-report.json", ["status"], "finished"),
    ("native-report.json", ["population", "methods"], True),
    ("native-report.json", ["population", "unique_five_label_grain_total"], 6895),
    (
        "native-report.json",
        ["PPE_ERV_field_vegetation_Nordic_or_untouched_claim"],
        True,
    ),
    ("native-report.json", ["negative_contrasts_retained"], []),
    ("source-support.json", ["counts", "Namibia_T1", 0], True),
    ("source-support.json", ["areas_m2", "Namibia_T1", "100", 0], 0),
    ("overlap-folds.json", ["groups"], [["Namibia_T4"], ["Namibia_T5"]]),
    ("prediction-ledger.json", ["source_already_exposed"], False),
    ("prediction-ledger.json", ["predictions", 0, "training_groups"], [["Namibia_T1"]]),
    (
        "prediction-ledger.json",
        ["predictions", 0, "predicted_five_taxon_fractions"],
        [1, 0, 0, 0, 0],
    ),
    ("scores.json", ["prediction_ledger_sha256"], "0" * 64),
    ("scores.json", ["scores", 0, "squared_Hellinger"], 1.5),
    (
        "scores.json",
        ["scores", 0, "observed_deposited_calculated_area_fractions"],
        [1, 0, 0, 0, 0],
    ),
    ("scores.json", ["summaries", 0, "site_denominator"], 9),
    ("scores.json", ["all300_paired_contrasts"], []),
    ("independent-numerical-review.json", ["total_numeric_fields_compared"], 7289),
    ("independent-numerical-review.json", ["maximum_abs_numerical_gap"], "1e-3"),
    (
        "independent-numerical-review.json",
        ["same_interpreter_different_numerical_implementation"],
        False,
    ),
    (
        "original-account-saved-result-qualification.json",
        ["native_pending_report_preserved"],
        False,
    ),
    (
        "independent-account-review.json",
        ["actual_unfamiliar_reader_exercises_completed_by_this_review"],
        1,
    ),
    (
        "independent-account-review.json",
        ["qualified_external_review_decisions_received_by_this_review"],
        1,
    ),
]


@pytest.mark.parametrize("name,route,changed", SEMANTIC_MUTATIONS)
def test_actual_shaped_source_and_scope_refusals(
    fixture: tuple[Path, Path, dict[str, object]],
    name: str,
    route: list[str | int],
    changed: object,
) -> None:
    """Verify actual shaped source and scope refusals."""
    values = copy.deepcopy(fixture[2])
    target = values[name]
    for part in route[:-1]:
        target = (
            _object(target)[part] if isinstance(part, str) else _array(target)[part]
        )
    terminal = route[-1]
    if isinstance(terminal, str):
        _object(target)[terminal] = changed
    else:
        _array(target)[terminal] = changed
    with pytest.raises(ValueError):
        sources.validate(values)


def test_compact_account_preserves_all_radii_and_stronger_baseline_losses(
    fixture: tuple[Path, Path, dict[str, object]],
) -> None:
    """Verify compact account preserves all radii and stronger baseline losses."""
    rendered = products(fixture[2])
    assert set(rendered) == {
        "report.json",
        "comparisons.json",
        "assumptions.json",
        "source-account.json",
    }
    report = rendered["report.json"]
    assert report["population"]["unique_five_label_grain_total"] == 6894
    assert (
        report["original_native_pending_status"]
        == "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"
    )
    assert (
        report["original_report_pending_status"]
        == "new_training_only_development_consumer_completed_pending_independent_numerical_review"
    )
    assert report["subsequent_qualification"]["independent_numeric_fields"] == 7290
    assert (
        report["subsequent_qualification"]["qualified_external_reviews_received"] == 0
    )
    assert (
        report["untouched_field_vegetation_PPE_ERV_or_historical_reproduction_claim"]
        is False
    )
    comparison = rendered["comparisons.json"]
    assert comparison["all_original_radii_m"] == list(range(100, 1501, 100))
    assert len(comparison["all45_method_radius_means"]) == 45
    assert len(comparison["all300_paired_contrasts"]) == 300
    assert len(comparison["all110_poorer_contrasts"]) == 110
    assert comparison["paired_better_poorer_counts"] == {
        "uncorrected_pollen": {"better": 130, "poorer": 20},
        "training_mapped_composition": {"better": 60, "poorer": 90},
    }
    assert (
        comparison["all_radius_mean_better_poorer_counts"]["equal_site"][
            "training_mapped_composition"
        ]["poorer"]
        == 8
    )
    assert (
        comparison["all_radius_mean_better_poorer_counts"]["equal_group"][
            "training_mapped_composition"
        ]["poorer"]
        == 9
    )
    assert len(json.dumps(rendered).encode()) < 192 * 1024
    forbidden = {
        "counts",
        "areas_m2",
        "coordinate_tokens",
        "source_sample_ids",
        "predicted_five_taxon_fractions",
        "observed_deposited_calculated_area_fractions",
    }

    def check(value: object) -> None:
        if isinstance(value, dict):
            assert not set(value) & forbidden
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    check(rendered)


def test_unlisted_source_family_member_refused(
    fixture: tuple[Path, Path, dict[str, object]],
) -> None:
    """Verify unlisted source family member refused."""
    repository, store, _ = fixture
    extra = store / SOURCE_ID / "unexpected.json"
    extra.write_text("{}")
    try:
        with pytest.raises(ValueError, match="unexpected members"):
            sources.load_inputs(repository, store)
    finally:
        extra.unlink()


def test_late_source_tamper_removes_promoted_report(
    fixture: tuple[Path, Path, dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify late source tamper removes promoted report."""
    repository, store, _ = fixture
    output = repository / "artifacts/late-tamper-refusal"
    path = store / SOURCE_ID / "scores.json"
    original = path.read_bytes()
    real_load = sources.load_inputs
    calls = 0

    def load_with_late_tamper(repository: Path, source_root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 3:
            path.write_bytes(original + b" ")
        return dict(real_load(repository, source_root))

    monkeypatch.setattr(producer, "load_inputs", load_with_late_tamper)
    try:
        with pytest.raises((ValueError, ReportRebuildError)):
            producer.publish(repository, store, output)
        assert calls == 3
        assert not output.exists()
        assert not list(output.parent.glob("namibia-mapped-area-*"))
    finally:
        path.write_bytes(original)


def test_existing_user_output_is_preserved(
    fixture: tuple[Path, Path, dict[str, object]],
) -> None:
    """Verify existing user output is preserved."""
    repository, store, _ = fixture
    output = repository / "artifacts/user-output"
    output.mkdir()
    (output / "user.txt").write_text("preserve")
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, output)
    assert (output / "user.txt").read_text() == "preserve"


def test_lexical_and_symlink_writer_ownership(
    fixture: tuple[Path, Path, dict[str, object]],
) -> None:
    """Verify lexical and symlink writer ownership."""
    repository, store, _ = fixture
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, repository / "artifacts/../outside")
    target = repository / "artifacts/real-parent"
    target.mkdir()
    alias = repository / "artifacts/alias-parent"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, alias / "output")


def test_atomic_promotion_failure_leaves_no_report(
    fixture: tuple[Path, Path, dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify atomic promotion failure leaves no report."""
    repository, store, _ = fixture
    output = repository / "artifacts/refused-account"

    def refuse(*_: object) -> None:
        raise OSError("actual atomic promotion refusal")

    monkeypatch.setattr(os, "rename", refuse)
    with pytest.raises(OSError, match="promotion refusal"):
        producer.publish(repository, store, output)
    assert not output.exists()
    assert not list(output.parent.glob("namibia-mapped-area-*"))


@pytest.mark.parametrize("explicit", [False, True])
def test_cli_accepts_only_default_or_exact_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    """Verify cli accepts only default or exact descriptor."""
    calls = []

    def capture(repository: Path, source_root: Path, output: Path) -> dict[str, object]:
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
        "configs/../qualified-report-sources/namibia-grouped-mapped-area.json",
    ],
)
def test_cli_refuses_descriptor_before_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor: str
) -> None:
    """Verify cli refuses descriptor before writer."""

    def refuse(*_: object) -> None:
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
