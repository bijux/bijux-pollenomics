from __future__ import annotations

import copy
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
    ReleaseEvidenceError,
    build_release_evidence_manifest,
    hash_repository_object,
    validate_release_evidence_manifest,
)
from bijux_pollenomics.provenance.release_evidence import validate_recorded_gate

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
    path: str = "validation.json",
    gate_id: str = "quality",
    status: str = "PASS",
) -> str:
    gate_input = root / "gate-input.txt"
    gate_input.write_text("current gate input\n", encoding="utf-8")
    evidence_directory = root / "gate-evidence"
    evidence_directory.mkdir(exist_ok=True)
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
    content: dict[str, object] = {
        "schema_version": "recorded-gate.v1",
        "gate_id": gate_id,
        "argv": ["pytest", "-q"],
        "command_digest": _json_digest(["pytest", "-q"]),
        "environment_digest": _json_digest({}),
        "environment_keys": [],
        "inputs": inputs,
        "input_digest": _json_digest(inputs),
        "duration_monotonic_ns": 1,
        "exit_code": exit_code,
        "status": status,
        "reason_code": reason_code,
        "stdout": repository_record(f"gate-evidence/{gate_id}.stdout.log"),
        "stderr": repository_record(f"gate-evidence/{gate_id}.stderr.log"),
        "junit": repository_record(f"gate-evidence/{gate_id}.junit.xml"),
    }
    record = {"record_digest": _json_digest(content), **content}
    payload = _canonical_json(record) + b"\n"
    output = root / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    return _digest(payload)


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
    digests["validation.json"] = _write_gate_record(
        root, gate_id=gate_id, status=gate_status
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
        ("validation", "validation_result", "validation.json", (output_ref,)),
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
                    "recorded-gate.v1" if role == "validation_result" else "fixture.v1"
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
    zeta_digest = _write_gate_record(
        tmp_path, path="zeta-validation.json", gate_id="zeta"
    )
    artifacts.append(
        ArtifactInput(
            **{
                **alpha_validation.__dict__,
                "identity": "zeta-validation",
                "path": "zeta-validation.json",
                "output_digest": zeta_digest,
            }
        )
    )
    gates = [
        GateResult("zeta", "PASS", False, zeta_digest),
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
        "release_ready": True,
        "status": "verified_complete",
        "reason_codes": [],
    }
    validate_release_evidence_manifest(tmp_path, first)


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


def test_recorded_gate_rejects_stale_declared_input(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / "gate-input.txt").write_text("changed input\n", encoding="utf-8")

    with pytest.raises(ReleaseEvidenceError, match="input changed"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_rejects_internal_record_digest_tamper(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    path = tmp_path / "validation.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["duration_monotonic_ns"] = 2
    path.write_bytes(_canonical_json(record) + b"\n")
    _refresh_validation_artifact(tmp_path, artifacts)

    with pytest.raises(ReleaseEvidenceError, match="record_digest mismatch"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    "relative_path, expected_message",
    [
        ("gate-evidence/quality.stdout.log", "stdout changed"),
        ("gate-evidence/quality.stderr.log", "stderr changed"),
        ("gate-evidence/quality.junit.xml", "JUnit changed"),
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
    with pytest.raises(ReleaseEvidenceError, match="symlink"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    "status", ["FAIL", "SKIPPED", "BLOCKED_EXTERNAL", "NOT_APPLICABLE"]
)
def test_nonpassing_required_gate_never_claims_release_ready(
    tmp_path: Path, status: str
) -> None:
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
        "reason_codes": ["blocker:source_rights_unverified"],
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
        "reason_codes": ["candidate_dirty"],
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
