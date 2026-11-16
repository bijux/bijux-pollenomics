"""Authenticate captured facet buffers before deriving separate source qualifications."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    NeotomaResourceLimits,
    NeotomaResourceSpec,
)
from .models import SCOPED_FACET_SCHEMA, NeotomaFacetScopeInputs
from .profiles import PROFILE_SCHEMA, qualify_neotoma_facet_body
from .replay import (
    _control,
    _read_authenticated_facet_body,
    _replay_facet_capture,
    replay_neotoma_facet_capture,
)


def qualify_neotoma_facet_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
) -> dict[str, Any]:
    """Leave original HTTP assessments intact, including blocked or incomplete roots."""
    return _qualify_facet_capture(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        limits=limits,
        scope_inputs=scope_inputs,
    )


def _qualify_facet_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    _before_body_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Add operation refusals without changing native qualification or capture history."""
    replay = (
        replay_neotoma_facet_capture
        if _before_body_read is None
        else _replay_facet_capture
    )
    options: dict[str, Any] = (
        {} if _before_body_read is None else {"_before_body_read": _before_body_read}
    )
    capture = replay(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        limits=limits,
        scope_inputs=scope_inputs,
        **options,
    )
    manifest, _, _, _ = _control(directory, expected_manifest_sha256)
    verification = (
        "authenticated_source_inputs"
        if manifest["schema_version"] == SCOPED_FACET_SCHEMA
        else "not_recorded_legacy_capture"
    )
    entries = []
    for entry in capture.facets:
        derived: dict[str, Any] = {
            "source_facet_key": entry["facet_key"],
            "source_capture_manifest_sha256": capture.manifest_sha256,
            "capture_terminal_status": entry["terminal_status"],
            "root_identity": entry["root_identity"],
            "facet": entry["facet"],
            "content_version": entry["content_version"],
            "api_version": entry["api_version"],
            "scientific_admission": "not_asserted",
            "parent_scope_verification": verification,
            "effective_parent_scope_role": entry.get("parent_scope_role"),
        }
        if entry["terminal_status"] != "received_complete_unqualified_facet":
            derived.update(
                qualification_status="source_entity_unavailable",
                reason=entry["terminal_status"],
            )
        else:
            resource = NeotomaResourceSpec(
                **entry["root_identity"], versions=("current",)
            )
            body = _read_authenticated_facet_body(
                directory,
                resource,
                entry["facet"],
                entry,
                limits,
                _before_body_read=_before_body_read,
            )
            if _before_body_read is not None:
                _before_body_read()
            derived.update(
                qualify_neotoma_facet_body(
                    resource,
                    entry["facet"],
                    body.body,
                    expected_body_sha256=body.body_sha256,
                )
            )
            derived["source_receipt_sha256"] = body.receipt_sha256
        entries.append(derived)
    return {
        "schema_version": PROFILE_SCHEMA,
        "source_capture_manifest_sha256": capture.manifest_sha256,
        "entries": entries,
        "partitions": dict(
            sorted(Counter(row["qualification_status"] for row in entries).items())
        ),
        "capture_assessments_relabelled": False,
        "scientific_admission": "not_asserted",
        "HTTP_requests": 0,
    }
