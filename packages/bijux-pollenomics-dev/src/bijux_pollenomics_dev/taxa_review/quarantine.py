"""Keep private intake header candidates outside accepted taxonomy namespaces."""

from __future__ import annotations

from typing import Any

from ..source_completion.evidence import EvidenceReader, digest
from .rows import review_row


def rootsi_rows(
    reader: EvidenceReader, path: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inventory = reader.json(path)
    if (
        inventory is None
        or inventory.get("schema_version") != "quarantined-rootsi-header-review.v1"
    ):
        raise ValueError("Missing or unsupported private Rootsi inspection")
    if (
        inventory.get("publication_allowed") is not False
        or inventory.get("derived_analysis_allowed") is not False
    ):
        raise ValueError("Rootsi quarantine restrictions are required")
    rows = []
    for header in inventory["headers"]:
        identity = [
            inventory["archive_sha256"],
            header["archive_member"],
            header["sheet"],
            header["column_index"],
        ]
        row = review_row(
            row_id=f"rootsi:column:{digest(identity)[:24]}",
            source="rootsi_private_quarantine",
            native_id=identity,
            label=None,
            domain="quarantined_column_header_candidates",
            evidence={
                "inventory_path": path,
                "archive_sha256": inventory["archive_sha256"],
                **header,
            },
        )
        row.update(
            source_header_candidates=header["source_header_candidates"],
            current_mapping_status="quarantined_unclassified",
            derived_analysis_allowed=False,
            country_dimension="source_receipt_country_claim_not_spatial_verification",
        )
        rows.append(row)
    return rows, {
        "archive_sha256": inventory["archive_sha256"],
        "workbook_sheet_count": len(inventory["workbooks"]),
        "column_count": len(rows),
        "header_row_selection": "unresolved; all first-six-row textual candidates retained",
        "publication_allowed": False,
        "derived_analysis_allowed": False,
    }
