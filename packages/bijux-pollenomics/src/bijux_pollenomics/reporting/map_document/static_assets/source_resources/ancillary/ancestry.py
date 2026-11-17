"""Selected ancestry identities and recorded-only metadata posture."""

from collections.abc import Mapping
from typing import Any


def validate_selected_ancestry(
    header: Mapping[str, Any], records: list[dict[str, Any]]
) -> None:
    """Keep recorded graph projections distinct from permission or native validation."""
    if (
        header.get("integrity_scope") != "SELECTED_RECORDED_TARGETS_ONLY"
        or header.get("scientific_admission") != "not_asserted"
        or any(
            header.get(key) is not False
            for key in (
                "current_roles_revalidated",
                "native_source_fields_revalidated",
                "GET_authorized",
            )
        )
        or type(header.get("native_entity_bodies_opened")) is not int
        or header["native_entity_bodies_opened"] != 0
    ):
        raise ValueError("Selected ancestry metadata posture differs")
    seen = set()
    for record in records:
        row = record["entry"]
        kind, identity = row.get("kind"), row.get("native_id")
        key = row.get("target_key")
        node = row.get("recorded_node")
        if (
            type(kind) is not str
            or kind not in {"taxon", "publication"}
            or type(identity) is not int
            or not 0 < identity < 2**53
            or key != f"{kind}-{identity}"
            or key in seen
            or not isinstance(node, dict)
            or node.get("target_kind") != kind
            or any(
                node.get(field) != row[field]
                or type(node.get(field)) is not type(row[field])
                for field in ("target_key", "native_id")
            )
        ):
            raise ValueError("Selected ancestry target native identity differs")
        seen.add(key)
        if (
            row.get("integrity_scope") != "anchored_selected_metadata_parts_only"
            or row.get("scientific_admission") != "not_asserted"
            or any(
                row.get(field) is not False
                for field in (
                    "current_roles_revalidated",
                    "native_source_fields_revalidated",
                    "GET_authorized",
                )
            )
            or type(row.get("native_entity_bodies_opened")) is not int
            or row["native_entity_bodies_opened"] != 0
        ):
            raise ValueError("Selected ancestry target verification differs")
