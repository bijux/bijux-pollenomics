"""SEAD evidence admission and atlas projection."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from pathlib import Path

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)

from .admission import (
    object_rows as _owned_object_rows,
)
from .admission import (
    validate_evidence_headers as _owned_validate_evidence_headers,
)
from .projection import project_sead
from .relations import (
    reconcile_relation_denominators as _owned_reconcile_relation_denominators,
)
from .relations import (
    site_by_entity_owner as _owned_site_by_entity_owner,
)

_object_rows = _owned_object_rows
_validate_sead_evidence_headers = _owned_validate_evidence_headers
_reconcile_sead_relation_denominators = _owned_reconcile_relation_denominators
_site_by_entity_owner = _owned_site_by_entity_owner


def _project_sead(
    context_root: Path,
    layers: Sequence[MutableMapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Project governed SEAD evidence using the pinned public identities."""
    return project_sead(
        context_root,
        layers,
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        expected_admission_sha256=SEAD_GOVERNED_ADMISSION_SHA256,
    )
