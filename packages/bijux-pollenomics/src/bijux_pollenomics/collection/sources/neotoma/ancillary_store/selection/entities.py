"""Guard exact ancillary occurrences before reading and returning authenticated entities."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.facets.protocol import request_for as facet_request
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    NeotomaResourceLimits,
)
from ...client import positive_native_id
from ..linked_evidence.selection import _POINTERS as _POINTERS
from ..linked_evidence.selection import read_linked, read_linked_entity
from .access import (
    _body as _body,
)
from .access import (
    _facet_resource as _facet_resource,
)
from .access import (
    _observation as _observation,
)
from .access import (
    _prepare as _prepare,
)
from .access import (
    _response as _response,
)
from .access import (
    _result as _result,
)
from .access import (
    _role_row as _role_row,
)
from .access import (
    _source as _source,
)


def _facet(
    directory: Path, *, observation_id: str, dataset_id: int, facet: str, **kwargs: Any
) -> tuple[dict[str, Any], Any]:
    """Guard once and retain the native resource alongside the authenticated bytes."""
    dataset = positive_native_id(dataset_id)
    metadata, scope = _prepare(directory, kwargs)
    row = _observation(metadata, observation_id, "facet")
    if (
        row.get("facet") != facet
        or row.get("root_identity", {}).get("dataset_id") != dataset
    ):
        raise ValueError("Selected facet identity differs")
    capture, entry = _source(metadata, row, "facet")
    resource = _facet_resource(capture, entry)
    parents = scope.guard([entry["root_identity"]])
    role = parents[dataset]["effective_scope_role"]
    _role_row(row, role)
    metadata.slot(row, parents[dataset])
    scope.original(metadata, capture, entry)
    body, receipt = _body(
        metadata,
        capture,
        entry,
        facet_request(resource, facet, len(entry["attempts"])),
        row,
    )
    return _result(row, body, receipt, linked=False), resource


def read_neotoma_ancillary_facet_entity(
    directory: Path,
    *,
    observation_id: str,
    dataset_id: int,
    facet: str,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Return a forensic entity; failed HTTP/source status remains explicit."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    return _facet(
        directory,
        observation_id=observation_id,
        dataset_id=dataset_id,
        facet=facet,
        **kwargs,
    )[0]


def read_neotoma_ancillary_facet(
    directory: Path,
    *,
    observation_id: str,
    dataset_id: int,
    facet: str,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Add native schema qualification; no method or scientific admission is inferred."""
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    result, resource = _facet(
        directory,
        observation_id=observation_id,
        dataset_id=dataset_id,
        facet=facet,
        **kwargs,
    )
    if result["terminal_status"] != "received_complete_unqualified_facet":
        raise ValueError("Typed facet source is not a complete successful entity")
    qualified = qualify_neotoma_facet_body(
        resource,
        facet,
        result["body"],
        expected_body_sha256=result["body_sha256"],
    )
    if qualified["qualification_status"] != "qualified_source_schema":
        raise ValueError("Selected facet native source schema is unqualified")
    return {**result, "source_qualification": qualified}


def read_neotoma_ancillary_linked_entity(
    directory: Path,
    *,
    observation_id: str,
    occurrence_id: str,
    kind: str,
    native_id: int,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Read one global entity through its scoped source and current-use guards."""
    return read_linked_entity(
        directory,
        observation_id=observation_id,
        occurrence_id=occurrence_id,
        kind=kind,
        native_id=native_id,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_context_sha256=expected_context_sha256,
        expected_native_archive_sha256=expected_native_archive_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
        limits=limits,
        evidence_sources=evidence_sources,
    )


def read_neotoma_ancillary_linked(
    directory: Path,
    *,
    observation_id: str,
    occurrence_id: str,
    kind: str,
    native_id: int,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Read one global entity through its scoped source and current-use guards."""
    return read_linked(
        directory,
        observation_id=observation_id,
        occurrence_id=occurrence_id,
        kind=kind,
        native_id=native_id,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_context_sha256=expected_context_sha256,
        expected_native_archive_sha256=expected_native_archive_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
        limits=limits,
        evidence_sources=evidence_sources,
    )
