"""Stable schema identities for compact AADR source accountability."""

from __future__ import annotations

AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION = "aadr-source-accountability.v1"
AADR_SOURCE_COUNTRY_POLICY_VERSION = "aadr-source-political-entity-exact.v1"
AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE = "application/x-ndjson"
AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS = "reproducible_untracked_artifact"

POLITICAL_ENTITY_DISPOSITIONS = (
    "DK",
    "FI",
    "NO",
    "SE",
    "other",
    "missing",
    "conflict",
)

__all__ = [
    "AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE",
    "AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS",
    "AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION",
    "AADR_SOURCE_COUNTRY_POLICY_VERSION",
    "POLITICAL_ENTITY_DISPOSITIONS",
]
