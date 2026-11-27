"""Fresh operation-scoped preflight with immutable metadata-only projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from ...capture.receipts import _object
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from .metadata import MAX_METADATA, SelectedMetadata, _selected_metadata
from .parts import MAX_BYTES, MAX_FILES, VerifiedParts
from .preflight import FacetAccess, _prepared_facet_access
from .scope import CurrentScope, current_scope

if TYPE_CHECKING:
    from ..linked_evidence.preflight import LinkedAccess


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class PreflightProjection:
    """No live cache, scope object, resolver or native entity is exposed."""

    row: Mapping[str, Any]
    parents: Mapping[int, Any]
    source: Mapping[str, Any]
    witness: Mapping[str, Any] | None
    entity_bodies_verified: bool = field(default=False, init=False)
    native_field_value_verified: bool = field(default=False, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row": _thaw(self.row),
            "parents": _thaw(self.parents),
            "source": _thaw(self.source),
            "witness": _thaw(self.witness),
            "entity_bodies_verified": False,
            "native_field_value_verified": False,
            "scientific_admission": "not_asserted",
            "related_resource_graph_complete": False,
        }


def _source(
    capture: dict[str, Any],
    entry: dict[str, Any],
    request: Any,
    response: tuple[dict[str, Any], int],
) -> dict[str, Any]:
    digest = capture["descriptor"]["files"]["capture-manifest.json"]["sha256"]
    reference = entry["attempts"][-1]
    return {
        "capsule_manifest_sha256": capture["capsule_pin"],
        "source_capture_manifest_sha256": digest,
        "request_name": request.name,
        "request_url": request.url,
        "receipt": response[0],
        "response_bound": response[1],
        "body_relative_path": f"captures/{digest}/{reference['body_file']}",
        "body_descriptor": capture["descriptor"]["files"][reference["body_file"]],
    }


def _projection(access: FacetAccess | LinkedAccess) -> PreflightProjection:
    witness = None
    if not isinstance(access, FacetAccess):
        witness = {
            "source_proof": access.proof,
            "evidence_locator": access.locator,
            "source": _source(
                access.predecessor,
                access.source_entry,
                access.source_request,
                access.source_response,
            ),
        }
    return PreflightProjection(
        _freeze(access.row),
        _freeze(access.parents),
        _freeze(_source(access.capture, access.entry, access.request, access.response)),
        _freeze(witness),
    )


class NeotomaPreflightBatch:
    """One dated source operation; successful close seals its input bindings."""

    def __init__(
        self,
        directory: Path,
        *,
        expected_manifest_sha256: str,
        expected_context_sha256: str,
        expected_native_archive_sha256: str,
        context_directory: Path,
        native_archive_directory: Path,
        capsule_sources: Mapping[str, Path],
        limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
        evidence_sources: Mapping[str, Path] | None = None,
        metadata_max_bytes: int = MAX_BYTES,
        metadata_max_files: int = MAX_FILES,
    ) -> None:
        self._parts = VerifiedParts(metadata_max_bytes, metadata_max_files)
        self._directory, self._context, self._native = (
            Path(path).absolute()
            for path in (directory, context_directory, native_archive_directory)
        )
        self._capsules = dict(capsule_sources)
        self._evidence = None if evidence_sources is None else dict(evidence_sources)
        self._options: dict[str, Any] = {
            "expected_manifest_sha256": expected_manifest_sha256,
            "expected_context_sha256": expected_context_sha256,
            "expected_native_archive_sha256": expected_native_archive_sha256,
            "capsule_sources": self._capsules,
            "limits": limits,
            "evidence_sources": self._evidence,
        }
        self._status = "created"
        self._metadata: SelectedMetadata | None = None
        self._scope: CurrentScope | None = None

    def __enter__(self) -> NeotomaPreflightBatch:
        if self._status != "created":
            raise ValueError("Preflight operation is closed or cannot reopen")
        try:
            roots = [
                self._directory,
                self._context,
                self._native,
                *self._capsules.values(),
                *(self._evidence or {}).values(),
            ]
            for root in roots:
                self._parts.root(root)
            metadata = _selected_metadata(
                self._directory, **self._options, parts=self._parts
            )
            scope = current_scope(metadata, self._context, self._native)
            self._parts.declarations(metadata.root, metadata.manifest["files"])
            self._parts.declarations(self._context, scope.context.manifest["files"])
            assert scope._native_manifest is not None
            self._parts.declarations(self._native, scope._native_manifest["files"])
            for source in scope.inputs.metadata_captures.values():
                prefix = source.relative_to(self._native).as_posix() + "/"
                self._parts.declarations(
                    self._native,
                    {
                        name: member
                        for name, member in scope._native_manifest["files"].items()
                        if name.startswith(prefix)
                    },
                    bodies=True,
                )
            for digest, root in self._capsules.items():
                document = _object(
                    self._parts.read(
                        root / "manifest.json", digest, MAX_METADATA, source=digest
                    )
                )
                self._parts.declarations(root, document["files"])
            for digest, root in (self._evidence or {}).items():
                document = _object(
                    self._parts.read(
                        root / "evidence-manifest.json",
                        digest,
                        MAX_METADATA,
                        source=digest,
                    )
                )
                for part in document["parts"]:
                    self._parts.seal(
                        root / "proofs" / (part["sha256"] + ".json"), part["bytes"]
                    )
            scope._freeze_operation()
            self._parts.validate()
            self._metadata, self._scope = metadata, scope
            self._status = "open"
            return self
        except BaseException:
            self._parts.close()
            self._status = "closed"
            raise

    def _active(self) -> tuple[SelectedMetadata, CurrentScope]:
        if self._status != "open" or self._metadata is None or self._scope is None:
            raise ValueError("Preflight operation is not open or was not entered")
        return self._metadata, self._scope

    def facet(
        self, *, observation_id: str, dataset_id: int, facet: str
    ) -> PreflightProjection:
        metadata, scope = self._active()
        return _projection(
            _prepared_facet_access(
                metadata,
                scope,
                observation_id=observation_id,
                dataset_id=dataset_id,
                facet=facet,
            )
        )

    def linked(
        self, *, observation_id: str, occurrence_id: str, kind: str, native_id: int
    ) -> PreflightProjection:
        metadata, scope = self._active()
        # Linked preflight also imports selection metadata, so resolve it at use.
        from ..linked_evidence.preflight import _prepared_linked_access

        return _projection(
            _prepared_linked_access(
                metadata,
                scope,
                observation_id=observation_id,
                occurrence_id=occurrence_id,
                kind=kind,
                native_id=native_id,
                parts=self._parts,
            )
        )

    def close(self) -> None:
        if self._status == "closed":
            return
        try:
            if self._status == "open":
                self._parts.validate()
        finally:
            self._status = "closed"
            self._metadata, self._scope = None, None
            self._parts.close()

    def _abort(self) -> None:
        """Close without a second validation when preserving a primary failure."""
        self._status = "closed"
        self._metadata, self._scope = None, None
        self._parts.close()

    def __exit__(self, *_error: Any) -> None:
        self.close()


def prepare_neotoma_preflight_batch(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
    metadata_max_bytes: int = MAX_BYTES,
    metadata_max_files: int = MAX_FILES,
) -> NeotomaPreflightBatch:
    """Create a fresh batch; no caller-provided scope or shared cache is accepted."""
    return NeotomaPreflightBatch(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_context_sha256=expected_context_sha256,
        expected_native_archive_sha256=expected_native_archive_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
        limits=limits,
        evidence_sources=evidence_sources,
        metadata_max_bytes=metadata_max_bytes,
        metadata_max_files=metadata_max_files,
    )
