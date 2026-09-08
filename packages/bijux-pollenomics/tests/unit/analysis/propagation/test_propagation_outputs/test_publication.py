"""Publication tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation.outputs import (
    PropagationOutputRefusalError,
)

from .support import (
    _REPOSITORY_ROOT,
    _classification_bundle,
    _event,
    _materialize,
    _read_json,
)


def test_symlinked_schema_root_and_contract_components_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    linked_schema_root = tmp_path / "linked-schemas"
    linked_schema_root.symlink_to(schema_root, target_is_directory=True)
    with pytest.raises(PropagationOutputRefusalError) as linked_root:
        _materialize(
            output_root=tmp_path / "linked-root-output",
            allowed_output_parent=tmp_path,
            schema_root=linked_schema_root,
        )

    contract_path = schema_root / "propagation-model.v1.yaml"
    real_contract = tmp_path / "governed-model.yaml"
    real_contract.write_bytes(contract_path.read_bytes())
    contract_path.unlink()
    contract_path.symlink_to(real_contract)
    with pytest.raises(PropagationOutputRefusalError) as linked_contract:
        _materialize(
            output_root=tmp_path / "linked-contract-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_path=contract_path,
        )

    assert linked_root.value.reason_code == "invalid_propagation_identity"
    assert linked_contract.value.reason_code == "invalid_propagation_identity"


def test_symlinked_classification_bundle_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_parent = tmp_path / "classification-parent"
    real_parent.mkdir()
    classification_root, classification_digest = _classification_bundle(real_parent, 0)
    linked_parent = tmp_path / "linked-classification-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "classification-ancestor-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=linked_parent / classification_root.name,
            classification_review_digest=classification_digest,
        )

    assert refusal.value.reason_code == "invalid_classification_identity"


def test_symlinked_repository_root_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    linked_parent = tmp_path / "linked-repository-parent"
    linked_parent.symlink_to(_REPOSITORY_ROOT.parent, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "repository-ancestor-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            repository_root=linked_parent / _REPOSITORY_ROOT.name,
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"


def test_symlinked_output_parent_ancestor_is_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_container = tmp_path / "output-container"
    allowed_parent = real_container / "allowed"
    allowed_parent.mkdir(parents=True)
    linked_container = tmp_path / "linked-output-container"
    linked_container.symlink_to(real_container, target_is_directory=True)
    linked_parent = linked_container / "allowed"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=linked_parent / "published",
            allowed_output_parent=linked_parent,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "unsafe_output_path"
    assert not (allowed_parent / "published").exists()


def test_non_identical_overwrite_is_refused_without_modification(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    altered_path = output_root / "release_metadata.json"
    altered_path.write_text("altered\n", encoding="utf-8")

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "non_identical_overwrite_refused"
    assert altered_path.read_text(encoding="utf-8") == "altered\n"
    assert not tuple(tmp_path.glob(".propagation.staging-*"))
    assert not (tmp_path / ".propagation.materialization.lock").exists()


def test_staging_failure_leaves_no_partial_bundle(
    tmp_path: Path,
    schema_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_root = tmp_path / "propagation"

    def refuse_fsync(_descriptor: int) -> None:
        raise OSError("injected staging write failure")

    monkeypatch.setattr(
        "bijux_pollenomics.analysis.propagation.outputs.publication.os.fsync",
        refuse_fsync,
    )

    with pytest.raises(OSError, match="injected staging write failure"):
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert not output_root.exists()
    assert not tuple(tmp_path.glob(".propagation.staging-*"))
    assert not (tmp_path / ".propagation.materialization.lock").exists()


@pytest.mark.parametrize("unsafe_kind", ("relative", "parent", "nested"))
def test_unsafe_output_paths_are_refused_before_writing(
    tmp_path: Path, schema_root: Path, unsafe_kind: str
) -> None:
    output_root = {
        "relative": Path("relative-propagation"),
        "parent": tmp_path,
        "nested": tmp_path / "nested" / "propagation",
    }[unsafe_kind]

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )

    assert refusal.value.reason_code == "unsafe_output_path"


def test_symlink_output_and_zero_mapping_event_input_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    real_output = tmp_path / "real-output"
    real_output.mkdir()
    linked_output = tmp_path / "linked-output"
    linked_output.symlink_to(real_output, target_is_directory=True)

    with pytest.raises(PropagationOutputRefusalError) as symlink_refusal:
        _materialize(
            output_root=linked_output,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
        )
    with pytest.raises(PropagationOutputRefusalError) as classification_refusal:
        _materialize(
            output_root=tmp_path / "classified-output",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            events=(_event("unaccepted"),),
        )

    assert symlink_refusal.value.reason_code == "unsafe_output_path"
    assert classification_refusal.value.reason_code == "unaccepted_classification_input"
    assert not (tmp_path / "classified-output").exists()


def test_schema_failure_refuses_the_bundle_before_publication(
    tmp_path: Path, schema_root: Path
) -> None:
    event_schema_path = schema_root / "phenomenon-event.schema.json"
    event_schema = _read_json(event_schema_path)
    properties = event_schema["properties"]
    assert isinstance(properties, dict)
    coordinate_quality = properties["coordinate_quality"]
    assert isinstance(coordinate_quality, dict)
    coordinate_quality["enum"] = ["exact"]
    event_schema_path.write_text(json.dumps(event_schema), encoding="utf-8")
    output_root = tmp_path / "propagation"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            events=(_event("schema-invalid"),),
            accepted_mapping_count=1,
        )

    assert refusal.value.reason_code == "schema_validation_failed"
    assert not output_root.exists()
