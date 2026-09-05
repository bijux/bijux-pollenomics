"""Shared release-evidence writer fixtures and deterministic builders."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    CountReconciliation,
    GateResult,
    hash_repository_object,
    write_release_evidence_manifest,
)
from bijux_pollenomics.provenance.gates import RecordedGateSpecification
from bijux_pollenomics.provenance import writer as writer_module
from bijux_pollenomics.provenance.release_evidence import ArtifactRole, GateStatus

COMMIT = "3" * 40


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _json_digest(value: object) -> str:
    return _digest(_canonical_json(value))


def _write_fixture_policy(root: Path) -> bytes:
    producer = "inputs/producer.py"
    ownership = [
        ("source_receipt", "inputs/receipt.json"),
        ("source_snapshot", "inputs/snapshot"),
        ("configuration", "inputs/config.json"),
        ("configuration", "configs/release_evidence_policy.json"),
        ("classification", "inputs/classification.csv"),
        ("scenario", "inputs/scenario.json"),
        ("boundary", "inputs/boundary.geojson"),
        ("producer", producer),
        ("dependency_lock", "inputs/uv.lock"),
        ("generated_output", "inputs/output.json"),
        ("validation_result", "artifacts/gate-evidence"),
    ]
    inventory = [
        ("boundary", "boundary", "inputs/boundary.geojson"),
        ("classification", "classification", "inputs/classification.csv"),
        ("config", "configuration", "inputs/config.json"),
        ("lock", "dependency_lock", "inputs/uv.lock"),
        ("output", "generated_output", "inputs/output.json"),
        ("producer", "producer", producer),
        (
            "release-evidence-policy",
            "configuration",
            "configs/release_evidence_policy.json",
        ),
        ("receipt", "source_receipt", "inputs/receipt.json"),
        ("scenario", "scenario", "inputs/scenario.json"),
        ("snapshot", "source_snapshot", "inputs/snapshot"),
        (
            "validation",
            "validation_result",
            "artifacts/gate-evidence/quality.json",
        ),
    ]
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
        "recording_authority_path": producer,
        "authorized_producer_paths": [producer],
        "artifact_ownership": [
            {
                "artifact_role": role,
                "artifact_path_prefix": prefix,
                "producer_path": producer,
            }
            for role, prefix in sorted(ownership, key=lambda item: (item[1], item[0]))
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
                "producer_path": producer,
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
            for identity, role, path in sorted(inventory)
        ],
        "embedded_producer_identities": [],
        "bundle_inventories": [],
        "allowed_cross_role_digest_aliases": [],
        "required_gate_ids": ["quality"],
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


def _write_gate_record(root: Path, status: str) -> None:
    gate_input = root / "inputs/gate-input.txt"
    gate_input.parent.mkdir(parents=True, exist_ok=True)
    gate_input.write_text("current gate input\n", encoding="utf-8")
    stdout = root / "artifacts/gate-evidence/quality.stdout.log"
    stderr = root / "artifacts/gate-evidence/quality.stderr.log"
    junit = root / "artifacts/gate-evidence/quality.junit.xml"
    stdout.parent.mkdir(parents=True, exist_ok=True)
    stdout.write_text("passed\n", encoding="utf-8")
    stderr.write_bytes(b"")
    junit.write_text('<testsuite failures="0"/>\n', encoding="utf-8")

    def repository_record(relative: str) -> dict[str, object]:
        return {"path": relative, **hash_repository_object(root, relative)}

    inputs = [repository_record("inputs/gate-input.txt")]
    specification = _fixture_specification(root, "quality")
    specification_record = specification.as_record(root)
    exit_code = 0 if status == "PASS" else 1
    reason_code = "command_passed" if status == "PASS" else "command_failed"
    content: dict[str, object] = {
        "schema_version": "recorded-gate.v4",
        "producer": specification_record["producer"],
        "attestation": specification_record["attestation"],
        "repository_root_digest": specification_record["repository_root_digest"],
        "gate_id": "quality",
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
        "stdout": repository_record("artifacts/gate-evidence/quality.stdout.log"),
        "stderr": repository_record("artifacts/gate-evidence/quality.stderr.log"),
        "junit": repository_record("artifacts/gate-evidence/quality.junit.xml"),
    }
    record = {"record_digest": _json_digest(content), **content}
    (root / "artifacts/gate-evidence/quality.json").write_bytes(
        _canonical_json(record) + b"\n"
    )


def _fixture_specification(root: Path, gate_id: str) -> RecordedGateSpecification:
    return RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=("pytest", "-q"),
        environment=(),
        input_paths=("inputs/gate-input.txt",),
        artifacts_directory="artifacts/gate-evidence",
        junit_path=f"artifacts/gate-evidence/{gate_id}.junit.xml",
    )


def _inputs(
    root: Path, *, gate_status: str = "PASS"
) -> tuple[list[ArtifactInput], list[CountReconciliation]]:
    policy_payload = _write_fixture_policy(root)
    contents = {
        "inputs/receipt.json": b"receipt\n",
        "inputs/snapshot/records.csv": b"record_id,value\n1,2\n",
        "inputs/config.json": b"{}\n",
        "inputs/classification.csv": b"source,concept\na,b\n",
        "inputs/scenario.json": b'{"scenario":"strict"}\n',
        "inputs/boundary.geojson": b'{"type":"FeatureCollection","features":[]}\n',
        "inputs/producer.py": b"def build(): return 1\n",
        "inputs/uv.lock": b"version = 1\n",
        "inputs/output.json": b'{"records":1}\n',
        "configs/release_evidence_policy.json": policy_payload,
    }
    for relative_path, content in contents.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _write_gate_record(root, gate_status)
    validation_path = "artifacts/gate-evidence/quality.json"
    contents[validation_path] = (root / validation_path).read_bytes()
    digests = {
        relative_path: cast(
            str, hash_repository_object(root, relative_path)["output_digest"]
        )
        for relative_path in contents
        if relative_path != "inputs/snapshot/records.csv"
    }
    digests["inputs/snapshot"] = cast(
        str, hash_repository_object(root, "inputs/snapshot")["output_digest"]
    )
    producer_digest = digests["inputs/producer.py"]
    config_digests = tuple(
        digests[path]
        for path in (
            "inputs/config.json",
            "inputs/classification.csv",
            "inputs/scenario.json",
            "inputs/boundary.geojson",
            "inputs/uv.lock",
            "configs/release_evidence_policy.json",
        )
    )
    receipt = ArtifactReference("receipt", digests["inputs/receipt.json"])
    snapshot = ArtifactReference("snapshot", digests["inputs/snapshot"])
    output = ArtifactReference("output", digests["inputs/output.json"])
    definitions = (
        ("receipt", "source_receipt", "inputs/receipt.json", ()),
        ("snapshot", "source_snapshot", "inputs/snapshot", (receipt,)),
        ("config", "configuration", "inputs/config.json", ()),
        (
            "release-evidence-policy",
            "configuration",
            "configs/release_evidence_policy.json",
            (),
        ),
        ("classification", "classification", "inputs/classification.csv", ()),
        ("scenario", "scenario", "inputs/scenario.json", ()),
        ("boundary", "boundary", "inputs/boundary.geojson", ()),
        ("producer", "producer", "inputs/producer.py", ()),
        ("lock", "dependency_lock", "inputs/uv.lock", ()),
        ("output", "generated_output", "inputs/output.json", (snapshot,)),
        ("validation", "validation_result", validation_path, (output,)),
    )
    artifacts = [
        ArtifactInput(
            identity=identity,
            role=cast(ArtifactRole, role),
            path=path,
            media_type="application/octet-stream",
            schema_version=(
                "recorded-gate.v4" if role == "validation_result" else "fixture.v1"
            ),
            parents=parents,
            config_digests=(
                config_digests
                if role in {"generated_output", "validation_result"}
                else ()
            ),
            producer_digest=(digests[path] if role == "producer" else producer_digest),
            output_digest=digests[path],
        )
        for identity, role, path, parents in definitions
    ]
    reconciliations = [
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
        )
    ]
    for country in ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE"):
        reconciliations.append(
            CountReconciliation(
                identity=f"neotoma.samples.{country.lower()}",
                dimension="country",
                source="neotoma",
                entity="samples",
                country_code=country,
                candidate_count=0,
                eligible_count=0,
                accepted_count=0,
                unresolved_count=0,
                excluded_count=0,
                refused_count=0,
            )
        )
    return artifacts, reconciliations


def _arguments(root: Path, *, gate_status: str = "PASS") -> dict[str, object]:
    artifacts, reconciliations = _inputs(root, gate_status=gate_status)
    by_identity = {artifact.identity: artifact for artifact in artifacts}
    return {
        "code_commit": COMMIT,
        "dirty": False,
        "dependency_lock_digest": by_identity["lock"].output_digest,
        "artifacts": artifacts,
        "gates": [
            GateResult(
                identity="quality",
                status=cast(GateStatus, gate_status),
                required=True,
                evidence_digest=by_identity["validation"].output_digest,
            )
        ],
        "reconciliations": reconciliations,
        "blockers": (),
    }


def _write(
    root: Path, output_path: str, arguments: dict[str, object]
) -> dict[str, object]:
    return write_release_evidence_manifest(
        root,
        output_path,
        code_commit=cast(str, arguments["code_commit"]),
        dirty=cast(bool, arguments["dirty"]),
        dependency_lock_digest=cast(str, arguments["dependency_lock_digest"]),
        artifacts=cast(list[ArtifactInput], arguments["artifacts"]),
        gates=cast(list[GateResult], arguments["gates"]),
        reconciliations=cast(list[CountReconciliation], arguments["reconciliations"]),
        blockers=(),
    )


def _write_request_document(
    root: Path, request: dict[str, object]
) -> dict[str, object]:
    path = root / "artifacts/requests/generated.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(request) + b"\n")
    return writer_module._write_request(
        root, "artifacts/release/generated.json", request
    )
