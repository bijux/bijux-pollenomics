"""Repository-owned fixture policy construction."""

from __future__ import annotations

from pathlib import Path

from .codec import _canonical_json


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
        ("configuration", "configs/release_evidence_policy.json", "producer.py"),
        ("classification", "classification.csv", "producer.py"),
        ("scenario", "scenario.json", "producer.py"),
        ("boundary", "boundary.geojson", "producer.py"),
        ("producer", "producer.py", "producer.py"),
        ("dependency_lock", "uv.lock", "producer.py"),
        ("generated_output", "output.json", "producer.py"),
        ("validation_result", "artifacts/gate-evidence", "producer.py"),
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
