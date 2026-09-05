"""Complete admitted-acquisition fixture construction and entry points."""

from __future__ import annotations
from pathlib import Path
from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_VERSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    TABLE_PAYLOAD_SCHEMA_VERSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAcquisitionAdmission,
    SeadAdmissionExpectedIdentity,
    materialize_sead_acquisition_admission,
    validate_sead_acquisition_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SCOPED_RECEIPT_SCHEMA_VERSION,
    SEAD_SCOPED_TABLE_PLANS,
)

from .boundaries import _write_boundary_fixture
from .models import (
    _BUILD_ID,
    _JOIN_TABLES,
    _PARENT_RUN_ID,
    _RUN_ID,
    _SCOPE_ID,
    _SITE_PROJECTION,
    _TABLE_PRIMARY_KEYS,
)
from .receipts import _join_row, _query_receipt
from .serialization import (
    _canonical_bytes,
    _digest,
    _fixture_positive_int,
    _observed_schema,
    _read_json,
    _refresh_manifest,
    _refresh_scoped_receipt,
    _write_json,
)


def _expected_identity(
    snapshot: Path, decisions: Path
) -> SeadAdmissionExpectedIdentity:
    decision_payload = _read_json(decisions)
    boundary_authority = decision_payload.get("boundary_authority")
    if not isinstance(boundary_authority, dict):
        raise TypeError("fixture boundary authority must be an object")
    preflight = decision_payload.get("preflight_receipt")
    if not isinstance(preflight, dict):
        raise TypeError("fixture preflight receipt must be an object")
    return SeadAdmissionExpectedIdentity(
        scope_id=_SCOPE_ID,
        run_id=_RUN_ID,
        parent_run_id=_PARENT_RUN_ID,
        build_id=_BUILD_ID,
        country_authority_id=str(boundary_authority["authority_id"]),
        country_authority_artifact_digest=str(boundary_authority["artifact_digest"]),
        country_authority_root=(snapshot.parent.parent / "boundaries").resolve(),
        bbox_payload_sha256=str(preflight["content_sha256"]),
        acquisition_manifest_sha256=_digest((snapshot / "manifest.json").read_bytes()),
        country_decisions_sha256=_digest(decisions.read_bytes()),
    )


def _validate(snapshot: Path, decisions: Path) -> dict[str, object]:
    return validate_sead_acquisition_admission(
        snapshot,
        country_decisions_path=decisions,
        expected_identity=_expected_identity(snapshot, decisions),
    )


def _materialize(
    snapshot: Path, decisions: Path, output_root: Path
) -> SeadAcquisitionAdmission:
    return materialize_sead_acquisition_admission(
        snapshot,
        country_decisions_path=decisions,
        output_root=output_root,
        expected_identity=_expected_identity(snapshot, decisions),
    )


def _write_fixture(root: Path) -> tuple[Path, Path]:
    boundary_root, authority_id, authority_digest, boundary_version = (
        _write_boundary_fixture(root)
    )
    if boundary_root != (root / "boundaries").resolve():
        raise ValueError("fixture boundary root mismatch")
    boundary_manifest = _read_json(boundary_root / "raw" / "source_manifest.json")
    country_artifacts = boundary_manifest.get("country_artifacts")
    if not isinstance(country_artifacts, dict):
        raise TypeError("fixture country artifacts must be an object")
    country_artifact_sha256 = {
        country: str(record["sha256"])
        for country, record in country_artifacts.items()
        if isinstance(country, str) and isinstance(record, dict)
    }
    snapshot = root / "source" / "snapshot"
    rows_by_table: dict[str, list[dict[str, object]]] = {
        table: [] for table in SEAD_LINKED_SOURCE_TABLES
    }
    rows_by_table["tbl_sites"] = [
        {
            "site_id": 1,
            "site_name": "fixture",
            "national_site_identifier": None,
            "latitude_dd": 56.0,
            "longitude_dd": 13.0,
            "altitude": None,
            "site_description": None,
            "site_uuid": "fixture-site-uuid",
        }
    ]
    assignment_payload = [{"site_id": 1, "country_code": "SE"}]
    assignment_sha256 = _digest(_canonical_bytes(assignment_payload))
    base_scope: dict[str, object] = {
        "scope_id": _SCOPE_ID,
        "relation_scope": "chronology_relations",
        "countries": ["SE", "DK", "NO", "FI"],
        "bbox": [4.0, 54.0, 35.0, 72.0],
        "country_assignment_id": authority_id,
        "country_assignment_sha256": assignment_sha256,
        "orchestration_run_id": _RUN_ID,
        "parent_run_id": _PARENT_RUN_ID,
        "build_id": _BUILD_ID,
    }
    plans = {plan.table: plan for plan in SEAD_SCOPED_TABLE_PLANS}
    for table, rows in rows_by_table.items():
        primary_key = _TABLE_PRIMARY_KEYS[table]
        projection = (
            _SITE_PROJECTION if table == "tbl_sites" else plans[table].projection
        )
        payload = {
            "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
            "table": table,
            "rows": rows,
        }
        payload_path = snapshot / "payloads" / f"{table}.json"
        _write_json(payload_path, payload)
        schema = _observed_schema(rows)
        if table == "tbl_sites":
            requested_ids = [1]
            query_receipts = [
                _query_receipt(
                    table,
                    rows=rows,
                    spatial_scope={**base_scope, "kind": "governed_bbox"},
                )
            ]
        else:
            plan = plans[table]
            requested_ids = sorted(
                {
                    _fixture_positive_int(row[dependency.field])
                    for dependency in plan.dependencies
                    for row in rows_by_table[dependency.table]
                    if row.get(dependency.field) is not None
                }
            )
            query_receipts = (
                [
                    _query_receipt(
                        table,
                        rows=rows,
                        spatial_scope={
                            **base_scope,
                            "kind": "dependency_identity_filter",
                            "filter_field": plan.filter_field,
                            "filter_ids": requested_ids,
                        },
                    )
                ]
                if requested_ids
                else []
            )
        receipt: dict[str, object] = {
            "schema_version": SCOPED_RECEIPT_SCHEMA_VERSION,
            "source": "SEAD",
            "route": "postgrest_dependency_scoped",
            "table": table,
            "primary_key": primary_key,
            "projection": projection,
            "filter_field": primary_key
            if table == "tbl_sites"
            else plans[table].filter_field,
            "requested_identity_count": len(requested_ids),
            "requested_identities": requested_ids,
            "query_count": len(query_receipts),
            "query_receipts": query_receipts,
            "completion_basis": (
                "governed_bbox_filter"
                if table == "tbl_sites"
                else (
                    "all_dependency_batches_complete"
                    if requested_ids
                    else "empty_dependency_identity_set"
                )
            ),
            "country_scope": ["SE", "DK", "NO", "FI"],
            "spatial_scope": base_scope,
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "started_at": "2026-09-04T00:00:00Z",
            "completed_at": "2026-09-04T00:00:01Z",
            "row_count": len(rows),
            "canonical_schema": schema,
            "canonical_schema_sha256": _digest(_canonical_bytes(schema)),
            "content_sha256": _digest(payload_path.read_bytes()),
            "tool_version": "sead-scoped-relation-acquisition.v1",
            "status": "complete",
            "failure_reason": None,
        }
        if table == "tbl_sites":
            receipt.update(
                {
                    "bbox_row_count": 1,
                    "governed_row_count": 1,
                    "scope_excluded_site_ids": [],
                    "scope_exclusion_reason": "country_assignment_unassigned",
                    "governed_country_assignments": assignment_payload,
                }
            )
        _refresh_scoped_receipt(receipt)
        _write_json(snapshot / "receipts" / f"{table}.json", receipt)

    _write_json(
        snapshot / "reconciliation" / "countries.json",
        {
            "schema_version": "sead-country-reconciliation.v1",
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "row_count": 1,
            "counts": {"SE": 1, "DK": 0, "NO": 0, "FI": 0, "UNASSIGNED": 0},
            "assigned_count": 1,
            "unassigned_count": 0,
            "duplicate_site_ids": [],
            "reconciles": True,
            "bbox_row_count": 1,
            "scope_excluded_count": 0,
            "scope_excluded_site_ids": [],
            "country_assignment_id": authority_id,
            "country_assignment_sha256": assignment_sha256,
        },
    )
    _write_json(
        snapshot / "reconciliation" / "joins.json",
        {
            "schema_version": "sead-join-reconciliations.v1",
            "edges": [
                _join_row(edge, parent, child, rows_by_table)
                for edge, (parent, child) in _JOIN_TABLES.items()
            ],
        },
    )
    _refresh_manifest(snapshot)
    decisions = root / "source" / "country-decisions.json"
    _write_json(
        decisions,
        {
            "schema_version": "sead-live-country-decisions.v1",
            "job_id": _PARENT_RUN_ID,
            "run_id": _RUN_ID,
            "input_id": _SCOPE_ID,
            "build_id": _BUILD_ID,
            "bbox": [4.0, 54.0, 35.0, 72.0],
            "bbox_site_count": 1,
            "boundary_authority": {
                "schema": "nordic-boundary-authority-identity.v1",
                "authority_id": authority_id,
                "artifact_digest": authority_digest,
                "version": NATURAL_EARTH_VERSION,
                "manifest_sha256": _digest(
                    (boundary_root / "raw" / "source_manifest.json").read_bytes()
                ),
                "normalized_artifact_sha256": authority_digest.removeprefix("sha256:"),
                "source_asset_sha256": "6" * 64,
                "country_artifact_sha256": {
                    country: country_artifact_sha256[country]
                    for country in BOUNDARY_CODES
                },
            },
            "preflight_receipt": _query_receipt(
                "tbl_sites",
                rows=rows_by_table["tbl_sites"],
                spatial_scope={
                    **base_scope,
                    "scope_id": _SCOPE_ID,
                    "kind": "governed_bbox_country_decision_preflight",
                    "boundary_authority_id": authority_id,
                },
                parameters=[
                    [
                        "select",
                        _SITE_PROJECTION,
                    ],
                    ["latitude_dd", "gte.54.0"],
                    ["latitude_dd", "lte.72.0"],
                    ["longitude_dd", "gte.4.0"],
                    ["longitude_dd", "lte.35.0"],
                    ["order", "site_id"],
                ],
                max_pages=100,
            ),
            "country_counts": {
                "SE": 1,
                "DK": 0,
                "NO": 0,
                "FI": 0,
                "UNASSIGNED": 0,
            },
            "decision_method_counts": {"strict_boundary_containment": 1},
            "decision_status_counts": {"assigned": 1},
            "decisions": [
                {
                    "site_id": 1,
                    "site_uuid": "fixture-site-uuid",
                    "latitude_dd": 56.0,
                    "longitude_dd": 13.0,
                    "governed_country_code": "SE",
                    "decision": {
                        "decision_status": "assigned",
                        "decision_method": "strict_boundary_containment",
                        "candidate_countries": ["Sweden"],
                        "derived_country": "Sweden",
                        "ambiguity_reason": None,
                        "refusal_reason": None,
                        "raw_country": None,
                        "raw_country_comparison": "not_supplied",
                        "boundary_artifact_digest": authority_digest,
                        "boundary_version": boundary_version,
                    },
                }
            ],
        },
    )
    return snapshot.resolve(), decisions.resolve()
