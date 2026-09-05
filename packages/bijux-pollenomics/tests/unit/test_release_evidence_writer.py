from __future__ import annotations

from dataclasses import replace
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
    derive_release_evidence_request,
    hash_repository_object,
    release_evidence_main,
    validate_release_evidence_manifest,
    write_release_evidence_manifest,
    write_release_evidence_request,
)
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance import release_evidence as release_evidence_module
from bijux_pollenomics.provenance import request as request_module
from bijux_pollenomics.provenance import writer as writer_module
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
    _inputs(tmp_path)
    request_status = release_evidence_main(
        [
            "request",
            "--repository-root",
            str(tmp_path),
            "--output",
            "artifacts/requests/release.json",
        ]
    )
    request_summary = json.loads(capfd.readouterr().out)
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

    assert request_status == 0
    assert request_summary["schema_version"] == "release-evidence-request.v3"
    assert write_status == validate_status == 1
    assert write_output == validate_output
    assert write_output["release_ready"] is False
    assert write_output["status"] == "implemented_unverified"


def test_callable_cli_returns_nonzero_for_nonrelease_evidence(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    _inputs(tmp_path, gate_status="FAIL")
    write_release_evidence_request(tmp_path, "artifacts/requests/release.json")

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


def test_request_derivation_is_deterministic_and_locally_unverified(
    tmp_path: Path,
) -> None:
    _inputs(tmp_path)

    first = derive_release_evidence_request(tmp_path)
    second = derive_release_evidence_request(tmp_path)

    assert first == second
    assert first["schema_version"] == "release-evidence-request.v3"
    assert len(cast(list[object], first["artifacts"])) == 11
    assert len(cast(list[object], first["gates"])) == 1
    assert len(cast(list[object], first["reconciliations"])) == 7
    assert first["blockers"] == []
    manifest = _write_request_document(tmp_path, first)
    decision = cast(dict[str, object], manifest["release_decision"])
    assert decision["status"] == "implemented_unverified"
    assert decision["release_ready"] is False


def _write_request_document(
    root: Path, request: dict[str, object]
) -> dict[str, object]:
    path = root / "artifacts/requests/generated.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(request) + b"\n")
    return writer_module._write_request(
        root, "artifacts/release/generated.json", request
    )


@pytest.mark.parametrize("failure", ["missing", "stale", "old_schema"])
def test_request_derivation_rejects_invalid_recorded_gate(
    tmp_path: Path, failure: str
) -> None:
    _inputs(tmp_path)
    gate = tmp_path / "artifacts/gate-evidence/quality.json"
    if failure == "missing":
        gate.unlink()
    elif failure == "stale":
        (tmp_path / "inputs/gate-input.txt").write_text(
            "changed after gate\n", encoding="utf-8"
        )
    else:
        record = json.loads(gate.read_text(encoding="utf-8"))
        record["schema_version"] = "recorded-gate.v1"
        gate.write_bytes(_canonical_json(record) + b"\n")

    with pytest.raises(ReleaseEvidenceError):
        derive_release_evidence_request(tmp_path)


def test_request_writer_is_idempotent_and_refuses_different_bytes(
    tmp_path: Path,
) -> None:
    _inputs(tmp_path)
    relative = "artifacts/release-candidate/request.json"
    first = write_release_evidence_request(tmp_path, relative)
    output = tmp_path / relative
    before = output.stat()

    second = write_release_evidence_request(tmp_path, relative)
    after = output.stat()
    assert first == second
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)

    (tmp_path / "inputs/output.json").write_text('{"records":2}\n', encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="different bytes"):
        write_release_evidence_request(tmp_path, relative)


def test_request_writer_rejects_symlinked_output_parent(tmp_path: Path) -> None:
    _inputs(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "artifacts/release-candidate").symlink_to(
        outside, target_is_directory=True
    )

    with pytest.raises(ReleaseEvidenceError, match="unsafe output directory"):
        write_release_evidence_request(
            tmp_path, "artifacts/release-candidate/request.json"
        )


def test_request_derivation_rejects_concurrent_input_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _inputs(tmp_path)
    original = request_module.evidence._hash_repository_object
    mutated = False

    def mutating_hash(
        root: Path, relative_path: str, *, exclude_python_cache: bool = False
    ) -> dict[str, object]:
        nonlocal mutated
        result = original(
            root,
            relative_path,
            exclude_python_cache=exclude_python_cache,
        )
        if relative_path == "inputs/config.json" and not mutated:
            (root / relative_path).write_text('{"changed":true}\n', encoding="utf-8")
            mutated = True
        return result

    monkeypatch.setattr(
        request_module.evidence, "_hash_repository_object", mutating_hash
    )

    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        derive_release_evidence_request(tmp_path)
    assert mutated is True


def test_request_derivation_records_observed_dirty_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _inputs(tmp_path)
    state = {
        "mode": "fixture",
        "head_commit": None,
        "head_tree": None,
        "dirty": True,
        "status_digest": "sha256:" + "1" * 64,
        "tracked_paths_digest": None,
        "tracked_diff_digest": None,
        "untracked_objects": [],
    }
    monkeypatch.setattr(
        request_module.evidence,
        "_repository_state",
        lambda _root, _mode: dict(state),
    )

    request = derive_release_evidence_request(tmp_path)

    assert request["dirty"] is True


def test_exact_request_validation_rejects_hand_authored_change(tmp_path: Path) -> None:
    _inputs(tmp_path)
    request = derive_release_evidence_request(tmp_path)
    request["dirty"] = True

    with pytest.raises(ReleaseEvidenceError, match="differs from current"):
        request_module.validate_release_evidence_request(tmp_path, request)


def test_product_request_policy_has_exact_inventory_and_reconciliation_counts() -> None:
    root = Path(__file__).resolve().parents[4]
    policy = request_module.evidence._load_release_evidence_policy(root)

    rows = request_module._reconciliations(root, policy)
    by_identity = {row.identity: row for row in rows}

    assert len(policy.required_artifacts) == 24
    assert len(policy.required_gate_ids) == 5
    assert len(policy.required_reconciliations) == 28
    assert len(rows) == 390
    assert len({(row.source, row.entity) for row in rows}) == 28
    assert {
        status: sum(row.count_status == status for row in rows)
        for status in ("reported", "unavailable", "refused")
    } == {"reported": 327, "unavailable": 49, "refused": 14}
    request_module.evidence._validate_reconciliations(rows, policy)
    classification_metrics = {
        requirement.entity: requirement.derivation_metric
        for requirement in policy.required_reconciliations
        if requirement.source == "classification"
    }
    assert classification_metrics == {
        "ambiguous": "ambiguous_concepts",
        "concepts": "distinct_concepts",
        "mapped": "mapped_concepts",
        "unmapped": "unmapped_concepts",
    }

    sead = by_identity["sead.sites.source"]
    assert (
        sead.candidate_count,
        sead.eligible_count,
        sead.accepted_count,
        sead.unresolved_count,
        sead.excluded_count,
    ) == (2195, 2069, 2069, 103, 23)
    assert by_identity["sead.sites.country.unassigned"].unresolved_count == 103
    assert by_identity["sead.sites.country.outside"].excluded_count == 23

    observations = by_identity["neotoma.observations.country.unassigned"]
    assert observations.count_status == "reported"
    assert (observations.candidate_count, observations.unresolved_count) == (9700, 9700)
    outside = by_identity["neotoma.observations.country.outside"]
    assert outside.count_status == "reported"
    assert (outside.candidate_count, outside.excluded_count) == (0, 0)

    concepts = by_identity["classification.concepts.source"]
    unmapped = by_identity["classification.unmapped.source"]
    assert (
        concepts.candidate_count,
        concepts.accepted_count,
        concepts.unresolved_count,
        concepts.excluded_count,
    ) == (2555, 0, 2481, 74)
    assert concepts.candidate_count > 1351  # Country memberships, not global concepts.
    assert (unmapped.candidate_count, unmapped.unresolved_count) == (2481, 2481)
    assert by_identity["raa.records.source"].count_status == "refused"
    assert by_identity["raa.records.source"].candidate_count is None
    assert by_identity["propagation.evaluated_pairs.source"].candidate_count == 0


def test_product_request_policy_has_coherent_full_artifact_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).resolve().parents[4]
    policy = release_evidence_module._load_release_evidence_policy(root)
    artifacts, digests = request_module._artifact_inputs(root, policy)
    records = [
        release_evidence_module._artifact_record(root, artifact)
        for artifact in artifacts
    ]
    dependency_lock = next(
        digests[item.identity]
        for item in policy.required_artifacts
        if item.role == "dependency_lock"
    )
    validate_schema = release_evidence_module._validate_embedded_schema_identity

    def allow_pre_refresh_gate_schema(
        repository_root: Path,
        artifact: ArtifactInput,
        requirement: release_evidence_module._RequiredArtifact,
    ) -> None:
        if artifact.role != "validation_result":
            validate_schema(repository_root, artifact, requirement)

    monkeypatch.setattr(
        release_evidence_module,
        "_validate_embedded_schema_identity",
        allow_pre_refresh_gate_schema,
    )

    release_evidence_module._validate_artifact_graph(
        root,
        artifacts,
        records,
        dependency_lock,
        policy,
    )


def test_product_manifest_validation_rejects_caller_supplied_reconciliations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = _arguments(tmp_path)
    manifest = writer_module.build_release_evidence_manifest(
        tmp_path,
        code_commit=cast(str, arguments["code_commit"]),
        dirty=cast(bool, arguments["dirty"]),
        dependency_lock_digest=cast(str, arguments["dependency_lock_digest"]),
        artifacts=cast(list[ArtifactInput], arguments["artifacts"]),
        gates=cast(list[GateResult], arguments["gates"]),
        reconciliations=cast(list[CountReconciliation], arguments["reconciliations"]),
        blockers=(),
    )
    fixture_policy = release_evidence_module._load_release_evidence_policy(tmp_path)
    product_policy = replace(fixture_policy, mode="product")
    governed = tuple(cast(list[CountReconciliation], arguments["reconciliations"]))
    forged = cast(list[dict[str, object]], manifest["reconciliations"])
    forged[0]["candidate_count"] = cast(int, forged[0]["candidate_count"]) + 1
    forged[0]["eligible_count"] = cast(int, forged[0]["eligible_count"]) + 1
    forged[0]["accepted_count"] = cast(int, forged[0]["accepted_count"]) + 1
    monkeypatch.setattr(
        release_evidence_module,
        "_load_release_evidence_policy",
        lambda _root: product_policy,
    )
    monkeypatch.setattr(
        request_module, "_reconciliations", lambda _root, _policy: governed
    )

    with pytest.raises(ReleaseEvidenceError, match="governed derivation"):
        validate_release_evidence_manifest(tmp_path, manifest)


def test_country_adapter_rejects_dimension_substitution(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    policy = request_module.evidence._load_release_evidence_policy(root)
    requirement = next(
        item
        for item in policy.required_reconciliations
        if (item.source, item.entity) == ("sead", "sites")
    )
    cells = [
        {
            "source_family": "sead",
            "country_dimension": "source_reported",
            "resolution": "source",
            "country_code": country,
            "counts": {"sites": 0},
            "reason_codes": [],
        }
        for country in request_module.evidence._COUNTRIES
    ]
    ledger = tmp_path / "data/country_dimension_coverage.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(_canonical_json({"cells": cells}) + b"\n")

    assert request_module._governed_country_values(tmp_path, requirement) is None
