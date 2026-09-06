"""Product release-evidence policy contract tests."""

from __future__ import annotations

import json
from typing import cast

from bijux_pollenomics.provenance import ArtifactInput, hash_repository_object
from bijux_pollenomics.provenance.release_evidence import bundles as release_bundles
from bijux_pollenomics.provenance.release_evidence import embedded as release_embedded
from bijux_pollenomics.provenance.release_evidence import policy as release_policy
from tests.support.repository import REPOSITORY_ROOT

from ..support import _canonical_json


def test_product_policy_binds_exact_release_inventory_and_producer_authority() -> None:
    repository_root = REPOSITORY_ROOT
    policy_path = repository_root / "configs/release_evidence_policy.json"
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    artifacts = {item["identity"]: item for item in policy["required_artifacts"]}

    assert policy["mode"] == "product"
    assert policy_bytes == _canonical_json(policy) + b"\n"
    assert policy["recording_authority_path"] == (
        "packages/bijux-pollenomics/src/bijux_pollenomics/provenance"
    )
    assert policy["required_gate_ids"] == [
        "data",
        "doc-counts",
        "map",
        "provenance",
        "science",
    ]
    assert policy["propagation_contract"] == {
        "contract_id": "bijux-pollenomics.propagation-model",
        "contract_version": "1.0.0",
        "sha256": (
            "sha256:cd3c6ebdb01d1d3e2759df1984b8bc0e8993e19891e517dffe6babb77e11acea"
        ),
        "default_scenario": {
            "scenario_id": "rectangular_100km_100yr_v1",
            "maximum_distance_km": 100.0,
            "maximum_lag_years": 100.0,
        },
    }
    assert artifacts["dependency-lock"]["producer_path"] is None
    assert artifacts["aadr-snapshot"]["producer_path"].endswith("/adna")
    assert artifacts["classification"]["producer_path"].endswith(
        "/evidence/classification"
    )
    assert artifacts["classification"]["schema_version"] == (
        "classification-audit-manifest.v1"
    )
    assert artifacts["classification"]["path"] == (
        "artifacts/execution-control/classification/"
        "neotoma-audit-5a932522/manifest.json"
    )
    assert artifacts["country-coverage"]["schema_version"] == (
        "country-dimension-coverage-ledger.v1"
    )
    assert artifacts["propagation"]["schema_version"] == (
        "propagation-output-manifest.v2"
    )
    assert artifacts["scenario"]["path"].endswith("/sensitivity_summary.json")
    assert artifacts["scenario"]["schema_version"] == (
        "propagation-sensitivity-summary.v1"
    )
    embedded_producers = {
        item["artifact_identity"]: item
        for item in policy["embedded_producer_identities"]
    }
    assert set(embedded_producers) == {"classification", "propagation", "scenario"}
    assert embedded_producers["classification"]["producer_artifact_identity"] == (
        "producer-classification"
    )
    assert embedded_producers["classification"]["digest_prefix"] == "sha256:"
    classification_root = (
        "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification"
    )
    assert embedded_producers["classification"]["source_paths"] == [
        f"{classification_root}/neotoma/__init__.py",
        f"{classification_root}/neotoma/accounting.py",
        f"{classification_root}/neotoma/concepts.py",
        f"{classification_root}/neotoma/countries.py",
        f"{classification_root}/neotoma/partitions.py",
        f"{classification_root}/neotoma/rows.py",
        f"{classification_root}/audit_outputs/__init__.py",
        f"{classification_root}/audit_outputs/accounting.py",
        f"{classification_root}/audit_outputs/constants.py",
        f"{classification_root}/audit_outputs/manifest.py",
        f"{classification_root}/audit_outputs/models.py",
        f"{classification_root}/audit_outputs/partitions.py",
        f"{classification_root}/audit_outputs/payloads.py",
        f"{classification_root}/audit_outputs/publication.py",
        f"{classification_root}/audit_outputs/queues.py",
        f"{classification_root}/audit_outputs/values.py",
        f"{classification_root}/audit_outputs/workflow.py",
    ]
    assert embedded_producers["propagation"]["producer_artifact_identity"] == (
        "producer-analysis"
    )
    assert embedded_producers["propagation"]["digest_prefix"] == ""
    loaded_policy = release_policy._load_release_evidence_policy(repository_root)
    product_artifacts = {
        requirement.identity: ArtifactInput(
            identity=requirement.identity,
            role=requirement.role,
            path=requirement.path,
            media_type=requirement.media_type,
            schema_version=requirement.schema_version,
            parents=(),
            config_digests=(),
            producer_digest=None,
            output_digest=(
                cast(
                    str,
                    hash_repository_object(repository_root, requirement.path)[
                        "output_digest"
                    ],
                )
                if requirement.identity in {"classification", "propagation"}
                else "sha256:" + "0" * 64
            ),
        )
        for requirement in loaded_policy.required_artifacts
    }
    release_embedded._validate_embedded_producer_identities(
        repository_root, product_artifacts, loaded_policy
    )
    release_bundles._validate_manifest_bundle_closures(
        repository_root, product_artifacts, loaded_policy
    )
    release_embedded._validate_propagation_contract_binding(
        repository_root, product_artifacts, loaded_policy
    )
    assert artifacts["map-publication"]["path"].endswith("/nordic_map.html")
    for identity in ("classification", "country-coverage", "propagation", "scenario"):
        artifact = artifacts[identity]
        content = json.loads((repository_root / artifact["path"]).read_text())
        assert content[artifact["schema_identity_field"]] == artifact["schema_version"]
    assert all(
        "required_parent_identities" in item and "schema_identity_field" in item
        for item in artifacts.values()
    )
    for artifact in artifacts.values():
        producer_path = artifact["producer_path"]
        if producer_path is None:
            continue
        ownership_matches = [
            rule
            for rule in policy["artifact_ownership"]
            if rule["artifact_role"] == artifact["role"]
            and (
                artifact["path"] == rule["artifact_path_prefix"]
                or artifact["path"].startswith(rule["artifact_path_prefix"] + "/")
            )
        ]
        assert len(ownership_matches) == 1
        assert ownership_matches[0]["producer_path"] == producer_path
    assert set(artifacts["country-coverage"]["required_parent_identities"]) == {
        "aadr-snapshot",
        "boundary",
        "classification",
        "neotoma-snapshot",
        "sead-evidence",
    }
    assert set(artifacts["gate-map"]["required_parent_identities"]) == {
        "country-coverage",
        "map-publication",
        "propagation",
    }
    country_inputs = artifacts["country-coverage"]["required_embedded_input_paths"]
    country_document = json.loads(
        (repository_root / artifacts["country-coverage"]["path"]).read_text()
    )
    assert len(country_inputs) == 18
    assert set(country_inputs) == {
        item["path"] for item in country_document["input_artifacts"]
    }
    assert {
        (item["source"], item["entity"]) for item in policy["required_reconciliations"]
    } >= {
        ("aadr", "localities"),
        ("animal_adna", "localities"),
        ("classification", "ambiguous"),
        ("classification", "mapped"),
        ("classification", "unmapped"),
        ("propagation", "candidate_statuses"),
        ("propagation", "nodes"),
        ("propagation", "pair_refusals"),
        ("sead", "chronology_claims"),
        ("sead", "relations"),
    }
