"""Acquire fixed source-context dependencies without country reconciliation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict
from functools import partial
import time

from ..client import build_sead_in_filter
from ..full import SeadAcquisitionError, acquire_sead_table
from ..full.serialization import canonical_bytes, payload_bytes
from ..scoped.codec import _validate_identity
from ..scoped.models import NORDIC_TARGET_COUNTRIES, SeadScopedTablePlan
from ..scoped.plans.scoped import SEAD_SCOPED_TABLE_PLANS
from ..scoped.plans.site import SEAD_SITE_TABLE_PLAN
from ..scoped.validation import _dependency_ids, _required_source_id
from .contracts import DEFAULT_CONTEXT_LIMITS, SeadContextLimits, SeadContextSite
from .transport import ContextResponse, ContextTransport

CONTEXT_SCHEMA = "sead-unresolved-source-context.v1"
CONTEXT_PLANS = (SEAD_SITE_TABLE_PLAN, *SEAD_SCOPED_TABLE_PLANS)
UNEXPANDED_REFERENCES = (
    "analysis_entity_ages.chronology_id",
    "geochronology.dating_lab_id",
    "dendro_dates.dendro_lookup_id",
    "dendro_dates.season_id",
)


class ContextCollector:
    """Keep one private context epoch and all partial bounded response evidence."""

    def __init__(
        self,
        *,
        sites: Sequence[SeadContextSite],
        run_id: str,
        parent_run_id: str,
        build_id: str,
        opener: Callable[..., ContextResponse],
        limits: SeadContextLimits = DEFAULT_CONTEXT_LIMITS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Own the selected identities before making any request."""
        self.sites = tuple(sites)
        if (
            not 1 <= len(self.sites) <= 2
            or any(type(site) is not SeadContextSite for site in self.sites)
            or len({site.site_id for site in self.sites}) != len(self.sites)
            or len({site.site_uuid for site in self.sites}) != len(self.sites)
        ):
            raise ValueError("Context requires one or two unique unresolved sites")
        self.sites = tuple(sorted(self.sites, key=lambda site: site.site_id))
        for field, value in (
            ("run_id", run_id),
            ("parent_run_id", parent_run_id),
            ("build_id", build_id),
        ):
            _validate_identity(value, field, path_segment=field == "run_id")
        if type(limits) is not SeadContextLimits:
            raise ValueError("Context requires the reviewed finite limit contract")
        self.identities = {
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
        }
        self.transport = ContextTransport(opener, limits=limits, clock=clock)
        self.tables: dict[str, tuple[dict[str, object], ...]] = {}
        self.receipts: dict[str, dict[str, object]] = {}
        self.query_receipts: list[dict[str, object]] = []
        self.complete = False
        self.started = False

    def _page(
        self,
        plan: SeadScopedTablePlan,
        batch: tuple[int, ...],
        seen: set[int],
        endpoint: str,
        **kwargs: object,
    ) -> object:
        rows = self.transport.fetch(endpoint, **kwargs)  # type: ignore[arg-type]
        if not isinstance(rows, list):
            raise ValueError("Context source page is not an array")
        selected = {site.site_id: site.site_uuid for site in self.sites}
        expanded_fields = {
            dependency.field
            for downstream in CONTEXT_PLANS
            for dependency in downstream.dependencies
            if dependency.table == plan.table
        }
        for row in rows:
            if set(row) != set(plan.projection.split(",")):
                raise ValueError("Context source projection differs from fixed fields")
            key, owner = row[plan.primary_key], row[plan.filter_field]
            if (
                type(key) is not int
                or key <= 0
                or type(owner) is not int
                or owner not in batch
            ):
                raise ValueError("Context source key or dependency owner is invalid")
            if key in seen:
                raise ValueError("Context source contains duplicate primary keys")
            for field in expanded_fields:
                if row[field] is not None:
                    _required_source_id(row, field)
            seen.add(key)
            if plan.table == "tbl_sites" and row["site_uuid"] != selected[key]:
                raise ValueError("Context source site UUID changed")
        return rows

    def _table(self, plan: SeadScopedTablePlan, requested: tuple[int, ...]) -> None:
        limits = self.transport.limits
        if len(requested) > limits.max_dependency_ids:
            raise ValueError("Context dependency identity budget exceeded")
        rows: list[dict[str, object]] = []
        queries: list[dict[str, object]] = []
        seen: set[int] = set()
        for start in range(0, len(requested), limits.batch_size):
            batch = requested[start : start + limits.batch_size]

            try:
                result = acquire_sead_table(
                    plan.table,
                    fetch_json_fn=partial(self._page, plan, batch, seen),
                    select=plan.projection,
                    filters=((plan.filter_field, build_sead_in_filter(list(batch))),),
                    order_by=tuple(
                        dict.fromkeys((plan.filter_field, plan.primary_key))
                    ),
                    country_scope=NORDIC_TARGET_COUNTRIES,
                    spatial_scope={
                        "kind": "unresolved_source_context",
                        "legacy_country_scope_meaning": "regional_request_intent_only",
                        **self.identities,
                    },
                    parent_run_id=self.identities["parent_run_id"],
                    build_id=self.identities["build_id"],
                    page_size=limits.page_size,
                    max_pages=limits.max_pages,
                    request_retries=1,
                    request_timeout_seconds=limits.timeout_seconds,
                )
            except SeadAcquisitionError as error:
                self.query_receipts.append(dict(error.result.receipt))
                raise
            except Exception as error:
                self.query_receipts.append(
                    {
                        "table": plan.table,
                        "requested_ids": list(batch),
                        "status": "refused_context_query",
                        "failure_type": type(error).__name__,
                    }
                )
                raise
            queries.append(result.receipt)
            self.query_receipts.append(result.receipt)
            rows.extend(result.rows)
        rows.sort(key=lambda row: _required_source_id(row, plan.primary_key))
        if plan.table == "tbl_sites" and set(seen) != set(requested):
            raise ValueError("Context response does not cover selected site identities")
        self.tables[plan.table] = tuple(rows)
        self.receipts[plan.table] = {
            "schema_version": "sead-context-table-receipt.v1",
            "table": plan.table,
            "requested_ids": list(requested),
            "row_count": len(rows),
            "completion_basis": "all_dependency_batches_source_eof"
            if requested
            else "empty_dependency_identity_set",
            "query_receipts": queries,
            "country_admission": False,
            "legacy_country_scope_meaning": "regional_request_intent_only",
        }

    def acquire(self) -> dict[str, object]:
        """Acquire every fixed dependency once; never resume a refused epoch."""
        if self.started:
            raise ValueError("Context epoch already started; automatic rerun refused")
        self.started = True
        for plan in CONTEXT_PLANS:
            requested = (
                tuple(site.site_id for site in self.sites)
                if plan.table == "tbl_sites"
                else _dependency_ids(plan.dependencies, self.tables)
            )
            self._table(plan, requested)
        if (
            self.transport.clock() - self.transport.started
            >= self.transport.limits.max_seconds
        ):
            raise ValueError("Context wall budget exhausted before completion")
        self.complete = True
        return self.manifest()

    def manifest(self) -> dict[str, object]:
        """Describe context scope without country, FK-closure or event authority."""
        return {
            "schema_version": CONTEXT_SCHEMA,
            "status": "complete_context_only"
            if self.complete
            else "partial_context_only",
            **self.identities,
            "sites": [asdict(site) for site in self.sites],
            "country_admission": False,
            "ecological_event_admission": False,
            "legacy_country_scope_meaning": "regional_request_intent_only",
            "regional_request_intent": list(NORDIC_TARGET_COUNTRIES),
            "unexpanded_native_references": list(UNEXPANDED_REFERENCES),
            "tables": list(self.tables),
            "limits": asdict(self.transport.limits),
            "requests": self.transport.requests,
            "request_count": self.transport.request_count,
            "response_bytes": self.transport.byte_count,
            "row_count": self.transport.row_count,
        }

    def files(self) -> dict[str, bytes]:
        """Return copied immutable buffers including evidence from refused queries."""
        files = dict(self.transport.responses)
        files.update(
            {
                f"payloads/{table}.json": payload_bytes(table, rows)
                for table, rows in self.tables.items()
            }
        )
        files.update(
            {
                f"receipts/{table}.json": canonical_bytes(receipt)
                for table, receipt in self.receipts.items()
            }
        )
        files["query-receipts.json"] = canonical_bytes(self.query_receipts)
        return files
