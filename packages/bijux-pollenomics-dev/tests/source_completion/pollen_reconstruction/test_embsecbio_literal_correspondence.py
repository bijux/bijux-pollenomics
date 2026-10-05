"""Exercise source custody, conditional support and compact output boundaries."""

from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    validated_author_snapshot,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_literal_correspondence import (
    producer,
    sources,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_literal_correspondence.account import (
    products,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_literal_correspondence.authority import (
    CAPTURE,
    DESCRIPTOR,
    SOURCE_ID,
    SOURCE_SHA256,
)

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    selected = os.environ.get("BIJUX_EMB_CORRESPONDENCE_SOURCE_ROOT")
    if not selected:
        pytest.skip("qualified private correspondence source store is not provisioned")
    base = tmp_path_factory.mktemp("literal-correspondence-source")
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


def test_original_snapshot_and_conditional_scopes(fixture):
    repository, store, values = fixture
    qualified = validated_author_snapshot(repository, store, DESCRIPTOR)
    assert qualified.directory == store / SOURCE_ID
    generated = products(values)
    report = generated["report.json"]
    assert (
        report["conditional_support"]["shared_matches_with_incomplete_reported_axes"]
        == 110
    )
    assert (
        report["conditional_support"]["entire_saved_vectors_exact_rational_equal"] == 0
    )
    assert [
        row["native_sample_id"] for row in report["entire_reported_axis_cases"]
    ] == [53, 3862]
    assert report["entire_reported_axis_cases"][0]["denominator_contains_polypodiales"]
    assert report["entire_reported_axis_cases"][1]["basin_category_2017"] == "LARG"
    assert report["entire_reported_axis_cases"][1]["basin_category_2021"] == "SMAL"


@pytest.mark.parametrize("name", sorted(SOURCE_SHA256))
def test_every_original_source_byte_pin(fixture, name):
    repository, store, _ = fixture
    path = store / SOURCE_ID / name
    with mutated(path, path.read_bytes() + b" "):
        with pytest.raises((ValueError, ReportRebuildError)):
            sources.load_inputs(repository, store)


@pytest.mark.parametrize("relative", [CAPTURE, DESCRIPTOR])
def test_configuration_and_capture_pins(fixture, relative):
    repository, store, _ = fixture
    path = repository / relative
    with mutated(path, path.read_bytes() + b" "):
        with pytest.raises(ValueError, match="changed"):
            sources.load_inputs(repository, store)


def test_snapshot_manifest_requires_dictionary(fixture):
    repository, store, _ = fixture
    path = store / SOURCE_ID / "snapshot-manifest.json"
    original_manifest = json.loads(path.read_bytes())
    original_manifest["files"] = []
    body = json.dumps(original_manifest, sort_keys=True).encode()
    descriptor = json.loads((repository / DESCRIPTOR).read_bytes())
    descriptor["manifest"]["sha256"] = hashlib.sha256(body).hexdigest()
    descriptor["manifest"]["size"] = len(body)
    semantic_path = DESCRIPTOR.with_name("source-dictionary-refusal.json")
    (repository / semantic_path).write_text(json.dumps(descriptor, sort_keys=True))
    with mutated(path, body):
        with pytest.raises(ReportRebuildError):
            validated_author_snapshot(repository, store, semantic_path)


def test_snapshot_specs_must_be_sorted(fixture):
    repository, store, _ = fixture
    descriptor = json.loads((repository / DESCRIPTOR).read_bytes())
    descriptor["files"].reverse()
    path = DESCRIPTOR.with_name("source-spec-order-refusal.json")
    (repository / path).write_text(json.dumps(descriptor, sort_keys=True))
    with pytest.raises(ReportRebuildError, match="sorted"):
        validated_author_snapshot(repository, store, path)


def test_source_store_symlink_refused(fixture):
    repository, store, _ = fixture
    alias = store.with_name("source-store-alias")
    alias.symlink_to(store, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        sources.load_inputs(repository, alias)


@pytest.mark.parametrize(
    "kind",
    [
        "exit",
        "custody",
        "survivors",
        "population",
        "duplicate_candidate",
        "authenticated_bridge",
        "nonfinite_gap",
        "full_as_242",
        "offset_support",
        "lost_refusal",
        "review_upgrade",
        "full_association",
    ],
)
def test_semantic_scope_refusals(fixture, kind):
    _, _, source = fixture
    values = copy.deepcopy(source)
    if kind == "exit":
        values["native-terminal.json"]["native_exit_code"] = True
    elif kind == "custody":
        values["native-terminal.json"]["custody_after_unchanged"] = False
    elif kind == "survivors":
        values["native-terminal.json"]["owned_survivors"] = {"1": {}}
    elif kind == "population":
        values["source-account.json"]["eligible_saved_integer_source_records"] = 431
    elif kind == "duplicate_candidate":
        values["candidate-source-rows.json"][0] = copy.deepcopy(
            values["candidate-source-rows.json"][1]
        )
    elif kind == "authenticated_bridge":
        values["correspondence-diagnostics.json"][0]["bridge_authenticated"] = True
    elif kind == "nonfinite_gap":
        values["correspondence-diagnostics.json"][0][
            "max_abs_shared_percentage_point_difference"
        ] = "NaN"
    elif kind == "full_as_242":
        values["full-vector-source-account.json"][0]["diagnostic"][
            "literal_common_label_count"
        ] = 242
    elif kind == "offset_support":
        row = next(
            row
            for row in values["correspondence-diagnostics.json"]
            if row["coordinate_numeric_agreement"]
        )
        row["id_bridge_hypothesis"] = "native_id_plus_20000_unverified"
    elif kind == "lost_refusal":
        values["supplement-access-account.json"]["http_status"] = 200
    elif kind == "review_upgrade":
        values["independent-source-review.json"]["acceptance"][
            "rights_or_externalqualified_review_admitted"
        ] = True
    elif kind == "full_association":
        values["full-vector-source-account.json"][0]["diagnostic"][
            "source_count_sum_all_labels"
        ] = "180"
    with pytest.raises(ValueError):
        sources.validate(values)


def test_output_is_compact_and_preserves_negative_offset(fixture):
    _, _, values = fixture
    generated = products(values)
    body = json.dumps(generated, sort_keys=True)
    assert len(body.encode()) < 32768
    forbidden = {
        "original_native_pollen_rows",
        "native_shared_integer_counts",
        "original_curated_rows",
        "native_age_fields_unchanged",
        "age_models2021",
    }

    def check(value):
        if isinstance(value, dict):
            assert not set(value) & forbidden
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    check(generated)
    offsets = [
        row
        for row in generated["report.json"]["bridge_attempts"]["by_hypothesis"]
        if row["hypothesis"] == "native_id_plus_20000_unverified"
    ]
    assert {row["outcome"]: row["rows"] for row in offsets} == {
        "numeric_id_found_coordinate_mismatch": 218,
        "refused_curated_numeric_id_absent": 212,
    }
    assert generated["source-refusals.json"]["supplement"]["http_status"] == 403


def test_existing_output_preserves_user_bytes(fixture):
    repository, store, _ = fixture
    output = repository / "artifacts" / "existing-user-output"
    output.mkdir()
    marker = output / "user.txt"
    marker.write_text("preserve")
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, output)
    assert marker.read_text() == "preserve"


def test_lexical_and_symlink_output_refusals(fixture):
    repository, store, _ = fixture
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, repository / "artifacts/../outside")
    target = repository / "artifacts" / "symlink-target"
    target.mkdir()
    alias = repository / "artifacts" / "symlink-alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        producer.publish(repository, store, alias / "output")


def test_atomic_publication_failure(fixture, monkeypatch):
    repository, store, _ = fixture
    output = repository / "artifacts" / "refused-publication"

    def refuse(*_):
        raise OSError("registered atomic-promotion refusal")

    monkeypatch.setattr(producer.os, "rename", refuse)
    with pytest.raises(OSError, match="promotion refusal"):
        producer.publish(repository, store, output)
    assert not output.exists()
    assert not list(output.parent.glob("literal-correspondence-*"))


@pytest.mark.parametrize("explicit", [False, True])
def test_descriptor_cli_accepts_default_and_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    repository = tmp_path / "absent-repository"
    source_root = tmp_path / "absent-source-store"
    output = tmp_path / "absent-output"
    calls: list[tuple[Path, Path, Path]] = []

    def capture(repository: Path, source_root: Path, output: Path) -> dict:
        calls.append((repository, source_root, output))
        return {}

    monkeypatch.setattr(producer, "publish", capture)
    argv = [
        "--repository",
        str(repository),
        "--source-root",
        str(source_root),
        "--output",
        str(output),
    ]
    if explicit:
        argv.extend(["--source-descriptor", DESCRIPTOR.as_posix()])
    assert producer.main(argv) == 0
    assert calls == [(repository, source_root, output)]
    assert not repository.exists() and not source_root.exists() and not output.exists()


@pytest.mark.parametrize(
    "descriptor",
    [
        "configs/ci/qualified-report-sources/unrelated.json",
        "/configs/ci/qualified-report-sources/embsecbio-literal-correspondence.json",
        "../configs/ci/qualified-report-sources/embsecbio-literal-correspondence.json",
        "configs/ci/qualified-report-sources/../qualified-report-sources/embsecbio-literal-correspondence.json",
    ],
)
def test_descriptor_cli_refuses_before_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor: str
) -> None:
    repository = tmp_path / "absent-repository"
    source_root = tmp_path / "absent-source-store"
    output = tmp_path / "absent-output"

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("descriptor refusal must precede publication")

    monkeypatch.setattr(producer, "publish", forbidden)
    with pytest.raises(SystemExit) as error:
        producer.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(source_root),
                "--output",
                str(output),
                "--source-descriptor",
                descriptor,
            ]
        )
    assert error.value.code == 2
    assert not repository.exists() and not source_root.exists() and not output.exists()
