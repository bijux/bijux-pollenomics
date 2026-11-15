"""Immutable metadata capture receipts and bounded source-file readers."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..client import decode_neotoma_json_object
from .models import _HEADERS, _Request
from .transport import NeotomaHttpResponse


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
    record: dict[str, Any],
    request: _Request,
    body: bytes,
    bound: int,
    *,
    require_success: bool = True,
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
    }
    if require_success:
        expected.update(
            http_status=200, body_complete=True, terminal_status="complete_http_200"
        )
    elif (
        type(record.get("http_status")) is not int
        or not 100 <= record["http_status"] <= 599
        or type(record.get("body_complete")) is not bool
    ):
        raise ValueError("Neotoma source response status or completeness is invalid")
    if request.dataset_id is not None:
        expected["expected_dataset_id"] = request.dataset_id
    for field, value in expected.items():
        if record.get(field) != value:
            raise ValueError(f"Neotoma metadata receipt {field} identity differs")
    if (
        len(body) > bound + int(not require_success and not record["body_complete"])
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
        if (
            name.lower() == "content-length"
            and (require_success or record["body_complete"])
            and int(value) != len(body)
        ):
            raise ValueError("Neotoma metadata content length differs")
        if (
            require_success
            and name.lower() == "content-encoding"
            and value.lower() != "identity"
        ):
            raise ValueError("Neotoma metadata entity uses unexpected content encoding")
    start, end = (_utc(record.get(name)) for name in ("utc_start", "utc_end"))
    if start > end:
        raise ValueError("Neotoma metadata request timestamps are reversed")


def _request_record(request: _Request, started: str) -> dict[str, Any]:
    parts = urlsplit(request.url)
    record: dict[str, Any] = {
        "requested_url": request.url,
        "request_method": "GET",
        "request_target": parts.path + ("?" + parts.query if parts.query else ""),
        "parameters": request.parameters,
        "role": request.role,
        "expected_site_id": request.site_id,
        "request_headers": [list(pair) for pair in _HEADERS],
        "tls_mode": "verified_no_insecure_fallback",
        "utc_start": started,
    }
    if request.dataset_id is not None:
        record["expected_dataset_id"] = request.dataset_id
    return record


def _retain_http_response(
    directory: Path, request: _Request, response: NeotomaHttpResponse, started: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = _request_record(request, started)
    record.update(
        utc_end=datetime.now(UTC).isoformat(),
        final_url=response.final_url,
        http_status=response.http_status,
        response_headers=[list(pair) for pair in response.headers],
        body_file=f"{request.name}.body",
        body_complete=response.body_complete,
        retained_body_bytes=len(response.body),
        retained_body_sha256=sha256(response.body).hexdigest(),
        terminal_status="complete_http_200"
        if response.http_status == 200 and response.body_complete
        else "refused_http_response",
    )
    with (directory / record["body_file"]).open("xb") as stream:
        stream.write(response.body)
    filename = f"{request.name}.receipt.json"
    digest = _write_json(directory / filename, record)
    return {
        "request_name": request.name,
        "receipt_file": filename,
        "receipt_sha256": digest,
        "body_file": record["body_file"],
    }, record


def _retain_transport_failure(
    directory: Path, request: _Request, started: str, error: Exception
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = _request_record(request, started)
    record.update(
        utc_end=datetime.now(UTC).isoformat(),
        terminal_status="transport_failure",
        error=f"{type(error).__name__}: {error}",
        body_complete=False,
    )
    filename = f"{request.name}.receipt.json"
    digest = _write_json(directory / filename, record)
    return {
        "request_name": request.name,
        "receipt_file": filename,
        "receipt_sha256": digest,
    }, record


def _validate_transport_failure(record: dict[str, Any], request: _Request) -> None:
    started = record.get("utc_start")
    if not isinstance(started, str):
        raise ValueError("Neotoma transport failure request timestamp is missing")
    for field, value in _request_record(request, started).items():
        if record.get(field) != value:
            raise ValueError("Neotoma transport failure request identity differs")
    if (
        record.get("terminal_status") != "transport_failure"
        or record.get("body_complete") is not False
        or not isinstance(record.get("error"), str)
    ):
        raise ValueError("Neotoma transport failure receipt is malformed")
    if _utc(record.get("utc_start")) > _utc(record.get("utc_end")):
        raise ValueError("Neotoma transport failure time is reversed")


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
        value = decode_neotoma_json_object(content)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Neotoma capture input is not bounded JSON") from error
    if not isinstance(value, dict):
        raise ValueError("Neotoma capture JSON must be an object")
    return value
