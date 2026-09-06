from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import os
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)

from .constants import (
    _MAX_GOVERNED_FILE_BYTES,
    _PART_TARGET_BYTES,
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
    MULTIPART_SCHEMA_VERSION,
)
from .derivation import build_sead_source_native_evidence_bundle
from .serialization import (
    _canonical_bytes,
    _directory_bytes,
    _reject_symlink_ancestors,
    _stable_id,
)


def write_sead_source_native_evidence_bundle(
    acquisition_root: Path,
    output_directory: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> tuple[Path, ...]:
    """Atomically publish deterministic SEAD evidence files and their manifest."""
    if (
        not output_directory.is_absolute()
        or output_directory.name in {"", ".", ".."}
        or ".." in output_directory.parts
    ):
        raise ValueError("SEAD evidence output must be a safe absolute path")
    parent = output_directory.parent
    _reject_symlink_ancestors(parent)
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("SEAD evidence output parent must be a regular directory")
    output = parent / output_directory.name
    payloads = build_sead_source_native_evidence_bundle(
        acquisition_root, expected_identity=expected_identity
    )
    materialized, multipart_documents = _materialize_payloads(payloads)
    evidence_manifest = {
        "schema_version": EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": payloads["source_native_observations.json"]["source_run_id"],
        "build_id": payloads["source_native_observations.json"]["build_id"],
        "acquisition_manifest_sha256": payloads["source_native_observations.json"][
            "acquisition_manifest_sha256"
        ],
        "acquisition_bundle_sha256": payloads["source_native_observations.json"][
            "acquisition_bundle_sha256"
        ],
        "parent_admission_sha256": payloads["source_native_observations.json"][
            "parent_admission_sha256"
        ],
        "source_table_count": 61,
        "chronology_claim_count": payloads["chronology_claims.json"]["claim_count"],
        "observation_count": payloads["source_native_observations.json"][
            "observation_count"
        ],
        "eligible_event_count": payloads["evidence_events.json"][
            "eligible_event_count"
        ],
        "refused_event_count": payloads["evidence_events.json"]["refused_event_count"],
        "maximum_file_byte_count": _MAX_GOVERNED_FILE_BYTES,
        "multipart_documents": multipart_documents,
        "files": [
            {
                "path": name,
                "byte_count": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in sorted(materialized.items())
        ],
        "file_set_sha256": _stable_id(
            "sead-evidence-files",
            *(
                f"{name}:{hashlib.sha256(content).hexdigest()}:{len(content)}"
                for name, content in sorted(materialized.items())
            ),
        ).removeprefix("sead-evidence-files:"),
    }
    materialized["evidence_materialization_manifest.json"] = _canonical_bytes(
        evidence_manifest
    )
    if output.exists() or output.is_symlink():
        if output.is_symlink() or not output.is_dir():
            raise FileExistsError(f"Unsafe existing SEAD evidence bundle: {output}")
        if _directory_bytes(output) == materialized:
            return tuple(output / name for name in sorted(materialized))
        raise FileExistsError(f"Non-identical SEAD evidence bundle exists: {output}")
    staging = parent / f".{output.name}.staging-{os.getpid()}"
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"SEAD evidence staging collision: {staging}")
    staging.mkdir()
    try:
        for name, content in sorted(materialized.items()):
            destination = staging.joinpath(*Path(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        if _directory_bytes(staging) != materialized:
            raise ValueError("Staged SEAD evidence bundle bytes changed")
        from .validation import validate_sead_source_native_evidence_materialization

        validate_sead_source_native_evidence_materialization(staging)
        os.replace(staging, output)
    finally:
        if staging.exists() and not staging.is_symlink():
            for path in sorted(staging.rglob("*"), reverse=True):
                if path.is_file() and not path.is_symlink():
                    path.unlink()
                elif path.is_dir() and not path.is_symlink():
                    path.rmdir()
            staging.rmdir()
    return tuple(output / name for name in sorted(materialized))


def _materialize_payloads(
    payloads: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, bytes], dict[str, object]]:
    materialized: dict[str, bytes] = {}
    multipart_documents: dict[str, object] = {}
    for name, payload in sorted(payloads.items()):
        content = _canonical_bytes(payload)
        if len(content) <= _MAX_GOVERNED_FILE_BYTES:
            materialized[name] = content
            continue
        root_payload = dict(payload)
        partitioned_fields: dict[str, object] = {}
        document_parts: list[str] = []
        for field, value in sorted(payload.items()):
            if not isinstance(value, list) or not value:
                continue
            records = []
            row_start = 0
            chunks = _bounded_chunks(value)
            for part_number, rows in enumerate(chunks, start=1):
                row_end = row_start + len(rows)
                part_path = (
                    f"{name.removesuffix('.json')}/{field}-{part_number:05d}.json"
                )
                part_payload = {
                    "schema_version": MULTIPART_SCHEMA_VERSION,
                    "logical_document": name,
                    "field": field,
                    "part_number": part_number,
                    "row_start": row_start,
                    "row_end": row_end,
                    field: rows,
                }
                part_content = _canonical_bytes(part_payload)
                if len(part_content) > _MAX_GOVERNED_FILE_BYTES:
                    raise ValueError(
                        f"SEAD evidence part exceeds file limit: {part_path}"
                    )
                materialized[part_path] = part_content
                records.append(
                    {
                        "path": part_path,
                        "part_number": part_number,
                        "row_start": row_start,
                        "row_end": row_end,
                        "row_count": len(rows),
                        "byte_count": len(part_content),
                        "sha256": hashlib.sha256(part_content).hexdigest(),
                    }
                )
                document_parts.append(part_path)
                row_start = row_end
            if row_start != len(value):
                raise ValueError(
                    f"SEAD evidence partition rows do not reconcile: {name}"
                )
            root_payload.pop(field)
            partitioned_fields[field] = {
                "row_count": len(value),
                "part_count": len(records),
                "parts": records,
            }
        if not partitioned_fields:
            raise ValueError(
                f"SEAD evidence document cannot be safely partitioned: {name}"
            )
        root_payload["partitioned_fields"] = partitioned_fields
        root_content = _canonical_bytes(root_payload)
        if len(root_content) > _MAX_GOVERNED_FILE_BYTES:
            raise ValueError(f"SEAD evidence index exceeds file limit: {name}")
        materialized[name] = root_content
        multipart_documents[name] = {
            "partitioned_fields": sorted(partitioned_fields),
            "part_count": len(document_parts),
            "parts": sorted(document_parts),
        }
    return materialized, multipart_documents


def _bounded_chunks(rows: Sequence[object]) -> list[list[object]]:
    chunks: list[list[object]] = []
    current: list[object] = []
    current_bytes = 0
    for row in rows:
        row_bytes = len(_canonical_bytes(row))
        if row_bytes > _PART_TARGET_BYTES:
            raise ValueError("A single SEAD evidence row exceeds the partition target")
        if current and current_bytes + row_bytes > _PART_TARGET_BYTES:
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(row)
        current_bytes += row_bytes
    if current:
        chunks.append(current)
    return chunks
