"""Deterministic, refusal-safe classification-audit publication."""

# ruff: noqa: F401 - legacy module attributes remain import-compatible.

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import cast

from .accounting import (
    validate_accounting_reconciliation as _validate_accounting_reconciliation,
    validated_accounting_rows as _validated_accounting_rows,
)
from .constants import (
    ACCEPTED_STATUSES as _ACCEPTED_STATUSES,
    COUNTRY_PARTITION as _COUNTRY_PARTITION,
    MANIFEST_NAME as _MANIFEST_NAME,
    MAPPING_STATUSES as _MAPPING_STATUSES,
    OUTPUT_NAMES as _OUTPUT_NAMES,
    REVIEW_STATUSES as _REVIEW_STATUSES,
    SHA256_PATTERN as _SHA256_PATTERN,
    ZERO_ACCEPTED_REASON_CODES as _ZERO_ACCEPTED_REASON_CODES,
)
from .manifest import (
    build_manifest as _build_manifest,
    canonical_json_bytes as _canonical_json_bytes,
    payload_record_count as _payload_record_count,
    sha256 as _sha256,
)
from .models import (
    ClassificationAuditMaterializationResult,
    ClassificationAuditOutputPaths,
    ClassificationAuditRefusalError,
)
from .partitions import (
    country_partitions as _country_partitions,
    observation_country_counts as _observation_country_counts,
)
from .payloads import build_payloads as _build_payloads
from .publication import (
    existing_bundle_is_identical as _existing_bundle_is_identical,
    publish_atomically as _publish_atomically,
    validate_output_paths as _validate_output_paths,
)
from .queues import queue_payload as _queue_payload, queue_row as _queue_row
from .values import (
    mapping_sequence as _mapping_sequence,
    nonempty as _nonempty,
    refuse as _refuse,
    required_digest as _required_digest,
    required_text as _required_text,
    sequence_values as _sequence_values,
)
from .workflow import materialize_classification_audit

__all__ = [
    "ClassificationAuditMaterializationResult",
    "ClassificationAuditOutputPaths",
    "ClassificationAuditRefusalError",
    "materialize_classification_audit",
]
