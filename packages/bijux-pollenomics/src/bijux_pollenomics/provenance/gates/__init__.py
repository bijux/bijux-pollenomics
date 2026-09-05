"""Exact-command gate execution with durable, canonical evidence records."""

from __future__ import annotations

from .artifacts import (
    _artifact_member as _artifact_member,
    _atomic_replace as _atomic_replace,
    _fsync_directory as _fsync_directory,
    _prepare_artifacts_directory as _prepare_artifacts_directory,
    _temporary_path as _temporary_path,
)
from .catalog import (
    _GATE_FIXED_INPUTS as _GATE_FIXED_INPUTS,
    _GATE_GLOBS as _GATE_GLOBS,
    _GATE_TESTS as _GATE_TESTS,
    _GATE_TRUST_INPUTS as _GATE_TRUST_INPUTS,
)
from .codec import _canonical_bytes as _canonical_bytes
from .codec import _digest_json as _digest_json
from .execution import run_recorded_gate
from .model import RecordedGateSpecification
from .producer import (
    _LOCAL_ATTESTATION as _LOCAL_ATTESTATION,
    _PRODUCER_ID as _PRODUCER_ID,
    _PRODUCER_MODULE as _PRODUCER_MODULE,
    _PRODUCER_VERSION as _PRODUCER_VERSION,
    _producer_record as _producer_record,
    _producer_source_files as _producer_source_files,
    _read_executing_source_bytes as _read_executing_source_bytes,
    _runtime_identity as _runtime_identity,
)
from .repository import (
    _input_records as _input_records,
    _output_record as _output_record,
    _repository_root as _repository_root,
)
from .specification import build_product_gate_specification
from .validation import (
    _IDENTITY_PATTERN as _IDENTITY_PATTERN,
    _exact_argv as _exact_argv,
    _exact_environment as _exact_environment,
    _relative_parts as _relative_parts,
    _validate_gate_id as _validate_gate_id,
    _validate_passing_junit as _validate_passing_junit,
)

__all__ = [
    "RecordedGateSpecification",
    "build_product_gate_specification",
    "run_recorded_gate",
]
