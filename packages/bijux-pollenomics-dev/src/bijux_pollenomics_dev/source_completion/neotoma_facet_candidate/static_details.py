"""Bounded authenticated decoding of registered candidate detail chunks."""

from __future__ import annotations

import base64
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.filesystem import read_regular_file

_PREFIX = b"globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
_MAX_RAW = 8 * 1024 * 1024
_MAX_DECODED = 64 * 1024 * 1024


def _pinned(path: Path, pin: str, limit: int) -> bytes:
    if not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None:
        raise ValueError("Candidate asset pin is malformed")
    data = read_regular_file(path, max_bytes=limit)
    if sha256(data).hexdigest() != pin:
        raise ValueError("Candidate asset identity differs")
    return data


def decode_details(
    root: Path, files: dict[str, str]
) -> tuple[str, list[dict[str, Any]]]:
    """Read only registered details using the exact producer-declared identities."""
    html = _pinned(root / "nordic_map.html", files["nordic_map.html"], 1024 * 1024)
    matches = re.findall(
        rb'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
    )
    if len(matches) != 1:
        raise ValueError("Candidate bootstrap differs")
    bootstrap = json.loads(matches[0])
    fields = bootstrap["assets"]["fields"]
    rows = bootstrap["assets"]["records"]
    if (
        not isinstance(fields, list)
        or not all(type(x) is str for x in fields)
        or len(set(fields)) != len(fields)
        or not isinstance(rows, list)
        or len(rows) > 20000
    ):
        raise ValueError("Candidate asset inventory differs")
    build = bootstrap["build_id"]
    if not isinstance(build, str) or not build:
        raise ValueError("Candidate build identity differs")
    output: list[dict[str, Any]] = []
    raw_total = decoded_total = 0
    for sequence, values in enumerate(rows):
        if not isinstance(values, list) or len(values) != len(fields):
            raise ValueError("Candidate asset row differs")
        row = dict(zip(fields, values, strict=True))
        if row.get("domain") != "details":
            continue
        digest = row.get("sha256")
        payload_digest = row.get("payload_sha256")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not isinstance(payload_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", payload_digest) is None
        ):
            raise ValueError("Candidate detail asset digest differs")
        name = f"nordic.atlas-details.{sequence:04d}.{digest[:16]}.js"
        if files.get(name) != digest:
            raise ValueError("Candidate detail registration differs")
        raw = _pinned(root / name, digest, _MAX_RAW)
        raw_total += len(raw)
        if (
            raw_total > 2 * 1024**3
            or type(row.get("byte_count")) is not int
            or len(raw) != row["byte_count"]
            or not raw.startswith(_PREFIX)
            or not raw.endswith(b");\n")
        ):
            raise ValueError("Candidate detail wrapper or byte budget differs")
        envelope = json.loads(raw[len(_PREFIX) : -3])
        key = f"details:{sequence}"
        if (
            envelope.get("asset_key") != key
            or envelope.get("payload_sha256") != payload_digest
        ):
            raise ValueError("Candidate detail envelope identity differs")
        if envelope.get("payload_encoding") == "gzip_base64":
            with gzip.GzipFile(
                fileobj=io.BytesIO(
                    base64.b64decode(envelope["payload_gzip_base64"], validate=True)
                )
            ) as stream:
                decoded = stream.read(_MAX_DECODED + 1)
        elif envelope.get("payload_encoding") == "json":
            decoded = envelope["payload_json"].encode()
        else:
            raise ValueError("Candidate detail encoding differs")
        decoded_total += len(decoded)
        if (
            len(decoded) > _MAX_DECODED
            or decoded_total > 4 * 1024**3
            or type(row.get("decoded_byte_count")) is not int
            or len(decoded) != row["decoded_byte_count"]
            or sha256(decoded).hexdigest() != payload_digest
        ):
            raise ValueError("Candidate detail decoded identity or budget differs")
        payload = json.loads(decoded)
        if (
            payload.get("build_id") != build
            or payload.get("asset_key") != key
            or not isinstance(payload.get("records"), list)
            or type(row.get("record_count")) is not int
            or len(payload["records"]) != row["record_count"]
        ):
            raise ValueError("Candidate detail record identity differs")
        for record in payload["records"]:
            if not isinstance(record, dict):
                raise ValueError("Candidate detail record is malformed")
            if isinstance(record.get("record_id"), str) and record[
                "record_id"
            ].startswith("neotoma:site:"):
                output.append(record)
    return build, output
