"""Publish portable request, original evidence and lineage without replacement."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any

from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from ...inputs.validation import validate_request
from ..models import canonical_bytes, producer_identity
from ..reading import NeotomaEvidence
from ..workflow import output_destination
from .inputs import assert_files_unchanged
from .models import SyntheticRequestReport


def publish_request(
    *,
    template: dict[str, Any],
    lineage: dict[str, Any],
    evidence: NeotomaEvidence,
    input_root: Path,
    files: dict[str, tuple[str, bytes]],
    fixture: str,
    producer: dict[str, Any],
    output_directory: Path,
) -> SyntheticRequestReport:
    destination = output_destination(output_directory, evidence)
    if destination.is_relative_to(input_root) or input_root.is_relative_to(destination):
        raise ValueError("Synthetic projection output must not overlap input evidence")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )
    for authority, root, members in (
        ("raw", evidence.raw_root, evidence.raw_files),
        ("normalized", evidence.normalized_root, evidence.normalized_files),
    ):
        for relative, digest in members:
            content = (root / relative).read_bytes()
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError("Source authority changed before evidence copy")
            _write(stage / "source" / authority / relative, content)
    for item in template["evidence"]:
        relative, content = files[item["evidence_id"]]
        item["path"] = f"evidence/{relative}"
        target = stage / item["path"]
        if target.exists():
            if target.read_bytes() != content:
                raise ValueError("Conflicting evidence destination")
        else:
            _write(target, content)
    validated = validate_request(template, input_root=stage)
    _write(stage / "request.json", validated.canonical_json.encode())
    _write(stage / "lineage.json", canonical_bytes(lineage))
    artifacts = [
        {
            "path": path.relative_to(stage).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(stage.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "schema_version": "synthetic-source-lra-projection.v1",
        "data_kind": "synthetic",
        "synthetic_fixture_id": fixture,
        "purpose": "exploratory",
        "scientific_review_status": "not_applicable_synthetic_fixture",
        "empirical_validation_status": "not_evaluated",
        "request_path": "request.json",
        "request_sha256": validated.sha256,
        "inputs": evidence.input_records(),
        "source_projection_verification": lineage["source_projection_verification"],
        "producer": producer,
        "artifacts": artifacts,
    }
    content = canonical_bytes(manifest)
    _write(stage / "manifest.json", content)
    evidence.assert_unchanged()
    assert_files_unchanged(input_root, files)
    if producer_identity() != producer:
        raise ValueError("Host producer changed during synthetic projection")
    output_destination(destination, evidence)
    publish_new_output_tree(final_output_root=destination, staging_output_root=stage)
    return SyntheticRequestReport(
        destination,
        validated.sha256,
        hashlib.sha256(content).hexdigest(),
        fixture,
        lineage["selected_samples"],
        lineage["selected_cells"],
    )


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
