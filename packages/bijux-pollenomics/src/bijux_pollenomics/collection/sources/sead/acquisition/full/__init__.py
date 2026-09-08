"""Auditable, fail-closed acquisition primitives for SEAD PostgREST tables."""

from __future__ import annotations

from . import model as _model
from . import publication as _publication
from . import reconciliation as _reconciliation
from . import retrieval as _retrieval
from . import serialization as _serialization
from . import validation as _validation

ACQUISITION_RECEIPT_SCHEMA_VERSION = _model.ACQUISITION_RECEIPT_SCHEMA_VERSION
TABLE_PAYLOAD_SCHEMA_VERSION = _model.TABLE_PAYLOAD_SCHEMA_VERSION
ACQUISITION_MANIFEST_SCHEMA_VERSION = _model.ACQUISITION_MANIFEST_SCHEMA_VERSION
ACQUISITION_TOOL_VERSION = _model.ACQUISITION_TOOL_VERSION
NORDIC_COUNTRY_CODES = _model.NORDIC_COUNTRY_CODES
SeadTableAcquisition = _model.SeadTableAcquisition
SeadAcquisitionError = _model.SeadAcquisitionError

acquire_sead_table = _retrieval.acquire_sead_table
reconcile_sead_countries = _reconciliation.reconcile_sead_countries
reconcile_sead_join = _reconciliation.reconcile_sead_join
assert_sead_join_complete = _reconciliation.assert_sead_join_complete
materialize_sead_acquisition = _publication.materialize_sead_acquisition

_build_result = _serialization.build_result
_raise_acquisition_error = _serialization.raise_acquisition_error
_observed_schema = _serialization.observed_schema
_json_type = _serialization.json_type
_payload_bytes = _serialization.payload_bytes
_canonical_bytes = _serialization.canonical_bytes
_utc_text = _serialization.utc_text
_child_identity = _reconciliation.child_identity_for
_validate_request = _validation.validate_request
_validate_table_name = _validation.validate_table_name
_safe_output_root = _validation.safe_output_root
_publish_directory = _publication.publish_directory

__all__ = [
    "NORDIC_COUNTRY_CODES",
    "SeadAcquisitionError",
    "SeadTableAcquisition",
    "acquire_sead_table",
    "assert_sead_join_complete",
    "materialize_sead_acquisition",
    "reconcile_sead_countries",
    "reconcile_sead_join",
]
