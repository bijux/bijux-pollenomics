"""Identity tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation.outputs import (
    PropagationOutputRefusalError,
)

from .support import (
    _MODEL,
    _MODEL_BYTES,
    _PROPAGATION_CONTRACT_DIGEST,
    _PROPAGATION_CONTRACT_VERSION,
    _PROPAGATION_PRODUCER_DIGEST,
    _PROPAGATION_PRODUCER_ID,
    _PROPAGATION_PRODUCER_VERSION,
    _canonical_json_bytes,
    _classification_bundle,
    _event,
    _materialize,
    _read_json,
    _rehash_classification_bundle,
)


@pytest.mark.parametrize(
    (
        "contract_version",
        "contract_digest",
        "producer_id",
        "producer_version",
        "producer_digest",
        "reason_code",
    ),
    (
        (
            "",
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            "2.0.0",
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_propagation_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            "not-a-digest",
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            "",
            _PROPAGATION_PRODUCER_VERSION,
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            "",
            _PROPAGATION_PRODUCER_DIGEST,
            "invalid_build_identity",
        ),
        (
            _PROPAGATION_CONTRACT_VERSION,
            _PROPAGATION_CONTRACT_DIGEST,
            _PROPAGATION_PRODUCER_ID,
            _PROPAGATION_PRODUCER_VERSION,
            "A" * 64,
            "invalid_build_identity",
        ),
    ),
)
def test_missing_or_invalid_propagation_identity_is_refused_before_publication(
    tmp_path: Path,
    schema_root: Path,
    contract_version: str,
    contract_digest: str,
    producer_id: str,
    producer_version: str,
    producer_digest: str,
    reason_code: str,
) -> None:
    output_root = tmp_path / "propagation"

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_version=contract_version,
            propagation_contract_digest=contract_digest,
            propagation_producer_id=producer_id,
            propagation_producer_version=producer_version,
            propagation_producer_digest=producer_digest,
        )

    assert refusal.value.reason_code == reason_code
    assert not output_root.exists()


def test_changed_propagation_identity_refuses_existing_bundle_without_modification(
    tmp_path: Path, schema_root: Path
) -> None:
    output_root = tmp_path / "propagation"
    _materialize(
        output_root=output_root,
        allowed_output_parent=tmp_path,
        schema_root=schema_root,
    )
    original_manifest = (output_root / "manifest.json").read_bytes()
    original_release = (output_root / "release_metadata.json").read_bytes()

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_digest=hashlib.sha256(
                b"different-propagation-producer"
            ).hexdigest(),
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"
    assert (output_root / "manifest.json").read_bytes() == original_manifest
    assert (output_root / "release_metadata.json").read_bytes() == original_release


def test_classification_identity_is_bound_to_manifested_bytes_and_counts(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, classification_digest = _classification_bundle(tmp_path, 0)
    release_path = classification_root / "release_metadata.json"
    release_path.write_bytes(release_path.read_bytes() + b" ")

    with pytest.raises(PropagationOutputRefusalError) as changed_bytes:
        _materialize(
            output_root=tmp_path / "changed-bytes",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=classification_digest,
        )
    assert changed_bytes.value.reason_code == "invalid_classification_identity"

    classification_root, classification_digest = _classification_bundle(tmp_path, 0)
    with pytest.raises(PropagationOutputRefusalError) as changed_count:
        _materialize(
            output_root=tmp_path / "changed-count",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=classification_digest,
            accepted_mapping_count=1,
        )
    assert changed_count.value.reason_code == "invalid_classification_reconciliation"

    release_path = classification_root / "release_metadata.json"
    release = _read_json(release_path)
    release["accepted_mapping_count"] = 1
    release_path.write_bytes(_canonical_json_bytes(release))
    manifest_path = classification_root / "manifest.json"
    manifest = _read_json(manifest_path)
    entries = manifest["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        if entry["path"] == "release_metadata.json":
            entry["sha256"] = hashlib.sha256(release_path.read_bytes()).hexdigest()
    manifest["bundle_digest"] = hashlib.sha256(
        "".join(
            f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
            for entry in entries
        ).encode()
    ).hexdigest()
    manifest_path.write_bytes(_canonical_json_bytes(manifest))
    rehashed_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    with pytest.raises(PropagationOutputRefusalError) as rehashed_release:
        _materialize(
            output_root=tmp_path / "rehashed-release",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=rehashed_digest,
            accepted_mapping_count=1,
        )
    assert rehashed_release.value.reason_code == "invalid_classification_reconciliation"


@pytest.mark.parametrize(
    ("payload_name", "mutation"),
    (
        (
            "accepted_mapping_queue.json",
            lambda payload: payload.update(record_count=1),
        ),
        (
            "release_metadata.json",
            lambda payload: payload.update(human_approval_synthesized=True),
        ),
        (
            "concept_denominators.json",
            lambda payload: payload["mapping_status_counts"].update(unmapped=1),
        ),
    ),
)
def test_coherently_rehashed_classification_accounting_mutations_are_refused(
    tmp_path: Path,
    schema_root: Path,
    payload_name: str,
    mutation: object,
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 0)
    payload_path = classification_root / payload_name
    payload = _read_json(payload_path)
    assert callable(mutation)
    mutation(payload)
    payload_path.write_bytes(_canonical_json_bytes(payload))
    digest = _rehash_classification_bundle(classification_root)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / f"refused-{payload_name}",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=digest,
        )

    assert refusal.value.reason_code == "invalid_classification_reconciliation"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda accepted, release: accepted["records"][0].update(review_complete=False),
        lambda accepted, release: release.update(reviewed_accepted_mapping_count=0),
        lambda accepted, release: accepted["records"][0].update(
            citation_reference_ids=[]
        ),
    ),
)
def test_coherently_rehashed_accepted_mapping_requires_complete_review_evidence(
    tmp_path: Path,
    schema_root: Path,
    mutation: object,
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 1)
    accepted_path = classification_root / "accepted_mapping_queue.json"
    release_path = classification_root / "release_metadata.json"
    accepted = _read_json(accepted_path)
    release = _read_json(release_path)
    assert callable(mutation)
    mutation(accepted, release)
    accepted_path.write_bytes(_canonical_json_bytes(accepted))
    release_path.write_bytes(_canonical_json_bytes(release))
    digest = _rehash_classification_bundle(classification_root)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "refused-incomplete-review",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=digest,
            accepted_mapping_count=1,
        )

    assert refusal.value.reason_code == "invalid_classification_reconciliation"


def test_caller_cannot_authorize_a_coherent_fabricated_classification_bundle(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, forged_manifest_digest = _classification_bundle(tmp_path, 1)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / "forged-accepted-classification",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest=forged_manifest_digest,
            accepted_mapping_count=1,
            events=(_event("forged-acceptance"),),
            use_product_classification_authority=True,
        )

    assert refusal.value.reason_code == "invalid_classification_authority"
    assert not (tmp_path / "forged-accepted-classification").exists()


def test_opaque_classification_and_build_claims_are_refused(
    tmp_path: Path, schema_root: Path
) -> None:
    classification_root, _ = _classification_bundle(tmp_path, 1)
    with pytest.raises(PropagationOutputRefusalError) as opaque_digest:
        _materialize(
            output_root=tmp_path / "opaque-digest",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            classification_review_digest="0" * 64,
            accepted_mapping_count=1,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_build:
        _materialize(
            output_root=tmp_path / "wrong-build",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            accepted_mapping_count=1,
            build_id="forged-build",
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_version:
        _materialize(
            output_root=tmp_path / "wrong-version",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            classification_bundle_root=classification_root,
            accepted_mapping_count=1,
            classification_contract_version="forged-classification",
        )

    assert opaque_digest.value.reason_code == "invalid_classification_identity"
    assert wrong_build.value.reason_code == "invalid_classification_identity"
    assert wrong_version.value.reason_code == "invalid_classification_identity"


def test_contract_and_producer_pins_are_recomputed_from_governed_files(
    tmp_path: Path, schema_root: Path
) -> None:
    changed_model = dict(_MODEL)
    default_scenario = _MODEL["default_scenario"]
    assert isinstance(default_scenario, dict)
    changed_model["default_scenario"] = {
        **default_scenario,
        "spatial": {"maximum_distance_km": 101.0},
    }
    changed_bytes = json.dumps(changed_model, sort_keys=True).encode()
    contract_path = schema_root / "propagation-model.v1.yaml"
    contract_path.write_bytes(changed_bytes)

    with pytest.raises(PropagationOutputRefusalError) as semantic_change:
        _materialize(
            output_root=tmp_path / "changed-contract",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_digest=hashlib.sha256(changed_bytes).hexdigest(),
        )
    assert semantic_change.value.reason_code == "invalid_propagation_identity"

    contract_path.write_bytes(_MODEL_BYTES)
    with pytest.raises(PropagationOutputRefusalError) as opaque_producer:
        _materialize(
            output_root=tmp_path / "opaque-producer",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_digest="0" * 64,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_repository:
        _materialize(
            output_root=tmp_path / "wrong-repository",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            repository_root=tmp_path,
        )
    with pytest.raises(PropagationOutputRefusalError) as wrong_producer_id:
        _materialize(
            output_root=tmp_path / "wrong-producer-id",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_producer_id="forged-producer",
        )

    assert opaque_producer.value.reason_code == "invalid_propagation_identity"
    assert wrong_repository.value.reason_code == "invalid_propagation_identity"
    assert wrong_producer_id.value.reason_code == "invalid_propagation_identity"


@pytest.mark.parametrize(
    ("section", "field", "value"),
    (
        ("scientific_claim", "establishes_route", True),
        ("scientific_claim", "establishes_causation", True),
        ("scientific_claim", "establishes_human_migration", True),
        ("scientific_claim", "establishes_plant_migration", True),
        ("scientific_claim", "establishes_local_cultivation", True),
        ("scientific_claim", "preferred_label", "propagation route"),
        ("scientific_claim", "alternate_label", "migration"),
        ("event_contract", "non_pollen_domain_posture", "merge all evidence"),
        ("geographic_scope", "domestic_and_cross_border_rules_identical", False),
        ("candidate_logic", "no_midpoint_shortcut", False),
        ("output_edge_contract", "route_interpretation_allowed", True),
    ),
)
def test_rehashed_normative_claim_semantic_mutations_are_refused(
    tmp_path: Path,
    schema_root: Path,
    section: str,
    field: str,
    value: object,
) -> None:
    changed_model = json.loads(json.dumps(_MODEL))
    changed_section = changed_model[section]
    assert isinstance(changed_section, dict)
    changed_section[field] = value
    changed_bytes = json.dumps(changed_model, sort_keys=True).encode()
    contract_path = schema_root / "propagation-model.v1.yaml"
    contract_path.write_bytes(changed_bytes)

    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _materialize(
            output_root=tmp_path / f"changed-{section}-{field}",
            allowed_output_parent=tmp_path,
            schema_root=schema_root,
            propagation_contract_digest=hashlib.sha256(changed_bytes).hexdigest(),
        )

    assert refusal.value.reason_code == "invalid_propagation_identity"
