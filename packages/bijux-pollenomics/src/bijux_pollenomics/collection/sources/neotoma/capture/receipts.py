"""Immutable metadata capture receipts and bounded source-file readers."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .models import _HEADERS, _Request


def _write_json(path: Path, payload: object) -> str:
    content = (
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2
        )
        + "\n"
    ).encode()
    with path.open("xb") as stream:
        stream.write(content)
    return sha256(content).hexdigest()


def _safe_root(path: Path) -> Path:
    path = Path(path).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Neotoma metadata capture cannot use symlink paths")
    if not path.parent.is_dir():
        raise ValueError("Neotoma metadata output parent must already exist")
    return path


def _validate_receipt(
    record: dict[str, Any], request: _Request, body: bytes, bound: int
) -> None:
    parts = urlsplit(request.url)
    expected = {
        "requested_url": request.url,
        "final_url": request.url,
        "request_method": "GET",
        "request_target": parts.path + ("?" + parts.query if parts.query else ""),
        "parameters": request.parameters,
        "role": request.role,
        "expected_site_id": request.site_id,
        "request_headers": [list(pair) for pair in _HEADERS],
        "tls_mode": "verified_no_insecure_fallback",
        "http_status": 200,
        "body_complete": True,
        "terminal_status": "complete_http_200",
    }
    if request.dataset_id is not None:
        expected["expected_dataset_id"] = request.dataset_id
    for field, value in expected.items():
        if record.get(field) != value:
            raise ValueError(f"Neotoma metadata receipt {field} identity differs")
    if (
        len(body) > bound
        or record.get("retained_body_bytes") != len(body)
        or record.get("retained_body_sha256") != sha256(body).hexdigest()
    ):
        raise ValueError("Neotoma metadata body identity or byte limit differs")
    headers = record.get("response_headers")
    if not isinstance(headers, list) or any(
        not isinstance(pair, list)
        or len(pair) != 2
        or any(not isinstance(value, str) for value in pair)
        for pair in headers
    ):
        raise ValueError("Neotoma metadata response headers are malformed")
    for name, value in headers:
        if name.lower() == "content-length" and int(value) != len(body):
            raise ValueError("Neotoma metadata content length differs")
        if name.lower() == "content-encoding" and value.lower() != "identity":
            raise ValueError("Neotoma metadata entity uses unexpected content encoding")
    start, end = (_utc(record.get(name)) for name in ("utc_start", "utc_end"))
    if start > end:
        raise ValueError("Neotoma metadata request timestamps are reversed")


def _utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Neotoma metadata UTC timestamp is missing")
    result = datetime.fromisoformat(value)
    offset = result.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("Neotoma metadata timestamp is not UTC")
    return result


def _read(path: Path, bound: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > bound:
        raise ValueError(f"Neotoma capture input is not a bounded regular file: {path}")
    return path.read_bytes()


def _object(content: bytes) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Neotoma capture input is not bounded JSON") from error
    if not isinstance(value, dict):
        raise ValueError("Neotoma capture JSON must be an object")
    return value
