"""Complete frozen facet roots and exact protected metadata dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from ...client import positive_native_id
from ..facets.models import (
    FACET_SCHEMA,
    SCOPED_FACET_SCHEMA,
    SUPPORTED_DATASET_FACETS,
    NeotomaFacetPlan,
    NeotomaFacetScopeInputs,
)
from ..facets.replay import _control
from ..facets.scope import prepare_facet_parent_scope
from ..parent_scope import _roster
from ..receipts import _object, _read, _safe_root
from ..resources.models import DEVELOPMENT_ROLES, NeotomaResourceSpec
from ..resources.protocol import identity
from ..resources.replay import _same_json

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}
MAX_INPUT_BYTES = 32 * 1024 * 1024
MAX_SOURCE_BYTES = 768 * 1024 * 1024
MAX_SOURCE_FILES = 32768


def _digest(value: Any) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise ValueError("Linked evidence source digest is invalid")
    return value


def source_bindings(
    *,
    expected_roster_sha256: str,
    scope: NeotomaFacetScopeInputs,
    source_facets: Mapping[str, Path],
    legacy_rosters: Mapping[str, Path] | None = None,
) -> dict[str, Path]:
    """Use logical source identifiers so publications never encode checkout paths."""
    _digest(expected_roster_sha256)
    if not isinstance(scope, NeotomaFacetScopeInputs) or not isinstance(
        source_facets, Mapping
    ):
        raise ValueError("Complete linked source scope is required")
    if legacy_rosters is not None and not isinstance(legacy_rosters, Mapping):
        raise ValueError("Original linked roster resolver scope is malformed")
    result = {"roster": scope.roster_path}
    for digest, path in (legacy_rosters or {}).items():
        result["legacy_roster:" + _digest(digest)] = path
    if scope.alias_authority is not None:
        result["alias_authority"] = scope.alias_authority
    for digest, path in (scope.historical_metadata_parts or {}).items():
        result["historical:" + _digest(digest)] = path
    for kind, roots in (
        ("facet", source_facets),
        ("metadata", scope.metadata_captures),
    ):
        if not isinstance(roots, Mapping):
            raise ValueError("Linked source resolver scope is malformed")
        for digest, directory in sorted(roots.items()):
            _digest(digest)
            root = _safe_root(directory)
            members: list[Path] = []
            for path in root.iterdir():
                if len(result) + len(members) >= MAX_SOURCE_FILES:
                    raise ValueError(
                        "Linked source namespace exceeds its finite population"
                    )
                members.append(path)
            for path in sorted(members):
                if not path.is_file() or path.is_symlink():
                    raise ValueError("Linked source namespace contains a non-file")
                result[f"{kind}:{digest}:{path.name}"] = path
    if len(result) > MAX_SOURCE_FILES:
        raise ValueError("Linked source namespace exceeds its finite population")
    return result


def source_pins(
    bindings: Mapping[str, Path], *, _before_body_read: Callable[[], None] | None = None
) -> dict[str, dict[str, Any]]:
    """Hash bounded source buffers without decoding numerical predecessors again."""
    result = {}
    total = 0
    for key, path in sorted(bindings.items()):
        if path.suffix == ".body" and _before_body_read is not None:
            _before_body_read()
        raw = _read(path, min(MAX_INPUT_BYTES, MAX_SOURCE_BYTES - total))
        if path.suffix == ".body" and _before_body_read is not None:
            _before_body_read()
        total += len(raw)
        result[key] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    return result


def _pointer(value: Any, pointer: str) -> Any:
    for part in pointer.removeprefix("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _protected_contacts(
    proof: dict[str, Any],
    scope: NeotomaFacetScopeInputs,
) -> dict[str, Any]:
    contacts: dict[str, Any] = {}
    for parent in proof["parents"]:
        role = parent["effective_scope_role"]
        if role in DEVELOPMENT_ROLES:
            continue
        for witness in parent["metadata_sources"]:
            if "capture_manifest_sha256" not in witness:
                continue
            root = scope.metadata_captures[witness["capture_manifest_sha256"]]
            raw = _read(root / witness["body_file"], MAX_INPUT_BYTES)
            if sha256(raw).hexdigest() != witness["body_sha256"]:
                raise ValueError("Protected linked metadata source identity differs")
            native = _pointer(_object(raw), witness["json_pointer"])
            if positive_native_id(native.get("datasetid")) != parent["dataset_id"]:
                raise ValueError("Protected linked metadata dataset differs")
            rows = native.get("datasetpi")
            if rows is None:
                continue
            if not isinstance(rows, list):
                raise ValueError("Protected linked metadata PI population is malformed")
            for index, row in enumerate(rows):
                if not isinstance(row, dict) or "contactid" not in row:
                    raise ValueError("Protected linked PI native identity is missing")
                if row["contactid"] is None:
                    continue
                native_id = positive_native_id(row["contactid"])
                record = contacts.setdefault(
                    str(native_id),
                    {
                        "exposure_role": role,
                        "metadata_witnesses": [],
                    },
                )
                record["exposure_role"] = max(
                    (record["exposure_role"], role), key=_RANK.__getitem__
                )
                record["metadata_witnesses"].append(
                    {
                        **witness,
                        "root_dataset_id": parent["dataset_id"],
                        "native_contactid": native_id,
                        "inherited_exposure_role": role,
                        "json_pointer": witness["json_pointer"]
                        + f"/datasetpi/{index}/contactid",
                    }
                )
    return dict(sorted(contacts.items(), key=lambda row: int(row[0])))


def _capture_namespace(root: Path, manifest: dict[str, Any]) -> None:
    files = {"request-plan.json", "capture-manifest.json"}
    if manifest["schema_version"] == SCOPED_FACET_SCHEMA:
        files.add("parent-scope.json")
    for entry in manifest["facets"]:
        for reference in entry["attempts"]:
            for field in ("receipt_file", "body_file"):
                name = reference[field]
                if (
                    not isinstance(name, str)
                    or Path(name).name != name
                    or name in {"", ".", ".."}
                ):
                    raise ValueError("Linked source member name is malformed")
                files.add(name)
    seen = set()
    for path in root.iterdir():
        if path.name not in files or path.is_symlink() or not path.is_file():
            raise ValueError(
                "Linked capture namespace contains unclaimed source members"
            )
        seen.add(path.name)
    if seen != files:
        raise ValueError("Linked capture namespace is incomplete")


def authenticate_linked_root_metadata(
    *, expected_roster_sha256: str, scope: NeotomaFacetScopeInputs
) -> dict[str, Any]:
    """Authenticate current roots and protected PI metadata, never facet bodies or GETs."""
    try:
        _digest(expected_roster_sha256)
        if not isinstance(scope, NeotomaFacetScopeInputs):
            raise ValueError("Complete linked source scope is required")
        roster = _roster(scope.roster_path, expected_roster_sha256)
        resources = tuple(
            NeotomaResourceSpec(
                **{
                    key: row[key]
                    for key in (
                        "dataset_id",
                        "site_id",
                        "collection_unit_id",
                        "dataset_type",
                        "database",
                    )
                },
                exposure_role=row["exposure_roles"]["current"],
                metadata_sha256=row["metadata_locator"]["response_sha256"],
                metadata_pointer=row["metadata_locator"]["json_pointer"],
                versions=("current",),
            )
            for row in roster["resources"]
        )
        proof = prepare_facet_parent_scope(
            NeotomaFacetPlan(
                resources, expected_roster_sha256, SUPPORTED_DATASET_FACETS
            ),
            scope,
        )
        protected = _protected_contacts(proof, scope)
        roles = {
            row["dataset_id"]: row["effective_scope_role"] for row in proof["parents"]
        }
        roots = {resource.dataset_id: identity(resource) for resource in resources}
        expected = {
            f"dataset-{resource.dataset_id}-facet-{facet}-current"
            for resource in resources
            for facet in SUPPORTED_DATASET_FACETS
        }
        return {
            "roster": roster,
            "resources": resources,
            "proof": proof,
            "protected": protected,
            "roles": roles,
            "roots": roots,
            "expected": expected,
        }
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError("Malformed linked root metadata") from error


def authenticate_linked_source_scope(
    *,
    expected_roster_sha256: str,
    scope: NeotomaFacetScopeInputs,
    source_facets: Mapping[str, Path],
    legacy_rosters: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Require every frozen facet slot before a caller can select shared targets."""
    try:
        metadata = authenticate_linked_root_metadata(
            expected_roster_sha256=expected_roster_sha256, scope=scope
        )
        roster, resources, proof, protected, roles, roots, expected = (
            metadata[key]
            for key in (
                "roster",
                "resources",
                "proof",
                "protected",
                "roles",
                "roots",
                "expected",
            )
        )
        seen: set[str] = set()
        captures = {}
        original_rows: dict[str, dict[int, Any]] = {}
        if legacy_rosters is not None and not isinstance(legacy_rosters, Mapping):
            raise ValueError("Original linked roster resolver scope is malformed")
        if not isinstance(source_facets, Mapping) or not source_facets:
            raise ValueError("Complete linked source capture population is required")
        for digest, directory in sorted(source_facets.items()):
            source_root = _safe_root(directory)
            manifest, facet_plan, _, _ = _control(source_root, _digest(digest))
            _capture_namespace(source_root, manifest)
            legacy = manifest["schema_version"] == FACET_SCHEMA
            if legacy:
                original = facet_plan.roster_sha256
                if legacy_rosters is None or original not in legacy_rosters:
                    raise ValueError(
                        "Legacy linked source requires its original roster"
                    )
                if original not in original_rows:
                    original_rows[original] = {
                        row["dataset_id"]: row
                        for row in _roster(legacy_rosters[original], original)[
                            "resources"
                        ]
                    }
            keys = []
            for entry in manifest["facets"]:
                key = entry["facet_key"]
                root = entry["root_identity"]
                dataset = positive_native_id(root["dataset_id"])
                if key not in expected or key in seen or dataset not in roots:
                    raise ValueError(
                        "Linked frozen source facet scope is missing or duplicated"
                    )
                if legacy:
                    old = original_rows[facet_plan.roster_sha256].get(dataset)
                    if old is None:
                        raise ValueError(
                            "Legacy source root absent from original roster"
                        )
                    original_identity = {
                        key: old[key]
                        for key in (
                            "dataset_id",
                            "site_id",
                            "collection_unit_id",
                            "dataset_type",
                            "database",
                        )
                    }
                    original_identity.update(
                        exposure_role=old["exposure_roles"]["current"],
                        metadata_sha256=old["metadata_locator"]["response_sha256"],
                        metadata_pointer=old["metadata_locator"]["json_pointer"],
                    )
                    if not _same_json(root, original_identity):
                        raise ValueError(
                            "Legacy source root differs from original roster"
                        )
                if not _same_json(root, roots[dataset]):
                    raise ValueError("Linked native root differs from frozen roster")
                if (
                    entry["facet"] not in SUPPORTED_DATASET_FACETS
                    or key != f"dataset-{dataset}-facet-{entry['facet']}-current"
                ):
                    raise ValueError("Linked native facet identity differs")
                if roles[dataset] in DEVELOPMENT_ROLES:
                    if (
                        entry["terminal_status"]
                        != "received_complete_unqualified_facet"
                        or len(entry["attempts"]) != 1
                    ):
                        raise ValueError(
                            "Linked complete development source is unavailable"
                        )
                elif entry["attempts"] or entry["terminal_status"] not in {
                    "not_attempted_exposure_role",
                    "not_attempted_parent_scope",
                }:
                    raise ValueError("Protected linked source has transport attempts")
                seen.add(key)
                keys.append(key)
            captures[digest] = {
                "schema_version": manifest["schema_version"],
                "parent_scope_verification": "not_recorded_legacy_capture"
                if legacy
                else "authenticated_source_inputs",
                "original_roster_sha256": facet_plan.roster_sha256,
                "facet_keys": keys,
                "capture_utc_start": manifest["capture_utc_start"],
                "capture_utc_end": manifest["capture_utc_end"],
            }
        if set(legacy_rosters or {}) != set(original_rows):
            raise ValueError("Legacy original roster resolver population differs")
        if seen != expected:
            raise ValueError("Linked complete frozen facet scope population differs")
        return {
            "schema_version": "neotoma-linked-source-authority.v1",
            "roster_sha256": expected_roster_sha256,
            "resource_count": len(resources),
            "facet_slot_count": len(expected),
            "protected_contacts": protected,
            "root_identities": {
                str(key): value for key, value in sorted(roots.items())
            },
            "effective_parent_roles": {
                str(key): value for key, value in sorted(roles.items())
            },
            "source_captures": captures,
            "legacy_roster_sha256s": sorted(original_rows),
            "policy_sources": roster["policy_sources"],
            "parent_scope_sha256": sha256(
                json.dumps(
                    proof, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest(),
            "scientific_admission": "not_asserted",
        }
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError("Malformed complete linked source scope") from error


def validate_linked_authority(value: dict[str, Any]) -> None:
    """Reconcile owned metadata counts and roles without reopening source outcomes."""
    from ..receipts import _utc
    from ..resources.models import EXPOSURE_ROLES

    try:
        expected_fields = {
            "schema_version",
            "roster_sha256",
            "resource_count",
            "facet_slot_count",
            "protected_contacts",
            "root_identities",
            "effective_parent_roles",
            "source_captures",
            "legacy_roster_sha256s",
            "policy_sources",
            "parent_scope_sha256",
            "scientific_admission",
        }
        if (
            set(value) != expected_fields
            or value["schema_version"] != "neotoma-linked-source-authority.v1"
            or value["scientific_admission"] != "not_asserted"
        ):
            raise ValueError("Linked evidence authority fields differ")
        _digest(value["roster_sha256"])
        _digest(value["parent_scope_sha256"])
        roots, roles = value["root_identities"], value["effective_parent_roles"]
        if (
            not isinstance(roots, dict)
            or not roots
            or not isinstance(roles, dict)
            or set(roots) != set(roles)
        ):
            raise ValueError("Linked evidence authority root population differs")
        if (
            type(value["resource_count"]) is not int
            or value["resource_count"] != len(roots)
            or type(value["facet_slot_count"]) is not int
            or value["facet_slot_count"] != len(roots) * len(SUPPORTED_DATASET_FACETS)
        ):
            raise ValueError("Linked evidence authority slot account differs")
        expected: set[str] = set()
        for key, root in roots.items():
            native = positive_native_id(root["dataset_id"])
            if (
                str(native) != key
                or not isinstance(roles[key], str)
                or roles[key] not in EXPOSURE_ROLES
            ):
                raise ValueError(
                    "Linked evidence authority native root or role differs"
                )
            for field in ("site_id", "collection_unit_id"):
                positive_native_id(root[field])
            if (
                not isinstance(root["exposure_role"], str)
                or root["exposure_role"] not in EXPOSURE_ROLES
                or _RANK[roles[key]] < _RANK[root["exposure_role"]]
            ):
                raise ValueError("Linked evidence authority role was downgraded")
            expected.update(
                f"dataset-{native}-facet-{facet}-current"
                for facet in SUPPORTED_DATASET_FACETS
            )
        seen = set()
        if not isinstance(value["source_captures"], dict):
            raise ValueError("Linked evidence authority captures are malformed")
        for digest, capture in value["source_captures"].items():
            _digest(digest)
            if capture["schema_version"] not in {
                FACET_SCHEMA,
                SCOPED_FACET_SCHEMA,
            } or not isinstance(capture["facet_keys"], list):
                raise ValueError("Linked evidence source capture schema differs")
            expected_scope = (
                "not_recorded_legacy_capture"
                if capture["schema_version"] == FACET_SCHEMA
                else "authenticated_source_inputs"
            )
            if capture.get("parent_scope_verification") != expected_scope:
                raise ValueError("Linked evidence source scope epoch differs")
            _digest(capture["original_roster_sha256"])
            if _utc(capture["capture_utc_start"]) > _utc(capture["capture_utc_end"]):
                raise ValueError("Linked evidence source capture time differs")
            for key in capture["facet_keys"]:
                if not isinstance(key, str) or key not in expected or key in seen:
                    raise ValueError("Linked evidence source facet scope differs")
                seen.add(key)
        if seen != expected:
            raise ValueError(
                "Linked evidence authority complete slot population differs"
            )
        if not isinstance(value["protected_contacts"], dict):
            raise ValueError("Linked evidence protected metadata namespace differs")
        for key, contact in value["protected_contacts"].items():
            native = positive_native_id(int(key))
            witnesses = contact["metadata_witnesses"]
            if str(native) != key or not isinstance(witnesses, list) or not witnesses:
                raise ValueError("Linked protected metadata witness population differs")
            witness_roles = []
            for witness in witnesses:
                root_key = str(positive_native_id(witness["root_dataset_id"]))
                if (
                    root_key not in roles
                    or roles[root_key] in DEVELOPMENT_ROLES
                    or positive_native_id(witness["native_contactid"]) != native
                    or witness["inherited_exposure_role"] != roles[root_key]
                ):
                    raise ValueError(
                        "Linked protected native metadata ownership differs"
                    )
                for field in (
                    "capture_manifest_sha256",
                    "receipt_sha256",
                    "body_sha256",
                ):
                    _digest(witness[field])
                witness_roles.append(roles[root_key])
            if contact["exposure_role"] != max(witness_roles, key=_RANK.__getitem__):
                raise ValueError("Linked protected metadata role account differs")
        if not isinstance(value["legacy_roster_sha256s"], list) or len(
            set(value["legacy_roster_sha256s"])
        ) != len(value["legacy_roster_sha256s"]):
            raise ValueError("Linked original roster population differs")
        for digest in value["legacy_roster_sha256s"]:
            _digest(digest)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError) as error:
        raise ValueError("Malformed linked evidence authority") from error
