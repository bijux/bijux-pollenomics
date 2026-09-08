"""Repository fixtures for scientific-evidence materialization tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_VERSION,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    _CLASSIFICATION_AUTHORITY as CLASSIFICATION_AUTHORITY,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    _OUTPUT_NAMES as PROPAGATION_OUTPUT_NAMES,
)
from bijux_pollenomics.evidence.classification.audit_outputs.constants import (
    OUTPUT_NAMES as CLASSIFICATION_OUTPUT_NAMES,
)
from bijux_pollenomics_dev.ci import scientific_evidence


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def repository_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, object]]:
    """Create a closed repository and bind the imported product authority to it."""
    root = tmp_path / "repository"
    root.mkdir()
    classification_sources = (
        "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/producer.py",
    )
    propagation_sources = (
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/producer.py",
    )
    for path in (*classification_sources, *propagation_sources):
        _write(root / path, f"source:{path}\n".encode())
    classification_digest = scientific_evidence._producer_digest(
        root, classification_sources
    )
    propagation_digest = scientific_evidence._producer_digest(root, propagation_sources)
    classification_contract = (
        b'contract_id: "bijux-pollenomics.ecological-classification"\n'
        b'contract_version: "1.0.0"\n'
    )
    propagation_contract = (
        b'contract_id: "bijux-pollenomics.propagation-model"\n'
        b'contract_version: "1.0.0"\n'
    )
    _write(
        root / "configs/scientific-contracts/ecological-classification.v1.yaml",
        classification_contract,
    )
    _write(
        root / "configs/scientific-contracts/propagation-model.v1.yaml",
        propagation_contract,
    )
    monkeypatch.setattr(
        scientific_evidence,
        "PROPAGATION_PRODUCER_SOURCE_PATHS",
        propagation_sources,
    )
    authority = replace(
        CLASSIFICATION_AUTHORITY,
        manifest_sha256="c" * 64,
        source_snapshot_id="sha256:source",
        build_id="sha256:build",
        contract_digest=f"sha256:{hashlib.sha256(classification_contract).hexdigest()}",
        producer_digest=f"sha256:{classification_digest}",
        accepted_mapping_count=0,
    )
    monkeypatch.setattr(scientific_evidence, "_CLASSIFICATION_AUTHORITY", authority)
    classification_root = f"artifacts/execution-control/classification/neotoma-{classification_digest[:8]}"
    propagation_root = (
        f"artifacts/execution-control/propagation/neotoma-{propagation_digest[:8]}"
    )
    policy: dict[str, object] = {
        "schema_version": "release-evidence-policy.v3",
        "mode": "product",
        "required_artifacts": [
            {
                "identity": "classification",
                "role": "classification",
                "media_type": "application/json",
                "path": f"{classification_root}/manifest.json",
                "producer_path": scientific_evidence._CLASSIFICATION_PRODUCER_ROOT,
                "schema_identity_field": "schema_version",
                "schema_version": "classification-audit-manifest.v1",
            },
            {
                "identity": "propagation",
                "role": "generated_output",
                "media_type": "application/json",
                "path": f"{propagation_root}/manifest.json",
                "producer_path": scientific_evidence._PROPAGATION_PRODUCER_ROOT,
                "schema_identity_field": "schema_version",
                "schema_version": "propagation-output-manifest.v2",
            },
            {
                "identity": "scenario",
                "role": "scenario",
                "media_type": "application/json",
                "path": f"{propagation_root}/sensitivity_summary.json",
                "producer_path": scientific_evidence._PROPAGATION_PRODUCER_ROOT,
                "schema_identity_field": "schema_version",
                "schema_version": "propagation-sensitivity-summary.v1",
            },
        ],
        "embedded_producer_identities": [
            {
                "artifact_identity": "classification",
                "producer_id": authority.producer_id,
                "producer_version": authority.producer_version,
                "source_paths": list(classification_sources),
            },
            {
                "artifact_identity": "propagation",
                "producer_id": PROPAGATION_PRODUCER_ID,
                "producer_version": PROPAGATION_PRODUCER_VERSION,
                "source_paths": list(propagation_sources),
            },
        ],
        "bundle_inventories": [
            {
                "artifact_identity": "classification",
                "filenames": sorted(CLASSIFICATION_OUTPUT_NAMES),
            },
            {
                "artifact_identity": "propagation",
                "filenames": sorted(PROPAGATION_OUTPUT_NAMES),
            },
        ],
        "propagation_contract": {
            "contract_id": "bijux-pollenomics.propagation-model",
            "contract_version": "1.0.0",
            "sha256": f"sha256:{hashlib.sha256(propagation_contract).hexdigest()}",
        },
    }
    policy_path = root / "configs/release_evidence_policy.json"
    _write(policy_path, json.dumps(policy).encode())
    (root / "data/neotoma/relational").mkdir(parents=True)
    return root, policy


__all__ = ["repository_fixture"]
