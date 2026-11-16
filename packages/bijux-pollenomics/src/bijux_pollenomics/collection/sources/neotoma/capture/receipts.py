"""Immutable metadata capture receipts and bounded source-file readers."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import IO, TYPE_CHECKING, Any
from urllib.parse import urlsplit

from ..client import decode_neotoma_json_object
from .models import _HEADERS, _Request
from .transport import NeotomaHttpResponse

if TYPE_CHECKING:
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter


def _write_json(
    path: Path, payload: object, *, writer: OwnedTreeWriter | None = None
) -> str:
    content = (
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2
        )
        + "\n"
    ).encode()
    _write_bytes(path, content, writer=writer)
    return sha256(content).hexdigest()


def _write_bytes(path: Path, content: bytes, *, writer: OwnedTreeWriter | None) -> None:
    if writer is not None:
        writer.write_bytes(path.relative_to(writer.root).as_posix(), content)
    else:
        with path.open("xb") as stream:
            stream.write(content)


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
    directory: Path,
    request: _Request,
    response: NeotomaHttpResponse,
    started: str,
    *,
    writer: OwnedTreeWriter | None = None,
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
    _write_bytes(directory / record["body_file"], response.body, writer=writer)
    filename = f"{request.name}.receipt.json"
    digest = _write_json(directory / filename, record, writer=writer)
    return {
        "request_name": request.name,
        "receipt_file": filename,
        "receipt_sha256": digest,
        "body_file": record["body_file"],
    }, record


def _retain_transport_failure(
    directory: Path,
    request: _Request,
    started: str,
    error: Exception,
    *,
    writer: OwnedTreeWriter | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = _request_record(request, started)
    record.update(
        utc_end=datetime.now(UTC).isoformat(),
        terminal_status="transport_failure",
        error=f"{type(error).__name__}: {error}",
        body_complete=False,
    )
    filename = f"{request.name}.receipt.json"
    digest = _write_json(directory / filename, record, writer=writer)
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


def _open_source(path: Path) -> IO[bytes]:
    """Open without following a replaced link or waiting for a replaced FIFO."""
    if not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_NONBLOCK")):
        raise ValueError("Neotoma nonblocking regular source opens are unavailable")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise ValueError(
            f"Neotoma capture input is not a bounded regular file: {path}"
        ) from error
    try:
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def _read(path: Path, bound: int) -> bytes:
    if type(bound) is not int or bound < 0:
        raise ValueError(
            "Neotoma capture byte bound must be a nonnegative native integer"
        )
    try:
        node = path.stat(follow_symlinks=False)
    except OSError as error:
        raise ValueError(
            f"Neotoma capture input is not a bounded regular file: {path}"
        ) from error
    if not stat.S_ISREG(node.st_mode) or node.st_size > bound:
        raise ValueError(f"Neotoma capture input is not a bounded regular file: {path}")
    with _open_source(path) as stream:
        opened = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size > bound
            or (opened.st_dev, opened.st_ino) != (node.st_dev, node.st_ino)
        ):
            raise ValueError("Neotoma capture input identity changed while opening")
        content = stream.read(bound + 1)
    if len(content) > bound:
        raise ValueError("Neotoma capture input grew beyond its byte bound")
    return content


def _object(content: bytes) -> dict[str, Any]:
    try:
        value = decode_neotoma_json_object(content)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Neotoma capture input is not bounded JSON") from error
    if not isinstance(value, dict):
        raise ValueError("Neotoma capture JSON must be an object")
    return value
