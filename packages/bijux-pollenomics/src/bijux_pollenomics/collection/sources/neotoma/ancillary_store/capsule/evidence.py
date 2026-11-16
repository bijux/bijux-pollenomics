"""Own one complete evidence session per independent capsule source identity."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from pathlib import Path

from ...capture.linked_resources.evidence_parts.ownership import _LinkedEvidenceSources
from ...capture.linked_resources.evidence_parts.session import _LinkedEvidenceSession
from ...capture.linked_resources.models import SCOPED_LINKED_SCHEMA
from ..linked_evidence.sources import _evidence_inputs
from .models import CapsuleMetadata


@contextmanager
def _evidence_sessions(
    prepared: CapsuleMetadata,
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    predecessor_facets: Mapping[str, Path] | None,
    evidence_sources: Mapping[str, Path] | None,
    before_body_read: Callable[[], None],
) -> Iterator[tuple[dict[str, _LinkedEvidenceSession], object]]:
    """Reuse no authority outside this lifetime and never cache native entities."""
    groups: dict[str, dict[str, Path]] = {}
    for digest, directory in prepared.linked_sources.items():
        if prepared.documents[digest]["schema_version"] == SCOPED_LINKED_SCHEMA:
            pin = prepared.controls[digest]["source_evidence"]["manifest_sha256"]
            groups.setdefault(pin, {})[digest] = directory
    sessions: dict[str, _LinkedEvidenceSession] = {}
    operation = object()
    all_facets = {**(predecessor_facets or {}), **prepared.facet_sources}
    with ExitStack() as stack:
        for captures in groups.values():
            first = next(iter(captures))
            before_body_read()
            inputs = _evidence_inputs(
                prepared.controls[first], prepared.context, evidence_sources, all_facets
            )
            session = stack.enter_context(
                _LinkedEvidenceSession(
                    source_owner=_LinkedEvidenceSources(
                        evidence=inputs["evidence"],
                        source_facets=inputs["source_facets"],
                        capture_sources=captures,
                        context_directory=context_directory,
                        expected_context_sha256=expected_context_sha256,
                        native_archive_directory=native_archive_directory,
                        expected_native_archive_sha256=prepared.context.manifest[
                            "native_archive"
                        ]["manifest_sha256"],
                    ),
                    scope_inputs=inputs["scope_inputs"],
                    legacy_rosters=inputs["legacy_rosters"],
                    operation=operation,
                    _before_body_read=before_body_read,
                )
            )
            sessions.update(dict.fromkeys(captures, session))
        yield sessions, operation
