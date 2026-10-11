"""Retained native joint authority, exact-source failures and output scope."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.joint_uncertainty import (
    DESCRIPTOR,
    compact_products,
    load_joint_inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.producer import (
    publish,
)


def _object(value: object) -> dict[str, object]:
    """Require a retained JSON object while preserving its mutation identity."""
    assert isinstance(value, dict) and all(isinstance(key, str) for key in value)
    return value


def _array(value: object) -> list[object]:
    """Require a retained JSON array while preserving its mutation identity."""
    assert isinstance(value, list)
    return value


@pytest.fixture
def source_store() -> Path:
    """Provide source store for the retained source contract."""
    root = os.environ.get("BIJUX_POLLENOMICS_JOINT_SOURCE_ROOT")
    if not root:
        pytest.skip("Exact retained Nordic joint external snapshot is not provisioned")
    return Path(root).resolve(strict=True)


@pytest.fixture
def repository(tmp_path: Path, source_store: Path) -> Path:
    """Provide repository for the retained source contract."""
    repository = tmp_path / "repository"
    repository.mkdir()
    target = repository / DESCRIPTOR
    target.parent.mkdir(parents=True)
    original = Path(__file__).resolve().parents[5] / DESCRIPTOR
    # The exercised candidate owns this exact descriptor; no inferred source inventory.
    shutil.copy2(original, target)
    return repository


@pytest.fixture
def inputs(repository: Path, source_store: Path) -> dict[str, dict[str, object]]:
    """Provide inputs for the retained source contract."""
    return {
        name: _object(value)
        for name, value in load_joint_inputs(repository, source_store).items()
    }


def test_actual_native_authority_and_compact_domain(
    inputs: dict[str, dict[str, object]],
) -> None:
    """Verify actual native authority and compact domain."""
    values = compact_products(inputs)
    assert set(values) == {"joint-uncertainty.json", "joint-capture-authority.json"}
    compact = values["joint-uncertainty.json"]
    authority = values["joint-capture-authority.json"]
    assert len(compact["axes"]) == 182 and compact["cover_components"] == 518
    assert (
        compact["distinct_count_supports"] == 80
        and len(compact["same_count_geometry_contrasts"]) == 124
    )
    assert compact["raw_sample_counts_published"] is False
    assert authority["execution_record"]["prelaunch_registration_succeeded"] is False
    assert authority["native_stage_exits"] == [0, 0, 0]
    assert authority["execution_record"]["frozen_members_verified"] == 9410
    assert authority["execution_record"]["control_files_verified"] == 10
    assert (
        "launch_record_incident" not in authority
        and "postexecution_review" not in authority
    )
    assert (
        authority["capture_source_file_sha256"]["launch-record-incident.json"]
        == authority["execution_record"]["launch_incident_source_sha256"]
    )
    assert "STATE" not in json.dumps(authority) and "shell" not in json.dumps(authority)
    assert (
        authority["independent_Decimal50"]["all_joint_covariance_cells_compared"]
        == 804972
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "failed_terminal",
        "failed_stage",
        "changed_plan",
        "changed_native_output",
        "changed_scientific_source",
        "changed_review_product",
        "changed_review_population",
        "changed_review_tolerance",
        "lost_incident",
        "false_prelaunch_success",
        "changed_postexecution_scope",
        "changed_source_report",
        "changed_axes",
        "changed_same_count_pair",
        "accuracy_claim",
    ],
)
def test_exact_retained_authority_refusals(
    inputs: dict[str, dict[str, object]], mutation: str
) -> None:
    """Verify exact retained authority refusals."""
    data = deepcopy(inputs)
    if mutation == "failed_terminal":
        _object(data["native-terminal.json"])["status"] = "FAIL"
    elif mutation == "failed_stage":
        _object(_array(_object(data["native-terminal.json"])["stages"])[1])[
            "native_exit"
        ] = 1
    elif mutation == "changed_plan":
        _object(data["native-terminal.json"])["plan_sha256"] = "0" * 64
    elif mutation == "changed_native_output":
        _object(data["native-terminal.json"])["joint_product_sha256"] = "0" * 64
    elif mutation == "changed_scientific_source":
        _object(
            _object(
                _object(_object(data["native-terminal.json"])["source_context"])[
                    "source_changes"
                ]
            )["bijux_pollenomics_lra/reconstruction/joint_fixed_site_covariance.py"]
        )["sha256"] = "0" * 64
    elif mutation == "changed_review_product":
        _object(data["independent-review.json"])["current_joint_product_sha256"] = (
            "0" * 64
        )
    elif mutation == "changed_review_population":
        _object(data["independent-review.json"])["distinct_count_supports"] = 182
    elif mutation == "changed_review_tolerance":
        _object(
            _object(data["independent-review.json"])["maximum_absolute_differences"]
        )["cover"] = "0.01"
    elif mutation == "lost_incident":
        _object(data["launch-record-incident.json"])["actual_prelaunch_exit"] = 0
    elif mutation == "false_prelaunch_success":
        _object(data["launch-record-incident.json"])["launch_record_status"] = (
            "registered before execution"
        )
    elif mutation == "changed_postexecution_scope":
        _object(data["postexecution-review.json"])["review_timing"] = (
            "prelaunch accepted"
        )
    elif mutation == "changed_source_report":
        _object(_object(data["joint-covariance.json"])["source_input_sha256"])[
            "native_report"
        ] = "0" * 64
    elif mutation == "changed_axes":
        _array(_object(data["joint-covariance.json"])["axes"]).pop()
    elif mutation == "changed_same_count_pair":
        _object(
            _array(_object(data["joint-covariance.json"])["geometry_contrasts"])[0]
        )["count_support_sha256"] = "0" * 64
    elif mutation == "accuracy_claim":
        _object(data["joint-covariance.json"])["vegetation_accuracy_claim"] = True
    with pytest.raises(ValueError):
        compact_products(data)


def test_changed_external_payload_refuses_exact_custody(
    repository: Path, source_store: Path, tmp_path: Path
) -> None:
    """Verify changed external payload refuses exact custody."""
    own = tmp_path / "own-source"
    shutil.copytree(source_store, own)
    packet = own / "nordic-shared-count-parameter-covariance"
    with (packet / "independent-review.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ReportRebuildError, match="source bytes differ"):
        load_joint_inputs(repository, own)


def test_joint_only_requires_explicit_source_root(
    repository: Path, tmp_path: Path
) -> None:
    """Verify joint only requires explicit source root."""
    with pytest.raises(ValueError, match="external source root"):
        publish(repository, repository / "artifacts/results", joint_only=True)


def test_joint_writer_retains_source_and_refuses_existing_output(
    repository: Path, source_store: Path
) -> None:
    """Verify joint writer retains source and refuses existing output."""
    output = repository / "artifacts/joint-account"
    values = publish(repository, output, source_root=source_store, joint_only=True)
    assert {p.name for p in output.iterdir()} == set(values)
    for name, value in values.items():
        assert json.loads((output / name).read_text()) == value
    with pytest.raises(ValueError, match="existing Nordic"):
        publish(repository, output, source_root=source_store, joint_only=True)
    assert compact_products(load_joint_inputs(repository, source_store)) == values


def test_configured_descriptor_accepts_exact_bound_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify configured descriptor accepts exact bound path."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
        producer,
    )

    calls = []
    monkeypatch.setattr(
        producer,
        "publish",
        lambda repository, output, **kwargs: calls.append((repository, output, kwargs)),
    )
    repository = tmp_path / "repository"
    output = repository / "artifacts/account"
    root = tmp_path / "qualified-sources"
    assert (
        producer.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(output),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--source-root",
                str(root),
            ]
        )
        == 0
    )
    assert calls == [(repository, output, {"source_root": root, "joint_only": False})]


@pytest.mark.parametrize(
    "descriptor",
    [
        "/absolute/joint-source-snapshot.json",
        "configs/ci/qualified-report-sources/other.json",
        "../joint-source-snapshot.json",
    ],
)
def test_configured_descriptor_refuses_wrong_identity_before_writer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, descriptor: str
) -> None:
    """Verify configured descriptor refuses wrong identity before writer."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
        producer,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("An unbound descriptor reached the publication writer")

    monkeypatch.setattr(producer, "publish", forbidden)
    with pytest.raises(ValueError, match="unexpected Nordic joint source descriptor"):
        producer.main(
            [
                "--repository",
                str(tmp_path),
                "--output",
                str(tmp_path / "artifacts/account"),
                "--source-descriptor",
                descriptor,
                "--source-root",
                str(tmp_path / "sources"),
            ]
        )


def test_configured_descriptor_requires_external_root_before_writer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify configured descriptor requires external root before writer."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
        producer,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "A descriptor without its external root reached the publication writer"
        )

    monkeypatch.setattr(producer, "publish", forbidden)
    with pytest.raises(
        ValueError, match="descriptor requires its external source root"
    ):
        producer.main(
            [
                "--repository",
                str(tmp_path),
                "--output",
                str(tmp_path / "artifacts/account"),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
            ]
        )


def test_configured_descriptor_optional_for_original_account_invocation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify configured descriptor optional for original account invocation."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
        producer,
    )

    calls = []
    monkeypatch.setattr(
        producer,
        "publish",
        lambda repository, output, **kwargs: calls.append((repository, output, kwargs)),
    )
    output = tmp_path / "artifacts/account"
    assert producer.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    assert calls == [(tmp_path, output, {"source_root": None, "joint_only": False})]
