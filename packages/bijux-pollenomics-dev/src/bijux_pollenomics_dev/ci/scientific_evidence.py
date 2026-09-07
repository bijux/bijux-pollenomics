"""Materialize policy-owned scientific evidence required by hosted verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Never, cast

import yaml
from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationMaterializationResult,
    materialize_propagation_outputs,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    _CLASSIFICATION_AUTHORITY,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    _OUTPUT_NAMES as PROPAGATION_OUTPUT_NAMES,
)
from bijux_pollenomics.evidence.classification.audit_outputs import (
    ClassificationAuditMaterializationResult,
    ClassificationAuditOutputPaths,
    materialize_classification_audit,
)
from bijux_pollenomics.evidence.classification.audit_outputs.constants import (
    OUTPUT_NAMES as CLASSIFICATION_OUTPUT_NAMES,
)
from bijux_pollenomics.evidence.classification.neotoma import (
    build_neotoma_classification_accounting,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    read_validated_neotoma_relational_manifest,
)

JsonObject = dict[str, object]

_POLICY_PATH = Path("configs/release_evidence_policy.json")
_SCIENTIFIC_CONTRACT_ROOT = Path("configs/scientific-contracts")
_CLASSIFICATION_CONTRACT_NAME = "ecological-classification.v1.yaml"
_PROPAGATION_CONTRACT_NAME = "propagation-model.v1.yaml"
_RELATIONAL_ROOT = Path("data/neotoma/relational")
_CLASSIFICATION_PRODUCER_ROOT = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification"
)
_PROPAGATION_PRODUCER_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis"
_CLASSIFICATION_MANIFEST_SCHEMA = "classification-audit-manifest.v1"
_PROPAGATION_MANIFEST_SCHEMA = "propagation-output-manifest.v2"
_SCENARIO_SCHEMA = "propagation-sensitivity-summary.v1"


class ScientificEvidenceMaterializationError(RuntimeError):
    """Refuse an unsafe or policy-incoherent scientific materialization."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class ScientificEvidenceMaterializationResult:
    """Results for the ordered classification and propagation publications."""

    classification: ClassificationAuditMaterializationResult
    propagation: PropagationMaterializationResult

    def as_json(self) -> JsonObject:
        """Return a compact deterministic command result."""
        return {
            "schema_version": "scientific-evidence-materialization-result.v1",
            "classification": {
                "output_root": str(self.classification.output_root),
                "disposition": self.classification.disposition,
                "manifest_sha256": self.classification.manifest_sha256,
                "accepted_mapping_count": (self.classification.accepted_mapping_count),
                "concept_count": self.classification.concept_count,
                "observation_count": self.classification.observation_count,
            },
            "propagation": {
                "output_root": str(self.propagation.output_root),
                "disposition": self.propagation.disposition,
                "manifest_sha256": self.propagation.manifest_sha256,
                "eligible_event_count": self.propagation.eligible_event_count,
                "directed_candidate_count": (
                    self.propagation.primary_directed_candidate_count
                ),
            },
        }


@dataclass(frozen=True)
class _ProducerPolicy:
    artifact_identity: str
    producer_id: str
    producer_version: str
    source_paths: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class _MaterializationPolicy:
    classification_root: Path
    propagation_root: Path
    scenario_path: Path
    classification_producer: _ProducerPolicy
    propagation_producer: _ProducerPolicy
    propagation_contract_version: str
    propagation_contract_digest: str


def _refuse(reason_code: str, detail: str) -> Never:
    raise ScientificEvidenceMaterializationError(reason_code, detail)


def _mapping(value: object, label: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        _refuse("invalid_evidence_policy", f"{label} must be an object")
    return cast(JsonObject, value)


def _nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _refuse("invalid_evidence_policy", f"{label} must be non-empty text")
    return value


def _safe_relative_path(value: object, label: str) -> Path:
    text = _nonempty_text(value, label)
    pure = PurePosixPath(text)
    if (
        pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != text
    ):
        _refuse("unsafe_evidence_path", f"{label} is not a canonical relative path")
    return Path(*pure.parts)


def _reject_symlink_components(path: Path, *, boundary: Path) -> None:
    candidate = path
    while True:
        if candidate.exists() and candidate.is_symlink():
            _refuse("unsafe_evidence_path", f"path traverses a symlink: {candidate}")
        if candidate == boundary:
            return
        if candidate.parent == candidate:
            _refuse("unsafe_evidence_path", f"path escapes repository: {path}")
        candidate = candidate.parent


def _validated_repository_root(path: Path) -> Path:
    root = Path(path)
    if not root.is_absolute() or root == Path(root.anchor):
        _refuse(
            "unsafe_repository_root", "repository root must be a safe absolute path"
        )
    _reject_symlink_components(root, boundary=Path(root.anchor))
    if root.is_symlink() or not root.is_dir():
        _refuse("unsafe_repository_root", "repository root must be a directory")
    return root.resolve(strict=True)


def _prepare_output_parent(output_root: Path, *, repository_root: Path) -> None:
    parent = output_root.parent
    _reject_symlink_components(parent, boundary=repository_root)
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ScientificEvidenceMaterializationError(
            "unsafe_evidence_path", f"cannot create output namespace: {parent}"
        ) from error
    _reject_symlink_components(parent, boundary=repository_root)
    if not parent.is_dir() or not parent.resolve(strict=True).is_relative_to(
        repository_root
    ):
        _refuse("unsafe_evidence_path", f"invalid output namespace: {parent}")


def _read_regular_bytes(path: Path, *, repository_root: Path) -> bytes:
    _reject_symlink_components(path, boundary=repository_root)
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        _refuse("missing_evidence_input", f"required input is missing: {path}")
        raise AssertionError from error
    if not stat.S_ISREG(mode):
        _refuse("unsafe_evidence_path", f"input is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        _refuse("unreadable_evidence_input", f"cannot read input: {path}")
        raise AssertionError from error


def _json_object(path: Path, *, repository_root: Path, label: str) -> JsonObject:
    try:
        value = json.loads(_read_regular_bytes(path, repository_root=repository_root))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ScientificEvidenceMaterializationError(
            "invalid_evidence_input", f"{label} is not valid JSON: {path}"
        ) from error
    return _mapping(value, label)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _producer_digest(repository_root: Path, source_paths: Sequence[str]) -> str:
    records: list[JsonObject] = []
    for source_path in source_paths:
        relative = _safe_relative_path(source_path, "producer source path")
        payload = _read_regular_bytes(
            repository_root / relative,
            repository_root=repository_root,
        )
        records.append({"path": source_path, "sha256": _sha256(payload)})
    serialized = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return _sha256(serialized)


def _required_artifact(policy: JsonObject, identity: str) -> JsonObject:
    entries = policy.get("required_artifacts")
    if not isinstance(entries, list):
        _refuse("invalid_evidence_policy", "required_artifacts must be an array")
    matches = [
        _mapping(entry, f"required artifact {identity}")
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("identity") == identity
    ]
    if len(matches) != 1:
        _refuse(
            "invalid_evidence_policy",
            f"required artifact identity must occur exactly once: {identity}",
        )
    return matches[0]


def _embedded_producer(policy: JsonObject, identity: str) -> JsonObject:
    entries = policy.get("embedded_producer_identities")
    if not isinstance(entries, list):
        _refuse(
            "invalid_evidence_policy", "embedded_producer_identities must be an array"
        )
    matches = [
        _mapping(entry, f"embedded producer {identity}")
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("artifact_identity") == identity
    ]
    if len(matches) != 1:
        _refuse(
            "invalid_evidence_policy",
            f"embedded producer must occur exactly once: {identity}",
        )
    return matches[0]


def _bundle_inventory(policy: JsonObject, identity: str) -> tuple[str, ...]:
    entries = policy.get("bundle_inventories")
    if not isinstance(entries, list):
        _refuse("invalid_evidence_policy", "bundle_inventories must be an array")
    matches = [
        _mapping(entry, f"bundle inventory {identity}")
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("artifact_identity") == identity
    ]
    if len(matches) != 1:
        _refuse(
            "invalid_evidence_policy",
            f"bundle inventory must occur exactly once: {identity}",
        )
    filenames = matches[0].get("filenames")
    if not isinstance(filenames, list) or not all(
        isinstance(name, str) and Path(name).name == name for name in filenames
    ):
        _refuse("invalid_evidence_policy", f"invalid {identity} bundle inventory")
    names = cast(list[str], filenames)
    if names != sorted(names) or len(names) != len(set(names)):
        _refuse(
            "invalid_evidence_policy",
            f"{identity} bundle inventory must be unique and sorted",
        )
    return tuple(names)


def _artifact_manifest_root(
    repository_root: Path,
    artifact: JsonObject,
    *,
    identity: str,
    producer_path: str,
    producer_digest: str,
) -> Path:
    if (
        artifact.get("role")
        != ("classification" if identity == "classification" else "generated_output")
        or artifact.get("media_type") != "application/json"
        or artifact.get("producer_path") != producer_path
        or artifact.get("schema_identity_field") != "schema_version"
        or artifact.get("schema_version")
        != (
            _CLASSIFICATION_MANIFEST_SCHEMA
            if identity == "classification"
            else _PROPAGATION_MANIFEST_SCHEMA
        )
    ):
        _refuse("invalid_evidence_policy", f"{identity} artifact contract changed")
    relative = _safe_relative_path(artifact.get("path"), f"{identity} artifact path")
    if relative.name != "manifest.json":
        _refuse("invalid_evidence_policy", f"{identity} artifact is not a manifest")
    expected_prefix = Path("artifacts/execution-control") / identity
    if relative.parent.parent != expected_prefix:
        _refuse(
            "unsafe_evidence_path",
            f"{identity} bundle is outside its execution-control namespace",
        )
    if not relative.parent.name.endswith(f"-{producer_digest[:8]}"):
        _refuse(
            "invalid_evidence_identity",
            f"{identity} bundle path is not bound to the producer digest",
        )
    output_root = repository_root / relative.parent
    _reject_symlink_components(output_root.parent, boundary=repository_root)
    return output_root


def _parse_producer_policy(
    repository_root: Path,
    policy: JsonObject,
    *,
    identity: str,
) -> _ProducerPolicy:
    entry = _embedded_producer(policy, identity)
    source_paths = entry.get("source_paths")
    if not isinstance(source_paths, list) or not all(
        isinstance(path, str) and path for path in source_paths
    ):
        _refuse("invalid_evidence_policy", f"{identity} source_paths are invalid")
    paths = tuple(cast(list[str], source_paths))
    if len(paths) != len(set(paths)):
        _refuse("invalid_evidence_policy", f"{identity} source_paths are duplicated")
    return _ProducerPolicy(
        artifact_identity=identity,
        producer_id=_nonempty_text(entry.get("producer_id"), "producer_id"),
        producer_version=_nonempty_text(
            entry.get("producer_version"), "producer_version"
        ),
        source_paths=paths,
        digest=_producer_digest(repository_root, paths),
    )


def _load_materialization_policy(repository_root: Path) -> _MaterializationPolicy:
    policy = _json_object(
        repository_root / _POLICY_PATH,
        repository_root=repository_root,
        label="release evidence policy",
    )
    if (
        policy.get("schema_version") != "release-evidence-policy.v3"
        or policy.get("mode") != "product"
    ):
        _refuse("invalid_evidence_policy", "unsupported release evidence policy")
    classification_producer = _parse_producer_policy(
        repository_root, policy, identity="classification"
    )
    propagation_producer = _parse_producer_policy(
        repository_root, policy, identity="propagation"
    )
    if (
        classification_producer.producer_id != _CLASSIFICATION_AUTHORITY.producer_id
        or classification_producer.producer_version
        != _CLASSIFICATION_AUTHORITY.producer_version
        or f"sha256:{classification_producer.digest}"
        != _CLASSIFICATION_AUTHORITY.producer_digest
    ):
        _refuse(
            "invalid_classification_identity",
            "classification producer policy does not match product authority",
        )
    if (
        propagation_producer.producer_id != PROPAGATION_PRODUCER_ID
        or propagation_producer.producer_version != PROPAGATION_PRODUCER_VERSION
        or propagation_producer.source_paths != PROPAGATION_PRODUCER_SOURCE_PATHS
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation producer policy does not match product authority",
        )
    expected_classification_inventory = tuple(sorted(CLASSIFICATION_OUTPUT_NAMES))
    expected_propagation_inventory = tuple(sorted(PROPAGATION_OUTPUT_NAMES))
    if _bundle_inventory(policy, "classification") != expected_classification_inventory:
        _refuse("invalid_evidence_policy", "classification bundle inventory changed")
    if _bundle_inventory(policy, "propagation") != expected_propagation_inventory:
        _refuse("invalid_evidence_policy", "propagation bundle inventory changed")
    classification_root = _artifact_manifest_root(
        repository_root,
        _required_artifact(policy, "classification"),
        identity="classification",
        producer_path=_CLASSIFICATION_PRODUCER_ROOT,
        producer_digest=classification_producer.digest,
    )
    propagation_root = _artifact_manifest_root(
        repository_root,
        _required_artifact(policy, "propagation"),
        identity="propagation",
        producer_path=_PROPAGATION_PRODUCER_ROOT,
        producer_digest=propagation_producer.digest,
    )
    scenario = _required_artifact(policy, "scenario")
    scenario_relative = _safe_relative_path(scenario.get("path"), "scenario path")
    if (
        scenario.get("role") != "scenario"
        or scenario.get("media_type") != "application/json"
        or scenario.get("producer_path") != _PROPAGATION_PRODUCER_ROOT
        or scenario.get("schema_identity_field") != "schema_version"
        or scenario.get("schema_version") != _SCENARIO_SCHEMA
        or scenario_relative
        != propagation_root.relative_to(repository_root) / "sensitivity_summary.json"
    ):
        _refuse("invalid_evidence_policy", "propagation scenario contract changed")
    contract = _mapping(policy.get("propagation_contract"), "propagation_contract")
    digest = _nonempty_text(contract.get("sha256"), "propagation_contract.sha256")
    if not digest.startswith("sha256:") or len(digest) != 71:
        _refuse("invalid_evidence_policy", "propagation contract digest is invalid")
    version = _nonempty_text(
        contract.get("contract_version"), "propagation_contract.contract_version"
    )
    if contract.get("contract_id") != "bijux-pollenomics.propagation-model":
        _refuse("invalid_evidence_policy", "propagation contract identity changed")
    return _MaterializationPolicy(
        classification_root=classification_root,
        propagation_root=propagation_root,
        scenario_path=repository_root / scenario_relative,
        classification_producer=classification_producer,
        propagation_producer=propagation_producer,
        propagation_contract_version=version,
        propagation_contract_digest=digest.removeprefix("sha256:"),
    )


def _validated_yaml_contract(
    path: Path,
    *,
    repository_root: Path,
    contract_id: str,
    contract_version: str,
    expected_digest: str,
) -> None:
    payload = _read_regular_bytes(path, repository_root=repository_root)
    if _sha256(payload) != expected_digest:
        _refuse(
            "invalid_scientific_contract",
            f"scientific contract digest changed: {path.name}",
        )
    try:
        value = yaml.safe_load(payload)
    except yaml.YAMLError as error:
        raise ScientificEvidenceMaterializationError(
            "invalid_scientific_contract", f"scientific contract is invalid: {path}"
        ) from error
    contract = _mapping(value, f"scientific contract {path.name}")
    if (
        contract.get("contract_id") != contract_id
        or contract.get("contract_version") != contract_version
    ):
        _refuse(
            "invalid_scientific_contract",
            f"scientific contract identity changed: {path.name}",
        )


def _surface_rows(
    repository_root: Path,
    relational_root: Path,
    manifest: Mapping[str, object],
    surface_name: str,
) -> list[object]:
    surfaces = _mapping(manifest.get("surfaces"), "relational surfaces")
    surface = _mapping(surfaces.get(surface_name), f"surface {surface_name}")
    raw_parts = surface.get("parts")
    if not isinstance(raw_parts, list):
        _refuse("invalid_relational_manifest", f"surface parts missing: {surface_name}")
    rows: list[object] = []
    for raw_part in raw_parts:
        part = _mapping(raw_part, f"surface part {surface_name}")
        relative = _safe_relative_path(part.get("path"), f"{surface_name} part path")
        part_path = relational_root / relative
        part_bytes = _read_regular_bytes(part_path, repository_root=repository_root)
        expected_digest = part.get("sha256")
        if (
            not isinstance(expected_digest, str)
            or _sha256(part_bytes) != expected_digest
        ):
            _refuse(
                "invalid_relational_manifest",
                f"relational part changed after validation: {relative.as_posix()}",
            )
        try:
            part_value = json.loads(part_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ScientificEvidenceMaterializationError(
                "invalid_relational_manifest",
                f"relational part is not valid JSON: {relative.as_posix()}",
            ) from error
        payload = _mapping(part_value, f"relational part {relative.as_posix()}")
        part_rows = payload.get("rows")
        if not isinstance(part_rows, list):
            _refuse(
                "invalid_relational_manifest",
                f"relational part rows are invalid: {relative.as_posix()}",
            )
        if len(part_rows) != part.get("row_count"):
            _refuse(
                "invalid_relational_manifest",
                f"relational part count changed: {relative.as_posix()}",
            )
        rows.extend(part_rows)
    if len(rows) != surface.get("row_count"):
        _refuse(
            "invalid_relational_manifest",
            f"surface count changed after validation: {surface_name}",
        )
    return rows


def _classification_snapshot(
    repository_root: Path, relational_root: Path
) -> JsonObject:
    try:
        manifest = read_validated_neotoma_relational_manifest(relational_root)
    except (OSError, TypeError, ValueError) as error:
        raise ScientificEvidenceMaterializationError(
            "invalid_relational_manifest",
            "Neotoma relational materialization did not validate",
        ) from error
    return {
        "schema_version": manifest["relational_snapshot_schema_version"],
        "source_family": manifest["source_family"],
        "source_snapshot_id": manifest["source_snapshot_id"],
        "build_id": manifest["build_id"],
        "sites": _surface_rows(repository_root, relational_root, manifest, "sites"),
        "variables": _surface_rows(
            repository_root, relational_root, manifest, "variables"
        ),
        "observations": _surface_rows(
            repository_root, relational_root, manifest, "observations"
        ),
    }


def materialize_scientific_evidence(
    repository_root: Path,
) -> ScientificEvidenceMaterializationResult:
    """Materialize classification first, then its zero-accepted propagation refusal."""
    root = _validated_repository_root(repository_root)
    materialization_policy = _load_materialization_policy(root)
    contract_root = root / _SCIENTIFIC_CONTRACT_ROOT
    classification_contract_path = contract_root / _CLASSIFICATION_CONTRACT_NAME
    _validated_yaml_contract(
        classification_contract_path,
        repository_root=root,
        contract_id="bijux-pollenomics.ecological-classification",
        contract_version=_CLASSIFICATION_AUTHORITY.contract_version,
        expected_digest=_CLASSIFICATION_AUTHORITY.contract_digest.removeprefix(
            "sha256:"
        ),
    )
    propagation_contract_path = contract_root / _PROPAGATION_CONTRACT_NAME
    _validated_yaml_contract(
        propagation_contract_path,
        repository_root=root,
        contract_id="bijux-pollenomics.propagation-model",
        contract_version=materialization_policy.propagation_contract_version,
        expected_digest=materialization_policy.propagation_contract_digest,
    )
    _prepare_output_parent(
        materialization_policy.classification_root,
        repository_root=root,
    )
    _prepare_output_parent(
        materialization_policy.propagation_root,
        repository_root=root,
    )
    relational_root = (root / _RELATIONAL_ROOT).absolute()
    snapshot = _classification_snapshot(root, relational_root)
    accounting = build_neotoma_classification_accounting(snapshot)
    classification = materialize_classification_audit(
        accounting,
        paths=ClassificationAuditOutputPaths.under(
            materialization_policy.classification_root
        ),
        allowed_output_parent=materialization_policy.classification_root.parent,
        classification_contract_version=_CLASSIFICATION_AUTHORITY.contract_version,
        classification_contract_digest=_CLASSIFICATION_AUTHORITY.contract_digest,
        classification_producer_id=(
            materialization_policy.classification_producer.producer_id
        ),
        classification_producer_version=(
            materialization_policy.classification_producer.producer_version
        ),
        classification_producer_digest=(
            f"sha256:{materialization_policy.classification_producer.digest}"
        ),
    )
    if (
        classification.manifest_sha256 != _CLASSIFICATION_AUTHORITY.manifest_sha256
        or classification.accepted_mapping_count
        != _CLASSIFICATION_AUTHORITY.accepted_mapping_count
    ):
        _refuse(
            "invalid_classification_authority",
            "materialized classification does not match the product authority",
        )
    if classification.accepted_mapping_count != 0:
        _refuse(
            "accepted_classification_events_not_materialized",
            "accepted classification mappings require an explicit event producer",
        )
    propagation = materialize_propagation_outputs(
        (),
        output_root=materialization_policy.propagation_root,
        allowed_output_parent=materialization_policy.propagation_root.parent,
        schema_root=contract_root.absolute(),
        classification_bundle_root=materialization_policy.classification_root,
        propagation_contract_path=propagation_contract_path.absolute(),
        repository_root=root,
        build_id=_CLASSIFICATION_AUTHORITY.build_id,
        classification_contract_version=_CLASSIFICATION_AUTHORITY.contract_version,
        classification_review_digest=classification.manifest_sha256,
        accepted_classification_mapping_count=0,
        propagation_contract_version=(
            materialization_policy.propagation_contract_version
        ),
        propagation_contract_digest=materialization_policy.propagation_contract_digest,
        propagation_producer_id=materialization_policy.propagation_producer.producer_id,
        propagation_producer_version=(
            materialization_policy.propagation_producer.producer_version
        ),
        propagation_producer_digest=(
            materialization_policy.propagation_producer.digest
        ),
    )
    if materialization_policy.scenario_path != (
        propagation.output_root / "sensitivity_summary.json"
    ):
        _refuse(
            "invalid_evidence_policy",
            "materialized propagation scenario does not match policy path",
        )
    return ScientificEvidenceMaterializationResult(classification, propagation)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the hosted materializer from explicit repository identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        result = materialize_scientific_evidence(arguments.repository_root)
    except ScientificEvidenceMaterializationError as error:
        print(f"{error.reason_code}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result.as_json(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
