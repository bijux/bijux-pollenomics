"""Manifest-bound bundle release posture tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import ArtifactInput, ReleaseEvidenceError
from bijux_pollenomics.provenance.release_evidence import embedded as release_embedded
from bijux_pollenomics.provenance.release_evidence import policy as release_policy

from .support import (
    _artifacts,
    _build,
    _fixture_bundle_payloads,
    _rewrite_fixture_policy,
)


def _configure_release_metadata_bundle(
    root: Path,
    artifacts: list[ArtifactInput],
    *,
    public_release_allowed: bool | None,
    manifest_schema_version: str = "fixture-bundle-manifest.v1",
    release_schema_version: str = "fixture-release-metadata.v1",
    status_namespace: str = "fixture_release",
    release_status: str,
    release_reason_field: str = "release_reason_codes",
    release_reason_codes: tuple[str, ...] = (),
) -> None:
    filenames = ("release_metadata.json",)
    bundle_digest = _fixture_bundle_payloads(
        root,
        "classification-bundle",
        filenames,
        manifest_schema_version=manifest_schema_version,
        public_release_allowed=public_release_allowed,
        release_schema_version=release_schema_version,
        status_namespace=status_namespace,
        release_status=release_status,
        release_reason_field=release_reason_field,
        release_reason_codes=release_reason_codes,
    )
    classification = next(
        artifact for artifact in artifacts if artifact.identity == "classification"
    )
    for index, artifact in enumerate(artifacts):
        updates: dict[str, object] = {}
        if artifact.identity == "classification":
            updates.update(
                path="classification-bundle/manifest.json",
                media_type="application/json",
                schema_version=manifest_schema_version,
                output_digest=bundle_digest,
            )
        if artifact.role in {"generated_output", "validation_result"}:
            updates["config_digests"] = tuple(
                bundle_digest if digest == classification.output_digest else digest
                for digest in artifact.config_digests
            )
        if updates:
            artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})

    def require_bundle(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        requirement = next(
            item for item in requirements if item["identity"] == "classification"
        )
        requirement["path"] = "classification-bundle/manifest.json"
        requirement["media_type"] = "application/json"
        requirement["schema_version"] = manifest_schema_version
        requirement["schema_identity_field"] = "schema_version"
        ownership = cast(list[dict[str, object]], policy["artifact_ownership"])
        next(
            item
            for item in ownership
            if item["artifact_path_prefix"] == "classification.csv"
        )["artifact_path_prefix"] = "classification-bundle"
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
                "filenames": list(filenames),
            }
        ]

    _rewrite_fixture_policy(root, artifacts, require_bundle)


def test_manifest_decision_preserves_bound_bundle_release_refusal(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    _configure_release_metadata_bundle(
        tmp_path,
        artifacts,
        public_release_allowed=False,
        release_status="review_required",
        release_reason_codes=("independent_scientific_review_required",),
    )
    manifest = _build(tmp_path, artifacts=artifacts)

    assert manifest["release_decision"] == {
        "release_ready": False,
        "status": "refused_invalid",
        "reason_codes": [
            (
                "required_artifact_release_refused:classification:"
                "fixture-release-metadata.v1:fixture_release:review_required:"
                "independent_scientific_review_required"
            ),
            "required_gate_not_independently_attested:quality",
        ],
    }


@pytest.mark.parametrize(
    (
        "public_release_allowed",
        "release_status",
        "release_reason_codes",
        "error",
    ),
    [
        (None, "approved", (), "release metadata approval is invalid"),
        (True, "", (), "release metadata release_status is invalid"),
        (
            True,
            "refused",
            (),
            "release metadata approval contradicts refusal posture",
        ),
        (
            True,
            "approved",
            ("scientific_release_refused",),
            "release metadata approval contradicts refusal posture",
        ),
    ],
)
def test_declared_bundle_release_metadata_requires_explicit_valid_posture(
    tmp_path: Path,
    public_release_allowed: bool | None,
    release_status: str,
    release_reason_codes: tuple[str, ...],
    error: str,
) -> None:
    artifacts = _artifacts(tmp_path)
    _configure_release_metadata_bundle(
        tmp_path,
        artifacts,
        public_release_allowed=public_release_allowed,
        release_status=release_status,
        release_reason_codes=release_reason_codes,
    )

    with pytest.raises(ReleaseEvidenceError, match=error):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    (
        "manifest_schema_version",
        "release_schema_version",
        "status_namespace",
        "error",
    ),
    [
        (
            "fixture-bundle-manifest.v1",
            "fixture-release-metadata.v1",
            "fixture_release",
            "release metadata contract is not governed",
        ),
        (
            "classification-audit-manifest.v1",
            "unknown-release-metadata.v1",
            "classification_release",
            "release metadata schema does not match bundle authority",
        ),
        (
            "classification-audit-manifest.v1",
            "classification-release-metadata.v1",
            "unknown_release",
            "release metadata namespace does not match bundle authority",
        ),
    ],
)
def test_product_bundle_release_metadata_requires_governed_contract(
    tmp_path: Path,
    manifest_schema_version: str,
    release_schema_version: str,
    status_namespace: str,
    error: str,
) -> None:
    artifacts = _artifacts(tmp_path)
    _configure_release_metadata_bundle(
        tmp_path,
        artifacts,
        public_release_allowed=False,
        manifest_schema_version=manifest_schema_version,
        release_schema_version=release_schema_version,
        status_namespace=status_namespace,
        release_status="refused",
        release_reason_codes=("scientific_release_refused",),
    )
    policy = replace(
        release_policy._load_release_evidence_policy(tmp_path), mode="product"
    )

    with pytest.raises(ReleaseEvidenceError, match=error):
        release_embedded._bundle_release_refusal_reasons(
            tmp_path,
            {artifact.identity: artifact for artifact in artifacts},
            policy,
        )


@pytest.mark.parametrize(
    (
        "manifest_schema_version",
        "release_schema_version",
        "status_namespace",
        "release_reason_field",
    ),
    [
        (
            "classification-audit-manifest.v1",
            "classification-release-metadata.v1",
            "classification_release",
            "release_reason_codes",
        ),
        (
            "propagation-output-manifest.v2",
            "propagation-release-metadata.v2",
            "propagation_release",
            "reason_codes",
        ),
    ],
)
def test_governed_product_bundle_refusal_preserves_native_reason(
    tmp_path: Path,
    manifest_schema_version: str,
    release_schema_version: str,
    status_namespace: str,
    release_reason_field: str,
) -> None:
    artifacts = _artifacts(tmp_path)
    _configure_release_metadata_bundle(
        tmp_path,
        artifacts,
        public_release_allowed=False,
        manifest_schema_version=manifest_schema_version,
        release_schema_version=release_schema_version,
        status_namespace=status_namespace,
        release_status="refused",
        release_reason_field=release_reason_field,
        release_reason_codes=("scientific_release_refused",),
    )
    policy = replace(
        release_policy._load_release_evidence_policy(tmp_path), mode="product"
    )

    assert release_embedded._bundle_release_refusal_reasons(
        tmp_path,
        {artifact.identity: artifact for artifact in artifacts},
        policy,
    ) == (
        (
            f"required_artifact_release_refused:classification:"
            f"{release_schema_version}:{status_namespace}:refused:"
            f"scientific_release_refused"
        ),
    )
