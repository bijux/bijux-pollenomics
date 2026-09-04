from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import cast

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
        "schema_version": "recorded-gate.v3",
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
    root: Path, *, gate_id: str = "quality", gate_status: str = "PASS"
) -> list[ArtifactInput]:
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
    }
    for relative, value in content.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    digests = {relative: _digest(value) for relative, value in content.items()}
    validation_path = f"artifacts/gate-evidence/{gate_id}.json"
    digests[validation_path] = _write_gate_record(
        root, path=validation_path, gate_id=gate_id, status=gate_status
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
        ("classification", "classification", "classification.csv", ()),
        ("scenario", "scenario", "scenario.json", ()),
        ("boundary", "boundary", "boundary.geojson", ()),
        ("producer", "producer", "producer.py", ()),
        ("lock", "dependency_lock", "uv.lock", ()),
        ("output", "generated_output", "output.json", (snapshot_ref,)),
        ("validation", "validation_result", validation_path, (output_ref,)),
    ]
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
                    "recorded-gate.v3" if role == "validation_result" else "fixture.v1"
                ),
                parents=parents,
                config_digests=configs
                if role in {"generated_output", "validation_result"}
                else (),
                producer_digest=producer,
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
    artifacts = _artifacts(tmp_path, gate_id="alpha")
    alpha_validation = next(
        artifact for artifact in artifacts if artifact.identity == "validation"
    )
    zeta_path = "artifacts/gate-evidence/zeta.json"
    zeta_digest = _write_gate_record(tmp_path, path=zeta_path, gate_id="zeta")
    artifacts.append(
        ArtifactInput(
            **{
                **alpha_validation.__dict__,
                "identity": "zeta-validation",
                "path": zeta_path,
                "output_digest": zeta_digest,
            }
        )
    )
    gates = [
        GateResult("zeta", "PASS", True, zeta_digest),
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
    artifacts = _artifacts(tmp_path)
    second_path = tmp_path / "secondary-producer.py"
    second_path.write_bytes(b"def render(): return 2\n")
    second_digest = _digest(second_path.read_bytes())
    artifacts.append(
        ArtifactInput(
            identity="secondary-producer",
            role="producer",
            path="secondary-producer.py",
            media_type="text/x-python",
            schema_version="fixture.v1",
            parents=(),
            config_digests=(),
            producer_digest=second_digest,
            output_digest=second_digest,
        )
    )
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "producer_digest": second_digest}
    )

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
    with pytest.raises(ReleaseEvidenceError, match="identity mismatch"):
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
    ["argv", "environment", "empty-inputs", "substituted-input", "producer", "root"],
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
        else:
            record["repository_root_digest"] = _json_digest("/relocated")

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
            "version": "3",
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


@pytest.mark.parametrize("attack", ["independent", "missing", "legacy-v2"])
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
            record["schema_version"] = "recorded-gate.v2"

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


def test_derived_artifact_requires_a_present_digest_matching_parent(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "parents": (ArtifactReference("missing", "sha256:" + "0" * 64),),
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="missing parent"):
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
