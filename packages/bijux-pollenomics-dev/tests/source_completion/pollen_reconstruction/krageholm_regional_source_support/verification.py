"""Authenticate literal source bytes and compare every independently read owner."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time
from typing import Any

from .native_rows import require
from .population import expected_result

PROTOCOL = "reports/science/pollen-reconstruction/krageholm-regional-source-support/protocol.json"
SOURCE = "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json"


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while refusing duplicate member names."""
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON object member")
        result[key] = value
    return result


def refuse_constant(token: str) -> None:
    """Refuse a nonfinite JSON constant token."""
    raise ValueError("Nonfinite JSON constant: " + token)


def decode(body: bytes) -> dict[str, Any]:
    """Decode an object with exact decimal tokens and unique member names."""
    value: Any = json.loads(
        body,
        parse_float=Decimal,
        parse_constant=refuse_constant,
        object_pairs_hook=pairs,
    )
    require(type(value) is dict, "literal JSON object required")
    assert isinstance(value, dict)
    return value


def same(actual: Any, expected: Any) -> None:
    """Keep JSON integer/decimal/boolean types distinct; ages retain binary64 meaning."""
    if isinstance(expected, dict):
        require(
            type(actual) is dict and set(actual) == set(expected),
            "result object members differ",
        )
        for key in expected:
            same(actual[key], expected[key])
    elif isinstance(expected, list):
        require(
            type(actual) is list and len(actual) == len(expected),
            "result array population differs",
        )
        for left, right in zip(actual, expected, strict=True):
            same(left, right)
    elif type(expected) in (Decimal, float):
        require(type(actual) in (Decimal, float), "native decimal token type changed")
        left, right = float(actual), float(expected)
        require(
            math.isfinite(left) and math.isfinite(right) and left == right,
            "native decimal binary64 interpretation changed",
        )
    else:
        require(
            type(actual) is type(expected) and actual == expected,
            "native scalar type or exact value differs",
        )


def source_bytes(path: Path, expected: dict[str, Any], limit: int) -> bytes:
    """Read bounded unaliased source bytes and verify their declared identity."""
    require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(node.is_symlink() for node in (path, *path.parents)),
        "unaliased regular source path required",
    )
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= limit,
            "bounded single-link regular source required",
        )
        body = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    final = path.stat()
    require(
        all(
            getattr(before, key) == getattr(after, key) == getattr(final, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
                "st_mode",
                "st_nlink",
            )
        ),
        "source changed during literal read",
    )
    require(
        len(body) == expected["bytes"]
        and sha256(body).hexdigest() == expected["sha256"],
        "original source byte identity differs",
    )
    return body


def verify(repository: Path, result_path: Path) -> dict[str, Any]:
    """Compare the saved regional result with independent literal accounting."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    protocol_path = repository / PROTOCOL
    protocol_body = protocol_path.read_bytes()
    protocol = decode(protocol_body)
    require(
        protocol["source"]["path"] == SOURCE
        and type(protocol["source"]["bytes"]) is int
        and 0 < protocol["source"]["bytes"] <= 32 * 1024**2
        and protocol["source_max_bytes"] == 32 * 1024**2,
        "bounded declared source differs",
    )
    source_path = repository / SOURCE
    original_body = source_bytes(
        source_path, protocol["source"], int(protocol["source_max_bytes"])
    )
    expected = expected_result(decode(original_body), protocol)
    result_body = result_path.read_bytes()
    require(
        len(result_body) <= 2 * 1024**2, "source-support result exceeds output budget"
    )
    actual = decode(result_body)
    require(
        set(actual) == {*expected, "source_commit", "elapsed_seconds"},
        "result authority fields differ",
    )
    head = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    require(
        actual["source_commit"] == head,
        "source result does not bind current frozen HEAD",
    )
    elapsed = actual["elapsed_seconds"]
    require(
        type(elapsed) in (int, Decimal) and 0 <= float(elapsed) <= 120,
        "producer elapsed bound differs",
    )
    same({key: actual[key] for key in expected}, expected)
    require(
        protocol_path.read_bytes() == protocol_body
        and result_path.read_bytes() == result_body
        and source_bytes(
            source_path, protocol["source"], int(protocol["source_max_bytes"])
        )
        == original_body,
        "consumed source or result changed",
    )
    return {
        "status": "independent_krageholm_source_support_pass",
        "source_commit": head,
        "source_sha256": protocol["source"]["sha256"],
        "result_sha256": sha256(result_body).hexdigest(),
        "native_sample_owners_checked": 96,
        "native_sample_order_preserved": True,
        "selected_chronology_id": 13366,
        "native_collection_default_reference": 13365,
        "native_default_flags_preserved": [13365, 13366],
        "fixed_windows_checked": 6,
        "population": expected["population"],
        "support_summary": expected["support_summary"],
        "engine_calls": 0,
        "model_fits": 0,
        "scientific_or_field_admission": False,
        "elapsed_seconds": time.monotonic() - started,
    }
