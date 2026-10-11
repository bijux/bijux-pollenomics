"""Normalize source-row ownership through the existing AADR reconciliation."""

from __future__ import annotations

from collections.abc import Iterator

from ..projection import (
    build_aadr_accountability_summary,
    iter_aadr_accountability_records,
)
from ..reconciliation import AadrPanelReconciliation
from .contracts import (
    boundary,
    claim_key,
    member_key,
    object_mapping,
    object_rows,
    strings,
    text,
    validate_digest,
)


def iter_member_documents(
    reconciliation: AadrPanelReconciliation,
    *,
    release_manifest_sha256: str,
) -> Iterator[tuple[str, dict[str, object]]]:
    """Yield ownership-table records without copying raw tokens into each claim."""
    validate_digest(release_manifest_sha256)
    summary = build_aadr_accountability_summary(reconciliation)
    yield "source_files.json", {"source_files": summary["source_files"]}
    for record in iter_aadr_accountability_records(reconciliation):
        source_rows = object_rows(record["source_rows"])
        row_keys = [
            text(object_mapping(row["source_row"])["key"]) for row in source_rows
        ]
        keyed = record["record_kind"] == "reconciled_genetic_id"
        owner_kind = "member" if keyed else "unkeyed_row"
        owner = (
            member_key(release_manifest_sha256, text(record["genetic_id"]))
            if keyed
            else row_keys[0]
        )
        for row in source_rows:
            yield "source_rows.ndjson", row
        claims: dict[str, list[str]] = {"coordinate": [], "chronology": []}
        for kind in claims:
            for evidence in object_rows(record[f"{kind}_evidence_groups"]):
                key = claim_key(
                    kind, owner_kind, owner, strings(evidence["source_row_keys"])
                )
                claims[kind].append(key)
                yield (
                    f"{kind}_claims.ndjson",
                    {
                        "claim_key": key,
                        "owner_kind": owner_kind,
                        "owner_key": owner,
                        "evidence": evidence,
                    },
                )
        common: dict[str, object] = {
            "genetic_id_raw_values": record["genetic_id_raw_values"],
            "dataset_names": record["dataset_names"],
            "statuses": record["statuses"],
            "source_row_keys": row_keys,
            "coordinate_claim_keys": claims["coordinate"],
            "chronology_claim_keys": claims["chronology"],
            "admission_boundary": boundary(),
        }
        if keyed:
            yield (
                "members.ndjson",
                {"member_key": owner, "genetic_id": record["genetic_id"], **common},
            )
        else:
            yield (
                "unkeyed_rows.ndjson",
                {
                    "source_row_key": owner,
                    "refusal_reason_code": record["refusal_reason_code"],
                    **common,
                },
            )
