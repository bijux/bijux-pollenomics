"""Exact-command gate execution with durable, canonical evidence records."""

from __future__ import annotations

from .artifacts import (
    _artifact_member as _artifact_member,
)
from .artifacts import (
    _atomic_replace as _atomic_replace,
)
from .artifacts import (
    _fsync_directory as _fsync_directory,
)
from .artifacts import (
    _prepare_artifacts_directory as _prepare_artifacts_directory,
)
from .artifacts import (
    _temporary_path as _temporary_path,
)
from .catalog import (
    _GATE_FIXED_INPUTS as _GATE_FIXED_INPUTS,
)
from .catalog import (
    _GATE_GLOBS as _GATE_GLOBS,
)
from .catalog import (
    _GATE_TESTS as _GATE_TESTS,
)
from .catalog import (
    _GATE_TRUST_INPUTS as _GATE_TRUST_INPUTS,
)
from .codec import _canonical_bytes as _canonical_bytes
from .codec import _digest_json as _digest_json
from .execution import run_recorded_gate
from .model import RecordedGateSpecification
from .producer import (
    _LOCAL_ATTESTATION as _LOCAL_ATTESTATION,
)
from .producer import (
    _PRODUCER_ID as _PRODUCER_ID,
)
from .producer import (
    _PRODUCER_MODULE as _PRODUCER_MODULE,
)
from .producer import (
    _PRODUCER_VERSION as _PRODUCER_VERSION,
)
from .producer import (
    _producer_record as _producer_record,
)
from .producer import (
    _producer_source_files as _producer_source_files,
)
from .producer import (
    _read_executing_source_bytes as _read_executing_source_bytes,
)
from .producer import (
    _runtime_identity as _runtime_identity,
)
from .repository import (
    _input_records as _input_records,
)
from .repository import (
    _output_record as _output_record,
)
from .repository import (
    _repository_root as _repository_root,
)
from .specification import build_product_gate_specification
from .validation import (
    _IDENTITY_PATTERN as _IDENTITY_PATTERN,
)
from .validation import (
    _exact_argv as _exact_argv,
)
from .validation import (
    _exact_environment as _exact_environment,
)
from .validation import (
    _relative_parts as _relative_parts,
)
from .validation import (
    _validate_gate_id as _validate_gate_id,
)
from .validation import (
    _validate_passing_junit as _validate_passing_junit,
)

__all__ = [
    "RecordedGateSpecification",
    "build_product_gate_specification",
    "run_recorded_gate",
]
