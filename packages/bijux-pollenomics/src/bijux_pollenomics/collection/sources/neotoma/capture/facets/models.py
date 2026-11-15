"""Finite ancillary dataset requests with inherited resource exposure roles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..resources.models import NeotomaResourceSpec

FACET_SCHEMA = "neotoma-dataset-facet-http-capture.v1"
DATASET_FACETS = ("chronologies", "lithology", "projects", "publications", "taxa")


@dataclass(frozen=True)
class NeotomaFacetPlan:
    """Select current facets independently of the parent's download versions."""

    resources: tuple[NeotomaResourceSpec, ...]
    roster_sha256: str
    facets: tuple[str, ...] = DATASET_FACETS


@dataclass(frozen=True)
class NeotomaFacetCapture:
    manifest_sha256: str
    facets: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]


@dataclass(frozen=True)
class NeotomaFacetBody:
    """Authenticated entity whose native schema and payload owner remain unqualified."""

    facet_key: str
    root_identity: dict[str, Any]
    body: bytes
    body_sha256: str
    receipt_sha256: str
