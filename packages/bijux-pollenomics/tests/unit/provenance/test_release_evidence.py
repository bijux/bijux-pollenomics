from __future__ import annotations

from collections.abc import Callable
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT
import shutil
import subprocess
from typing import Literal, cast

import pytest

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    Blocker,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
    build_release_evidence_manifest,
    hash_repository_object,
    validate_recorded_gate,
    validate_release_evidence_manifest,
)
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance import release_evidence as release_evidence_module
from bijux_pollenomics.provenance.gates import RecordedGateSpecification

COMMIT = "1" * 40


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def test_producer_tree_digest_excludes_python_runtime_cache(tmp_path: Path) -> None:
    producer = tmp_path / "producer"
    producer.mkdir()
    (producer / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    cache = producer / "__pycache__"
    cache.mkdir()
    cached_bytecode = cache / "source.cpython-311.pyc"
    cached_bytecode.write_bytes(b"first runtime cache")
    optimized_bytecode = cache / "source.cpython-311.pyo"
    optimized_bytecode.write_bytes(b"first optimized runtime cache")
    nested_source = cache / "real_source.py"
    nested_source.write_text("CACHE_HELPER = 1\n", encoding="utf-8")
    suffix_directory = producer / "owned.pyc"
    suffix_directory.mkdir()
    suffix_source = suffix_directory / "real_source.py"
    suffix_source.write_text("SUFFIX_HELPER = 1\n", encoding="utf-8")
    digest = cast(
        str,
        release_evidence_module._hash_repository_object(
            tmp_path,
            "producer",
            exclude_python_cache=True,
        )["output_digest"],
    )
    artifact = ArtifactInput(
        identity="producer",
        role="producer",
        path="producer",
        media_type="text/x-python",
        schema_version="producer.v1",
        parents=(),
        config_digests=(),
        producer_digest=digest,
        output_digest=digest,
    )

    before = release_evidence_module._artifact_record(tmp_path, artifact)
    generic_before = hash_repository_object(tmp_path, "producer")
    cached_bytecode.write_bytes(b"different runtime cache")
    optimized_bytecode.write_bytes(b"different optimized runtime cache")
    after = release_evidence_module._artifact_record(tmp_path, artifact)

    assert before == after
    assert hash_repository_object(tmp_path, "producer") != generic_before
    nested_source.write_text("CACHE_HELPER = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_evidence_module._artifact_record(tmp_path, artifact)
    nested_source.write_text("CACHE_HELPER = 1\n", encoding="utf-8")
    suffix_source.write_text("SUFFIX_HELPER = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_evidence_module._artifact_record(tmp_path, artifact)
    suffix_source.write_text("SUFFIX_HELPER = 1\n", encoding="utf-8")
    (producer / "source.py").write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_evidence_module._artifact_record(tmp_path, artifact)


def test_producer_tree_cache_exclusion_does_not_hide_symlink(
    tmp_path: Path,
) -> None:
    producer = tmp_path / "producer"
    producer.mkdir()
    (producer / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    (producer / "linked.pyc").symlink_to(producer / "source.py")

    with pytest.raises(ReleaseEvidenceError, match="safely open"):
        release_evidence_module._hash_repository_object(
            tmp_path,
            "producer",
            exclude_python_cache=True,
        )


def _json_digest(value: object) -> str:
    return _digest(_canonical_json(value))


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
    loaded_policy = release_evidence_module._load_release_evidence_policy(
        repository_root
    )
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
    release_evidence_module._validate_embedded_producer_identities(
        repository_root, product_artifacts, loaded_policy
    )
    release_evidence_module._validate_manifest_bundle_closures(
        repository_root, product_artifacts, loaded_policy
    )
    release_evidence_module._validate_propagation_contract_binding(
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


def _write_fixture_policy(
    root: Path,
    *,
    gate_ids: tuple[str, ...] = ("quality",),
    secondary_producer: bool = False,
    output_uses_secondary: bool = True,
) -> bytes:
    producer_paths = ["producer.py"]
    ownership = [
        ("source_receipt", "receipt.json", "producer.py"),
        ("source_snapshot", "snapshot", "producer.py"),
        ("configuration", "config.json", "producer.py"),
        (
            "configuration",
            "configs/release_evidence_policy.json",
            "producer.py",
        ),
        ("classification", "classification.csv", "producer.py"),
        ("scenario", "scenario.json", "producer.py"),
        ("boundary", "boundary.geojson", "producer.py"),
        ("producer", "producer.py", "producer.py"),
        ("dependency_lock", "uv.lock", "producer.py"),
        ("generated_output", "output.json", "producer.py"),
        (
            "validation_result",
            "artifacts/gate-evidence",
            "producer.py",
        ),
    ]
    if secondary_producer:
        producer_paths.append("secondary-producer.py")
        ownership.append(("producer", "secondary-producer.py", "secondary-producer.py"))
        if output_uses_secondary:
            ownership = [
                (
                    role,
                    prefix,
                    "secondary-producer.py" if prefix == "output.json" else producer,
                )
                for role, prefix, producer in ownership
            ]
    artifact_inventory = [
        ("boundary", "boundary", "boundary.geojson"),
        ("classification", "classification", "classification.csv"),
        ("config", "configuration", "config.json"),
        ("lock", "dependency_lock", "uv.lock"),
        ("output", "generated_output", "output.json"),
        ("producer", "producer", "producer.py"),
        (
            "release-evidence-policy",
            "configuration",
            "configs/release_evidence_policy.json",
        ),
        ("receipt", "source_receipt", "receipt.json"),
        ("scenario", "scenario", "scenario.json"),
        ("snapshot", "source_snapshot", "snapshot"),
    ]
    if secondary_producer:
        artifact_inventory.append(
            ("secondary-producer", "producer", "secondary-producer.py")
        )
    for index, gate_id in enumerate(gate_ids):
        artifact_inventory.append(
            (
                "validation" if index == 0 else f"{gate_id}-validation",
                "validation_result",
                f"artifacts/gate-evidence/{gate_id}.json",
            )
        )
    config_identities = [
        "boundary",
        "classification",
        "config",
        "lock",
        "release-evidence-policy",
        "scenario",
    ]
    policy = {
        "schema_version": "release-evidence-policy.v3",
        "mode": "fixture",
        "recording_authority_path": "producer.py",
        "authorized_producer_paths": sorted(producer_paths),
        "artifact_ownership": [
            {
                "artifact_role": role,
                "artifact_path_prefix": prefix,
                "producer_path": producer,
            }
            for role, prefix, producer in sorted(
                ownership, key=lambda item: (item[1], item[0])
            )
        ],
        "required_artifacts": [
            {
                "identity": identity,
                "role": role,
                "path": path,
                "media_type": "application/octet-stream",
                "schema_version": (
                    "recorded-gate.v4" if role == "validation_result" else "fixture.v1"
                ),
                "schema_identity_field": None,
                "producer_path": (
                    "secondary-producer.py"
                    if secondary_producer
                    and (
                        identity == "secondary-producer"
                        or (output_uses_secondary and identity == "output")
                    )
                    else "producer.py"
                ),
                "required_config_identities": (
                    config_identities
                    if role in {"generated_output", "validation_result"}
                    else []
                ),
                "required_parent_identities": (
                    ["receipt"]
                    if identity == "snapshot"
                    else ["snapshot"]
                    if identity == "output"
                    else ["output"]
                    if role == "validation_result"
                    else []
                ),
                "required_embedded_input_paths": [],
            }
            for identity, role, path in sorted(artifact_inventory)
        ],
        "embedded_producer_identities": [],
        "bundle_inventories": [],
        "allowed_cross_role_digest_aliases": [],
        "required_gate_ids": sorted(gate_ids),
        "governed_request_artifact_ids": ["receipt"],
        "propagation_contract": {
            "contract_id": "fixture.propagation",
            "contract_version": "1",
            "sha256": "sha256:" + "0" * 64,
            "default_scenario": {
                "scenario_id": "fixture",
                "maximum_distance_km": 1.0,
                "maximum_lag_years": 1.0,
            },
        },
        "required_reconciliations": [
            {
                "source": "neotoma",
                "entity": "samples",
                "dimension": "country",
                "scope_values": {},
                "derivation_adapter": "unavailable",
                "derivation_metric": "samples",
                "unavailable_status": "unavailable",
                "unavailable_reason_code": "fixture_count_not_materialized",
            }
        ],
    }
    payload = _canonical_json(policy) + b"\n"
    path = root / "configs/release_evidence_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def _write_gate_record(
    root: Path,
    *,
    path: str | None = None,
    gate_id: str = "quality",
    status: str = "PASS",
) -> str:
    path = path or f"artifacts/gate-evidence/{gate_id}.json"
    gate_input = root / "gate-input.txt"
    gate_input.write_text("current gate input\n", encoding="utf-8")
    evidence_directory = root / "artifacts/gate-evidence"
    evidence_directory.mkdir(parents=True, exist_ok=True)
    stdout_path = evidence_directory / f"{gate_id}.stdout.log"
    stderr_path = evidence_directory / f"{gate_id}.stderr.log"
    junit_path = evidence_directory / f"{gate_id}.junit.xml"
    stdout_path.write_text("passed\n", encoding="utf-8")
    stderr_path.write_bytes(b"")
    junit_path.write_text('<testsuite failures="0"/>\n', encoding="utf-8")

    def repository_record(relative: str) -> dict[str, object]:
        return {"path": relative, **hash_repository_object(root, relative)}

    inputs = [repository_record("gate-input.txt")]
    if status == "PASS":
        exit_code: int | None = 0
        reason_code = "command_passed"
    elif status == "FAIL":
        exit_code = 1
        reason_code = "command_failed"
    else:
        exit_code = None
        reason_code = status.lower()
    specification = _fixture_specification(root, gate_id)
    specification_record = specification.as_record(root)
    content: dict[str, object] = {
        "schema_version": "recorded-gate.v4",
        "producer": specification_record["producer"],
        "attestation": specification_record["attestation"],
        "repository_root_digest": specification_record["repository_root_digest"],
        "gate_id": gate_id,
        "required": specification.required,
        "argv": ["pytest", "-q"],
        "command_digest": _json_digest(["pytest", "-q"]),
        "environment_digest": _json_digest({}),
        "environment": {},
        "inputs": inputs,
        "input_digest": _json_digest(inputs),
        "artifacts_directory": specification.artifacts_directory,
        "specification_digest": _json_digest(specification_record),
        "timeout_seconds": specification.timeout_seconds,
        "duration_monotonic_ns": 1,
        "exit_code": exit_code,
        "status": status,
        "reason_code": reason_code,
        "stdout": repository_record(f"artifacts/gate-evidence/{gate_id}.stdout.log"),
        "stderr": repository_record(f"artifacts/gate-evidence/{gate_id}.stderr.log"),
        "junit": repository_record(f"artifacts/gate-evidence/{gate_id}.junit.xml"),
    }
    record = {"record_digest": _json_digest(content), **content}
    payload = _canonical_json(record) + b"\n"
    output = root / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    return _digest(payload)


def _fixture_specification(root: Path, gate_id: str) -> RecordedGateSpecification:
    return RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=("pytest", "-q"),
        environment=(),
        input_paths=("gate-input.txt",),
        artifacts_directory="artifacts/gate-evidence",
        junit_path=f"artifacts/gate-evidence/{gate_id}.junit.xml",
    )


@pytest.fixture(autouse=True)
def _trusted_fixture_gate_specification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate_module,
        "build_product_gate_specification",
        _fixture_specification,
    )


def _artifacts(
    root: Path,
    *,
    gate_id: str = "quality",
    gate_status: str = "PASS",
    gate_ids: tuple[str, ...] | None = None,
    secondary_producer: bool = False,
    output_uses_secondary: bool = True,
) -> list[ArtifactInput]:
    gate_ids = gate_ids or (gate_id,)
    policy_payload = _write_fixture_policy(
        root,
        gate_ids=gate_ids,
        secondary_producer=secondary_producer,
        output_uses_secondary=output_uses_secondary,
    )
    content = {
        "receipt.json": b"receipt\n",
        "snapshot/data.csv": b"record_id,value\n1,2\n",
        "config.json": b"{}\n",
        "classification.csv": b"source,concept\na,b\n",
        "scenario.json": b'{"scenario":"strict"}\n',
        "boundary.geojson": b'{"type":"FeatureCollection","features":[]}\n',
        "producer.py": b"def build(): return 1\n",
        "uv.lock": b"version = 1\n",
        "output.json": b'{"records":1}\n',
        "configs/release_evidence_policy.json": policy_payload,
    }
    if secondary_producer:
        content["secondary-producer.py"] = b"def render(): return 2\n"
    for relative, value in content.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    digests = {relative: _digest(value) for relative, value in content.items()}
    validation_paths = []
    for current_gate_id in gate_ids:
        validation_path = f"artifacts/gate-evidence/{current_gate_id}.json"
        validation_paths.append(validation_path)
        digests[validation_path] = _write_gate_record(
            root,
            path=validation_path,
            gate_id=current_gate_id,
            status=gate_status,
        )
    producer = digests["producer.py"]
    configs = tuple(
        digests[name]
        for name in (
            "config.json",
            "classification.csv",
            "scenario.json",
            "boundary.geojson",
            "uv.lock",
            "configs/release_evidence_policy.json",
        )
    )
    snapshot_digest = _json_digest(
        [
            {
                "path": "data.csv",
                "output_digest": digests["snapshot/data.csv"],
                "byte_size": len(content["snapshot/data.csv"]),
            }
        ]
    )
    receipt_ref = ArtifactReference("receipt", digests["receipt.json"])
    snapshot_ref = ArtifactReference("snapshot", snapshot_digest)
    output_ref = ArtifactReference("output", digests["output.json"])
    specs = [
        ("receipt", "source_receipt", "receipt.json", ()),
        ("snapshot", "source_snapshot", "snapshot", (receipt_ref,)),
        ("config", "configuration", "config.json", ()),
        (
            "release-evidence-policy",
            "configuration",
            "configs/release_evidence_policy.json",
            (),
        ),
        ("classification", "classification", "classification.csv", ()),
        ("scenario", "scenario", "scenario.json", ()),
        ("boundary", "boundary", "boundary.geojson", ()),
        ("producer", "producer", "producer.py", ()),
        ("lock", "dependency_lock", "uv.lock", ()),
        ("output", "generated_output", "output.json", (snapshot_ref,)),
    ]
    for index, validation_path in enumerate(validation_paths):
        current_gate_id = gate_ids[index]
        specs.append(
            (
                "validation" if index == 0 else f"{current_gate_id}-validation",
                "validation_result",
                validation_path,
                (output_ref,),
            )
        )
    if secondary_producer:
        specs.insert(
            -2,
            (
                "secondary-producer",
                "producer",
                "secondary-producer.py",
                (),
            ),
        )
    artifacts = []
    for identity, role, relative, parents in specs:
        output_digest = snapshot_digest if relative == "snapshot" else digests[relative]
        artifacts.append(
            ArtifactInput(
                identity=identity,
                role=role,  # type: ignore[arg-type]
                path=relative,
                media_type="application/octet-stream",
                schema_version=(
                    "recorded-gate.v4" if role == "validation_result" else "fixture.v1"
                ),
                parents=parents,
                config_digests=configs
                if role in {"generated_output", "validation_result"}
                else (),
                producer_digest=(
                    digests["secondary-producer.py"]
                    if secondary_producer
                    and output_uses_secondary
                    and identity == "output"
                    else output_digest
                    if role == "producer"
                    else producer
                ),
                output_digest=output_digest,
            )
        )
    return artifacts


def _reconciliations() -> list[CountReconciliation]:
    counts = {
        "SE": (4, 3, 2, 1, 0, 1),
        "DK": (2, 2, 2, 0, 0, 0),
        "NO": (1, 0, 0, 1, 0, 0),
        "FI": (0, 0, 0, 0, 0, 0),
        "UNASSIGNED": (1, 0, 0, 0, 1, 0),
        "OUTSIDE": (0, 0, 0, 0, 0, 0),
    }
    rows = [
        CountReconciliation(
            identity="neotoma.samples.source",
            dimension="source",
            source="neotoma",
            entity="samples",
            country_code=None,
            candidate_count=8,
            eligible_count=5,
            accepted_count=4,
            unresolved_count=2,
            excluded_count=1,
            refused_count=1,
        )
    ]
    for country, values in counts.items():
        rows.append(
            CountReconciliation(
                identity=f"neotoma.samples.{country.lower()}",
                dimension="country",
                source="neotoma",
                entity="samples",
                country_code=country,
                candidate_count=values[0],
                eligible_count=values[1],
                accepted_count=values[2],
                unresolved_count=values[3],
                excluded_count=values[4],
                refused_count=values[5],
            )
        )
    return rows


def _refresh_validation_artifact(root: Path, artifacts: list[ArtifactInput]) -> None:
    validation = next(item for item in artifacts if item.identity == "validation")
    artifacts[artifacts.index(validation)] = ArtifactInput(
        **{
            **validation.__dict__,
            "output_digest": cast(
                str,
                hash_repository_object(root, validation.path)["output_digest"],
            ),
        }
    )


def _rewrite_gate_record(
    root: Path,
    artifacts: list[ArtifactInput],
    transform: Callable[[dict[str, object]], None],
) -> None:
    path = root / "artifacts/gate-evidence/quality.json"
    record = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    transform(record)
    content = {key: value for key, value in record.items() if key != "record_digest"}
    record["record_digest"] = _json_digest(content)
    path.write_bytes(_canonical_json(record) + b"\n")
    _refresh_validation_artifact(root, artifacts)


def _rewrite_fixture_policy(
    root: Path,
    artifacts: list[ArtifactInput],
    transform: Callable[[dict[str, object]], None],
) -> None:
    path = root / "configs/release_evidence_policy.json"
    policy = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    old_digest = _digest(path.read_bytes())
    transform(policy)
    path.write_bytes(_canonical_json(policy) + b"\n")
    new_digest = _digest(path.read_bytes())
    for index, artifact in enumerate(artifacts):
        updates: dict[str, object] = {}
        if artifact.identity == "release-evidence-policy":
            updates["output_digest"] = new_digest
        if artifact.role in {"generated_output", "validation_result"}:
            updates["config_digests"] = tuple(
                new_digest if digest == old_digest else digest
                for digest in artifact.config_digests
            )
        if updates:
            artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})


def _build(
    root: Path,
    *,
    artifacts: list[ArtifactInput] | None = None,
    gates: list[GateResult] | None = None,
    reconciliations: list[CountReconciliation] | None = None,
    blockers: list[Blocker] | None = None,
) -> dict[str, object]:
    artifacts = artifacts or _artifacts(root)
    by_identity = {artifact.identity: artifact for artifact in artifacts}
    gates = gates or [
        GateResult(
            identity="quality",
            status="PASS",
            required=True,
            evidence_digest=by_identity["validation"].output_digest,
        )
    ]
    return build_release_evidence_manifest(
        root,
        code_commit=COMMIT,
        dirty=False,
        dependency_lock_digest=by_identity["lock"].output_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations or _reconciliations(),
        blockers=blockers or (),
    )


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


def _fixture_bundle_payloads(
    root: Path, directory: str, filenames: tuple[str, ...]
) -> str:
    entries: list[dict[str, object]] = []
    bundle_root = root / directory
    bundle_root.mkdir()
    for filename in filenames:
        payload = _canonical_json({"record_count": 1, "records": [filename]}) + b"\n"
        (bundle_root / filename).write_bytes(payload)
        entries.append(
            {
                "path": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "record_count": 1,
            }
        )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    manifest_payload = (
        _canonical_json(
            {
                "schema_version": "fixture-bundle-manifest.v1",
                "payload_file_count": len(entries),
                "bundle_digest": hashlib.sha256(digest_input).hexdigest(),
                "files": entries,
            }
        )
        + b"\n"
    )
    (bundle_root / "manifest.json").write_bytes(manifest_payload)
    return _digest(manifest_payload)


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
    policy = release_evidence_module._load_release_evidence_policy(tmp_path)
    policy = replace(
        policy,
        bundle_inventories=(
            release_evidence_module._BundleInventory(
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
        release_evidence_module._validate_manifest_bundle_closures(
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


def test_fixture_policy_is_refused_inside_a_git_worktree(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / ".git").mkdir()

    with pytest.raises(
        ReleaseEvidenceError, match="fixture release policy is forbidden"
    ):
        _build(tmp_path, artifacts=artifacts)


def test_product_repository_state_binds_git_and_untracked_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    untracked = tmp_path / "untracked.txt"
    untracked.write_text("untracked bytes\n", encoding="utf-8")
    commit = "a" * 40
    tree = "b" * 40
    responses = {
        ("rev-parse", "--show-toplevel"): f"{tmp_path}\n".encode(),
        ("rev-parse", "HEAD"): f"{commit}\n".encode(),
        ("rev-parse", "HEAD^{tree}"): f"{tree}\n".encode(),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"): (
            b"?? untracked.txt\0"
        ),
        ("ls-files", "-z"): b"tracked.txt\0",
        ("diff", "--binary", "HEAD", "--"): b"tracked diff\n",
        ("ls-files", "--others", "--exclude-standard", "-z"): (b"untracked.txt\0"),
    }
    calls: list[tuple[str, ...]] = []

    def fake_run(
        argv: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        assert argv[:3] == ("git", "-C", str(tmp_path))
        arguments = argv[3:]
        calls.append(arguments)
        return subprocess.CompletedProcess(argv, 0, responses[arguments], b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    state = release_evidence_module._repository_state(tmp_path, "product")

    assert state["head_commit"] == commit
    assert state["head_tree"] == tree
    assert state["dirty"] is True
    assert state["untracked_objects"] == [
        {"path": "untracked.txt", **hash_repository_object(tmp_path, "untracked.txt")}
    ]
    assert calls == list(responses)


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


def test_tree_hash_is_stable_and_accounts_for_members(tmp_path: Path) -> None:
    _artifacts(tmp_path)

    observed = hash_repository_object(tmp_path, "snapshot")

    assert observed["object_type"] == "tree"
    assert observed["file_count"] == 1
    assert observed["byte_size"] == len(b"record_id,value\n1,2\n")


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


def test_recorded_gate_validator_binds_identity_status_and_required_policy(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    validation = next(item for item in artifacts if item.identity == "validation")
    expected = GateResult("quality", "PASS", True, validation.output_digest)

    record = validate_recorded_gate(tmp_path, validation.path, expected_gate=expected)

    assert record["gate_id"] == "quality"
    assert record["status"] == "PASS"
    with pytest.raises(ReleaseEvidenceError, match="gate inventory"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[GateResult("other", "PASS", True, validation.output_digest)],
        )
    with pytest.raises(ReleaseEvidenceError, match="status mismatch"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[GateResult("quality", "FAIL", True, validation.output_digest)],
        )
    with pytest.raises(ReleaseEvidenceError, match="required flag"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[
                GateResult(
                    "quality",
                    "PASS",
                    cast(bool, 1),
                    validation.output_digest,
                )
            ],
        )
    with pytest.raises(ReleaseEvidenceError, match="required policy mismatch"):
        validate_recorded_gate(
            tmp_path,
            validation.path,
            expected_gate=GateResult(
                "quality", "PASS", False, validation.output_digest
            ),
        )


def test_recorded_gate_rejects_stale_declared_input(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / "gate-input.txt").write_text("changed input\n", encoding="utf-8")

    with pytest.raises(ReleaseEvidenceError, match="input changed"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_rejects_internal_record_digest_tamper(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    path = tmp_path / "artifacts/gate-evidence/quality.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["duration_monotonic_ns"] = 2
    path.write_bytes(_canonical_json(record) + b"\n")
    _refresh_validation_artifact(tmp_path, artifacts)

    with pytest.raises(ReleaseEvidenceError, match="record_digest mismatch"):
        _build(tmp_path, artifacts=artifacts)


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


def test_recorded_gate_producer_is_bound_to_executing_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate_module, "_read_executing_source_bytes", lambda: b"A")
    artifacts = _artifacts(tmp_path)
    monkeypatch.setattr(gate_module, "_read_executing_source_bytes", lambda: b"B")

    with pytest.raises(ReleaseEvidenceError, match="producer identity mismatch"):
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


@pytest.mark.parametrize("attack", ["independent", "missing", "legacy-v2", "legacy-v3"])
def test_local_gate_attestation_is_required_and_cannot_be_upgraded_or_grandfathered(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "independent":
            record["attestation"] = {
                "class": "independent_execution_attestation",
                "independent_execution_attested": True,
                "external_authority_id": "attacker",
            }
        elif attack == "missing":
            del record["attestation"]
        else:
            record["schema_version"] = attack.replace("legacy-", "recorded-gate.")

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="attestation|schema|fields"):
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


def test_nonlocal_gate_is_refused_without_product_owned_trust_configuration(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    gate = GateResult(
        "quality",
        "PASS",
        True,
        artifacts[-1].output_digest,
        attestation="independent_execution_attestation",
        authority_id="unconfigured-verifier",
    )

    with pytest.raises(
        ReleaseEvidenceError, match="non-local gate attestation trust is not configured"
    ):
        _build(tmp_path, artifacts=artifacts, gates=[gate])


@pytest.mark.parametrize("attack", ["aliased-logs", "arbitrary-log", "aliased-junit"])
def test_gate_artifact_roles_cannot_alias_or_select_arbitrary_paths(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "aliased-logs":
            record["stdout"] = record["stderr"]
        elif attack == "aliased-junit":
            record["junit"] = record["stdout"]
        else:
            arbitrary = tmp_path / "arbitrary.log"
            arbitrary.write_text("arbitrary\n", encoding="utf-8")
            record["stdout"] = {
                "path": "arbitrary.log",
                **hash_repository_object(tmp_path, "arbitrary.log"),
            }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="role|alias"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    "junit_payload",
    [
        '<testsuite failures="1"/>\n',
        '<testsuite errors="1"/>\n',
        '<testsuite skipped="1"/>\n',
        "<testsuite><testcase><failure/></testcase></testsuite>\n",
    ],
)
def test_coherently_rehashed_pass_record_requires_passing_junit(
    tmp_path: Path, junit_payload: str
) -> None:
    artifacts = _artifacts(tmp_path)
    junit_path = tmp_path / "artifacts/gate-evidence/quality.junit.xml"
    junit_path.write_text(junit_payload, encoding="utf-8")

    def mutate(record: dict[str, object]) -> None:
        record["junit"] = {
            "path": "artifacts/gate-evidence/quality.junit.xml",
            **hash_repository_object(
                tmp_path, "artifacts/gate-evidence/quality.junit.xml"
            ),
        }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="nonpassing JUnit"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_is_bound_to_repository_root(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    validation = next(item for item in artifacts if item.identity == "validation")
    relocated = tmp_path.parent / f"{tmp_path.name}-relocated"
    shutil.copytree(tmp_path, relocated)

    with pytest.raises(ReleaseEvidenceError, match="repository root mismatch"):
        validate_recorded_gate(relocated, validation.path)


def test_recorded_gate_timeout_is_bound_to_product_policy(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        record["timeout_seconds"] = 1.0

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="timeout differs"):
        _build(tmp_path, artifacts=artifacts)


def test_descriptor_relative_hashing_resists_parent_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    governed = tmp_path / "governed"
    governed.mkdir()
    (governed / "input.txt").write_text("governed\n", encoding="utf-8")
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    (attacker / "input.txt").write_text("attacker\n", encoding="utf-8")
    original_open = os.open
    substituted = False

    def swapping_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal substituted
        if path == "input.txt" and dir_fd is not None and not substituted:
            governed.rename(tmp_path / "governed-original")
            governed.symlink_to(attacker, target_is_directory=True)
            substituted = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swapping_open)

    observed = hash_repository_object(tmp_path, "governed/input.txt")

    assert substituted is True
    assert observed["output_digest"] == _digest(b"governed\n")


@pytest.mark.parametrize(
    "relative_path, expected_message",
    [
        ("artifacts/gate-evidence/quality.stdout.log", "stdout changed"),
        ("artifacts/gate-evidence/quality.stderr.log", "stderr changed"),
        ("artifacts/gate-evidence/quality.junit.xml", "JUnit changed"),
    ],
)
def test_recorded_gate_rejects_tampered_result_artifact(
    tmp_path: Path, relative_path: str, expected_message: str
) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / relative_path).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ReleaseEvidenceError, match=expected_message):
        _build(tmp_path, artifacts=artifacts)


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


def test_null_counts_are_rejected_while_zero_is_valid(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    rows = cast(list[dict[str, object]], manifest["reconciliations"])
    zero_row = next(row for row in rows if row["country_code"] == "FI")
    assert zero_row["candidate_count"] == 0

    reconciliations = _reconciliations()
    fi = next(item for item in reconciliations if item.country_code == "FI")
    reconciliations[reconciliations.index(fi)] = CountReconciliation(
        **{**fi.__dict__, "candidate_count": None}
    )
    with pytest.raises(ReleaseEvidenceError, match="non-null"):
        _build(tmp_path, reconciliations=reconciliations)


def test_country_totals_must_reconcile_to_source_without_omission(
    tmp_path: Path,
) -> None:
    missing_unassigned = [
        item for item in _reconciliations() if item.country_code != "UNASSIGNED"
    ]
    with pytest.raises(ReleaseEvidenceError, match="complete country reconciliation"):
        _build(tmp_path, reconciliations=missing_unassigned)

    reconciliations = _reconciliations()
    se = next(item for item in reconciliations if item.country_code == "SE")
    reconciliations[reconciliations.index(se)] = CountReconciliation(
        **{**se.__dict__, "candidate_count": 5, "excluded_count": 1}
    )
    with pytest.raises(ReleaseEvidenceError, match="country/source count mismatch"):
        _build(tmp_path, reconciliations=reconciliations)

    missing_outside = [
        item for item in _reconciliations() if item.country_code != "OUTSIDE"
    ]
    with pytest.raises(ReleaseEvidenceError, match="complete country reconciliation"):
        _build(tmp_path, reconciliations=missing_outside)


def test_caller_cannot_omit_a_policy_required_source_entity_group(
    tmp_path: Path,
) -> None:
    other_group = [
        CountReconciliation(
            **{
                **item.__dict__,
                "identity": item.identity.replace("neotoma", "sead"),
                "source": "sead",
            }
        )
        for item in _reconciliations()
    ]

    with pytest.raises(
        ReleaseEvidenceError, match="missing required reconciliation groups"
    ):
        _build(tmp_path, reconciliations=other_group)


def test_unavailable_counts_remain_null_and_reason_coded(tmp_path: Path) -> None:
    unavailable = [
        CountReconciliation(
            **{
                **item.__dict__,
                "candidate_count": None,
                "eligible_count": None,
                "accepted_count": None,
                "unresolved_count": None,
                "excluded_count": None,
                "refused_count": None,
                "count_status": "unavailable",
                "reason_codes": ("source_dimension_unavailable",),
            }
        )
        for item in _reconciliations()
    ]

    manifest = _build(tmp_path, reconciliations=unavailable)

    rows = cast(list[dict[str, object]], manifest["reconciliations"])
    assert all(row["candidate_count"] is None for row in rows)
    assert all(row["count_status"] == "unavailable" for row in rows)


def test_reconciliation_rejects_unexpected_groups_and_mixed_availability(
    tmp_path: Path,
) -> None:
    unexpected = [
        CountReconciliation(
            **{
                **item.__dict__,
                "identity": item.identity.replace("neotoma", "sead"),
                "source": "sead",
            }
        )
        for item in _reconciliations()
    ]
    with pytest.raises(ReleaseEvidenceError, match="unexpected reconciliation groups"):
        _build(tmp_path, reconciliations=[*_reconciliations(), *unexpected])

    unavailable = [
        CountReconciliation(
            **{
                **item.__dict__,
                "candidate_count": None,
                "eligible_count": None,
                "accepted_count": None,
                "unresolved_count": None,
                "excluded_count": None,
                "refused_count": None,
                "count_status": "unavailable",
                "reason_codes": ("source_dimension_unavailable",),
            }
        )
        for item in _reconciliations()
    ]
    country_row = unavailable[1]
    unavailable[1] = CountReconciliation(
        **{
            **country_row.__dict__,
            "count_status": "refused",
            "reason_codes": ("source_dimension_refused",),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="availability statuses differ"):
        _build(tmp_path, reconciliations=unavailable)


def test_policy_owned_scope_cross_product_cannot_be_omitted(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)

    def require_statuses(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_reconciliations"])
        requirements[0]["dimension"] = "scope"
        requirements[0]["scope_values"] = {"status": ["accepted", "refused"]}

    _rewrite_fixture_policy(tmp_path, artifacts, require_statuses)
    rows = [
        CountReconciliation(
            identity="neotoma.samples.source",
            dimension="source",
            source="neotoma",
            entity="samples",
            country_code=None,
            candidate_count=0,
            eligible_count=0,
            accepted_count=0,
            unresolved_count=0,
            excluded_count=0,
            refused_count=0,
        ),
        CountReconciliation(
            identity="neotoma.samples.accepted",
            dimension="scope",
            source="neotoma",
            entity="samples",
            country_code=None,
            scope=(("status", "accepted"),),
            candidate_count=0,
            eligible_count=0,
            accepted_count=0,
            unresolved_count=0,
            excluded_count=0,
            refused_count=0,
        ),
    ]

    with pytest.raises(
        ReleaseEvidenceError, match="scope partition inventory mismatch"
    ):
        _build(tmp_path, artifacts=artifacts, reconciliations=rows)


def test_paths_cannot_escape_or_traverse_symlinks(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    escaped = ArtifactInput(**{**receipt.__dict__, "path": "../receipt.json"})
    artifacts[artifacts.index(receipt)] = escaped
    with pytest.raises(ReleaseEvidenceError, match="escapes repository"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    outside = tmp_path.parent / "outside-release-evidence.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "linked-receipt.json"
    link.symlink_to(outside)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{
            **receipt.__dict__,
            "path": "linked-receipt.json",
            "output_digest": _digest(b"outside\n"),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="unsafe"):
        _build(tmp_path, artifacts=artifacts)


def test_failed_required_gate_never_claims_release_ready(tmp_path: Path) -> None:
    status = "FAIL"
    artifacts = _artifacts(tmp_path, gate_status=status)
    manifest = _build(
        tmp_path,
        artifacts=artifacts,
        gates=[
            GateResult(
                "quality",
                status,  # type: ignore[arg-type]
                True,
                artifacts[-1].output_digest,
            )
        ],
    )

    decision = manifest["release_decision"]
    assert isinstance(decision, dict)
    assert decision["release_ready"] is False
    assert decision["status"] != "verified_complete"


@pytest.mark.parametrize("status", ["SKIPPED", "BLOCKED_EXTERNAL", "NOT_APPLICABLE"])
def test_recorded_gate_refuses_statuses_the_producer_cannot_emit(
    tmp_path: Path, status: str
) -> None:
    artifacts = _artifacts(tmp_path, gate_status=status)
    with pytest.raises(ReleaseEvidenceError, match="invalid recorded gate status"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[
                GateResult(
                    "quality",
                    status,  # type: ignore[arg-type]
                    True,
                    artifacts[-1].output_digest,
                )
            ],
        )


def test_blockers_and_dirty_state_refuse_release_ready_claim(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    manifest = _build(
        tmp_path,
        artifacts=artifacts,
        blockers=[
            Blocker(
                "rights-review",
                "source_rights_unverified",
                artifacts[0].output_digest,
                kind="unverified",
                required_scope="public redistribution rights",
                owner="data-governance",
                first_observed_at="2026-09-04T00:00:00Z",
                last_observed_at="2026-09-05T00:00:00Z",
                request_status="governed",
                request_artifact_identity=artifacts[0].identity,
                request_fingerprint=artifacts[0].output_digest,
                response_class="human_review_pending",
                observations=("licence decision absent",),
                attempts=("review packet prepared",),
                impact="public release remains unavailable",
                expected_artifact="signed rights decision",
                impacted_gates=("quality",),
                next_action="obtain qualified rights decision",
                recheck_condition="signed decision is attached",
            )
        ],
    )
    assert manifest["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "blocker:source_rights_unverified",
            "required_gate_not_independently_attested:quality",
        ],
    }

    dirty = build_release_evidence_manifest(
        tmp_path,
        code_commit=COMMIT,
        dirty=True,
        dependency_lock_digest=next(
            item.output_digest for item in artifacts if item.identity == "lock"
        ),
        artifacts=artifacts,
        gates=[GateResult("quality", "PASS", True, artifacts[-1].output_digest)],
        reconciliations=_reconciliations(),
    )
    assert dirty["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "candidate_dirty",
            "required_gate_not_independently_attested:quality",
        ],
    }


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    [("external", "external_blocked"), ("refused", "refused_invalid")],
)
def test_actionable_blocker_kind_controls_truthful_release_state(
    tmp_path: Path, kind: str, expected_status: str
) -> None:
    artifacts = _artifacts(tmp_path)
    blocker = Blocker(
        identity=f"{kind}-source",
        reason_code=f"{kind}_source_unavailable",
        evidence_digest=artifacts[0].output_digest,
        kind=cast(Literal["external", "unverified", "refused", "reduced_scope"], kind),
        required_scope="governed source capture",
        owner="source-acquisition",
        first_observed_at="2026-09-04T00:00:00Z",
        last_observed_at="2026-09-05T00:00:00Z",
        request_status="refused",
        response_class="source_response",
        observations=("source response recorded",),
        attempts=("one bounded acquisition attempt",),
        impact="affected source cannot be released",
        expected_artifact="immutable source receipt",
        impacted_gates=("quality",),
        next_action="recheck source under approved authority",
        recheck_condition="source response or review decision changes",
    )

    manifest = _build(tmp_path, artifacts=artifacts, blockers=[blocker])

    assert (
        cast(dict[str, object], manifest["release_decision"])["status"]
        == expected_status
    )


def test_rejects_duplicate_paths_invalid_sha_and_output_overwrite(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "path": "receipt.json",
            "output_digest": _digest(b"receipt\n"),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="output overwrite"):
        _build(tmp_path, artifacts=artifacts)

    with pytest.raises(ReleaseEvidenceError, match="Git SHA"):
        build_release_evidence_manifest(
            tmp_path,
            code_commit="ABC",
            dirty=False,
            dependency_lock_digest="sha256:" + "0" * 64,
            artifacts=(),
            gates=(),
            reconciliations=(),
        )


def test_rejects_missing_paths_duplicate_identities_and_invalid_vocabularies(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "path": "missing.json"}
    )
    with pytest.raises(ReleaseEvidenceError, match="path is missing"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    duplicate = ArtifactInput(**{**artifacts[0].__dict__, "path": "duplicate.json"})
    (tmp_path / "duplicate.json").write_bytes(b"receipt\n")
    artifacts.append(duplicate)
    with pytest.raises(ReleaseEvidenceError, match="duplicate artifact identity"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    validation_digest = next(
        item.output_digest for item in artifacts if item.identity == "validation"
    )
    with pytest.raises(ReleaseEvidenceError, match="invalid gate status"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[
                GateResult(
                    "quality",
                    "pass",  # type: ignore[arg-type]
                    True,
                    validation_digest,
                )
            ],
        )

    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "output_digest": "0" * 64}
    )
    with pytest.raises(ReleaseEvidenceError, match="canonical SHA-256"):
        _build(tmp_path, artifacts=artifacts)
