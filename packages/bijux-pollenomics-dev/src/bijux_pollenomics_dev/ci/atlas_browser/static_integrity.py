"""Content and provider-policy audit for a published static atlas."""

from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path
import re
from typing import cast

from .contracts import AtlasBrowserContractError, AtlasCandidate, AtlasScope, JsonObject

_ASSET_FIELDS = (
    "domain",
    "sha256",
    "payload_sha256",
    "decoded_byte_count",
    "byte_count",
    "record_count",
    "layer_index",
    "layer_key",
    "layer_kind",
    "country_keys",
    "bounds",
    "time_min_bp",
    "time_max_bp",
    "untimed_record_count",
    "scientific_signal_ids",
)
_ASSET_DOMAINS = frozenset(
    {"provenance", "nodes", "details", "edges", "sequences", "indexes"}
)
_MAX_SAFE_INTEGER = 9_007_199_254_740_991
_FORBIDDEN_PROVIDER_MARKERS = (
    "cartocdn.com",
    "api_key_required",
    "api key required",
    "apikey=",
    "api_key=",
    "access_token=",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: object, *, label: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise AtlasBrowserContractError(f"{label} must be an object")
    return cast(JsonObject, value)


def _nonnegative_integer(value: object, *, label: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > _MAX_SAFE_INTEGER
    ):
        raise AtlasBrowserContractError(f"{label} must be a non-negative safe integer")
    return value


def _positive_integer(value: object, *, label: str) -> int:
    numeric = _nonnegative_integer(value, label=label)
    if numeric == 0:
        raise AtlasBrowserContractError(f"{label} must be a positive safe integer")
    return numeric


def _finite_number(value: object, *, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < -_MAX_SAFE_INTEGER
        or value > _MAX_SAFE_INTEGER
    ):
        raise AtlasBrowserContractError(f"{label} must be a finite safe number")
    return float(value)


def _validate_asset_counts_and_time(asset: JsonObject, *, sequence: int) -> None:
    record_count = _nonnegative_integer(
        asset["record_count"], label=f"manifest asset row {sequence} record_count"
    )
    _positive_integer(
        asset["decoded_byte_count"],
        label=f"manifest asset row {sequence} decoded_byte_count",
    )
    _nonnegative_integer(
        asset["byte_count"], label=f"manifest asset row {sequence} byte_count"
    )
    is_node_asset = asset["domain"] == "nodes"
    untimed = asset["untimed_record_count"]
    if is_node_asset:
        untimed_count = _nonnegative_integer(
            untimed,
            label=f"manifest asset row {sequence} untimed_record_count",
        )
        if untimed_count > record_count:
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} untimed_record_count exceeds record_count"
            )
    elif untimed is not None:
        raise AtlasBrowserContractError(
            f"manifest asset row {sequence} non-node untimed_record_count must be null"
        )
    minimum = asset["time_min_bp"]
    maximum = asset["time_max_bp"]
    if (minimum is None) != (maximum is None):
        raise AtlasBrowserContractError(
            f"manifest asset row {sequence} has asymmetric BP bounds"
        )
    if minimum is not None:
        younger = _finite_number(
            minimum, label=f"manifest asset row {sequence} time_min_bp"
        )
        older = _finite_number(
            maximum, label=f"manifest asset row {sequence} time_max_bp"
        )
        if younger > older:
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} BP bounds are reversed"
            )
    if is_node_asset:
        all_records_are_untimed = untimed_count == record_count
        if (minimum is None) != all_records_are_untimed:
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} BP bounds contradict untimed_record_count"
            )
    elif minimum is not None:
        raise AtlasBrowserContractError(
            f"manifest asset row {sequence} non-node BP bounds must be null"
        )


def _assets(manifest: JsonObject) -> tuple[JsonObject, ...]:
    table = _mapping(manifest.get("assets"), label="manifest.assets")
    if table.get("fields") != list(_ASSET_FIELDS):
        raise AtlasBrowserContractError("manifest asset fields are not canonical")
    raw_records = table.get("records")
    if not isinstance(raw_records, list):
        raise AtlasBrowserContractError("manifest asset records must be an array")
    table_record_count = _nonnegative_integer(
        table.get("record_count"), label="manifest asset record_count"
    )
    if table_record_count != len(raw_records):
        raise AtlasBrowserContractError("manifest asset record_count is inconsistent")
    assets: list[JsonObject] = []
    for sequence, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, list) or len(raw_record) != len(_ASSET_FIELDS):
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} is malformed"
            )
        asset = dict(zip(_ASSET_FIELDS, raw_record, strict=True))
        domain = asset["domain"]
        digest = asset["sha256"]
        if domain not in _ASSET_DOMAINS or not isinstance(digest, str):
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} identity is malformed"
            )
        _validate_asset_counts_and_time(asset, sequence=sequence)
        asset["path"] = (
            f"{manifest['scope_slug']}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"
        )
        assets.append(asset)
    return tuple(assets)


def audit_static_atlas(
    repository_root: Path,
    scope: AtlasScope,
    candidate: AtlasCandidate,
) -> JsonObject:
    """Verify every declared byte, manifest budget, identity, and keyless provider."""
    root = repository_root.resolve()
    document_path = root / scope.document
    manifest_path = root / scope.manifest
    try:
        document = document_path.read_bytes()
        manifest_bytes = manifest_path.read_bytes()
        manifest = _mapping(
            json.loads(manifest_bytes.decode("utf-8")), label="manifest"
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasBrowserContractError(
            f"cannot load static atlas scope: {scope.name}"
        ) from error
    if manifest.get("schema_version") != "atlas-static-bootstrap.v2":
        raise AtlasBrowserContractError("manifest schema_version is unsupported")
    if manifest.get("scope_slug") != scope.name:
        raise AtlasBrowserContractError("manifest scope_slug does not match the plan")
    if manifest.get("build_id") != candidate.build_id:
        raise AtlasBrowserContractError(
            "manifest build_id does not match the candidate"
        )
    if candidate.build_id.encode() not in document:
        raise AtlasBrowserContractError(
            "document does not embed the candidate build_id"
        )
    lower_document = document.lower()
    forbidden = [
        marker
        for marker in _FORBIDDEN_PROVIDER_MARKERS
        if marker.encode() in lower_document
    ]
    if forbidden:
        raise AtlasBrowserContractError(
            f"document contains forbidden provider markers: {forbidden}"
        )
    if b"https://tile.openstreetmap.org/{z}/{x}/{y}.png" not in document:
        raise AtlasBrowserContractError(
            "document does not use the keyless OSM endpoint"
        )
    assets = _assets(manifest)
    output_dir = document_path.parent
    inventory: list[JsonObject] = []
    total_bytes = 0
    for asset in assets:
        path = output_dir / str(asset["path"])
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise AtlasBrowserContractError(
                f"declared asset is absent: {path}"
            ) from error
        digest = _sha256(payload)
        if digest != asset["sha256"]:
            raise AtlasBrowserContractError(
                f"declared asset digest mismatch: {asset['path']}"
            )
        if len(payload) != asset["byte_count"]:
            raise AtlasBrowserContractError(
                f"declared asset byte_count mismatch: {asset['path']}"
            )
        total_bytes += len(payload)
        inventory.append(
            {
                "path": asset["path"],
                "byte_count": len(payload),
                "sha256": digest,
                "integrity": "sha256-"
                + base64.b64encode(bytes.fromhex(digest)).decode("ascii"),
            }
        )
    budgets = _mapping(manifest.get("budgets"), label="manifest.budgets")
    max_files = _nonnegative_integer(
        budgets.get("static_assets_max_files"), label="static asset file budget"
    )
    max_bytes = _nonnegative_integer(
        budgets.get("static_assets_max_bytes"), label="static asset byte budget"
    )
    if len(assets) > max_files:
        raise AtlasBrowserContractError("static asset file budget is exceeded")
    if total_bytes > max_bytes:
        raise AtlasBrowserContractError("static asset byte budget is exceeded")
    script_paths = {
        Path(match.decode("utf-8")).name
        for match in re.findall(rb'<script[^>]+src="([^"]+\.js)"', document)
        if b".atlas-" in match
    }
    declared_paths = {str(asset["path"]) for asset in assets}
    physical_paths = {path.name for path in output_dir.glob(f"{scope.name}.atlas-*.js")}
    if physical_paths != declared_paths:
        raise AtlasBrowserContractError(
            "physical static atlas scripts do not equal the manifest inventory"
        )
    if not script_paths.issubset(declared_paths):
        raise AtlasBrowserContractError(
            "document references a static atlas script outside the manifest inventory"
        )
    return {
        "schema_version": "atlas-static-integrity-audit.v1",
        "scope": scope.name,
        "status": "PASS",
        "candidate": candidate.as_json(),
        "document": {
            "path": scope.document,
            "byte_count": len(document),
            "sha256": _sha256(document),
        },
        "manifest": {
            "path": scope.manifest,
            "byte_count": len(manifest_bytes),
            "sha256": _sha256(manifest_bytes),
            "build_id": manifest["build_id"],
        },
        "assets": inventory,
        "asset_count": len(inventory),
        "asset_bytes": total_bytes,
        "provider_policy": {
            "keyless_osm": True,
            "carto_absent": True,
            "api_key_markers_absent": True,
        },
    }
