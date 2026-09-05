"""Bundle Closure tests."""

from __future__ import annotations
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    ReleaseEvidenceError,
    hash_repository_object,
)
from bijux_pollenomics.provenance.release_evidence import bundles as release_bundles
from bijux_pollenomics.provenance.release_evidence import models as release_models
from bijux_pollenomics.provenance.release_evidence import policy as release_policy
from .conftest import (
    _artifacts,
    _build,
    _canonical_json,
    _configure_fixture_embedded_producer,
    _digest,
    _fixture_bundle_payloads,
    _rewrite_fixture_policy,
)


@pytest.mark.parametrize("attack", ["old-schema", "current-producer"])
def test_embedded_producer_and_schema_reject_coherent_bundle_attacks(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)
    _configure_fixture_embedded_producer(tmp_path, artifacts)
    _build(tmp_path, artifacts=artifacts)

    if attack == "old-schema":
        path = tmp_path / "classification.csv"
        document = cast(dict[str, object], json.loads(path.read_bytes()))
        document["schema_version"] = "fixture-classification.v1"
        payload = _canonical_json(document) + b"\n"
        old_digest = _digest(path.read_bytes())
        path.write_bytes(payload)
        new_digest = _digest(payload)
        for index, artifact in enumerate(artifacts):
            updates: dict[str, object] = {}
            if artifact.identity == "classification":
                updates["output_digest"] = new_digest
            if artifact.role in {"generated_output", "validation_result"}:
                updates["config_digests"] = tuple(
                    new_digest if digest == old_digest else digest
                    for digest in artifact.config_digests
                )
            if updates:
                artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})
        error = "embedded schema identity mismatch"
    else:
        path = tmp_path / "producer.py"
        old_digest = _digest(path.read_bytes())
        path.write_bytes(b"def build(): return 2\n")
        new_digest = _digest(path.read_bytes())
        for index, artifact in enumerate(artifacts):
            updates = {}
            if artifact.identity == "producer":
                updates.update(
                    producer_digest=new_digest,
                    output_digest=new_digest,
                )
            elif artifact.producer_digest == old_digest:
                updates["producer_digest"] = new_digest
            if updates:
                artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})
        error = "embedded producer digest mismatch"

    with pytest.raises(ReleaseEvidenceError, match=error):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    ("bundle_identity", "filename"),
    [
        ("propagation", "release_metadata.json"),
        ("propagation", "primary_scenario_candidates.json"),
        ("propagation", "phenomenon_events.json"),
        ("classification", "accepted_mapping_queue.json"),
        ("classification", "release_metadata.json"),
    ],
)
def test_bundle_manifest_rejects_payload_only_tampering(
    tmp_path: Path, bundle_identity: str, filename: str
) -> None:
    artifacts = _artifacts(tmp_path)
    classification_files = (
        "accepted_mapping_queue.json",
        "release_metadata.json",
    )
    propagation_files = (
        "phenomenon_events.json",
        "primary_scenario_candidates.json",
        "release_metadata.json",
    )
    classification_digest = _fixture_bundle_payloads(
        tmp_path, "classification-bundle", classification_files
    )
    propagation_digest = _fixture_bundle_payloads(
        tmp_path, "propagation-bundle", propagation_files
    )
    old_classification = next(
        artifact for artifact in artifacts if artifact.identity == "classification"
    )
    for index, artifact in enumerate(artifacts):
        updates: dict[str, object] = {}
        if artifact.identity == "classification":
            updates.update(
                path="classification-bundle/manifest.json",
                media_type="application/json",
                schema_version="fixture-bundle-manifest.v1",
                output_digest=classification_digest,
            )
        elif artifact.identity == "output":
            updates.update(
                path="propagation-bundle/manifest.json",
                media_type="application/json",
                schema_version="fixture-bundle-manifest.v1",
                output_digest=propagation_digest,
            )
        if artifact.role in {"generated_output", "validation_result"}:
            updates["config_digests"] = tuple(
                classification_digest
                if digest == old_classification.output_digest
                else digest
                for digest in artifact.config_digests
            )
        if artifact.role == "validation_result":
            updates["parents"] = (ArtifactReference("output", propagation_digest),)
        if updates:
            artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})

    def require_bundles(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        for identity, path in (
            ("classification", "classification-bundle/manifest.json"),
            ("output", "propagation-bundle/manifest.json"),
        ):
            requirement = next(
                item for item in requirements if item["identity"] == identity
            )
            requirement["path"] = path
            requirement["media_type"] = "application/json"
            requirement["schema_version"] = "fixture-bundle-manifest.v1"
            requirement["schema_identity_field"] = "schema_version"
        ownership = cast(list[dict[str, object]], policy["artifact_ownership"])
        next(
            item
            for item in ownership
            if item["artifact_path_prefix"] == "classification.csv"
        )["artifact_path_prefix"] = "classification-bundle"
        next(
            item for item in ownership if item["artifact_path_prefix"] == "output.json"
        )["artifact_path_prefix"] = "propagation-bundle"
        policy["artifact_ownership"] = sorted(
            ownership,
            key=lambda item: (
                str(item["artifact_path_prefix"]),
                str(item["artifact_role"]),
            ),
        )
        policy["bundle_inventories"] = [
            {
                "artifact_identity": "classification",
                "filenames": list(classification_files),
            },
            {
                "artifact_identity": "output",
                "filenames": list(propagation_files),
            },
        ]

    _rewrite_fixture_policy(tmp_path, artifacts, require_bundles)
    _build(tmp_path, artifacts=artifacts)

    directory = (
        "classification-bundle"
        if bundle_identity == "classification"
        else "propagation-bundle"
    )
    (tmp_path / directory / filename).write_bytes(
        _canonical_json({"record_count": 1, "records": ["tampered"]}) + b"\n"
    )
    with pytest.raises(ReleaseEvidenceError, match="bundle member digest mismatch"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize("artifact_identity", ["classification", "propagation"])
def test_bundle_validator_rejects_public_directory_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_identity: str,
) -> None:
    _artifacts(tmp_path)
    filenames = (
        ("accepted_mapping_queue.json", "release_metadata.json")
        if artifact_identity == "classification"
        else ("phenomenon_events.json", "release_metadata.json")
    )
    directory_name = f"{artifact_identity}-bundle"
    manifest_digest = _fixture_bundle_payloads(tmp_path, directory_name, filenames)
    artifact = ArtifactInput(
        identity=artifact_identity,
        role="classification"
        if artifact_identity == "classification"
        else "generated_output",
        path=f"{directory_name}/manifest.json",
        media_type="application/json",
        schema_version="fixture-bundle-manifest.v1",
        parents=(),
        config_digests=(),
        producer_digest=None,
        output_digest=manifest_digest,
    )
    policy = release_policy._load_release_evidence_policy(tmp_path)
    policy = replace(
        policy,
        bundle_inventories=(
            release_models._BundleInventory(
                artifact_identity=artifact_identity,
                filenames=filenames,
            ),
        ),
    )
    public_directory = tmp_path / directory_name
    attacker_directory = tmp_path / f"{directory_name}-attacker"
    original_directory = tmp_path / f"{directory_name}-original"
    shutil.copytree(public_directory, attacker_directory)
    original_listdir = os.listdir
    swapped = False

    def swapping_listdir(directory_descriptor: int) -> list[str]:
        nonlocal swapped
        names = original_listdir(directory_descriptor)
        if not swapped:
            public_directory.rename(original_directory)
            attacker_directory.rename(public_directory)
            swapped = True
        return names

    monkeypatch.setattr(os, "listdir", swapping_listdir)
    with pytest.raises(ReleaseEvidenceError, match="public bundle directory changed"):
        release_bundles._validate_manifest_bundle_closures(
            tmp_path, {artifact_identity: artifact}, policy
        )
    assert swapped


def test_embedded_input_inventory_rejects_stale_governed_input_digest(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    payload = (
        _canonical_json(
            {
                "input_artifacts": [
                    {
                        "path": "receipt.json",
                        "sha256": "0" * 64,
                        "byte_count": len(b"immutable receipt\n"),
                    }
                ]
            }
        )
        + b"\n"
    )
    (tmp_path / "output.json").write_bytes(payload)
    output_digest = _digest(payload)
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "output_digest": output_digest}
    )
    validation = next(item for item in artifacts if item.identity == "validation")
    artifacts[artifacts.index(validation)] = ArtifactInput(
        **{
            **validation.__dict__,
            "parents": (ArtifactReference("output", output_digest),),
        }
    )

    def require_embedded_receipt(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        output_requirement = next(
            item for item in requirements if item["identity"] == "output"
        )
        output_requirement["required_embedded_input_paths"] = ["receipt.json"]

    _rewrite_fixture_policy(tmp_path, artifacts, require_embedded_receipt)

    with pytest.raises(ReleaseEvidenceError, match="embedded input digest mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_input_output_ancestor_overlap_is_refused_after_coherent_rehash(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    nested_output = tmp_path / "snapshot/generated/output.json"
    nested_output.parent.mkdir(parents=True)
    nested_output.write_bytes((tmp_path / "output.json").read_bytes())
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "path": "snapshot/generated/output.json"}
    )
    snapshot = next(item for item in artifacts if item.identity == "snapshot")
    snapshot_digest = cast(
        str, hash_repository_object(tmp_path, "snapshot")["output_digest"]
    )
    artifacts[artifacts.index(snapshot)] = ArtifactInput(
        **{**snapshot.__dict__, "output_digest": snapshot_digest}
    )
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "parents": (ArtifactReference("snapshot", snapshot_digest),),
        }
    )

    def move_output(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        next(item for item in requirements if item["identity"] == "output")["path"] = (
            "snapshot/generated/output.json"
        )
        rules = cast(list[dict[str, object]], policy["artifact_ownership"])
        next(item for item in rules if item["artifact_role"] == "generated_output")[
            "artifact_path_prefix"
        ] = "snapshot/generated/output.json"
        rules.sort(
            key=lambda item: (item["artifact_path_prefix"], item["artifact_role"])
        )

    _rewrite_fixture_policy(tmp_path, artifacts, move_output)

    with pytest.raises(ReleaseEvidenceError, match="overlaps an immutable input"):
        _build(tmp_path, artifacts=artifacts)
