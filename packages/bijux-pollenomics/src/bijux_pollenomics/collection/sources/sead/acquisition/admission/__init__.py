"""Validate and immutably admit completed SEAD acquisitions."""

from .models import (
    ADMISSION_SCHEMA_VERSION,
    SeadAcquisitionAdmission,
    SeadAdmissionExpectedIdentity,
    SeadMaterializedAdmissionSnapshot,
)
from .service import (
    materialize_sead_acquisition_admission,
    materialize_sead_full_evidence_admission,
    read_materialized_sead_full_evidence_admission,
    validate_materialized_sead_full_evidence_admission,
    validate_sead_acquisition_admission,
    validate_sead_full_evidence_admission,
)

__all__ = [
    "ADMISSION_SCHEMA_VERSION",
    "SeadAcquisitionAdmission",
    "SeadAdmissionExpectedIdentity",
    "SeadMaterializedAdmissionSnapshot",
    "materialize_sead_full_evidence_admission",
    "materialize_sead_acquisition_admission",
    "validate_materialized_sead_full_evidence_admission",
    "read_materialized_sead_full_evidence_admission",
    "validate_sead_full_evidence_admission",
    "validate_sead_acquisition_admission",
]
