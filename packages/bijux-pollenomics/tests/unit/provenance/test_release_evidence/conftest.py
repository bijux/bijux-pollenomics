"""Shared builders for release-evidence contract tests."""

from __future__ import annotations
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    Blocker,
    CountReconciliation,
    GateResult,
    build_release_evidence_manifest,
    hash_repository_object,
)
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance.gates import RecordedGateSpecification

COMMIT = "1" * 40


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


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
