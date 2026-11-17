"""Keep verified baseline facts immutable under their original live source owner."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .....resource_catalogue.archive.files import _digest, encoded_json
from ....receipts import _object
from ....resources.models import DEVELOPMENT_ROLES
from ...evidence import iter_neotoma_linked_evidence_occurrences
from ...replay import _control
from .. import publication as baseline_publication
from .models import (
    NeotomaTaxonAncestryChainLimits,
    NeotomaTaxonAncestryChainSources,
    baseline_limits,
    entity_role,
    strongest_roles,
)
from .projection import project

if TYPE_CHECKING:
    from .authority import ChainOperation


def _scope(sources: NeotomaTaxonAncestryChainSources) -> tuple[Any, ...]:
    def mapping(values: Mapping[str, Path]) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted((pin, str(Path(root).absolute())) for pin, root in values.items())
        )

    original = sources.recorded_baseline_sources
    return (
        str(Path(original.evidence.directory).absolute()),
        original.evidence.manifest_sha256,
        mapping(original.capture_sources),
        mapping(original.source_facets),
        str(Path(original.context_directory).absolute()),
        original.expected_context_sha256,
        str(Path(original.native_archive_directory).absolute()),
        original.expected_native_archive_sha256,
        str(Path(sources.baseline_projection_directory).absolute()),
        sources.expected_baseline_projection_sha256,
        str(Path(sources.current_context_directory).absolute()),
        sources.expected_current_context_sha256,
        str(Path(sources.current_native_archive_directory).absolute()),
        sources.expected_current_native_archive_sha256,
        mapping(sources.chain_sources),
        mapping(sources.context_sources),
        mapping(sources.native_archive_sources),
    )


@dataclass(frozen=True)
class _BaselineQualification:
    """Borrow only detached verified facts while the original owner remains live."""

    _sources: NeotomaTaxonAncestryChainSources
    _limits: NeotomaTaxonAncestryChainLimits
    _facts: bytes
    _scope: tuple[Any, ...]
    _check_owner: Callable[[], None]

    def check(self) -> None:
        """Refuse expired, changed or rebound original source authority."""
        self._check_owner()
        if _scope(self._sources) != self._scope:
            raise ValueError("Ancestry baseline qualification source bindings changed")

    def read(
        self,
        sources: NeotomaTaxonAncestryChainSources,
        limits: NeotomaTaxonAncestryChainLimits,
    ) -> dict[str, Any]:
        """Return fresh working facts without sharing mutable projections or roles."""
        self.check()
        if _scope(sources) != self._scope or limits != self._limits:
            raise ValueError("Ancestry baseline qualification scope or limits differ")
        facts = _object(self._facts)
        self.check()
        return facts


def resolve_baseline(
    operation: ChainOperation,
    limits: NeotomaTaxonAncestryChainLimits,
    *,
    native_replay: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Rebuild current duties before borrowing or replaying verified native facts."""
    sources, original = operation.sources, operation.sources.recorded_baseline_sources
    if not _digest(sources.expected_baseline_projection_sha256):
        raise ValueError("Ancestry baseline projection anchor is invalid")
    operation.seal(original.context_directory, bound=512 * 1024 * 1024)
    operation.seal(original.native_archive_directory, bound=512 * 1024 * 1024)
    operation.seal(sources.baseline_projection_directory)
    operation.seal(original.evidence.directory)
    for root in [
        *original.capture_sources.values(),
        *original.source_facets.values(),
    ]:
        operation.seal(root)
    operation.epoch(
        sources.expected_current_context_sha256,
        sources.expected_current_native_archive_sha256,
    )
    recorded_epoch = operation.epoch(
        original.expected_context_sha256, original.expected_native_archive_sha256
    )
    operation.history = dict(recorded_epoch["roles"])
    duties = strongest_roles(*(epoch["roles"] for epoch in operation.epochs.values()))
    recorded = baseline_publication._readback(
        sources.baseline_projection_directory,
        sources.expected_baseline_projection_sha256,
    )
    direct: dict[str, set[int]] = {}
    for proof, _ in iter_neotoma_linked_evidence_occurrences(
        original.evidence.directory,
        expected_manifest_sha256=original.evidence.manifest_sha256,
    ):
        direct.setdefault(f"{proof['target_kind']}-{proof['native_id']}", set()).add(
            proof["root_dataset_id"]
        )
    results = {}
    for pin, root in sorted(original.capture_sources.items()):
        manifest, _, _, _, _ = _control(root, pin)
        for entry in manifest["resources"]:
            key = entry["target_key"]
            if key in results or key not in direct:
                raise ValueError(
                    "Ancestry baseline result identity is foreign or duplicated"
                )
            target = entry["identity"]
            role = entity_role(target, direct[key], duties, operation.epochs.values())
            if entry["attempts"] and role not in DEVELOPMENT_ROLES:
                raise ValueError(
                    "Ancestry protected current baseline duties forbid body access"
                )
            results[key] = {
                "source_capture_manifest_sha256": pin,
                "source_terminal_status": entry["terminal_status"],
                "qualification_status": "retained_direct_result",
                "recorded_hop": 0 if target["kind"] == "taxon" else None,
                "attempted": bool(entry["attempts"]),
            }
    state = {
        "seed_ids": recorded["authority"]["declared_seed_taxon_ids"],
        "edges": {row["edge_id"]: row for row in recorded["edges"]},
        "direct_roots": direct,
        "results": results,
        "baseline_sha256": sources.expected_baseline_projection_sha256,
        "evidence_sha256": original.evidence.manifest_sha256,
        "new_request_count": 0,
    }
    # Inherited restrictions travel through the complete pinned graph before replay.
    first = project(state, duties, limits)
    if any(
        row["current_use_role"] not in DEVELOPMENT_ROLES
        and row["source_result"] is not None
        and row["source_result"]["source_terminal_status"]
        == "received_complete_unqualified_linked_resource"
        for row in first["nodes"].values()
    ):
        raise ValueError(
            "Ancestry protected incoming root forbids baseline body access"
        )
    if native_replay:
        operation._check_live()
        if operation._borrowed_baseline is not None:
            verified = operation._borrowed_baseline.read(sources, limits)
        else:
            verified = baseline_publication._load_taxon_ancestry(
                sources.baseline_projection_directory,
                expected_manifest_sha256=sources.expected_baseline_projection_sha256,
                sources=original,
                _before_body_read=operation.check_permissions,
            )
            operation._check_live()
            operation._qualified_baseline = _BaselineQualification(
                sources,
                limits,
                encoded_json(verified),
                _scope(sources),
                operation._check_live,
            )
        operation._check_live()
        if recorded != verified:
            raise ValueError("Ancestry baseline changed during source replay")
    return state, project(
        state, recorded_epoch["roles"], baseline_limits(recorded["limits"])
    )
