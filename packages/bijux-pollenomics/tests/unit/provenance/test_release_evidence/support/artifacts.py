"""Release-evidence artifact graph fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    hash_repository_object,
)

from .codec import _digest, _json_digest
from .gates import _write_gate_record
from .policy import _write_fixture_policy


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
            ("secondary-producer", "producer", "secondary-producer.py", ()),
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
                config_digests=(
                    configs if role in {"generated_output", "validation_result"} else ()
                ),
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
