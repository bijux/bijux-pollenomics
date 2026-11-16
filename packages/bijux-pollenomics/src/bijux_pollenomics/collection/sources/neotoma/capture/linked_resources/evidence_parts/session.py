"""Explicit operation-owned evidence metadata with live source and permission seals."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from ...facets.models import NeotomaFacetScopeInputs
from ...receipts import _object, _safe_root
from ..authority import MAX_SOURCE_BYTES, source_bindings
from ..models import NeotomaLinkedEvidence

if TYPE_CHECKING:
    from ..ancestry.models import NeotomaTaxonAncestrySources

_METADATA_BYTES = 16 * 1024 * 1024


def _path(path: Path) -> str:
    return str(Path(path).absolute())


def _paths(values: Mapping[str, Path] | None) -> tuple[tuple[str, str], ...]:
    if values is None:
        return ()
    if not isinstance(values, Mapping):
        raise ValueError("Evidence session source resolver must be a mapping")
    return tuple(sorted((pin, _path(path)) for pin, path in values.items()))


def _scopes(values: Mapping[str, NeotomaFacetScopeInputs] | None) -> tuple[Any, ...]:
    if not isinstance(values, Mapping):
        raise ValueError("Evidence session complete current scope is required")
    result = []
    for pin, scope in sorted(values.items()):
        if not isinstance(scope, NeotomaFacetScopeInputs):
            raise ValueError("Evidence session current scope type differs")
        result.append(
            (
                pin,
                _path(scope.roster_path),
                _paths(scope.metadata_captures),
                _paths(scope.historical_metadata_parts),
                None if scope.alias_authority is None else _path(scope.alias_authority),
            )
        )
    return tuple(result)


class _LinkedEvidenceSession:
    """Authenticate one complete evidence closure without caching native bodies."""

    def __init__(
        self,
        *,
        source_owner: NeotomaTaxonAncestrySources,
        scope_inputs: Mapping[str, NeotomaFacetScopeInputs],
        legacy_rosters: Mapping[str, Path],
        operation: object,
    ) -> None:
        """Bind a single ancestry operation and its exact independent source inputs."""
        from ..ancestry.chain.models import MAX_FILES
        from ..ancestry.models import NeotomaTaxonAncestrySources

        if (
            not isinstance(source_owner, NeotomaTaxonAncestrySources)
            or type(operation) is not object
        ):
            raise ValueError(
                "Evidence session requires its explicit ancestry operation"
            )
        self._max_source_files = MAX_FILES
        self._source_owner = source_owner
        self._scope_inputs = scope_inputs
        self._legacy_rosters = legacy_rosters
        self._operation = operation
        self._stack = ExitStack()
        self._trees: dict[tuple[Path, str | None], BoundedInputTree] = {}
        self._permissions: list[BoundedInputTree] = []
        self._pins: dict[Path, tuple[str, int, BoundedInputTree]] = {}
        self._members: dict[tuple[int, int], int] = {}
        self._header: bytes | None = None
        self._active = self._used = False
        self._initial = self._identity()

    def _identity(self) -> tuple[Any, ...]:
        owner = self._source_owner
        return (
            _path(owner.evidence.directory),
            owner.evidence.manifest_sha256,
            _paths(owner.source_facets),
            _paths(owner.capture_sources),
            _path(owner.context_directory),
            owner.expected_context_sha256,
            _path(owner.native_archive_directory),
            owner.expected_native_archive_sha256,
            _scopes(self._scope_inputs),
            _paths(self._legacy_rosters),
        )

    def _seal(
        self, directory: Path, *, selected: str | None = None, permission: bool = False
    ) -> BoundedInputTree:
        root = _safe_root(directory)
        key = root, selected
        if key not in self._trees:
            tree = self._stack.enter_context(
                BoundedInputTree(
                    root,
                    max_bytes=MAX_SOURCE_BYTES,
                    max_files=self._max_source_files,
                    selected=selected,
                )
            )
            for stamp in tree.files.values():
                self._members[stamp[0], stamp[1]] = stamp[4]
            if (
                len(self._members) > self._max_source_files
                or sum(self._members.values()) > MAX_SOURCE_BYTES
            ):
                raise ValueError(
                    "Evidence session source closure exceeds finite bounds"
                )
            self._trees[key] = tree
        tree = self._trees[key]
        if permission and tree not in self._permissions:
            self._permissions.append(tree)
        return tree

    def _tree_for(self, path: Path) -> BoundedInputTree:
        path = Path(path).absolute()
        candidates = [
            tree
            for (root, selected), tree in self._trees.items()
            if selected is None and path.is_relative_to(root)
        ]
        if candidates:
            return max(candidates, key=lambda tree: len(tree.root.parts))
        return self._seal(path.parent, selected=path.name)

    def _remember(
        self, path: Path, digest: str, size: int | None = None, *, read: bool = False
    ) -> bytes | None:
        path = Path(path).absolute()
        tree = self._tree_for(path)
        name = path.relative_to(tree.root).as_posix()
        actual = tree.files[name][4]
        if size is not None and actual != size:
            raise ValueError("Evidence session declared source size differs")
        self._pins[path] = digest, actual, tree
        if read:
            raw = tree.read(path, max_bytes=min(actual, _METADATA_BYTES))
            if sha256(raw).hexdigest() != digest:
                raise ValueError("Evidence session independent metadata pin differs")
            return raw
        return None

    def _check_trees(self, *, full: bool) -> None:
        if self._identity() != self._initial:
            raise ValueError(
                "Evidence session source owner or resolver identity changed"
            )
        for tree in self._trees.values() if full else self._permissions:
            tree.check()

    def __enter__(self) -> _LinkedEvidenceSession:
        """Validate using the unchanged maintained loader under live physical seals."""
        from .. import evidence

        if self._used:
            raise ValueError("Evidence session cannot be reused by another operation")
        self._used = True
        try:
            owner = self._source_owner
            header = evidence._index(
                _safe_root(owner.evidence.directory), owner.evidence.manifest_sha256
            )
            roster = header["authority"]["roster_sha256"]
            if set(self._scope_inputs) != {roster}:
                raise ValueError("Evidence session complete current roster differs")
            scope = self._scope_inputs[roster]
            for root in [
                *owner.source_facets.values(),
                *owner.capture_sources.values(),
            ]:
                self._seal(root)
            for root in scope.metadata_captures.values():
                self._seal(root, permission=True)
            for path in [
                scope.roster_path,
                *self._legacy_rosters.values(),
                *(scope.historical_metadata_parts or {}).values(),
                *([] if scope.alias_authority is None else [scope.alias_authority]),
            ]:
                self._seal(path.parent, selected=path.name, permission=True)
            self._seal(owner.evidence.directory)
            for path, digest in [
                (
                    owner.context_directory / "manifest.json",
                    owner.expected_context_sha256,
                ),
                (
                    owner.native_archive_directory / "manifest.json",
                    owner.expected_native_archive_sha256,
                ),
            ]:
                self._seal(path.parent, selected=path.name, permission=True)
                raw = self._remember(path, digest, read=True)
                if path.parent == owner.native_archive_directory:
                    assert raw is not None
                    catalogue_pin = _object(raw)["catalogue_manifest_sha256"]
                    catalogue = (
                        owner.native_archive_directory / "catalogue/manifest.json"
                    )
                    self._seal(
                        catalogue.parent, selected=catalogue.name, permission=True
                    )
                    self._remember(catalogue, catalogue_pin, read=True)
            inputs = {
                "expected_roster_sha256": roster,
                "scope": scope,
                "source_facets": owner.source_facets,
                "legacy_rosters": self._legacy_rosters,
            }
            bindings = source_bindings(**inputs)
            if set(bindings) != set(header["source_input_pins"]):
                raise ValueError(
                    "Evidence session complete source binding population differs"
                )
            for key, path in bindings.items():
                pin = header["source_input_pins"][key]
                self._remember(path, pin["sha256"], pin["bytes"])
            self._remember(
                owner.evidence.directory / "evidence-manifest.json",
                owner.evidence.manifest_sha256,
            )
            for part in header["parts"]:
                self._remember(
                    owner.evidence.directory / "proofs" / (part["sha256"] + ".json"),
                    part["sha256"],
                    part["bytes"],
                )
            index = evidence.load_neotoma_linked_evidence(
                owner.evidence.directory,
                expected_manifest_sha256=owner.evidence.manifest_sha256,
                **inputs,
            )
            self._header = json.dumps(
                index,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode()
            if len(self._header) > _METADATA_BYTES:
                raise ValueError(
                    "Evidence session header exceeds finite metadata bound"
                )
            self._check_trees(full=True)
            self._active = True
            return self
        except BaseException:
            self._close()
            raise

    def check(
        self,
        *,
        operation: object,
        evidence: NeotomaLinkedEvidence | None,
        source_facets: Mapping[str, Path],
        scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None,
        legacy_rosters: Mapping[str, Path] | None,
        full: bool = False,
        capture_directory: Path | None = None,
        capture_manifest_sha256: str | None = None,
    ) -> None:
        """Reject stale operations, changed resolvers and permission drift before bodies."""
        if not self._active or self._header is None or operation is not self._operation:
            raise ValueError(
                "Evidence session is inactive or belongs to another operation"
            )
        owner = self._source_owner
        if capture_directory is not None or capture_manifest_sha256 is not None:
            declared = (
                owner.capture_sources.get(capture_manifest_sha256)
                if isinstance(capture_manifest_sha256, str)
                else None
            )
            if (
                declared is None
                or capture_directory is None
                or _path(declared) != _path(capture_directory)
            ):
                raise ValueError("Evidence session exact capture resolver differs")
        if evidence is not None and (
            _path(evidence.directory),
            evidence.manifest_sha256,
        ) != (_path(owner.evidence.directory), owner.evidence.manifest_sha256):
            raise ValueError("Evidence session evidence resolver identity differs")
        expected = dict(_paths(owner.source_facets))
        supplied = _paths(source_facets)
        if (
            any(expected.get(pin) != path for pin, path in supplied)
            or _scopes(scope_inputs) != _scopes(self._scope_inputs)
            or _paths(legacy_rosters) != _paths(self._legacy_rosters)
        ):
            raise ValueError("Evidence session exact source or current scope differs")
        self._check_trees(full=full)

    def index(self, **inputs: Any) -> dict[str, Any]:
        """Return a fresh bounded metadata view, never the mutable cached authority."""
        self.check(**inputs)
        assert self._header is not None
        return _object(self._header)

    def _close(self) -> None:
        self._active = False
        self._header = None
        self._pins.clear()
        self._members.clear()
        self._trees.clear()
        self._permissions.clear()
        self._stack.close()

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        """Recheck exact previously authenticated members without opening unrelated files."""
        try:
            if kind is None:
                self._check_trees(full=True)
                for path, (digest, size, tree) in self._pins.items():
                    raw = tree.read(path, max_bytes=size)
                    if sha256(raw).hexdigest() != digest:
                        raise ValueError(
                            "Evidence session already-read content pin changed"
                        )
                self._check_trees(full=True)
        finally:
            self._close()


def _check_session(session: Any, **inputs: Any) -> None:
    if type(session) is not _LinkedEvidenceSession:
        raise ValueError("Only an active source-owned evidence session is accepted")
    session.check(**inputs)
