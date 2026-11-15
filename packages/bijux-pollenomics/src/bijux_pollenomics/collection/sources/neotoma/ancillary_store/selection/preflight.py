"""Close selected facet custody and scope without opening its native entity."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...capture.facets.protocol import request_for
from ...capture.resources.models import NeotomaResourceSpec
from ...client import positive_native_id
from .access import (
    _facet_resource,
    _observation,
    _prepare,
    _response,
    _role_row,
    _source,
)
from .metadata import SelectedMetadata
from .scope import CurrentScope


@dataclass(frozen=True)
class FacetAccess:
    """Operation-local metadata; native bytes and profile remain unverified."""

    metadata: SelectedMetadata
    scope: CurrentScope
    row: dict[str, Any]
    capture: dict[str, Any]
    entry: dict[str, Any]
    resource: NeotomaResourceSpec
    request: Any
    response: tuple[dict[str, Any], int]
    parents: dict[int, dict[str, Any]]
    entity_bodies_verified: bool = field(default=False, init=False)
    native_field_value_verified: bool = field(default=False, init=False)


def prepare_facet_access(
    directory: Path, *, observation_id: str, dataset_id: int, facet: str, **kwargs: Any
) -> FacetAccess:
    """Check independent anchors, native owner, original/current duties and budget."""
    dataset = positive_native_id(dataset_id)
    metadata, scope = _prepare(directory, kwargs)
    return _prepared_facet_access(
        metadata, scope, observation_id=observation_id, dataset_id=dataset, facet=facet
    )


def _prepared_facet_access(
    metadata: SelectedMetadata,
    scope: CurrentScope,
    *,
    observation_id: str,
    dataset_id: int,
    facet: str,
) -> FacetAccess:
    dataset = positive_native_id(dataset_id)
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
    request = request_for(resource, facet, len(entry["attempts"]))
    return FacetAccess(
        metadata,
        scope,
        row,
        capture,
        entry,
        resource,
        request,
        _response(metadata, capture, entry, request, row),
        parents,
    )
