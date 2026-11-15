"""Derive source unit metadata profiles beside unchanged HTTP capture ledgers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from .profiles import (
    _UnavailableUnitSource,
    parse_neotoma_unit_source,
    summarize_unit_source,
)
from .replay import read_neotoma_unit_body, replay_neotoma_unit_resources


def qualify_neotoma_unit_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    roster_path: Path,
    metadata_captures: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Reconcile full endpoint obligations before reading actual source buffers."""
    capture = replay_neotoma_unit_resources(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        roster_path=roster_path,
        metadata_captures=metadata_captures,
        limits=limits,
    )
    rows = []
    for entry in capture.units:
        scope = entry["identity"]
        row: dict[str, Any] = {
            "unit_key": entry["unit_key"],
            "scope": scope,
            "source_terminal_status": entry["terminal_status"],
            "scientific_admission": "not_asserted",
        }
        rows.append(row)
        if scope["exposure_role"] not in DEVELOPMENT_ROLES:
            row["qualification_status"] = "not_qualified_exposure_role"
            continue
        if entry["terminal_status"] != "received_complete_unqualified_unit_resource":
            row["qualification_status"] = "not_qualified_source_result"
            continue
        body = read_neotoma_unit_body(
            directory,
            expected_manifest_sha256=expected_manifest_sha256,
            unit_key=entry["unit_key"],
            roster_path=roster_path,
            metadata_captures=metadata_captures,
            limits=limits,
        )
        reference = entry["attempts"][-1]
        row["scope"] = body.scope
        row["source"] = {
            "capture_manifest_sha256": capture.manifest_sha256,
            "unit_key": body.unit_key,
            "content_version": "current",
            "api_version": "v2.0",
            "receipt_file": reference["receipt_file"],
            "receipt_sha256": body.receipt_sha256,
            "body_file": reference["body_file"],
            "body_sha256": body.body_sha256,
        }
        try:
            parsed = parse_neotoma_unit_source(
                body.scope, body.body, expected_body_sha256=body.body_sha256
            )
            row.update(
                qualification_status="parsed_unit_source",
                summary=summarize_unit_source(parsed),
            )
        except _UnavailableUnitSource as error:
            row.update(
                qualification_status="unavailable_unit_api_empty",
                reason=str(error),
                absence_certified=False,
            )
        except ValueError as error:
            row.update(qualification_status="refused_unit_source", reason=str(error))
    return {
        "schema_version": "neotoma-unit-source-qualification.v1",
        "source_capture_manifest_sha256": capture.manifest_sha256,
        "source_capture_relabelled": False,
        "units": rows,
        "partitions": dict(
            sorted(Counter(row["qualification_status"] for row in rows).items())
        ),
        "scope": "selected current collection-unit entities; no complete physical-entity or vegetation-reference population claim",
        "HTTP_requests": 0,
        "scientific_admission": "not_asserted",
    }
