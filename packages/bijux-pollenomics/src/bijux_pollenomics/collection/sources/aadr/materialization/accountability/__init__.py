"""Compact, non-admitting AADR source-accountability materialization."""

from .contracts import (
    AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE,
    AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS,
    AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
    AADR_SOURCE_COUNTRY_POLICY_VERSION,
)
from .models import (
    AadrPoliticalEntityEvidence,
    AadrPoliticalEntityEvidenceGroup,
    AadrPoliticalEntityReconciliation,
    AadrReleaseManifestIdentity,
)
from .political_entities import (
    FOUR_COUNTRY_EXACT_SOURCE_VALUES,
    reconcile_source_reported_political_entities,
    source_reported_political_entity_evidence,
)
from .projection import (
    build_aadr_accountability_stream_descriptor,
    build_aadr_source_accountability_receipt,
)
from .publication import (
    canonical_aadr_source_accountability_bytes,
    write_aadr_source_accountability_receipt,
)
from .validation import validate_aadr_source_accountability_receipt

__all__ = [
    "AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE",
    "AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS",
    "AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION",
    "AADR_SOURCE_COUNTRY_POLICY_VERSION",
    "FOUR_COUNTRY_EXACT_SOURCE_VALUES",
    "AadrPoliticalEntityEvidence",
    "AadrPoliticalEntityEvidenceGroup",
    "AadrPoliticalEntityReconciliation",
    "AadrReleaseManifestIdentity",
    "build_aadr_accountability_stream_descriptor",
    "build_aadr_source_accountability_receipt",
    "canonical_aadr_source_accountability_bytes",
    "reconcile_source_reported_political_entities",
    "source_reported_political_entity_evidence",
    "validate_aadr_source_accountability_receipt",
    "write_aadr_source_accountability_receipt",
]
