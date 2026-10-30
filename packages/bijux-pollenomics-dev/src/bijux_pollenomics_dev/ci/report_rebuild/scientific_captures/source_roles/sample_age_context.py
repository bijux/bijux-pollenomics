"""Authenticate additive sample-age context without relabelling native execution."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

_SAMPLE_AGE_CONTEXT_CONTRACTS: dict[
    str, tuple[int, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/evidence/chronology/audits/provenance.py": (
        2345,
        "f04ffd34c9230ef788bdb5f26cc9123591a1dbb6d52daa3061c29f51b2e5ea01",
        (
            (
                b"""from __future__ import annotations

from pathlib import Path


def _build_sample_chronology_provenance_rows(
""",
                b"""from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.tables.horse_source_fields import (
    horse_source_chronology_fields,
)
from bijux_pollenomics.adna.projects.sample_master.tables.horse_source_fields.alternatives import (
    horse_source_chronology_alternatives,
)


def _build_sample_chronology_provenance_rows(
""",
            ),
            (
                b"""
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            temporal_semantics = _temporal_semantics_for_chronology_row(row)
            rows.append(
                {
""",
                b"""
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        project_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        horse_fields: dict[str, dict[str, object]] = {}
        if project.project_accession == "PRJEB31613":
            master_rows = build_project_sample_master_rows(output_root, "PRJEB31613")
            source_owners = {
                row.repo_stable_sample_id: (
                    row.preferred_sample_label,
                    row.sample_lineage_locator,
                    row.sample_lineage_path,
                )
                for row in master_rows
            }
            chronology_owners = {
                row.repo_stable_sample_id: row.preferred_sample_label
                for row in project_rows
            }
            if (
                len(source_owners) != len(master_rows)
                or len(chronology_owners) != len(project_rows)
                or {key: owner[0] for key, owner in source_owners.items()}
                != chronology_owners
            ):
                raise ValueError("Horse master and chronology owner identities differ")
            horse_fields = horse_source_chronology_fields(
                output_root,
                owners=source_owners,
            )
        for row in project_rows:
            temporal_semantics = _temporal_semantics_for_chronology_row(row)
            rows.append(
                {
""",
            ),
            (
                b"""                    "time_end_bp": row.time_end_bp,
                    "time_mean_bp": row.time_mean_bp,
                    "temporal_semantics": temporal_semantics,
                }
            )
    rows.sort(
""",
                b"""                    "time_end_bp": row.time_end_bp,
                    "time_mean_bp": row.time_mean_bp,
                    "temporal_semantics": temporal_semantics,
                    **(
                        {
                            "source_chronology_fields": horse_fields[
                                row.repo_stable_sample_id
                            ],
                            "source_chronology_alternatives": horse_source_chronology_alternatives(
                                horse_fields[row.repo_stable_sample_id]
                            ),
                        }
                        if horse_fields
                        else {}
                    ),
                }
            )
    rows.sort(
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/sead/evidence/claims.py": (
        11264,
        "d2df7e356114828568e24cf00992858412d560fd361cc01457c227baf0d7f8f3",
        (
            (
                b''')

from .....core.files import write_json

CLAIM_BUNDLE_SCHEMA_VERSION: Final = "sead-chronology-claim-bundle.v1"
CLAIM_SCHEMA_VERSION: Final = "sead-chronology-claim.v1"


def build_sead_chronology_claim_bundle(
    acquisition_root: Path,
) -> dict[str, object]:
    """Validate raw-parent bytes and build one claim for every chronology row."""
    root = acquisition_root.resolve(strict=True)
''',
                b''')

from .....core.files import write_json
from .native_rows import attach_sead_native_source_rows

CLAIM_BUNDLE_SCHEMA_VERSION: Final = "sead-chronology-claim-bundle.v1"
CLAIM_SCHEMA_VERSION: Final = "sead-chronology-claim.v1"


def build_sead_chronology_claim_bundle(
    acquisition_root: Path, *, include_native_source_rows: bool = False
) -> dict[str, object]:
    """Validate raw-parent bytes and build one claim for every chronology row."""
    root = acquisition_root.resolve(strict=True)
''',
            ),
            (
                b'''        copied[relative_path] = payload

    return build_sead_chronology_claim_bundle_from_snapshot(
        SeadMaterializedAdmissionSnapshot(admission=admission, copied_files=copied)
    )


def build_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot,
) -> dict[str, object]:
    """Build claims exclusively from bytes retained by admission validation."""
    admission = snapshot.admission
''',
                b'''        copied[relative_path] = payload

    return build_sead_chronology_claim_bundle_from_snapshot(
        SeadMaterializedAdmissionSnapshot(admission=admission, copied_files=copied),
        include_native_source_rows=include_native_source_rows,
    )


def build_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot,
    *,
    include_native_source_rows: bool = False,
) -> dict[str, object]:
    """Build claims exclusively from bytes retained by admission validation."""
    admission = snapshot.admission
''',
            ),
            (
                b"""        claim_row["source_payload_sha256"] = payload_digests[claim["source_table"]]
        claim_row["acquisition_manifest_sha256"] = manifest_sha256

    country_counts = _partition_counts(claims, "country_code")
    claim_type_counts = _partition_counts(claims, "claim_type")
    comparability_counts = _partition_counts(claims, "comparability_status")
""",
                b"""        claim_row["source_payload_sha256"] = payload_digests[claim["source_table"]]
        claim_row["acquisition_manifest_sha256"] = manifest_sha256

    if include_native_source_rows:
        attach_sead_native_source_rows(claims, table_payloads)

    country_counts = _partition_counts(claims, "country_code")
    claim_type_counts = _partition_counts(claims, "claim_type")
    comparability_counts = _partition_counts(claims, "comparability_status")
""",
            ),
            (
                b'''

def write_sead_chronology_claim_bundle(
    acquisition_root: Path, output_path: Path
) -> Path:
    """Write the deterministic claim bundle through the repository JSON writer."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, build_sead_chronology_claim_bundle(acquisition_root))
    return destination


def write_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot, output_path: Path
) -> Path:
    """Write a claim bundle without reopening admission-controlled inputs."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, build_sead_chronology_claim_bundle_from_snapshot(snapshot))
    return destination


''',
                b'''

def write_sead_chronology_claim_bundle(
    acquisition_root: Path,
    output_path: Path,
    *,
    include_native_source_rows: bool = False,
) -> Path:
    """Write the deterministic claim bundle through the repository JSON writer."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bundle = (
        build_sead_chronology_claim_bundle(
            acquisition_root, include_native_source_rows=True
        )
        if include_native_source_rows
        else build_sead_chronology_claim_bundle(acquisition_root)
    )
    write_json(destination, bundle)
    return destination


def write_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot,
    output_path: Path,
    *,
    include_native_source_rows: bool = False,
) -> Path:
    """Write a claim bundle without reopening admission-controlled inputs."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bundle = (
        build_sead_chronology_claim_bundle_from_snapshot(
            snapshot, include_native_source_rows=True
        )
        if include_native_source_rows
        else build_sead_chronology_claim_bundle_from_snapshot(snapshot)
    )
    write_json(destination, bundle)
    return destination


''',
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/sead/evidence/normalization/models.py": (
        2176,
        "8b9643e4b059b63853094783f2b2b7ba6de209c282ea1d831da02bf22a52559f",
        (
            (
                b"""
from __future__ import annotations

from typing import TypedDict


class _TemporalRowGroup(TypedDict):
""",
                b"""
from __future__ import annotations

from typing import NotRequired, TypedDict


class _TemporalRowGroup(TypedDict):
""",
            ),
            (
                b"""    claim_type: str
    source_age_type: str
    source_age_value: dict[str, object]
    source_age_unit: str
    calibration_status: str
    younger_bp: int | None
""",
                b"""    claim_type: str
    source_age_type: str
    source_age_value: dict[str, object]
    source_native_row: NotRequired[dict[str, object]]
    source_age_unit: str
    calibration_status: str
    younger_bp: int | None
""",
            ),
        ),
    ),
}
SAMPLE_AGE_CONTEXT_SOURCES = frozenset(_SAMPLE_AGE_CONTEXT_CONTRACTS)
_SAMPLE_AGE_CONTEXT_CAPTURES = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


def sample_age_context_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Undo only the named context additions and require every original byte."""
    contract = _SAMPLE_AGE_CONTEXT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, checksum, pairs = contract
    if (
        len(captured) != size
        or hashlib.sha256(captured).hexdigest() != checksum
        or not 0 < len(current) <= 64 * 1024
    ):
        return False
    restored = current
    for previous, inserted in pairs:
        if captured.count(previous) != 1 or restored.count(inserted) != 1:
            return False
        restored = restored.replace(inserted, previous, 1)
    return restored == captured


def validated_sample_age_context_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Bind new source metadata and refusals to two fixed historical contexts."""
    name = historical.get("path")
    contract = (
        _SAMPLE_AGE_CONTEXT_CONTRACTS.get(name) if isinstance(name, str) else None
    )
    context = _SAMPLE_AGE_CONTEXT_CAPTURES.get(source_buffer.prefix)
    if contract is None or context is None or not isinstance(name, str):
        raise ReportRebuildError("Sample age source context is outside its fixed scope")
    size, checksum, _ = contract
    expected = {"bytes": size, "sha256": checksum}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Sample age source context binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current sample age context")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError("Sample age source must be bounded and single-link")
    current = path.read_bytes()
    if not sample_age_context_extension_matches(name, captured, current):
        raise ReportRebuildError("Sample age source differs beyond its named context")
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current sample age context")
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Sample age source changed during correspondence")
    return {
        "path": name,
        "classification": "additive_sample_age_source_context",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": checksum,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "old_selected_chronology_fields_preserved": True,
        "source_context_and_refusal_contract_intentionally_extended": True,
        "extension_kind": (
            "horse_literal_and_alternative_source_context"
            if name.endswith("/chronology/audits/provenance.py")
            else "sead_optional_native_source_rows_default_false"
        ),
        "current_provenance_output_equal_historical_claimed": False,
        "historical_native_execution_equal_current_claimed": False,
        "new_scientific_admission_claimed": False,
        "new_acquisition_or_native_execution_claimed": False,
        "historical_outputs_regenerated": False,
    }
