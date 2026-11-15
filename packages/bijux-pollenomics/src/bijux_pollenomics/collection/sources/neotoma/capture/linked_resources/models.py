"""Finite native detail targets whose authority comes from captured facet links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LINKED_SCHEMA = "neotoma-linked-resource-http-capture.v1"
LINKED_KINDS = ("contact", "publication", "taxon")


@dataclass(frozen=True)
class NeotomaLinkedTarget:
    kind: str
    native_id: int


@dataclass(frozen=True)
class NeotomaLinkedResourcePlan:
    """Explicit selection, without caller-supplied URLs, roles or source proofs."""

    source_facet_manifest_sha256s: tuple[str, ...]
    targets: tuple[NeotomaLinkedTarget, ...]
    include_higher_taxa: bool = False


@dataclass(frozen=True)
class NeotomaLinkedResourceCapture:
    manifest_sha256: str
    resources: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]


@dataclass(frozen=True)
class NeotomaLinkedBody:
    target_key: str
    body: bytes
    body_sha256: str
    receipt_sha256: str
    source_proofs: tuple[dict[str, Any], ...]
