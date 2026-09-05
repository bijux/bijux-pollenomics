"""Country-dimension coverage ledger orchestration."""

from __future__ import annotations

import os
from pathlib import Path
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_document,
)
from .boundaries import _validate_boundary_evidence
from .constants import (
    BOUNDARY_ARTIFACT_PATH,
    CELL_SCHEMA_ID,
    CELL_SCHEMA_SHA256,
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    COUNT_FIELDS,
    CountryCoverageError,
    INPUT_PATHS,
    LEDGER_SCHEMA_VERSION,
    PRODUCER_VERSION,
    SEAD_ADMISSION_PATH,
    SOURCE_FAMILIES,
)
from .decoding import (
    _canonical_bytes,
    _decode_object,
    _required_text,
    _rows,
    _sha256,
    _sha256_id_from_raw,
)
from .evidence import (
    _cell,
    _coverage_evidence,
    _source_snapshot_ids,
    _validate_stage_rows,
)
from .publication import (
    _read_governed_input,
    _regular_path_without_symlinks,
    _safe_output_destination,
    _write_atomic_no_follow,
)
from .reconciliation import _validate_cells, _validate_reconciliation


def build_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path
) -> dict[str, object]:
    """Build and validate a deterministic ledger from current governed artifacts."""
    root = repository_root.resolve(strict=True)
    schema_path = _regular_path_without_symlinks(
        cell_schema_path, "country coverage schema"
    )
    schema_bytes = schema_path.read_bytes()
    if _sha256(schema_bytes) != CELL_SCHEMA_SHA256:
        raise CountryCoverageError("country coverage schema content is not governed v2")
    schema = _decode_object(schema_bytes, "country coverage schema")
    if schema.get("$id") != CELL_SCHEMA_ID:
        raise CountryCoverageError("country coverage schema identity is not v2")

    input_bytes = {path: _read_governed_input(root, path) for path in INPUT_PATHS}
    if _sha256(input_bytes[SEAD_ADMISSION_PATH]) != SEAD_GOVERNED_ADMISSION_SHA256:
        raise CountryCoverageError("SEAD admission identity changed")
    input_documents = {
        path: _decode_object(payload, (root / path).as_posix())
        for path, payload in input_bytes.items()
    }
    inputs = [
        {
            "path": path,
            "sha256": _sha256(input_bytes[path]),
            "byte_count": len(input_bytes[path]),
        }
        for path in INPUT_PATHS
    ]
    producer = _producer_identity(root)
    configuration = {
        "cell_schema_id": CELL_SCHEMA_ID,
        "countries": list(COUNTRIES),
        "country_dimensions": list(COUNTRY_DIMENSIONS),
        "source_families": list(SOURCE_FAMILIES),
        "count_fields": list(COUNT_FIELDS),
        "input_paths": list(INPUT_PATHS),
        "sead_logical_document": "chronology_claims.json",
    }
    config_digest = f"sha256:{_sha256(_canonical_bytes(configuration))}"
    identity = {
        "cell_schema_sha256": _sha256(schema_bytes),
        "config_digest": config_digest,
        "inputs": inputs,
        "producer": producer,
    }
    build_id = f"sha256:{_sha256(_canonical_bytes(identity))}"

    stage_sequence = _rows(
        input_documents["data/source_family_evidence_stage_matrix.json"],
        "source stage matrix",
    )
    stage_keys = tuple(_required_text(row, "source_key") for row in stage_sequence)
    if len(stage_keys) != len(set(stage_keys)):
        raise CountryCoverageError("source stage matrix contains duplicate source keys")
    if stage_keys != SOURCE_FAMILIES:
        raise CountryCoverageError("source stage matrix order or inventory changed")
    _validate_stage_rows(stage_sequence)
    stage_rows = dict(zip(stage_keys, stage_sequence, strict=True))
    collection = input_documents["data/collection_summary.json"]
    boundary_manifest = input_documents["data/boundaries/raw/source_manifest.json"]
    boundary_raw_digest = _required_text(
        boundary_manifest, "normalized_artifact", "sha256"
    )
    boundary_digest = _sha256_id_from_raw(
        boundary_raw_digest,
        "boundary artifact digest",
    )
    if _sha256(input_bytes[BOUNDARY_ARTIFACT_PATH]) != boundary_raw_digest:
        raise CountryCoverageError("boundary artifact digest does not match its bytes")

    boundary_collections, boundary_counts, boundary_version = (
        _validate_boundary_evidence(
            boundary_manifest,
            input_documents[BOUNDARY_ARTIFACT_PATH],
        )
    )
    sead_claim_document = read_validated_sead_evidence_document(
        governed_sead_evidence_root(root / "data"),
        "chronology_claims.json",
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )

    evidence = _coverage_evidence(
        input_documents,
        input_bytes=input_bytes,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        boundary_collections=boundary_collections,
        boundary_counts=boundary_counts,
        sead_claim_document=sead_claim_document,
    )
    snapshot_ids = _source_snapshot_ids(collection, input_documents, input_bytes)
    cells: list[dict[str, object]] = []
    for source_family in SOURCE_FAMILIES:
        stage = stage_rows[source_family]
        for dimension in COUNTRY_DIMENSIONS:
            for country_code in COUNTRIES:
                cells.append(
                    _cell(
                        source_family=source_family,
                        dimension=dimension,
                        country_code=country_code,
                        evidence=evidence,
                        stage=stage,
                        snapshot_id=snapshot_ids[source_family],
                        boundary_digest=boundary_digest,
                        config_digest=config_digest,
                        build_id=build_id,
                    )
                )

    _validate_cells(cells, schema)
    _validate_reconciliation(cells)
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "cell_schema_id": CELL_SCHEMA_ID,
        "cell_schema_sha256": _sha256(schema_bytes),
        "producer": producer,
        "config_digest": config_digest,
        "build_id": build_id,
        "input_artifacts": inputs,
        "source_family_count": len(SOURCE_FAMILIES),
        "country_dimension_count": len(COUNTRY_DIMENSIONS),
        "country_partition_count": len(COUNTRIES),
        "cell_count": len(cells),
        "cells": cells,
    }


def _producer_identity(repository_root: Path) -> dict[str, object]:
    package_root = Path(__file__).resolve().parent
    source_records = [
        {
            "path": path.relative_to(repository_root).as_posix(),
            "sha256": _sha256(path.read_bytes()),
        }
        for path in sorted(package_root.rglob("*.py"))
    ]
    return {
        "path": package_root.relative_to(repository_root).as_posix(),
        "version": PRODUCER_VERSION,
        "sha256": _sha256(_canonical_bytes(source_records)),
    }


def write_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path, output_path: Path
) -> bytes:
    """Atomically write the ledger and return its canonical bytes."""
    root = repository_root.resolve(strict=True)
    schema_path = _regular_path_without_symlinks(
        cell_schema_path, "country coverage schema"
    )
    root_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        destination = _safe_output_destination(
            root,
            output_path,
            protected_paths=(
                schema_path,
                Path(__file__).resolve().parent,
                *(root / path for path in INPUT_PATHS),
            ),
        )
        payload = _canonical_bytes(
            build_country_dimension_coverage_ledger(root, cell_schema_path=schema_path)
        )
        _write_atomic_no_follow(
            root_descriptor,
            destination.relative_to(root),
            payload,
        )
        return payload
    finally:
        os.close(root_descriptor)
