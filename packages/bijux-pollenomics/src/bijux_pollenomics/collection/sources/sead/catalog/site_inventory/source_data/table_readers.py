"""Typed access boundary for SEAD catalog source tables."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    fetch_sead_rows,
    fetch_sead_rows_by_ids,
)

Row = dict[str, object]


class SeadTableReader(Protocol):
    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]: ...

    def rows_by_ids(
        self,
        table_name: str,
        *,
        select: str,
        filter_field: str,
        ids: Iterable[int],
        order_by: tuple[str, ...],
    ) -> list[Row]: ...


@dataclass(frozen=True, slots=True)
class ApiSeadTableReader:
    fetch_json_fn: Callable[..., object]

    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]:
        return fetch_sead_rows(
            table_name,
            fetch_json_fn=self.fetch_json_fn,
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
        return fetch_sead_rows_by_ids(
            table_name,
            fetch_json_fn=self.fetch_json_fn,
            select=select,
            filter_field=filter_field,
            ids=ids,
            order_by=order_by,
        )


@dataclass(frozen=True, slots=True)
class MappingSeadTableReader:
    """Read admitted immutable rows without emulating HTTP pagination."""

    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]]

    def all_rows(
        self, table_name: str, *, select: str, order_by: tuple[str, ...]
    ) -> list[Row]:
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
        admitted_ids = {int(value) for value in ids}
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
                value = source_row.get(filter_field)
                if isinstance(value, bool) or not isinstance(value, int):
                    continue
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
                    (row.get(field) is None, row.get(field)) for field in order_by
                )
            )
        return projected_rows


__all__ = ["ApiSeadTableReader", "MappingSeadTableReader", "SeadTableReader"]
