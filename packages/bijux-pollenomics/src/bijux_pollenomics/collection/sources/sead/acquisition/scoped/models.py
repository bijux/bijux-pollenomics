"""Scoped-acquisition identities, dependencies, and result models."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
    SeadTableAcquisition,
)


SCOPED_RECEIPT_SCHEMA_VERSION = "sead-scoped-acquisition-receipt.v1"
SCOPED_RESULT_SCHEMA_VERSION = "sead-scoped-acquisition-result.v1"
SCOPED_ORCHESTRATOR_VERSION = "sead-scoped-relation-acquisition.v1"
FULL_EVIDENCE_ORCHESTRATOR_VERSION = "sead-full-evidence-acquisition.v1"
NORDIC_TARGET_COUNTRIES = tuple(NORDIC_COUNTRY_CODES[:-1])

_SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


@dataclass(frozen=True)
class SeadDependency:
    """One upstream field whose values define a downstream query scope."""

    table: str
    field: str


@dataclass(frozen=True)
class SeadScopedTablePlan:
    """Projection and dependency filter for one SEAD table."""

    table: str
    primary_key: str
    projection: str
    filter_field: str
    dependencies: tuple[SeadDependency, ...]


@dataclass(frozen=True)
class SeadJoinPlan:
    """One relation edge to reconcile after scoped acquisition."""

    edge: str
    parent_table: str
    child_table: str
    parent_key: str
    child_key: str
    child_foreign_key: str
    reference_required: bool


@dataclass(frozen=True)
class SeadScopedAcquisitionResult:
    """In-memory result plus the immutable manifest path."""

    schema_version: str
    scope_id: str
    run_id: str
    parent_run_id: str
    build_id: str
    manifest_path: Path
    acquisitions: tuple[SeadTableAcquisition, ...]
    country_reconciliation: dict[str, object]
    join_reconciliations: tuple[dict[str, object], ...]


_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)
