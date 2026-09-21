"""Publish the bounded LandClim full-study metadata inventory."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import cast

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyMetadataInventory,
    StudyMetadataRecord,
    read_landclim_study_inventory,
    reopen_landclim_study_inventory,
)

JsonObject = dict[str, object]

_MANIFEST = "manifest.json"
_RECORDS = "records.jsonl"
_CROSSWALK = "primary-source-crosswalk.csv"
_REFUSALS = "refusals.csv"
_REPORT = "report.json"
_OUTPUT_NAMES = (_MANIFEST, _RECORDS, _CROSSWALK, _REFUSALS, _REPORT)
_EXPECTED_RECORDS = 1128
_EXPECTED_COLUMNS = 44
_REFUSAL_REQUIREMENTS = (
    (
        "historical_primary_pollen_counts",
        "not_authenticated",
        "historical_primary_pollen_counts_not_authenticated",
    ),
    (
        "historical_chronology",
        "not_authenticated",
        "historical_chronology_not_authenticated",
    ),
    (
        "historical_current_revision_crosswalk",
        "not_authenticated",
        "historical_current_revision_crosswalk_not_authenticated",
    ),
    (
        "per_sequence_rights",
        "unresolved",
        "per_sequence_rights_not_cleared",
    ),
)


class StudyInputProductError(ValueError):
    """Raised when a metadata-only ESSD product exceeds its evidence."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _json_line(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _json_object(content: bytes, name: str) -> JsonObject:
    value = json.loads(content)
    if not isinstance(value, dict):
        raise StudyInputProductError(f"Expected a JSON object in {name}")
    return cast(JsonObject, value)


def _claims() -> JsonObject:
    return {
        "historical_primary_pollen_inputs_recovered": False,
        "historical_chronology_inputs_recovered": False,
        "historical_current_revision_crosswalk_completed": False,
        "per_sequence_rights_cleared": False,
        "original_profile_r_rerun_executed": False,
        "native_r_parity_certified": False,
        "pft_discrepancy_resolved": False,
        "whole_paper_reproduction_certified": False,
        "publication_allowed": False,
        "independent_measured_vegetation_truth": False,
        "scientifically_accepted": False,
        "scientific_acceptance": "not_evaluated",
    }


def _validate_inventory(
    inventory: LandClimStudyMetadataInventory,
) -> LandClimStudyMetadataInventory:
    if (
        inventory.metadata_record_count != _EXPECTED_RECORDS
        or inventory.expected_record_count != _EXPECTED_RECORDS
        or len(inventory.header) != _EXPECTED_COLUMNS
    ):
        raise StudyInputProductError(
            "LandClim study metadata denominator is not 1,128 by 44"
        )
    expected_locators = tuple(
        f"landclim_ii_site_metadata.xlsx#{inventory.sheet_name}!{worksheet_row}"
        for worksheet_row in range(2, _EXPECTED_RECORDS + 2)
    )
    if (
        tuple(record.source_locator for record in inventory.records)
        != expected_locators
    ):
        raise StudyInputProductError(
            "LandClim study metadata row locators are incomplete or reordered"
        )
    for expected_row, record in enumerate(inventory.records, start=2):
        if record.worksheet_row != expected_row:
            raise StudyInputProductError("LandClim worksheet rows are not contiguous")
        if tuple(value.column for value in record.values) != inventory.header:
            raise StudyInputProductError(
                f"LandClim metadata row {expected_row} does not match the header"
            )
        if (
            record.primary_pollen_count_identity is not None
            or record.chronology_input_identity is not None
            or record.rights_status != "unresolved"
        ):
            raise StudyInputProductError(
                f"LandClim metadata row {expected_row} exceeds metadata-only scope"
            )
    expected_boundary = {
        "publication_metadata_only": True,
        "raw_pollen_counts_authenticated": False,
        "historical_chronologies_authenticated": False,
        "per_sequence_rights_cleared": False,
        "reproduction_input_complete": False,
        "publication_allowed": False,
        "scientifically_accepted": False,
        "scientific_acceptance": "not_evaluated",
    }
    observed_boundary = {
        "publication_metadata_only": inventory.publication_metadata_only,
        "raw_pollen_counts_authenticated": inventory.raw_pollen_counts_authenticated,
        "historical_chronologies_authenticated": (
            inventory.historical_chronologies_authenticated
        ),
        "per_sequence_rights_cleared": inventory.per_sequence_rights_cleared,
        "reproduction_input_complete": inventory.reproduction_input_complete,
        "publication_allowed": inventory.publication_allowed,
        "scientifically_accepted": inventory.scientifically_accepted,
        "scientific_acceptance": inventory.scientific_acceptance,
    }
    if observed_boundary != expected_boundary:
        raise StudyInputProductError(
            "LandClim inventory admission boundary changed; version the producer"
        )
    return inventory


def _raw(record: StudyMetadataRecord, column: str) -> str | None:
    matches = [value.raw for value in record.values if value.column == column]
    if len(matches) != 1:
        raise StudyInputProductError(
            f"LandClim metadata row {record.worksheet_row} lacks {column!r}"
        )
    return matches[0]


def _records_bytes(inventory: LandClimStudyMetadataInventory) -> bytes:
    chunks = []
    inventory_sha256 = inventory.sha256
    for record in inventory.records:
        payload = record.payload()
        payload["schema_version"] = "essd-study-metadata-record.v1"
        payload["inventory_sha256"] = inventory_sha256
        chunks.append(_json_line(payload))
    return b"".join(chunks)


def _crosswalk_bytes(inventory: LandClimStudyMetadataInventory) -> bytes:
    stream = io.StringIO(newline="")
    columns = (
        "worksheet_row",
        "source_locator",
        "publication_site_name_raw",
        "publication_csvfilename_raw",
        "publication_country_raw",
        "publication_source_credit_raw",
        "publication_restriction_label_raw",
        "historical_primary_input_identity",
        "current_revision_identity",
        "historical_primary_identity_status",
        "current_revision_identity_status",
        "crosswalk_status",
        "reason_code",
    )
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    for record in inventory.records:
        writer.writerow(
            (
                record.worksheet_row,
                record.source_locator,
                _raw(record, "SiteName"),
                _raw(record, "csvfilename"),
                _raw(record, "Country"),
                _raw(record, "Database/Authorname and/or data collector"),
                _raw(record, "DataRestricted/NotRestriced"),
                "",
                "",
                "not_authenticated",
                "not_evaluated",
                "unresolved",
                "metadata_only_no_authenticated_primary_or_revision_identity",
            )
        )
    return stream.getvalue().encode("utf-8")


def _refusals_bytes(inventory: LandClimStudyMetadataInventory) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        (
            "namespace",
            "worksheet_row",
            "source_locator",
            "requirement",
            "state",
            "reason_code",
            "evidence_note",
        )
    )
    for record in inventory.records:
        for requirement, state, reason_code in _REFUSAL_REQUIREMENTS:
            writer.writerow(
                (
                    "essd-study-input-requirement.v1",
                    record.worksheet_row,
                    record.source_locator,
                    requirement,
                    state,
                    reason_code,
                    "Pinned publication metadata row; "
                    "no authenticated primary input closure",
                )
            )
    return stream.getvalue().encode("utf-8")


def _label_counts(
    inventory: LandClimStudyMetadataInventory, column: str
) -> list[JsonObject]:
    counts = Counter(_raw(record, column) for record in inventory.records)
    return [
        {"raw": raw, "record_count": count}
        for raw, count in sorted(
            counts.items(), key=lambda item: (item[0] is not None, item[0] or "")
        )
    ]


def _report(inventory: LandClimStudyMetadataInventory) -> JsonObject:
    refusal_count = _EXPECTED_RECORDS * len(_REFUSAL_REQUIREMENTS)
    return {
        "schema_version": "essd-study-input-metadata-report.v1",
        "profile": "landclim-ii-publication-metadata-only-v1",
        "task_scope": "V2-ESSD-003-partial-input-accounting",
        "scope": {
            "pinned_publication_metadata_inventory_complete": True,
            "publication_metadata_only": True,
            "source_labels_are_not_governed_country_or_rights_decisions": True,
        },
        "denominators": {
            "expected_study_records": _EXPECTED_RECORDS,
            "publication_metadata_records": inventory.metadata_record_count,
            "crosswalk_ledger_records": inventory.metadata_record_count,
            "refusal_ledger_records": refusal_count,
            "authenticated_primary_pollen_count_records": 0,
            "authenticated_historical_chronology_records": 0,
            "authenticated_historical_current_revision_matches": 0,
            "rights_cleared_records": 0,
            "reproduction_ready_records": 0,
        },
        "source_label_denominators": {
            "publication_country_raw": _label_counts(inventory, "Country"),
            "publication_restriction_raw": _label_counts(
                inventory, "DataRestricted/NotRestriced"
            ),
        },
        "claims": _claims(),
        "blocking_dependencies": [
            "historical primary pollen counts and sample identities",
            "historical selected chronology and age-model identities",
            "historical-to-current source revision decisions",
            "per-sequence rights and redistribution decisions",
            "publication-specific R execution and intermediate matrices",
            "qualified 11/12/13 PFT discrepancy disposition",
            "qualified scientific review",
        ],
    }


def _manifest(
    inventory: LandClimStudyMetadataInventory, peers: dict[str, bytes]
) -> JsonObject:
    logical_rows = {
        _RECORDS: _EXPECTED_RECORDS,
        _CROSSWALK: _EXPECTED_RECORDS,
        _REFUSALS: _EXPECTED_RECORDS * len(_REFUSAL_REQUIREMENTS),
        _REPORT: 1,
    }
    artifacts: list[JsonObject] = []
    for name in (_RECORDS, _CROSSWALK, _REFUSALS, _REPORT):
        content = peers[name]
        artifacts.append(
            {
                "path": name,
                "byte_count": len(content),
                "sha256": _sha256(content),
                "logical_rows": logical_rows[name],
            }
        )
    return {
        "schema_version": "essd-study-input-metadata-manifest.v1",
        "producer": "bijux_pollenomics_dev.essd_reproduction.study_inputs",
        "profile": "landclim-ii-publication-metadata-only-v1",
        "source": {
            "inventory_schema_version": inventory.schema_version,
            "inventory_sha256": inventory.sha256,
            "inventory_canonical_byte_count": len(inventory.canonical_bytes),
            "dataset_doi": inventory.dataset_doi,
            "sheet_name": inventory.sheet_name,
            "header": list(inventory.header),
            "receipt": {
                "path": "data/landclim/raw/landclim_sources.json",
                "sha256": inventory.receipt_sha256,
            },
            "workbook": {
                "path": "data/landclim/raw/landclim_ii_site_metadata.xlsx",
                "sha256": inventory.workbook_sha256,
            },
        },
        "output_contract": {
            "output_file_count": len(_OUTPUT_NAMES),
            "publication_metadata_records": _EXPECTED_RECORDS,
            "crosswalk_ledger_records": _EXPECTED_RECORDS,
            "refusal_ledger_records": (_EXPECTED_RECORDS * len(_REFUSAL_REQUIREMENTS)),
            "csv_null_encoding": (
                "empty_field_only_with_an_explicit_status_or_source_raw_field"
            ),
        },
        "artifacts": artifacts,
        "claims": _claims(),
    }


def build_study_input_products(raw_dir: Path) -> dict[str, bytes]:
    """Build five deterministic metadata-only ESSD products."""
    inventory = _validate_inventory(read_landclim_study_inventory(Path(raw_dir)))
    reopened = reopen_landclim_study_inventory(inventory.canonical_bytes, Path(raw_dir))
    if reopened != inventory:
        raise StudyInputProductError(
            "LandClim inventory did not reopen from its authenticated parents"
        )
    peers = {
        _RECORDS: _records_bytes(inventory),
        _CROSSWALK: _crosswalk_bytes(inventory),
        _REFUSALS: _refusals_bytes(inventory),
        _REPORT: _json_bytes(_report(inventory)),
    }
    return {_MANIFEST: _json_bytes(_manifest(inventory, peers)), **peers}


def _validate_directory(output: Path, expected: dict[str, bytes]) -> dict[str, bytes]:
    if output.is_symlink() or not output.is_dir():
        raise StudyInputProductError(
            "ESSD study-input product must be a direct regular directory"
        )
    children = list(output.iterdir())
    if {path.name for path in children} != set(_OUTPUT_NAMES):
        raise StudyInputProductError(
            "ESSD study-input product file inventory does not match"
        )
    for name in _OUTPUT_NAMES:
        path = output / name
        if path.is_symlink() or not path.is_file():
            raise StudyInputProductError(f"ESSD study-input product is unsafe: {name}")
        if path.read_bytes() != expected[name]:
            raise StudyInputProductError(
                f"ESSD study-input product does not match raw parents: {name}"
            )
    return expected


def validate_study_input_products(raw_dir: Path, output: Path) -> dict[str, bytes]:
    """Rebuild from raw parents and exact-compare all five product files."""
    return _validate_directory(Path(output), build_study_input_products(Path(raw_dir)))


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _refuse_symlink_ancestors(path: Path) -> None:
    candidate = path.parent
    while True:
        if candidate.is_symlink():
            raise StudyInputProductError(
                f"Refusing a symlinked ESSD output ancestor: {candidate}"
            )
        parent = candidate.parent
        if parent == candidate:
            return
        candidate = parent


def _require_new_output(output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace existing output: {output}")


def publish_study_input_products(raw_dir: Path, output: Path) -> JsonObject:
    """Atomically publish a new, source-bound five-file ESSD bundle."""
    products = build_study_input_products(Path(raw_dir))
    output = Path(output).absolute()
    _refuse_symlink_ancestors(output)
    _require_new_output(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    _refuse_symlink_ancestors(output)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name in _OUTPUT_NAMES:
            with (temporary / name).open("xb") as stream:
                stream.write(products[name])
                stream.flush()
                os.fsync(stream.fileno())
        _validate_directory(temporary, products)
        _fsync_directory(temporary)
        _refuse_symlink_ancestors(output)
        _require_new_output(output)
        os.replace(temporary, output)
        _fsync_directory(output.parent)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return _json_object(products[_MANIFEST], _MANIFEST)


def main(argv: Sequence[str] | None = None) -> int:
    """Publish the bounded metadata/refusal bundle from the pinned raw directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest = publish_study_input_products(args.raw_dir, args.output)
    contract = cast(JsonObject, manifest["output_contract"])
    print(
        json.dumps(
            {
                "output": str(args.output),
                "publication_metadata_records": contract[
                    "publication_metadata_records"
                ],
                "refusal_ledger_records": contract["refusal_ledger_records"],
                "whole_paper_reproduction_certified": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
