"""Manifest-bound bundle fixture construction."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .codec import _canonical_json, _digest


def _fixture_bundle_payloads(
    root: Path, directory: str, filenames: tuple[str, ...]
) -> str:
    entries: list[dict[str, object]] = []
    bundle_root = root / directory
    bundle_root.mkdir()
    for filename in filenames:
        payload = _canonical_json({"record_count": 1, "records": [filename]}) + b"\n"
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
                "schema_version": "fixture-bundle-manifest.v1",
                "payload_file_count": len(entries),
                "bundle_digest": hashlib.sha256(digest_input).hexdigest(),
                "files": entries,
            }
        )
        + b"\n"
    )
    (bundle_root / "manifest.json").write_bytes(manifest_payload)
    return _digest(manifest_payload)
