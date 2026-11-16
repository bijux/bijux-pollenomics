"""Typed access boundary for SEAD catalog source tables."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    fetch_sead_rows,
    fetch_sead_rows_by_ids,
)
from bijux_pollenomics.collection.sources.sead.acquisition.identifiers import (
    optional_sead_identifier,
    required_sead_identifier,
)

Row = dict[str, object]


class SeadTableReader(Protocol):
    """Provide projected source rows for the site inventory relation graph."""

    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]:
        """Read all source rows with an explicit projection and key order."""
        ...

    def rows_by_ids(
        self,
        table_name: str,
        *,
        select: str,
        filter_field: str,
        ids: Iterable[int],
        order_by: tuple[str, ...],
    ) -> list[Row]:
        """Read the source rows owned by the requested native identities."""
        ...


@dataclass(frozen=True, slots=True)
class ApiSeadTableReader:
    """Read provider rows through the bounded source query contract."""

    fetch_json_fn: Callable[..., object]

    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]:
        """Collect a complete source table under the declared projection."""
        return _owned_rows(
            table_name,
            fetch_sead_rows(
                table_name,
                fetch_json_fn=self.fetch_json_fn,
                select=select,
                order_by=order_by,
            ),
            select=select,
        )

    def rows_by_ids(
        self,
        table_name: str,
        *,
        select: str,
        filter_field: str,
        ids: Iterable[int],
        order_by: tuple[str, ...],
    ) -> list[Row]:
        """Collect exact requested identities through bounded provider queries."""
        return _owned_rows(
            table_name,
            fetch_sead_rows_by_ids(
                table_name,
                fetch_json_fn=self.fetch_json_fn,
                select=select,
                filter_field=filter_field,
                ids=ids,
                order_by=order_by,
            ),
            select=select,
        )


@dataclass(frozen=True, slots=True)
class MappingSeadTableReader:
    """Read admitted immutable rows without emulating HTTP pagination."""

    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]]

    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]:
        """Project admitted rows while retaining native source values."""
        return self._project_rows(
            table_name,
            select=select,
            order_by=order_by,
        )

    def rows_by_ids(
        self,
        table_name: str,
        *,
        select: str,
        filter_field: str,
        ids: Iterable[int],
        order_by: tuple[str, ...],
    ) -> list[Row]:
        """Select exact identities without rewriting source representations."""
        admitted_ids = {required_sead_identifier(value) for value in ids}
        return self._project_rows(
            table_name,
            select=select,
            order_by=order_by,
            filter_field=filter_field,
            admitted_ids=admitted_ids,
        )

    def _project_rows(
        self,
        table_name: str,
        *,
        select: str,
        order_by: tuple[str, ...],
        filter_field: str | None = None,
        admitted_ids: set[int] | None = None,
    ) -> list[Row]:
        if table_name not in self.rows_by_table:
            raise ValueError(f"SEAD acquisition table is unavailable: {table_name}")
        fields = select.split(",")
        projected_rows: list[Row] = []
        for source_row in self.rows_by_table[table_name]:
            if filter_field is not None and admitted_ids is not None:
                value = optional_sead_identifier(source_row.get(filter_field))
                if value not in admitted_ids:
                    continue
            missing_fields = set(fields) - set(source_row)
            if missing_fields:
                raise ValueError(
                    f"SEAD cached {table_name} row misses projected fields: "
                    f"{sorted(missing_fields)}"
                )
            projected_rows.append({field: source_row[field] for field in fields})
        if order_by:
            projected_rows.sort(
                key=lambda row: tuple(
                    _source_order_value(row, field) for field in order_by
                )
            )
        return _owned_rows(table_name, projected_rows, select=select)


def _owned_rows(table_name: str, rows: list[Row], *, select: str) -> list[Row]:
    """Require unique owners when the declared projection requests their key."""
    # The collection facade imports catalog projections during initialization.
    from bijux_pollenomics.collection.sources.sead.collection.validation import (
        primary_key_for_table,
    )

    try:
        primary_key = primary_key_for_table(table_name)
    except ValueError:
        # Generic projections have no declared owner in the site inventory graph.
        return rows
    fields = {field.strip() for field in select.split(",")}
    if primary_key not in fields and "*" not in fields:
        return rows
    seen: set[int] = set()
    for row in rows:
        identity = required_sead_identifier(row.get(primary_key))
        if identity in seen:
            raise ValueError(f"Duplicate SEAD {table_name}.{primary_key}: {identity}")
        seen.add(identity)
    return rows


def _source_order_value(row: Mapping[str, object], field: str) -> tuple[bool, object]:
    value = row.get(field)
    if field.endswith("_id"):
        value = optional_sead_identifier(value)
    return value is None, value


__all__ = ["ApiSeadTableReader", "MappingSeadTableReader", "SeadTableReader"]
