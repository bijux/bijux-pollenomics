"""Manifest-bound bundle fixture construction."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .codec import _canonical_json, _digest


def _fixture_bundle_payloads(
    root: Path,
    directory: str,
    filenames: tuple[str, ...],
    *,
    manifest_schema_version: str = "fixture-bundle-manifest.v1",
    public_release_allowed: bool | None = True,
    release_schema_version: str = "fixture-release-metadata.v1",
    status_namespace: str = "fixture_release",
    release_status: str = "approved",
    release_reason_field: str = "reason_codes",
    release_reason_codes: tuple[str, ...] = (),
) -> str:
    entries: list[dict[str, object]] = []
    bundle_root = root / directory
    bundle_root.mkdir()
    for filename in filenames:
        document: dict[str, object] = {"record_count": 1, "records": [filename]}
        if filename == "release_metadata.json":
            document = {
                "schema_version": release_schema_version,
                "status_namespace": status_namespace,
                "release_status": release_status,
                release_reason_field: list(release_reason_codes),
                "record_count": 1,
            }
            if public_release_allowed is not None:
                document["public_release_allowed"] = public_release_allowed
        payload = _canonical_json(document) + b"\n"
        (bundle_root / filename).write_bytes(payload)
        entries.append(
            {
                "path": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "record_count": 1,
            }
        )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    manifest_payload = (
        _canonical_json(
            {
                "schema_version": manifest_schema_version,
                "payload_file_count": len(entries),
                "bundle_digest": hashlib.sha256(digest_input).hexdigest(),
                "files": entries,
            }
        )
        + b"\n"
    )
    (bundle_root / "manifest.json").write_bytes(manifest_payload)
    return _digest(manifest_payload)
