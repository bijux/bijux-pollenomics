"""Materialization harness for propagation output tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.analysis.propagation.network import PhenomenonEvent
from bijux_pollenomics.analysis.propagation.outputs import (
    PropagationMaterializationResult,
    materialize_propagation_outputs,
)
from bijux_pollenomics.analysis.propagation.outputs import (
    classification as propagation_classification,
)

from .classification import classification_bundle
from .json_codec import read_json
from .model import PROPAGATION_CONTRACT_DIGEST, PROPAGATION_CONTRACT_VERSION
from .producer import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_VERSION,
    REPOSITORY_ROOT,
    producer_digest,
)


def materialize(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    schema_root: Path,
    classification_bundle_root: Path | None = None,
    classification_review_digest: str | None = None,
    events: tuple[PhenomenonEvent, ...] = (),
    accepted_mapping_count: int = 0,
    build_id: str = "build-1",
    classification_contract_version: str = "classification.v1",
    propagation_contract_version: str = PROPAGATION_CONTRACT_VERSION,
    propagation_contract_digest: str = PROPAGATION_CONTRACT_DIGEST,
    propagation_contract_path: Path | None = None,
    propagation_producer_id: str = PROPAGATION_PRODUCER_ID,
    propagation_producer_version: str = PROPAGATION_PRODUCER_VERSION,
    propagation_producer_digest: str | None = None,
    repository_root: Path = REPOSITORY_ROOT,
    use_product_classification_authority: bool = False,
) -> PropagationMaterializationResult:
    """Invoke the product writer against a closed test authority."""
    if classification_bundle_root is None:
        classification_bundle_root, observed_review_digest = classification_bundle(
            allowed_output_parent,
            accepted_mapping_count,
        )
    else:
        observed_review_digest = hashlib.sha256(
            (classification_bundle_root / "manifest.json").read_bytes()
        ).hexdigest()
    if classification_review_digest is None:
        classification_review_digest = observed_review_digest
    if propagation_producer_digest is None:
        propagation_producer_digest = producer_digest()
    if propagation_contract_path is None:
        propagation_contract_path = schema_root / "propagation-model.v1.yaml"
    manifest = read_json(classification_bundle_root / "manifest.json")
    release = read_json(classification_bundle_root / "release_metadata.json")
    authority_accepted_count = release["accepted_mapping_count"]
    assert isinstance(authority_accepted_count, int)
    product_authority = getattr(
        propagation_classification,
        "_CLASSIFICATION_AUTHORITY",
    )
    test_authority = replace(
        product_authority,
        manifest_sha256=observed_review_digest,
        source_family=str(manifest["source_family"]),
        source_snapshot_id=str(manifest["source_snapshot_id"]),
        build_id=str(manifest["build_id"]),
        contract_version=str(manifest["classification_contract_version"]),
        contract_digest=str(manifest["classification_contract_digest"]),
        producer_id=str(manifest["classification_producer_id"]),
        producer_version=str(manifest["classification_producer_version"]),
        producer_digest=str(manifest["classification_producer_digest"]),
        accepted_mapping_count=authority_accepted_count,
    )

    def invoke() -> PropagationMaterializationResult:
        return materialize_propagation_outputs(
            events,
            output_root=output_root,
            allowed_output_parent=allowed_output_parent,
            schema_root=schema_root,
            classification_bundle_root=classification_bundle_root,
            propagation_contract_path=propagation_contract_path,
            repository_root=repository_root,
            build_id=build_id,
            classification_contract_version=classification_contract_version,
            classification_review_digest=classification_review_digest,
            accepted_classification_mapping_count=accepted_mapping_count,
            propagation_contract_version=propagation_contract_version,
            propagation_contract_digest=propagation_contract_digest,
            propagation_producer_id=propagation_producer_id,
            propagation_producer_version=propagation_producer_version,
            propagation_producer_digest=propagation_producer_digest,
        )

    if use_product_classification_authority:
        return invoke()
    with patch.object(
        propagation_classification, "_CLASSIFICATION_AUTHORITY", test_authority
    ):
        return invoke()
