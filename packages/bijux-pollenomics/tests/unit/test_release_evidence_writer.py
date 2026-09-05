from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
    hash_repository_object,
    release_evidence_main,
    validate_release_evidence_manifest,
    write_release_evidence_manifest,
)
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance.gates import RecordedGateSpecification

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


@pytest.fixture(autouse=True)
def _trusted_fixture_gate_specification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate_module,
        "build_product_gate_specification",
        _fixture_specification,
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
            role=role,  # type: ignore[arg-type]
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
                status=gate_status,  # type: ignore[arg-type]
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


def _request(arguments: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "release-evidence-request.v3",
        "code_commit": arguments["code_commit"],
        "dirty": arguments["dirty"],
        "dependency_lock_digest": arguments["dependency_lock_digest"],
        "artifacts": [
            asdict(artifact)
            for artifact in cast(list[ArtifactInput], arguments["artifacts"])
        ],
        "gates": [asdict(gate) for gate in cast(list[GateResult], arguments["gates"])],
        "reconciliations": [
            {**asdict(item), "scope": dict(item.scope)}
            for item in cast(list[CountReconciliation], arguments["reconciliations"])
        ],
        "blockers": [],
    }


def test_writer_emits_canonical_json_and_validates_immediately(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    manifest = _write(tmp_path, "artifacts/release/manifest.json", arguments)
    output = tmp_path / "artifacts/release/manifest.json"

    expected = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    assert output.read_bytes() == expected
    assert not list(output.parent.glob("*.writing"))
    validate_release_evidence_manifest(tmp_path, manifest)


def test_identical_output_is_preserved_without_rewrite(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    first = _write(tmp_path, output_path, arguments)
    output = tmp_path / output_path
    before = output.stat()

    second = _write(tmp_path, output_path, arguments)
    after = output.stat()

    assert second == first
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)


def test_different_existing_output_is_refused_and_preserved(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    _write(tmp_path, output_path, arguments)
    output = tmp_path / output_path
    original = output.read_bytes()
    changed = dict(arguments)
    changed["dirty"] = True

    with pytest.raises(ReleaseEvidenceError, match="different bytes"):
        _write(tmp_path, output_path, changed)

    assert output.read_bytes() == original


@pytest.mark.parametrize(
    "output_path",
    ["release.json", "../release.json", "artifacts/../release.json"],
)
def test_writer_rejects_outputs_outside_artifacts(
    tmp_path: Path, output_path: str
) -> None:
    arguments = _arguments(tmp_path)

    with pytest.raises(ReleaseEvidenceError):
        _write(tmp_path, output_path, arguments)


def test_writer_rejects_symlinked_output_directory(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    release_directory = tmp_path / "artifacts/release"
    release_directory.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ReleaseEvidenceError, match="unsafe output directory"):
        _write(tmp_path, "artifacts/release/manifest.json", arguments)


def test_writer_refuses_output_parent_substitution_during_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = _arguments(tmp_path)
    release = tmp_path / "artifacts/release"
    release.mkdir(parents=True)
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    original_link = os.link
    substituted = False

    def substituting_link(
        source: str,
        destination: str,
        *,
        src_dir_fd: int | None = None,
        dst_dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal substituted
        release.rename(tmp_path / "artifacts/release-original")
        release.symlink_to(replacement, target_is_directory=True)
        substituted = True
        original_link(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(os, "link", substituting_link)

    with pytest.raises(ReleaseEvidenceError, match="output parent"):
        _write(tmp_path, "artifacts/release/manifest.json", arguments)

    assert substituted is True
    assert not (replacement / "manifest.json").exists()


def test_callable_cli_writes_and_validates_for_a_local_gate(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    arguments = _arguments(tmp_path)
    request_path = tmp_path / "artifacts/requests/release.json"
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps(_request(arguments), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    output_path = "artifacts/release/manifest.json"

    write_status = release_evidence_main(
        [
            "write",
            "--repository-root",
            str(tmp_path),
            "--request",
            "artifacts/requests/release.json",
            "--output",
            output_path,
        ]
    )
    write_output = json.loads(capfd.readouterr().out)
    validate_status = release_evidence_main(
        [
            "validate",
            "--repository-root",
            str(tmp_path),
            "--manifest",
            output_path,
        ]
    )
    validate_output = json.loads(capfd.readouterr().out)

    assert write_status == validate_status == 1
    assert write_output == validate_output
    assert write_output["release_ready"] is False
    assert write_output["status"] == "implemented_unverified"


def test_callable_cli_returns_nonzero_for_nonrelease_evidence(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    arguments = _arguments(tmp_path, gate_status="FAIL")
    request_path = tmp_path / "artifacts/requests/release.json"
    request_path.parent.mkdir(parents=True)
    request_path.write_text(json.dumps(_request(arguments)), encoding="utf-8")

    result = release_evidence_main(
        [
            "write",
            "--repository-root",
            str(tmp_path),
            "--request",
            "artifacts/requests/release.json",
            "--output",
            "artifacts/release/manifest.json",
        ]
    )
    summary = json.loads(capfd.readouterr().out)

    assert result == 1
    assert summary["release_ready"] is False
    assert summary["status"] == "failed"
    assert (tmp_path / "artifacts/release/manifest.json").is_file()


def test_validate_cli_detects_changed_immutable_input(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    _write(tmp_path, output_path, arguments)
    (tmp_path / "inputs/output.json").write_text('{"records":2}\n', encoding="utf-8")

    result = release_evidence_main(
        [
            "validate",
            "--repository-root",
            str(tmp_path),
            "--manifest",
            output_path,
        ]
    )
    captured = capfd.readouterr()

    assert result == 2
    assert captured.out == ""
    assert "release evidence refused" in captured.err
