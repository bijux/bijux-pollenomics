"""Deterministic baseline and refresh-drift review for Neotoma evidence."""

from __future__ import annotations

import hashlib as hashlib
import json as json

from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization as validate_neotoma_relational_materialization,
)

from ..lineage import LINEAGE_SCHEMA_VERSION as LINEAGE_SCHEMA_VERSION
from ..production import (
    load_validated_neotoma_raw_archive as load_validated_neotoma_raw_archive,
)
from .baseline import build_baseline as build_baseline
from .comparison import (
    build_review as build_review,
)
from .comparison import (
    change_kind as change_kind,
)
from .comparison import (
    collect_changes as collect_changes,
)
from .comparison import (
    optional_baseline_id as optional_baseline_id,
)
from .comparison import (
    validate_baseline as validate_baseline,
)
from .constants import BASELINE_SCHEMA_VERSION as BASELINE_SCHEMA_VERSION
from .constants import REFRESH_REVIEW_SCHEMA_VERSION as REFRESH_REVIEW_SCHEMA_VERSION
from .operations_api import (
    _change_kind as _change_kind,
)
from .operations_api import (
    _collect_changes as _collect_changes,
)
from .operations_api import (
    _optional_baseline_id as _optional_baseline_id,
)
from .operations_api import (
    _validate_baseline as _validate_baseline,
)
from .operations_api import (
    build_neotoma_refresh_baseline as build_neotoma_refresh_baseline,
)
from .operations_api import (
    build_neotoma_refresh_review as build_neotoma_refresh_review,
)
from .operations_api import (
    render_neotoma_refresh_review_markdown as render_neotoma_refresh_review_markdown,
)
from .operations_api import (
    write_neotoma_refresh_baseline as write_neotoma_refresh_baseline,
)
from .operations_api import (
    write_neotoma_refresh_review as write_neotoma_refresh_review,
)
from .serialization import render_markdown as render_markdown
from .serialization import write_baseline as write_baseline
from .serialization import write_review as write_review
from .validation import (
    canonical_json as canonical_json,
)
from .validation import (
    json_object as json_object,
)
from .validation import (
    mapping as mapping,
)
from .validation import (
    non_negative_integer as non_negative_integer,
)
from .validation import (
    read_regular_file as read_regular_file,
)
from .validation import (
    required_text as required_text,
)
from .validation import (
    safe_filename as safe_filename,
)
from .validation import (
    safe_public_path as safe_public_path,
)
from .validation import (
    write_atomic as write_atomic,
)
from .validation_api import (
    _canonical_json as _canonical_json,
)
from .validation_api import (
    _json_object as _json_object,
)
from .validation_api import (
    _mapping as _mapping,
)
from .validation_api import (
    _non_negative_integer as _non_negative_integer,
)
from .validation_api import (
    _read_regular_file as _read_regular_file,
)
from .validation_api import (
    _required_text as _required_text,
)
from .validation_api import (
    _safe_filename as _safe_filename,
)
from .validation_api import (
    _safe_public_path as _safe_public_path,
)
from .validation_api import (
    _write_atomic as _write_atomic,
)

__all__ = [
    "build_neotoma_refresh_baseline",
    "build_neotoma_refresh_review",
    "render_neotoma_refresh_review_markdown",
    "write_neotoma_refresh_baseline",
    "write_neotoma_refresh_review",
]

for _definition in (
    build_neotoma_refresh_baseline,
    build_neotoma_refresh_review,
    write_neotoma_refresh_baseline,
    write_neotoma_refresh_review,
    render_neotoma_refresh_review_markdown,
    _collect_changes,
    _change_kind,
    _validate_baseline,
    _optional_baseline_id,
    _write_atomic,
    _read_regular_file,
    _json_object,
    _mapping,
    _required_text,
    _non_negative_integer,
    _safe_filename,
    _safe_public_path,
    _canonical_json,
):
    _definition.__module__ = __name__
