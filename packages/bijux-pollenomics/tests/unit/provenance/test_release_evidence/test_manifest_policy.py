"""Manifest Policy tests."""

from __future__ import annotations
import copy
import json
from pathlib import Path
from tests.support.repository import REPOSITORY_ROOT
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    GateResult,
    ReleaseEvidenceError,
    hash_repository_object,
    validate_release_evidence_manifest,
)
from bijux_pollenomics.provenance.release_evidence import bundles as release_bundles
from bijux_pollenomics.provenance.release_evidence import embedded as release_embedded
from bijux_pollenomics.provenance.release_evidence import policy as release_policy
from .conftest import (
    _artifacts,
    _build,
    _canonical_json,
    _digest,
    _json_digest,
    _reconciliations,
    _rewrite_fixture_policy,
    _rewrite_gate_record,
)


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
        "neotoma-audit-7bdba3d4/manifest.json"
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


def test_manifest_is_deterministic_for_shuffled_inputs(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path, gate_id="alpha", gate_ids=("alpha", "zeta"))
    alpha_validation = next(
        artifact for artifact in artifacts if artifact.identity == "validation"
    )
    zeta_validation = next(
        artifact for artifact in artifacts if artifact.identity == "zeta-validation"
    )
    gates = [
        GateResult("zeta", "PASS", True, zeta_validation.output_digest),
        GateResult("alpha", "PASS", True, alpha_validation.output_digest),
    ]
    reconciliations = _reconciliations()

    first = _build(
        tmp_path, artifacts=artifacts, gates=gates, reconciliations=reconciliations
    )
    second = _build(
        tmp_path,
        artifacts=list(reversed(artifacts)),
        gates=list(reversed(gates)),
        reconciliations=list(reversed(reconciliations)),
    )

    assert first == second
    assert first["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "required_gate_not_independently_attested:alpha",
            "required_gate_not_independently_attested:zeta",
        ],
    }
    validate_release_evidence_manifest(tmp_path, first)


def test_artifacts_may_bind_distinct_governed_producers(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    second_digest = _digest(b"def render(): return 2\n")

    manifest = _build(tmp_path, artifacts=artifacts)

    producer_digests = {
        artifact["output_digest"]
        for artifact in cast(list[dict[str, object]], manifest["artifacts"])
        if artifact["role"] == "producer"
    }
    assert producer_digests == {
        _digest(b"def build(): return 1\n"),
        second_digest,
    }
    validate_release_evidence_manifest(tmp_path, manifest)


def test_coherent_producer_reassignment_is_refused_by_product_policy(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    output = next(item for item in artifacts if item.identity == "output")
    primary = next(item for item in artifacts if item.identity == "producer")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "producer_digest": primary.output_digest}
    )

    with pytest.raises(ReleaseEvidenceError, match="producer ownership mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_duplicate_digest_and_unused_producer_artifacts_are_refused(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    duplicate_path = tmp_path / "secondary-producer.py"
    duplicate_path.write_bytes(b"def build(): return 1\n")
    duplicate_digest = _digest(duplicate_path.read_bytes())
    secondary = next(
        item for item in artifacts if item.identity == "secondary-producer"
    )
    artifacts[artifacts.index(secondary)] = ArtifactInput(
        **{
            **secondary.__dict__,
            "producer_digest": duplicate_digest,
            "output_digest": duplicate_digest,
        }
    )
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "producer_digest": duplicate_digest}
    )
    with pytest.raises(ReleaseEvidenceError, match="duplicate producer digest"):
        _build(tmp_path, artifacts=artifacts)

    unused = _artifacts(
        tmp_path,
        secondary_producer=True,
        output_uses_secondary=False,
    )
    with pytest.raises(ReleaseEvidenceError, match="unused producer artifacts"):
        _build(tmp_path, artifacts=unused)


def test_outputs_must_bind_the_product_policy_digest(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    policy = next(
        item for item in artifacts if item.identity == "release-evidence-policy"
    )
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "config_digests": tuple(
                digest
                for digest in output.config_digests
                if digest != policy.output_digest
            ),
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="lacks release policy digest"):
        _build(tmp_path, artifacts=artifacts)


def test_output_configuration_closure_is_exact(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    boundary = next(item for item in artifacts if item.identity == "boundary")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "config_digests": tuple(
                digest
                for digest in output.config_digests
                if digest != boundary.output_digest
            ),
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="configuration closure mismatch"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)

    def narrow_only_generated_output(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        output_requirement = next(
            item for item in requirements if item["identity"] == "output"
        )
        output_requirement["required_config_identities"] = [
            identity
            for identity in cast(
                list[str], output_requirement["required_config_identities"]
            )
            if identity != "boundary"
        ]

    _rewrite_fixture_policy(tmp_path, artifacts, narrow_only_generated_output)
    with pytest.raises(ReleaseEvidenceError, match="configuration closure mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_artifact_inventory_binds_metadata_and_rejects_cross_role_digest_alias(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "media_type": "text/plain"}
    )
    with pytest.raises(ReleaseEvidenceError, match="exact product inventory"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    boundary = next(item for item in artifacts if item.identity == "boundary")
    (tmp_path / "receipt.json").write_bytes(
        (tmp_path / "boundary.geojson").read_bytes()
    )
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "output_digest": boundary.output_digest}
    )
    snapshot = next(item for item in artifacts if item.identity == "snapshot")
    artifacts[artifacts.index(snapshot)] = ArtifactInput(
        **{
            **snapshot.__dict__,
            "parents": (ArtifactReference("receipt", boundary.output_digest),),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="cross-role digest alias"):
        _build(tmp_path, artifacts=artifacts)


def test_json_artifact_schema_identity_is_checked_against_content(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / "receipt.json").write_text('{"receipt":1}\n', encoding="utf-8")
    receipt_digest = _digest(b'{"receipt":1}\n')
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "output_digest": receipt_digest}
    )
    snapshot = next(item for item in artifacts if item.identity == "snapshot")
    artifacts[artifacts.index(snapshot)] = ArtifactInput(
        **{
            **snapshot.__dict__,
            "parents": (ArtifactReference("receipt", receipt_digest),),
        }
    )

    def require_receipt_schema(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        receipt = next(item for item in requirements if item["identity"] == "receipt")
        receipt["media_type"] = "application/json"
        receipt["schema_version"] = "fixture-receipt.v1"
        receipt["schema_identity_field"] = "schema_version"

    _rewrite_fixture_policy(tmp_path, artifacts, require_receipt_schema)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{
            **receipt.__dict__,
            "media_type": "application/json",
            "schema_version": "fixture-receipt.v1",
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="embedded schema identity mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_policy_change_invalidates_existing_manifest(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    path = tmp_path / "configs/release_evidence_policy.json"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["required_reconciliations"].append(
        {
            "source": "sead",
            "entity": "sites",
            "dimension": "country",
            "scope_values": {},
            "derivation_adapter": "unavailable",
            "derivation_metric": "sites",
            "unavailable_status": "unavailable",
            "unavailable_reason_code": "fixture_count_not_materialized",
        }
    )
    path.write_bytes(_canonical_json(policy) + b"\n")

    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        validate_release_evidence_manifest(tmp_path, manifest)


def test_validation_detects_file_and_manifest_tampering(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    (tmp_path / "output.json").write_text('{"records":2}\n', encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        validate_release_evidence_manifest(tmp_path, manifest)

    (tmp_path / "output.json").write_text('{"records":1}\n', encoding="utf-8")
    altered = copy.deepcopy(manifest)
    altered["code_commit"] = "2" * 40
    with pytest.raises(
        ReleaseEvidenceError, match="content or an immutable input changed"
    ):
        validate_release_evidence_manifest(tmp_path, altered)


@pytest.mark.parametrize(
    "attack",
    [
        "argv",
        "environment",
        "empty-inputs",
        "substituted-input",
        "producer",
        "root",
        "runtime",
    ],
)
def test_coherently_rehashed_gate_cannot_replace_trusted_specification(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "argv":
            record["argv"] = ["true"]
            record["command_digest"] = _json_digest(record["argv"])
        elif attack == "environment":
            record["environment"] = {"PATH": "/attacker"}
            record["environment_digest"] = _json_digest(record["environment"])
        elif attack == "empty-inputs":
            record["inputs"] = []
            record["input_digest"] = _json_digest([])
        elif attack == "substituted-input":
            alternate = tmp_path / "alternate-input.txt"
            alternate.write_text("attacker input\n", encoding="utf-8")
            inputs = [
                {
                    "path": "alternate-input.txt",
                    **hash_repository_object(tmp_path, "alternate-input.txt"),
                }
            ]
            record["inputs"] = inputs
            record["input_digest"] = _json_digest(inputs)
        elif attack == "producer":
            producer = {"identity": "attacker", "version": "1"}
            record["producer"] = {**producer, "digest": _json_digest(producer)}
        elif attack == "root":
            record["repository_root_digest"] = _json_digest("/relocated")
        else:
            record["specification_digest"] = _json_digest(
                {"runtime_identity": {"command_executable_sha256": _digest(b"fake")}}
            )

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError):
        _build(tmp_path, artifacts=artifacts)


def test_coherently_rehashed_producer_source_substitution_is_refused(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        source_files = [
            {
                "module": "bijux_pollenomics.provenance.gates",
                "sha256": _digest(b"substituted producer"),
                "byte_count": len(b"substituted producer"),
            }
        ]
        producer_content = {
            "identity": "bijux-pollenomics.recorded-gate",
            "version": "4",
            "source_files": source_files,
            "source_digest": _json_digest(source_files),
        }
        record["producer"] = {
            **producer_content,
            "digest": _json_digest(producer_content),
        }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="producer identity mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_coherent_local_pass_is_diagnostic_but_never_release_ready(
    tmp_path: Path,
) -> None:
    manifest = _build(tmp_path)

    assert manifest["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "required_gate_not_independently_attested:quality",
        ],
    }


@pytest.mark.parametrize(
    ("target_identity", "attack", "expected_message"),
    [
        ("output", "reparent", "parent inventory mismatch"),
        ("output", "remove", "parent inventory mismatch"),
        ("output", "add", "parent inventory mismatch"),
        ("output", "stale", "parent digest mismatch"),
        ("validation", "unrelated-gate-ancestry", "parent inventory mismatch"),
    ],
)
def test_exact_parent_inventory_refuses_coherent_ancestry_attacks(
    tmp_path: Path, target_identity: str, attack: str, expected_message: str
) -> None:
    artifacts = _artifacts(tmp_path)
    target = next(item for item in artifacts if item.identity == target_identity)
    by_identity = {item.identity: item for item in artifacts}
    parents: tuple[ArtifactReference, ...]
    if attack == "reparent":
        parents = (ArtifactReference("receipt", by_identity["receipt"].output_digest),)
    elif attack == "remove":
        parents = ()
    elif attack == "add":
        parents = (
            *target.parents,
            ArtifactReference("receipt", by_identity["receipt"].output_digest),
        )
    elif attack == "stale":
        parents = (ArtifactReference("snapshot", "sha256:" + "0" * 64),)
    else:
        parents = (ArtifactReference("receipt", by_identity["receipt"].output_digest),)
    artifacts[artifacts.index(target)] = ArtifactInput(
        **{**target.__dict__, "parents": parents}
    )

    with pytest.raises(ReleaseEvidenceError, match=expected_message):
        _build(tmp_path, artifacts=artifacts)
