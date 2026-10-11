"""Byte-preserving, single-count SVAR WFS acquisition."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request

from bijux_pollenomics.core.http import fetch_url_bytes

from .replay import (
    CAPTURE_SCHEMA,
    SVAR_PAGE_SIZE,
    SVAR_WFS_URL,
    read_hits,
    request_parameters,
    validate_page,
)


def fetch_response(parameters: dict[str, str]) -> bytes:
    """Fetch response entity bytes without decoding/re-encoding the payload."""
    return fetch_url_bytes(
        Request(SVAR_WFS_URL + "?" + urlencode(parameters)),
        insecure=False,
        timeout=None,
    )


def capture_svar_wfs(
    directory: Path,
    *,
    fetch: Callable[[dict[str, str]], bytes] = fetch_response,
) -> str:
    """Capture a new attempt; preserve raw failures and return a complete digest."""
    directory = Path(directory)
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("svar_symlink_capture")
    directory = Path(os.path.abspath(directory))
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("svar_symlink_capture")
    directory.mkdir(parents=True, exist_ok=False)
    members: list[dict[str, object]] = []

    def retain(name: str, start: int | None) -> bytes:
        params = request_parameters(start)
        payload = fetch(dict(params))
        if not isinstance(payload, bytes):
            raise ValueError("svar_response_not_bytes")
        with (directory / name).open("xb") as stream:
            stream.write(payload)
        record = {
            "path": name,
            "byte_count": len(payload),
            "sha256": sha256(payload).hexdigest(),
            "parameters": params,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }
        with (directory / (name + ".json")).open("x", encoding="utf-8") as stream:
            json.dump(
                record, stream, sort_keys=True, ensure_ascii=False, allow_nan=False
            )
        members.append(record)
        return payload

    matched = read_hits(retain("hits.xml", None))
    seen: set[str] = set()
    for start in range(0, matched, SVAR_PAGE_SIZE):
        payload = retain(f"page-{start:09d}.xml", start)
        ids = validate_page(
            payload, matched=matched, expected=min(SVAR_PAGE_SIZE, matched - start)
        )
        if seen.intersection(ids):
            raise ValueError("svar_duplicate_record_id")
        seen.update(ids)
    manifest = {
        "schema_version": CAPTURE_SCHEMA,
        "source": "SMHI SVAR",
        "wfs_url": SVAR_WFS_URL,
        "matched_count": matched,
        "page_size": SVAR_PAGE_SIZE,
        "members": members,
        "scientific_review": "not_asserted",
        "rights_verification": "not_asserted",
        "snapshot_consistency": "count_and_identity_only; provider transaction snapshot unavailable",
    }
    content = (
        json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()
    with (directory / "capture.json").open("xb") as stream:
        stream.write(content)
    return sha256(content).hexdigest()
