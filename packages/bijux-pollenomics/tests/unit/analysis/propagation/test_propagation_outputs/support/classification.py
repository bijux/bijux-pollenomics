"""Classification authority bundles for propagation output tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .json_codec import canonical_json_bytes, read_json


def classification_bundle(parent: Path, accepted_count: int) -> tuple[Path, str]:
    """Materialize a closed classification-authority fixture bundle."""
    root = parent / f"classification-evidence-{accepted_count}"
    root.mkdir(exist_ok=True)
    common = {
        "source_family": "source-native-fixture",
        "source_snapshot_id": "snapshot-1",
        "build_id": "build-1",
        "classification_contract_version": "classification.v1",
        "classification_contract_digest": f"sha256:{'1' * 64}",
        "classification_producer_id": "classification-fixture",
        "classification_producer_version": "1",
        "classification_producer_digest": f"sha256:{'2' * 64}",
    }
    accepted_records = [
        {
            "classification_concept_id": f"accepted-{index}",
            "mapping_status": "accepted",
            "mapping_version": "fixture-crosswalk.v1",
            "reviewer_id": "reviewer-fixture",
            "decision_date": "2026-09-04",
            "accepted_taxon_concept_id": f"taxon-{index}",
            "citation_reference_ids": ["citation-fixture"],
            "review_complete": True,
            "release_eligible": True,
        }
        for index in range(accepted_count)
    ]
    mapping_status_counts = {
        "accepted": accepted_count,
        "accepted_qualified": 0,
        "contested": 0,
        "not_applicable": 0,
        "refused": 0,
        "unmapped": 0,
    }
    payloads: dict[str, dict[str, object]] = {
        "accepted_mapping_queue.json": {
            "schema_version": "classification-accepted-mapping-queue.v1",
            **common,
            "record_count": accepted_count,
            "records": accepted_records,
        },
        "concept_denominators.json": {
            "schema_version": "classification-concept-denominators.v1",
            **common,
            "record_count": accepted_count,
            "total_concept_count": accepted_count,
            "mapping_status_counts": mapping_status_counts,
            "accepted_queue_count": accepted_count,
            "unmapped_queue_count": 0,
            "not_applicable_queue_count": 0,
            "review_queue_count": 0,
        },
        "country_partitions.json": {
            "schema_version": "classification-country-partitions.v1",
            **common,
            "record_count": 0,
            "source_country": [],
            "governed_country": [],
            "country_relation": [],
        },
        "not_applicable_mapping_queue.json": {
            "schema_version": "classification-not-applicable-mapping-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "observation_denominators.json": {
            "schema_version": "classification-observation-denominators.v1",
            **common,
            "record_count": 0,
            "total_observation_count": 0,
            "mapping_status_counts": dict.fromkeys(mapping_status_counts, 0),
        },
        "observation_memberships.json": {
            "schema_version": "classification-observation-memberships.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "release_metadata.json": {
            "schema_version": "classification-release-metadata.v1",
            **common,
            "accepted_mapping_count": accepted_count,
            "reviewed_accepted_mapping_count": accepted_count,
            "release_eligible_mapping_count": accepted_count,
            "unmapped_mapping_count": 0,
            "not_applicable_mapping_count": 0,
            "human_approval_synthesized": False,
            "record_count": 1,
        },
        "review_queue.json": {
            "schema_version": "classification-review-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
        "unmapped_mapping_queue.json": {
            "schema_version": "classification-unmapped-mapping-queue.v1",
            **common,
            "record_count": 0,
            "records": [],
        },
    }
    serialized = {
        name: canonical_json_bytes(payload) for name, payload in payloads.items()
    }
    entries = [
        {
            "path": name,
            "sha256": hashlib.sha256(serialized[name]).hexdigest(),
            "record_count": payloads[name]["record_count"],
        }
        for name in sorted(serialized)
    ]
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode()
    manifest = {
        "schema_version": "classification-audit-manifest.v1",
        **common,
        "bundle_digest": hashlib.sha256(digest_input).hexdigest(),
        "payload_file_count": len(entries),
        "files": entries,
    }
    for name, value in serialized.items():
        (root / name).write_bytes(value)
    manifest_bytes = canonical_json_bytes(manifest)
    (root / "manifest.json").write_bytes(manifest_bytes)
    return root, hashlib.sha256(manifest_bytes).hexdigest()


def rehash_classification_bundle(root: Path) -> str:
    """Reclose a deliberately modified classification fixture."""
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    entries = manifest["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        payload_path = root / str(entry["path"])
        payload = read_json(payload_path)
        payload_bytes = canonical_json_bytes(payload)
        payload_path.write_bytes(payload_bytes)
        entry["sha256"] = hashlib.sha256(payload_bytes).hexdigest()
        entry["record_count"] = payload["record_count"]
    manifest["bundle_digest"] = hashlib.sha256(
        "".join(
            f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
            for entry in entries
        ).encode()
    ).hexdigest()
    manifest_bytes = canonical_json_bytes(manifest)
    manifest_path.write_bytes(manifest_bytes)
    return hashlib.sha256(manifest_bytes).hexdigest()
