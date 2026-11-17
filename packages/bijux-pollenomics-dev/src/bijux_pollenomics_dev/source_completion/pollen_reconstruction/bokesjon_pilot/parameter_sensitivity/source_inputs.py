"""Read only the independent public metadata needed for the nominal PPE bridge."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree, DirectoryAnchor

from ..taxa import legacyvegetation
from . import normalization

REPORT_PINS = {
    "author-parameter-binding": (
        "94ae944d1bb1f09fd0234f879915ce32c3d58e1587ad04165ef545f8d13ed202",
        8286,
    ),
    "parameter-correspondence": (
        "0b869d584239390967c226a82ced03acb1e2419a8fa66b4226ff36b586147f16",
        16964,
    ),
    "parameter-candidates": (
        "6f3290a73db9d5e02c4f66a9c38fe809cbf3d1795515186b7a9f0da9843e3065",
        18733,
    ),
}
REPORT_REVISION = "c198c998a2d7b6866d6fd10869a0bbe7321ad1fe"


def _read(root: Path, name: str, *, limit: int, checksum: str) -> bytes:
    path = root / name
    with BoundedInputTree(
        path.parent, selected=path.name, max_bytes=limit, max_files=1
    ) as tree:
        raw = tree.read(path, max_bytes=limit)
    if len(raw) > limit or sha256(raw).hexdigest() != checksum:
        raise ValueError("Normalization source bytes differ from independent authority")
    return raw


def read_normalization_context(
    repository: Path, reference: dict[str, Any]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Bind source-row metadata to exact source declarations without workbook reads."""
    root = repository.absolute()
    source_directory = root / legacyvegetation.DIRECTORY
    with DirectoryAnchor(source_directory) as anchor:
        source_raw = _read(
            source_directory,
            "source.json",
            limit=65536,
            checksum=legacyvegetation.SOURCE_SHA256,
        )
        source = json.loads(source_raw)
        tables = source["reference_tables"]
        if len(tables) != 2 or {r["path"] for r in tables} != set(
            legacyvegetation.TABLES
        ):
            raise ValueError(
                "Exactly the two independently declared reference tables required"
            )
        metadata = {
            "source.json": {
                "sha256": sha256(source_raw).hexdigest(),
                "bytes": len(source_raw),
            }
        }
        for row in tables:
            if type(row["bytes"]) is not int or not 0 < row["bytes"] <= 65536:
                raise ValueError("Reference table metadata exceeds its declared bound")
            metadata[row["path"]] = {k: row[k] for k in ["sha256", "bytes"]}
        expected: list[dict[str, Any]] = [
            {"path": name, **pin} for name, pin in metadata.items()
        ]
        observed = reference.get("source_pins", [])
        if len(observed) != 3 or sorted(observed, key=lambda r: r["path"]) != sorted(
            expected, key=lambda r: r["path"]
        ):
            raise ValueError(
                "Adapted reference pins differ from independent source declarations"
            )
        anchor.check()
    buffers = {"reference-source": source_raw}
    declarations = {}
    report_directory = root / normalization.PUBLIC_PREFIX
    with DirectoryAnchor(report_directory) as anchor:
        for role in normalization.ROLES:
            checksum, size = REPORT_PINS[role]
            name = role + "/report.json"
            raw = _read(report_directory, name, limit=size, checksum=checksum)
            if len(raw) != size:
                raise ValueError("Normalization report byte size differs")
            buffers[role] = raw
            declarations[role] = {
                # Logical buffer names do not grant authority to open a path.
                "path": role + ".json",
                "sha256": checksum,
                "bytes": size,
                "public_source_path": normalization.PUBLIC_PREFIX + name,
                "public_revision": REPORT_REVISION,
            }
            anchor.check()
    return buffers, {"normalization_evidence": declarations, "metadata": metadata}
