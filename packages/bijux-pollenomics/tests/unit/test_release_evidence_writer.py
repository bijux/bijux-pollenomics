from __future__ import annotations

from dataclasses import asdict
import json
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

COMMIT = "3" * 40


def _inputs(root: Path) -> tuple[list[ArtifactInput], list[CountReconciliation]]:
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
        "inputs/validation.json": b'{"status":"PASS"}\n',
    }
    for relative_path, content in contents.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
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
        )
    )
    receipt = ArtifactReference("receipt", digests["inputs/receipt.json"])
    snapshot = ArtifactReference("snapshot", digests["inputs/snapshot"])
    output = ArtifactReference("output", digests["inputs/output.json"])
    definitions = (
        ("receipt", "source_receipt", "inputs/receipt.json", ()),
        ("snapshot", "source_snapshot", "inputs/snapshot", (receipt,)),
        ("config", "configuration", "inputs/config.json", ()),
        ("classification", "classification", "inputs/classification.csv", ()),
        ("scenario", "scenario", "inputs/scenario.json", ()),
        ("boundary", "boundary", "inputs/boundary.geojson", ()),
        ("producer", "producer", "inputs/producer.py", ()),
        ("lock", "dependency_lock", "inputs/uv.lock", ()),
        ("output", "generated_output", "inputs/output.json", (snapshot,)),
        ("validation", "validation_result", "inputs/validation.json", (output,)),
    )
    artifacts = [
        ArtifactInput(
            identity=identity,
            role=role,  # type: ignore[arg-type]
            path=path,
            media_type="application/octet-stream",
            schema_version="fixture.v1",
            parents=parents,
            config_digests=(
                config_digests
                if role in {"generated_output", "validation_result"}
                else ()
            ),
            producer_digest=producer_digest,
            output_digest=digests[path],
        )
        for identity, role, path, parents in definitions
    ]
    zero_counts = {
        "candidate_count": 0,
        "eligible_count": 0,
        "accepted_count": 0,
        "unresolved_count": 0,
        "excluded_count": 0,
        "refused_count": 0,
    }
    reconciliations = [
        CountReconciliation(
            identity="neotoma.samples.source",
            dimension="source",
            source="neotoma",
            entity="samples",
            country_code=None,
            **zero_counts,
        )
    ]
    for country in ("SE", "DK", "NO", "FI", "UNASSIGNED"):
        reconciliations.append(
            CountReconciliation(
                identity=f"neotoma.samples.{country.lower()}",
                dimension="country",
                source="neotoma",
                entity="samples",
                country_code=country,
                **zero_counts,
            )
        )
    return artifacts, reconciliations


def _arguments(root: Path, *, gate_status: str = "PASS") -> dict[str, object]:
    artifacts, reconciliations = _inputs(root)
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
        "schema_version": "release-evidence-request.v1",
        "code_commit": arguments["code_commit"],
        "dirty": arguments["dirty"],
        "dependency_lock_digest": arguments["dependency_lock_digest"],
        "artifacts": [
            asdict(artifact)
            for artifact in cast(list[ArtifactInput], arguments["artifacts"])
        ],
        "gates": [asdict(gate) for gate in cast(list[GateResult], arguments["gates"])],
        "reconciliations": [
            asdict(item)
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
    artifacts = tmp_path / "artifacts"
    artifacts.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ReleaseEvidenceError, match="unsafe output directory"):
        _write(tmp_path, "artifacts/release/manifest.json", arguments)


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

    assert write_status == validate_status == 0
    assert write_output == validate_output
    assert write_output["release_ready"] is True
    assert write_output["status"] == "verified_complete"


def test_callable_cli_returns_nonzero_for_nonrelease_evidence(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    arguments = _arguments(tmp_path, gate_status="SKIPPED")
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
    assert summary["status"] == "implemented_unverified"
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
