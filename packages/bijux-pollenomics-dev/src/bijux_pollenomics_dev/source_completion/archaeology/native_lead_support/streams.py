"""Bound and retain complete private native archaeology witness streams."""

from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path


@dataclass
class WitnessBudget:
    """Share a decoded-byte ceiling across native witness streams."""

    maximum: int
    decoded: int = 0


class NativeWitness:
    """Write deterministic gzip witness rows under shared byte limits."""

    def __init__(self, path: Path, budget: WitnessBudget, row_maximum: int) -> None:
        """Open an absent witness file with a shared decoded-byte budget."""
        self.path = path
        self.budget = budget
        self.row_maximum = row_maximum
        self.rows = 0
        self.decoded = 0
        self.raw = path.open("xb")
        self.compressed = gzip.GzipFile(
            filename="", mode="wb", compresslevel=6, fileobj=self.raw, mtime=0
        )

    def write(self, row: dict[str, object]) -> None:
        """Append one JSON row after checking row and cumulative byte ceilings."""
        encoded = (
            json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        ).encode()
        if len(encoded) > self.row_maximum:
            raise ValueError("private native row byte ceiling exceeded")
        if self.budget.decoded + len(encoded) > self.budget.maximum:
            raise ValueError("private decoded witness byte ceiling exceeded")
        self.budget.decoded += len(encoded)
        self.decoded += len(encoded)
        self.compressed.write(encoded)
        self.rows += 1

    def close(self) -> dict[str, object]:
        """Close the witness and return its byte and row identities."""
        self.compressed.close()
        self.raw.close()
        with self.path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        return {
            "format": "deterministic gzip NDJSON",
            "sha256": digest,
            "bytes": self.path.stat().st_size,
            "rows": self.rows,
            "decoded_bytes": self.decoded,
        }
