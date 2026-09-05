"""Loading and validation of the governed release-evidence policy."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from .codec import (
    _canonical_json,
    _mapping,
    _mapping_list,
    _require_digest,
    _require_identity,
    _require_unique,
    _string_field,
    _string_items,
)
from .models import (
    ArtifactRole,
    ReleaseEvidenceError,
    _ARTIFACT_ROLES,
    _ArtifactOwnershipRule,
    _BundleInventory,
    _EmbeddedProducerIdentity,
    _PropagationContractIdentity,
    _RELEASE_POLICY_PATH,
    _ReleaseEvidencePolicy,
    _RequiredArtifact,
    _RequiredReconciliation,
)
from .repository import _path_has_prefix, _read_repository_file, _relative_path


def _load_release_evidence_policy(root: Path) -> _ReleaseEvidencePolicy:
    payload = _read_repository_file(root, _RELEASE_POLICY_PATH)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate release policy field: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            "release evidence policy is not valid JSON"
        ) from error
    record = _mapping(value, "release evidence policy")
    if payload != _canonical_json(record) + b"\n":
        raise ReleaseEvidenceError("release evidence policy is not canonical JSON")
    if set(record) != {
        "schema_version",
        "mode",
        "recording_authority_path",
        "authorized_producer_paths",
        "artifact_ownership",
        "required_artifacts",
        "embedded_producer_identities",
        "bundle_inventories",
        "allowed_cross_role_digest_aliases",
        "required_gate_ids",
        "governed_request_artifact_ids",
        "propagation_contract",
        "required_reconciliations",
    }:
        raise ReleaseEvidenceError("release evidence policy fields are invalid")
    if record["schema_version"] != "release-evidence-policy.v3":
        raise ReleaseEvidenceError("unsupported release evidence policy schema")
    mode = _string_field(record, "mode")
    if mode not in {"product", "fixture"}:
        raise ReleaseEvidenceError("invalid release evidence policy mode")
    if mode == "fixture" and (root / ".git").exists():
        raise ReleaseEvidenceError(
            "fixture release policy is forbidden in a Git worktree"
        )

    authorized = tuple(_string_items(record, "authorized_producer_paths"))
    if not authorized or list(authorized) != sorted(authorized):
        raise ReleaseEvidenceError(
            "authorized producer paths must be non-empty and sorted"
        )
    _require_unique(authorized, "authorized producer path")
    for path in authorized:
        _relative_path(path)
    recording_authority_path = _string_field(record, "recording_authority_path")
    if recording_authority_path not in authorized:
        raise ReleaseEvidenceError("recording authority must be an authorized producer")

    ownership: list[_ArtifactOwnershipRule] = []
    ownership_keys: list[str] = []
    for item in _mapping_list(record, "artifact_ownership"):
        if set(item) != {"artifact_role", "artifact_path_prefix", "producer_path"}:
            raise ReleaseEvidenceError("artifact ownership policy fields are invalid")
        role = _string_field(item, "artifact_role")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid artifact ownership role: {role}")
        prefix = _string_field(item, "artifact_path_prefix")
        producer_path = _string_field(item, "producer_path")
        _relative_path(prefix)
        _relative_path(producer_path)
        if producer_path not in authorized:
            raise ReleaseEvidenceError(
                f"artifact ownership names an unauthorized producer: {producer_path}"
            )
        ownership.append(
            _ArtifactOwnershipRule(
                artifact_role=cast(ArtifactRole, role),
                artifact_path_prefix=prefix,
                producer_path=producer_path,
            )
        )
        ownership_keys.append(f"{prefix}\0{role}")
    if not ownership:
        raise ReleaseEvidenceError("artifact ownership policy must not be empty")
    _require_unique(ownership_keys, "artifact ownership rule")
    if ownership_keys != sorted(ownership_keys):
        raise ReleaseEvidenceError("artifact ownership rules must be sorted")

    required_artifacts: list[_RequiredArtifact] = []
    required_artifact_identities: list[str] = []
    required_artifact_paths: list[str] = []
    for item in _mapping_list(record, "required_artifacts"):
        if set(item) != {
            "identity",
            "role",
            "path",
            "media_type",
            "schema_version",
            "schema_identity_field",
            "producer_path",
            "required_config_identities",
            "required_parent_identities",
            "required_embedded_input_paths",
        }:
            raise ReleaseEvidenceError("required artifact policy fields are invalid")
        identity = _string_field(item, "identity")
        role = _string_field(item, "role")
        path = _string_field(item, "path")
        media_type = _string_field(item, "media_type")
        schema_version = _string_field(item, "schema_version")
        raw_schema_identity_field = item["schema_identity_field"]
        if raw_schema_identity_field not in {
            None,
            "$schema",
            "schema",
            "schema_version",
        }:
            raise ReleaseEvidenceError(
                f"required artifact schema identity field is invalid: {identity}"
            )
        raw_producer_path = item["producer_path"]
        if raw_producer_path is not None and not isinstance(raw_producer_path, str):
            raise ReleaseEvidenceError(
                f"required artifact producer path is invalid: {identity}"
            )
        required_producer_path = raw_producer_path
        config_identities = tuple(_string_items(item, "required_config_identities"))
        parent_identities = tuple(_string_items(item, "required_parent_identities"))
        embedded_input_paths = tuple(
            _string_items(item, "required_embedded_input_paths")
        )
        _require_identity(identity, "required artifact identity")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid required artifact role: {role}")
        _relative_path(path)
        if not media_type.strip() or not schema_version.strip():
            raise ReleaseEvidenceError(
                f"required artifact lacks media/schema identity: {identity}"
            )
        if (
            required_producer_path is not None
            and required_producer_path not in authorized
        ):
            raise ReleaseEvidenceError(
                f"required artifact names an unauthorized producer: {identity}"
            )
        if list(config_identities) != sorted(config_identities):
            raise ReleaseEvidenceError(
                f"required config identities are not sorted: {identity}"
            )
        _require_unique(config_identities, "required config identity")
        if list(parent_identities) != sorted(parent_identities):
            raise ReleaseEvidenceError(
                f"required parent identities are not sorted: {identity}"
            )
        _require_unique(parent_identities, "required parent identity")
        if list(embedded_input_paths) != sorted(embedded_input_paths):
            raise ReleaseEvidenceError(
                f"required embedded input paths are not sorted: {identity}"
            )
        _require_unique(embedded_input_paths, "required embedded input path")
        for embedded_path in embedded_input_paths:
            _relative_path(embedded_path)
        required_artifacts.append(
            _RequiredArtifact(
                identity=identity,
                role=cast(ArtifactRole, role),
                path=path,
                media_type=media_type,
                schema_version=schema_version,
                schema_identity_field=raw_schema_identity_field,
                producer_path=required_producer_path,
                required_config_identities=config_identities,
                required_parent_identities=parent_identities,
                required_embedded_input_paths=embedded_input_paths,
            )
        )
        required_artifact_identities.append(identity)
        required_artifact_paths.append(path)
    if not required_artifacts:
        raise ReleaseEvidenceError("required artifact inventory must not be empty")
    _require_unique(required_artifact_identities, "required artifact identity")
    _require_unique(required_artifact_paths, "required artifact path")
    if required_artifact_identities != sorted(required_artifact_identities):
        raise ReleaseEvidenceError("required artifacts must be sorted by identity")
    known_required = set(required_artifact_identities)
    for requirement in required_artifacts:
        unknown_configs = set(requirement.required_config_identities) - known_required
        if unknown_configs:
            raise ReleaseEvidenceError(
                f"required artifact has unknown config identities: {requirement.identity}"
            )
        unknown_parents = set(requirement.required_parent_identities) - known_required
        if (
            unknown_parents
            or requirement.identity in requirement.required_parent_identities
        ):
            raise ReleaseEvidenceError(
                f"required artifact has unknown/self parent identities: {requirement.identity}"
            )

    embedded_producers: list[_EmbeddedProducerIdentity] = []
    for item in _mapping_list(record, "embedded_producer_identities"):
        if set(item) != {
            "artifact_identity",
            "producer_artifact_identity",
            "producer_id",
            "producer_version",
            "id_field",
            "version_field",
            "digest_field",
            "digest_prefix",
            "source_paths",
        }:
            raise ReleaseEvidenceError(
                "embedded producer identity policy fields are invalid"
            )
        artifact_identity = _string_field(item, "artifact_identity")
        producer_artifact_identity = _string_field(item, "producer_artifact_identity")
        producer_id = _string_field(item, "producer_id")
        producer_version = _string_field(item, "producer_version")
        id_field = _string_field(item, "id_field")
        version_field = _string_field(item, "version_field")
        digest_field = _string_field(item, "digest_field")
        digest_prefix = _string_field(item, "digest_prefix")
        source_paths = tuple(_string_items(item, "source_paths"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown artifact identity"
            )
        if producer_artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown producer artifact"
            )
        producer_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == producer_artifact_identity
        )
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            producer_requirement.role != "producer"
            or artifact_requirement.producer_path != producer_requirement.path
        ):
            raise ReleaseEvidenceError(
                "embedded producer does not match artifact ownership"
            )
        for value, field_name in (
            (producer_id, "embedded producer id"),
            (producer_version, "embedded producer version"),
            (id_field, "embedded producer id field"),
            (version_field, "embedded producer version field"),
            (digest_field, "embedded producer digest field"),
        ):
            _require_identity(value, field_name)
        if digest_prefix not in {"", "sha256:"}:
            raise ReleaseEvidenceError("embedded producer digest prefix is invalid")
        if not source_paths:
            raise ReleaseEvidenceError("embedded producer source closure is empty")
        _require_unique(source_paths, "embedded producer source path")
        for source_path in source_paths:
            _relative_path(source_path)
        if not any(
            _path_has_prefix(source_path, producer_requirement.path)
            for source_path in source_paths
        ):
            raise ReleaseEvidenceError(
                "embedded producer closure does not include its owned source tree"
            )
        embedded_producers.append(
            _EmbeddedProducerIdentity(
                artifact_identity=artifact_identity,
                producer_artifact_identity=producer_artifact_identity,
                producer_id=producer_id,
                producer_version=producer_version,
                id_field=id_field,
                version_field=version_field,
                digest_field=digest_field,
                digest_prefix=digest_prefix,
                source_paths=source_paths,
            )
        )
    embedded_artifact_identities = [
        item.artifact_identity for item in embedded_producers
    ]
    _require_unique(embedded_artifact_identities, "embedded producer artifact identity")
    if embedded_artifact_identities != sorted(embedded_artifact_identities):
        raise ReleaseEvidenceError(
            "embedded producer identities must be sorted by artifact identity"
        )

    bundle_inventories: list[_BundleInventory] = []
    for item in _mapping_list(record, "bundle_inventories"):
        if set(item) != {"artifact_identity", "filenames"}:
            raise ReleaseEvidenceError("bundle inventory policy fields are invalid")
        artifact_identity = _string_field(item, "artifact_identity")
        filenames = tuple(_string_items(item, "filenames"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError("bundle inventory names an unknown artifact")
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            artifact_requirement.media_type != "application/json"
            or PurePosixPath(artifact_requirement.path).name != "manifest.json"
        ):
            raise ReleaseEvidenceError(
                "bundle inventory artifact is not a JSON manifest"
            )
        if not filenames or list(filenames) != sorted(filenames):
            raise ReleaseEvidenceError(
                "bundle inventory filenames must be non-empty and sorted"
            )
        _require_unique(filenames, "bundle inventory filename")
        for filename in filenames:
            pure_filename = _relative_path(filename)
            if len(pure_filename.parts) != 1 or filename == "manifest.json":
                raise ReleaseEvidenceError("bundle inventory filename is unsafe")
        bundle_inventories.append(
            _BundleInventory(
                artifact_identity=artifact_identity,
                filenames=filenames,
            )
        )
    bundle_artifact_identities = [item.artifact_identity for item in bundle_inventories]
    _require_unique(bundle_artifact_identities, "bundle inventory artifact identity")
    if bundle_artifact_identities != sorted(bundle_artifact_identities):
        raise ReleaseEvidenceError(
            "bundle inventories must be sorted by artifact identity"
        )

    governed_request_artifact_ids = _string_items(
        record, "governed_request_artifact_ids"
    )
    if governed_request_artifact_ids != sorted(governed_request_artifact_ids):
        raise ReleaseEvidenceError("governed request artifact IDs must be sorted")
    _require_unique(governed_request_artifact_ids, "governed request artifact ID")
    if set(governed_request_artifact_ids) - known_required:
        raise ReleaseEvidenceError("governed request artifact IDs must be known")

    propagation_contract_record = _mapping(
        record["propagation_contract"], "propagation contract identity"
    )
    if set(propagation_contract_record) != {
        "contract_id",
        "contract_version",
        "sha256",
        "default_scenario",
    }:
        raise ReleaseEvidenceError("propagation contract identity fields are invalid")
    default_scenario = _mapping(
        propagation_contract_record["default_scenario"],
        "default propagation scenario",
    )
    if set(default_scenario) != {
        "scenario_id",
        "maximum_distance_km",
        "maximum_lag_years",
    }:
        raise ReleaseEvidenceError("default propagation scenario fields are invalid")
    propagation_digest = _string_field(propagation_contract_record, "sha256")
    _require_digest(propagation_digest, "propagation contract digest")
    contract_id = _string_field(propagation_contract_record, "contract_id")
    contract_version = _string_field(propagation_contract_record, "contract_version")
    scenario_id = _string_field(default_scenario, "scenario_id")
    _require_identity(contract_id, "propagation contract ID")
    _require_identity(contract_version, "propagation contract version")
    _require_identity(scenario_id, "default propagation scenario ID")
    maximum_distance_km = default_scenario["maximum_distance_km"]
    maximum_lag_years = default_scenario["maximum_lag_years"]
    if (
        isinstance(maximum_distance_km, bool)
        or not isinstance(maximum_distance_km, (int, float))
        or isinstance(maximum_lag_years, bool)
        or not isinstance(maximum_lag_years, (int, float))
        or maximum_distance_km <= 0
        or maximum_lag_years <= 0
    ):
        raise ReleaseEvidenceError("default propagation thresholds are invalid")
    propagation_contract = _PropagationContractIdentity(
        contract_id=contract_id,
        contract_version=contract_version,
        output_digest=propagation_digest,
        scenario_id=scenario_id,
        maximum_distance_km=float(maximum_distance_km),
        maximum_lag_years=float(maximum_lag_years),
    )

    allowed_aliases: set[frozenset[str]] = set()
    for item in _mapping_list(record, "allowed_cross_role_digest_aliases"):
        if set(item) != {"artifact_identities"}:
            raise ReleaseEvidenceError("digest alias policy fields are invalid")
        identities = _string_items(item, "artifact_identities")
        if len(identities) != 2 or identities != sorted(identities):
            raise ReleaseEvidenceError(
                "digest alias policy requires two sorted artifact identities"
            )
        pair = frozenset(identities)
        if not pair <= known_required:
            raise ReleaseEvidenceError("digest alias policy names unknown artifacts")
        if pair in allowed_aliases:
            raise ReleaseEvidenceError("duplicate digest alias policy")
        allowed_aliases.add(pair)

    required_gate_ids = tuple(_string_items(record, "required_gate_ids"))
    if not required_gate_ids or list(required_gate_ids) != sorted(required_gate_ids):
        raise ReleaseEvidenceError("required gate IDs must be non-empty and sorted")
    _require_unique(required_gate_ids, "required gate ID")
    for gate_id in required_gate_ids:
        _require_identity(gate_id, "required gate ID")

    required: list[_RequiredReconciliation] = []
    for item in _mapping_list(record, "required_reconciliations"):
        if set(item) != {
            "source",
            "entity",
            "dimension",
            "scope_values",
            "derivation_adapter",
            "derivation_metric",
            "unavailable_status",
            "unavailable_reason_code",
        }:
            raise ReleaseEvidenceError(
                "required reconciliation policy fields are invalid"
            )
        source = _string_field(item, "source")
        entity = _string_field(item, "entity")
        dimension = _string_field(item, "dimension")
        derivation_adapter = _string_field(item, "derivation_adapter")
        derivation_metric = _string_field(item, "derivation_metric")
        unavailable_status = _string_field(item, "unavailable_status")
        unavailable_reason_code = _string_field(item, "unavailable_reason_code")
        if dimension not in {"country", "scope"}:
            raise ReleaseEvidenceError("invalid required reconciliation dimension")
        if derivation_adapter not in {
            "classification_observation_memberships",
            "country_coverage",
            "neotoma_relational_reconciliation",
            "propagation_primary_reconciliation",
            "sead_chronology_claims",
            "unavailable",
        }:
            raise ReleaseEvidenceError("invalid reconciliation derivation adapter")
        if unavailable_status not in {"unavailable", "refused"}:
            raise ReleaseEvidenceError("invalid reconciliation unavailable status")
        _require_identity(derivation_metric, "reconciliation derivation metric")
        _require_identity(
            unavailable_reason_code, "reconciliation unavailable reason code"
        )
        raw_scope_values = _mapping(item["scope_values"], "scope values")
        scope_values: list[tuple[str, tuple[str, ...]]] = []
        for key, values in sorted(raw_scope_values.items()):
            if (
                not isinstance(key, str)
                or not isinstance(values, list)
                or any(not isinstance(value, str) for value in values)
            ):
                raise ReleaseEvidenceError("scope values must be string arrays")
            typed_values = tuple(cast(list[str], values))
            if not typed_values or list(typed_values) != sorted(typed_values):
                raise ReleaseEvidenceError("scope values must be non-empty and sorted")
            _require_unique(typed_values, "scope value")
            scope_values.append((key, typed_values))
        if dimension == "country" and scope_values:
            raise ReleaseEvidenceError("country requirement cannot define scope values")
        if dimension == "scope" and not scope_values:
            raise ReleaseEvidenceError("scope requirement must define scope values")
        _require_identity(source, "required reconciliation source")
        _require_identity(entity, "required reconciliation entity")
        required.append(
            _RequiredReconciliation(
                source=source,
                entity=entity,
                dimension=cast(Literal["country", "scope"], dimension),
                scope_values=tuple(scope_values),
                derivation_adapter=derivation_adapter,
                derivation_metric=derivation_metric,
                unavailable_status=cast(
                    Literal["unavailable", "refused"], unavailable_status
                ),
                unavailable_reason_code=unavailable_reason_code,
            )
        )
    if not required:
        raise ReleaseEvidenceError("required reconciliation policy must not be empty")
    _require_unique(
        (f"{item.source}\0{item.entity}" for item in required),
        "required reconciliation",
    )
    if [(item.source, item.entity) for item in required] != sorted(
        (item.source, item.entity) for item in required
    ):
        raise ReleaseEvidenceError("required reconciliations must be sorted")

    return _ReleaseEvidencePolicy(
        mode=mode,
        recording_authority_path=recording_authority_path,
        authorized_producer_paths=authorized,
        artifact_ownership=tuple(ownership),
        required_artifacts=tuple(required_artifacts),
        embedded_producer_identities=tuple(embedded_producers),
        bundle_inventories=tuple(bundle_inventories),
        allowed_cross_role_digest_aliases=frozenset(allowed_aliases),
        required_gate_ids=frozenset(required_gate_ids),
        governed_request_artifact_ids=frozenset(governed_request_artifact_ids),
        propagation_contract=propagation_contract,
        required_reconciliations=tuple(required),
        output_digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
    )
