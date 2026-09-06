"""Content and provider-policy audit for a published static atlas."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
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


def _assets(manifest: JsonObject) -> tuple[JsonObject, ...]:
    table = _mapping(manifest.get("assets"), label="manifest.assets")
    if table.get("fields") != list(_ASSET_FIELDS):
        raise AtlasBrowserContractError("manifest asset fields are not canonical")
    raw_records = table.get("records")
    if not isinstance(raw_records, list) or table.get("record_count") != len(
        raw_records
    ):
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
        if not isinstance(domain, str) or not isinstance(digest, str):
            raise AtlasBrowserContractError(
                f"manifest asset row {sequence} identity is malformed"
            )
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
    max_files = budgets.get("static_assets_max_files")
    max_bytes = budgets.get("static_assets_max_bytes")
    if not isinstance(max_files, int) or len(assets) > max_files:
        raise AtlasBrowserContractError(
            "static asset file budget is exceeded or invalid"
        )
    if not isinstance(max_bytes, int) or total_bytes > max_bytes:
        raise AtlasBrowserContractError(
            "static asset byte budget is exceeded or invalid"
        )
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
