"""Validate source-owned references while reading topologically ordered surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .contract import SURFACE_ID_FIELDS, required_text

_PARENT_FIELDS = {
    "collection_units": (("site_id", "sites"),),
    "datasets": (("site_id", "sites"), ("collection_unit_id", "collection_units")),
    "chronologies": (("site_id", "sites"), ("collection_unit_id", "collection_units")),
    "chronology_controls": (
        ("site_id", "sites"),
        ("collection_unit_id", "collection_units"),
        ("chronology_id", "chronologies"),
    ),
    "samples": (
        ("site_id", "sites"),
        ("collection_unit_id", "collection_units"),
        ("dataset_id", "datasets"),
    ),
    "age_claims": (
        ("site_id", "sites"),
        ("collection_unit_id", "collection_units"),
        ("dataset_id", "datasets"),
        ("subject_id", "samples"),
        ("chronology_id", "chronologies"),
    ),
    "observations": (
        ("site_id", "sites"),
        ("collection_unit_id", "collection_units"),
        ("dataset_id", "datasets"),
        ("sample_id", "samples"),
        ("variable_id", "variables"),
    ),
}
_OWNER_FIELDS = ("site_id", "collection_unit_id", "dataset_id", "country_code")
_PARENT_SURFACES = frozenset(
    parent for edges in _PARENT_FIELDS.values() for _, parent in edges
)


class NeotomaOwnershipIndex:
    """Keep compact parent ownership, without retaining the observation population."""

    def __init__(self) -> None:
        self._parents: dict[str, dict[str, dict[str, object]]] = {}

    def validate_rows(self, surface: str, rows: Sequence[object]) -> None:
        """Refuse dangling links and ancestry contradictions before publication."""
        for value in rows:
            if not isinstance(value, Mapping):
                raise ValueError(f"Non-object row in Neotoma {surface}")
            identifier = required_text(
                value.get(SURFACE_ID_FIELDS[surface]), f"{surface} row ID"
            )
            if surface == "age_claims" and value.get("subject_type") != "sample":
                raise ValueError("Neotoma age claims must retain sample-owned subjects")
            for field, parent_surface in _PARENT_FIELDS.get(surface, ()):
                reference = value.get(field)
                if (
                    surface == "age_claims"
                    and field == "chronology_id"
                    and field in value
                    and reference is None
                ):
                    # Unresolved source chronology stays null; no replacement is inferred.
                    continue
                reference = required_text(reference, f"{surface}.{identifier}.{field}")
                parent = self._parents.get(parent_surface, {}).get(reference)
                if parent is None:
                    raise ValueError(
                        f"Neotoma {surface}.{identifier}.{field} has a missing parent"
                    )
                for owner_field in _OWNER_FIELDS:
                    if (
                        owner_field in parent
                        and value.get(owner_field) != parent[owner_field]
                    ):
                        raise ValueError(
                            f"Neotoma {surface}.{identifier} contradicts parent {owner_field}"
                        )
            if surface in _PARENT_SURFACES:
                record = {
                    field: value[field] for field in _OWNER_FIELDS if field in value
                }
                self._parents.setdefault(surface, {})[identifier] = record
