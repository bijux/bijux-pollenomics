"""Authenticate the bounded FLINK snapshot and publish its literal panel projection."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.native_panel_rows import (
    SOURCE,
    encoded,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.native_panels import project
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import (
    decode,
    digest,
    physical,
    require,
)

PROTOCOL = "docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/flink-source-projection.json"
MAX_SOURCE = 32 * 1024**2
MAX_OUTPUT = 2 * 1024**2


def buffer(path: Path, checksum: str, size: int, maximum: int) -> bytes:
    """Authenticate the exact same regular-file buffer that will be decoded."""
    physical(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= maximum,
            "Bounded single-link regular source required",
        )
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    require(
        all(
            getattr(before, k) == getattr(after, k) == getattr(final, k)
            for k in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ),
        "Input changed during read",
    )
    require(
        len(raw) == size == before.st_size and digest(raw) == checksum,
        "Exact input buffer identity differs",
    )
    return raw


def materialize(
    source: Path, protocol_path: Path, protocol_sha256: str, output: Path
) -> dict[str, Any]:
    """Write two bounded owned JSON files; never create an executable LRA request."""
    physical(source)
    physical(protocol_path)
    physical(output)
    source_relative = Path(str(SOURCE["path"]))
    require(
        tuple(source.parts[-len(source_relative.parts) :]) == source_relative.parts,
        "Exact retained source path required",
    )
    repository = source.parents[len(source_relative.parts) - 1]
    require(
        protocol_path == repository / PROTOCOL, "Canonical projection protocol required"
    )
    require(
        output.is_relative_to(repository / "artifacts") and not output.exists(),
        "Fresh repository artifact output required",
    )
    protocol_raw = buffer(
        protocol_path, protocol_sha256, protocol_path.stat().st_size, 65536
    )
    protocol = decode(protocol_raw)
    require(protocol["source"] == SOURCE, "Retained source pin differs")
    source_raw = buffer(source, str(SOURCE["sha256"]), int(SOURCE["bytes"]), MAX_SOURCE)
    result = project(decode(source_raw), protocol)
    body = encoded(result)
    manifest = {
        "schema_version": "flink-native-panel-manifest.v1",
        "source": {
            "path": str(source),
            "sha256": digest(source_raw),
            "bytes": len(source_raw),
        },
        "protocol": {
            "path": str(protocol_path),
            "sha256": digest(protocol_raw),
            "bytes": len(protocol_raw),
        },
        "protocol_semantic_sha256": digest(encoded(protocol)),
        "files": [
            {
                "path": "panel-projection.json",
                "sha256": digest(body),
                "bytes": len(body),
            }
        ],
        "engine_calls": 0,
        "executable_request": None,
        "scope": result["scope"],
    }
    manifest_raw = encoded(manifest)
    require(
        len(body) + len(manifest_raw) <= MAX_OUTPUT, "Projection exceeds bounded output"
    )
    output.mkdir(parents=True)
    for name, payload in (
        ("panel-projection.json", body),
        ("manifest.json", manifest_raw),
    ):
        with (output / name).open("xb") as stream:
            stream.write(payload)
    return manifest


def main() -> None:
    """Parse arguments for the source-bound native-panel projection."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.source, args.protocol, args.protocol_sha256, args.output)


if __name__ == "__main__":
    main()
