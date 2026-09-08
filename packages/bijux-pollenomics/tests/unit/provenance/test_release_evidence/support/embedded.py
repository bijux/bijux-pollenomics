"""Embedded-producer identity fixture construction."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.provenance import ArtifactInput

from .codec import _canonical_json, _digest
from .mutation import _rewrite_fixture_policy


def _configure_fixture_embedded_producer(
    root: Path, artifacts: list[ArtifactInput]
) -> None:
    producer_path = "producer.py"
    source_records = [
        {
            "path": producer_path,
            "sha256": hashlib.sha256((root / producer_path).read_bytes()).hexdigest(),
        }
    ]
    producer_identity_digest = _digest(_canonical_json(source_records))
    payload = (
        _canonical_json(
            {
                "schema_version": "fixture-classification.v2",
                "fixture_producer_id": "fixture.classification-producer",
                "fixture_producer_version": "1",
                "fixture_producer_digest": producer_identity_digest,
            }
        )
        + b"\n"
    )
    classification_path = root / "classification.csv"
    old_classification_digest = _digest(classification_path.read_bytes())
    classification_path.write_bytes(payload)
    new_classification_digest = _digest(payload)
    for index, artifact in enumerate(artifacts):
        updates: dict[str, object] = {}
        if artifact.identity == "classification":
            updates.update(
                media_type="application/json",
                schema_version="fixture-classification.v2",
                output_digest=new_classification_digest,
            )
        if artifact.role in {"generated_output", "validation_result"}:
            updates["config_digests"] = tuple(
                new_classification_digest
                if digest == old_classification_digest
                else digest
                for digest in artifact.config_digests
            )
        if updates:
            artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})

    def require_embedded_producer(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        classification = next(
            item for item in requirements if item["identity"] == "classification"
        )
        classification["media_type"] = "application/json"
        classification["schema_version"] = "fixture-classification.v2"
        classification["schema_identity_field"] = "schema_version"
        policy["embedded_producer_identities"] = [
            {
                "artifact_identity": "classification",
                "producer_artifact_identity": "producer",
                "producer_id": "fixture.classification-producer",
                "producer_version": "1",
                "id_field": "fixture_producer_id",
                "version_field": "fixture_producer_version",
                "digest_field": "fixture_producer_digest",
                "digest_prefix": "sha256:",
                "source_paths": [producer_path],
            }
        ]

    _rewrite_fixture_policy(root, artifacts, require_embedded_producer)
