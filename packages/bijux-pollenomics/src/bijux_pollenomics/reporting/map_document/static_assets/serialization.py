"""Canonical payload serialization and immutable asset writes."""

import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any
import zlib

from .budgets import ATLAS_CHUNK_MAX_BYTES

_GZIP_OPERATING_SYSTEM_OFFSET = 9
_GZIP_OPERATING_SYSTEM_UNKNOWN = 255


def canonical_json(value: Any) -> str:
    """Serialize a JSON value with the atlas's deterministic encoding."""
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def chunk_script_bytes(
    *,
    asset_key: str,
    payload_sha256: str,
    payload_json: str,
    payload_encoding: str,
) -> bytes:
    """Wrap one payload in the static runtime registration protocol."""
    envelope: dict[str, object] = {
        "asset_key": asset_key,
        "payload_sha256": payload_sha256,
        "payload_encoding": payload_encoding,
    }
    if payload_encoding == "json":
        envelope["payload_json"] = payload_json
    elif payload_encoding == "gzip_base64":
        envelope["payload_gzip_base64"] = base64.b64encode(
            _canonical_gzip_compress(payload_json.encode("utf-8"))
        ).decode("ascii")
    else:
        raise ValueError("static atlas payload encoding is unsupported")
    envelope_json = canonical_json(envelope)
    statement = (
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
        f"globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push({envelope_json});\n"
    )
    return statement.encode("utf-8")


def _canonical_gzip_compress(payload: bytes) -> bytes:
    """Compress bytes without leaking the producer operating system."""
    compressed = bytearray(gzip.compress(payload, compresslevel=9, mtime=0))
    compressed[_GZIP_OPERATING_SYSTEM_OFFSET] = _GZIP_OPERATING_SYSTEM_UNKNOWN
    return bytes(compressed)


def decode_chunk_script(
    payload: bytes,
    *,
    expected_asset_key: str,
    expected_payload_sha256: str,
    expected_payload_encoding: str,
    expected_decoded_byte_count: int | None = None,
) -> dict[str, object]:
    """Decode and authenticate one runtime registration script."""
    prefix = (
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("static atlas chunk is not UTF-8") from exc
    if not text.startswith(prefix) or not text.endswith(");\n"):
        raise ValueError("static atlas chunk wrapper changed")
    try:
        envelope = json.loads(text[len(prefix) : -3])
    except json.JSONDecodeError as exc:
        raise ValueError("static atlas chunk envelope is invalid") from exc
    if not isinstance(envelope, dict):
        raise ValueError("static atlas chunk envelope must be an object")
    if envelope.get("asset_key") != expected_asset_key:
        raise ValueError("static atlas chunk envelope identity changed")
    if envelope.get("payload_sha256") != expected_payload_sha256:
        raise ValueError("static atlas chunk envelope digest changed")
    if envelope.get("payload_encoding") != expected_payload_encoding:
        raise ValueError("static atlas chunk envelope encoding changed")
    if expected_payload_encoding == "json":
        payload_json = envelope.get("payload_json")
        if not isinstance(payload_json, str):
            raise ValueError("static atlas chunk JSON payload is missing")
    elif expected_payload_encoding == "gzip_base64":
        payload_gzip_base64 = envelope.get("payload_gzip_base64")
        if not isinstance(payload_gzip_base64, str):
            raise ValueError("static atlas compressed payload is missing")
        try:
            compressed = base64.b64decode(payload_gzip_base64, validate=True)
        except ValueError as exc:
            raise ValueError("static atlas compressed payload is invalid") from exc
        try:
            payload_json = _bounded_gzip_decompress(compressed).decode("utf-8")
        except (UnicodeDecodeError, zlib.error) as exc:
            raise ValueError("static atlas compressed payload is invalid") from exc
    else:
        raise ValueError("static atlas chunk envelope encoding is unsupported")
    validate_decoded_payload_size(payload_json, asset_key=expected_asset_key)
    if (
        expected_decoded_byte_count is not None
        and len(payload_json.encode("utf-8")) != expected_decoded_byte_count
    ):
        raise ValueError("static atlas decoded payload byte count changed")
    if (
        hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        != expected_payload_sha256
    ):
        raise ValueError("static atlas chunk payload digest changed")
    try:
        decoded = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError("static atlas chunk payload JSON is invalid") from exc
    if not isinstance(decoded, dict):
        raise ValueError("static atlas chunk payload must be an object")
    return decoded


def _bounded_gzip_decompress(payload: bytes) -> bytes:
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    decoded = decoder.decompress(payload, ATLAS_CHUNK_MAX_BYTES + 1)
    if len(decoded) > ATLAS_CHUNK_MAX_BYTES or decoder.unconsumed_tail:
        raise ValueError("static atlas compressed payload exceeds its decoded budget")
    decoded += decoder.flush(ATLAS_CHUNK_MAX_BYTES + 1 - len(decoded))
    if (
        len(decoded) > ATLAS_CHUNK_MAX_BYTES
        or not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
    ):
        raise ValueError("static atlas compressed payload exceeds its decoded budget")
    return decoded


def validate_decoded_payload_size(payload_json: str, *, asset_key: str) -> None:
    """Enforce the decoded chunk budget before allocation or publication."""
    if len(payload_json.encode("utf-8")) > ATLAS_CHUNK_MAX_BYTES:
        raise ValueError(
            f"static atlas decoded payload exceeds its byte budget: {asset_key}"
        )


def write_immutable(path: Path, payload: bytes) -> None:
    """Write a new immutable asset or accept identical existing bytes."""
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
            raise ValueError(f"static atlas asset collision: {path.name}")
        return
    path.write_bytes(payload)


__all__ = [
    "canonical_json",
    "chunk_script_bytes",
    "decode_chunk_script",
    "validate_decoded_payload_size",
    "write_immutable",
]
