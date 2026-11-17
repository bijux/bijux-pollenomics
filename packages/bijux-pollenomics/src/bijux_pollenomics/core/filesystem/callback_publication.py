"""Publish trusted Path callbacks through exclusive completed-tree authorities."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import stat
from threading import RLock
from typing import Protocol, TypeVar

from ..errors.cleanup import add_cleanup_note
from .anchors import DIRECTORY_FLAGS, DirectoryAnchor, identity
from .owned_writes import OwnedTreeWriter
from .recovery_storage import resolve_publication_workspace_parent
from .regular_inputs import BoundedInputTree
from .replacement import ReplacementCandidate, publish_owned_replacement

T = TypeVar("T")


@dataclass
class _CallbackWorkspace:
    """Keep eager nested callback recovery outside the active candidate namespace."""

    writer: OwnedTreeWriter
    recovery: DirectoryAnchor
    root_identity: tuple[int, int, int]
    process_id: int
    active: bool = True
    children: int = 0


_CALLBACK_WORKSPACE: ContextVar[_CallbackWorkspace | None] = ContextVar(
    "callback_publication_workspace", default=None
)
_WORKSPACE_LOCK = RLock()
_WORKSPACES: dict[tuple[int, int, int], _CallbackWorkspace] = {}

__all__ = ["publish_callback_tree", "seal_completed_callback_tree"]


class _ReplacementPublisher(Protocol):
    """Retain the existing replacement injection boundary for callback wrappers."""

    def __call__(
        self,
        writer: ReplacementCandidate,
        *,
        final: Path,
        prior: BoundedInputTree | None,
        recovery: DirectoryAnchor,
        validate: Callable[[Path], object],
    ) -> object:
        """Attach and validate the already owned completed candidate."""
        ...


def _find_workspace(final: Path) -> _CallbackWorkspace | None:
    """Find live callback roots across threads without following moved authority."""
    # Nearest physical authority wins even after attachment or callback closure.
    # An active outer scope cannot lend its lease to a moved or closed child.
    for ancestor in (final, *final.parents):
        try:
            node = ancestor.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        matched = _WORKSPACES.get(identity(node))
        if matched is not None:
            return matched
    # Keep displaced attachments and expired copied contexts accountable when
    # their original physical root is no longer an observed ancestor.
    inherited = _CALLBACK_WORKSPACE.get()
    candidates = list(_WORKSPACES.values())
    if inherited is not None:
        candidates.append(inherited)
    return max(
        (item for item in candidates if final.is_relative_to(item.writer.root)),
        key=lambda item: len(item.writer.root.parts),
        default=None,
    )


@contextmanager
def _parent_workspace(final: Path, label: str) -> Iterator[_CallbackWorkspace | None]:
    with _WORKSPACE_LOCK:
        outer = _find_workspace(final)
        if outer is not None:
            if (
                not outer.active
                or outer.process_id != os.getpid()
                or final == outer.writer.root
            ):
                raise ValueError(
                    f"Nested {label.lower()} callback workspace is unavailable"
                )
            outer.writer.validate_attachment()
            outer.recovery.check()
            target_identity: tuple[int, int, int] | None
            try:
                target_identity = identity(final.stat(follow_symlinks=False))
            except FileNotFoundError:
                target_identity = None
            if target_identity == outer.root_identity:
                raise ValueError(
                    f"Nested {label.lower()} callback workspace is unavailable"
                )
            outer.children += 1
    try:
        yield outer
    finally:
        if outer is not None:
            with _WORKSPACE_LOCK:
                outer.children -= 1


@contextmanager
def _operation_workspace(
    writer: OwnedTreeWriter, recovery: DirectoryAnchor
) -> Iterator[_CallbackWorkspace]:
    with DirectoryAnchor(writer.root) as root:
        writer.validate_attachment()
        root.check()
        workspace = _CallbackWorkspace(writer, recovery, root.identity, os.getpid())
    with _WORKSPACE_LOCK:
        _WORKSPACES[workspace.root_identity] = workspace
    try:
        yield workspace
    finally:
        with _WORKSPACE_LOCK:
            workspace.active = False
            del _WORKSPACES[workspace.root_identity]


def publish_callback_tree(
    final_output_root: Path,
    publish: Callable[[Path], T],
    *,
    namespace: str,
    label: str,
    validate: Callable[[Path], object] | None = None,
    _replace: _ReplacementPublisher = publish_owned_replacement,
    _seal: Callable[[Path], BoundedInputTree] | None = None,
) -> T:
    """Publish a trusted, completed Path callback without borrowing another tree.

    Callback generation is not pre-budgeted. Its completed ordinary namespace
    supplies exact seals and finite bounds for subsequent attachment checks.
    Prior and refused trees remain in private recovery; no cleanup deletes them.
    Optional semantic validation runs before attachment and on final readback.
    """
    seal = seal_completed_callback_tree if _seal is None else _seal
    final = Path(final_output_root).absolute()
    with _parent_workspace(final, label) as outer, ExitStack() as stack:
        parent = stack.enter_context(
            DirectoryAnchor(final.parent, create=True, creation_mode=0o777)
        )
        prior = stack.enter_context(seal(final)) if os.path.lexists(final) else None
        storage_path = (
            outer.recovery.path / "nested"
            if outer is not None
            else resolve_publication_workspace_parent(final, namespace=namespace)
        )
        storage = stack.enter_context(DirectoryAnchor(storage_path, create=True))
        parent.check()
        storage.check()
        name = "publication-" + secrets.token_hex(16)
        os.mkdir(name, 0o700, dir_fd=storage.fd)
        recovery = stack.enter_context(DirectoryAnchor(storage_path / name))
        # This writer owns only the initially empty root. Callback member writes
        # have a separate completed-namespace contract, not a hidden writer budget.
        writer = stack.enter_context(
            OwnedTreeWriter(recovery.path / "candidate", max_bytes=1, max_files=1)
        )
        try:
            with _operation_workspace(writer, recovery) as workspace:
                token = _CALLBACK_WORKSPACE.set(workspace)
                try:
                    result = publish(writer.root)
                finally:
                    with _WORKSPACE_LOCK:
                        workspace.active = False
                        pending_children = workspace.children
                    _CALLBACK_WORKSPACE.reset(token)
                if pending_children:
                    raise ValueError(
                        f"{label} callback has incomplete child publications"
                    )
                parent.check()
                writer.validate_attachment()
                completed = stack.enter_context(seal(writer.root))
                candidate = _CompletedCallbackCandidate(writer, completed, parent)
                _replace(
                    candidate,
                    final=final,
                    prior=prior,
                    recovery=recovery,
                    validate=validate if validate is not None else (lambda _: None),
                )
                parent.check()
                return result
        except BaseException as error:
            add_cleanup_note(
                error,
                lambda: (
                    f"{label} publication evidence retained at {recovery.path}; "
                    f"expected directory identity {recovery.identity}; "
                    "current attachment must be verified"
                ),
            )
            raise


class _CompletedCallbackCandidate:
    """Combine exclusive root authority with a trusted callback completion seal."""

    def __init__(
        self,
        writer: OwnedTreeWriter,
        completed: BoundedInputTree,
        parent: DirectoryAnchor,
    ) -> None:
        self.root = writer.root
        self._writer, self._completed = writer, completed
        self._parent = parent

    def validate_attachment(self) -> None:
        self._parent.check()
        self._writer.validate_attachment()
        self._completed.check()
        self._parent.check()

    def validate_closed_attachment(self, root: Path) -> None:
        self._parent.check()
        self._writer.validate_publication_attachment(root)
        if self._completed.root != root:
            self._completed.rebind(root)
        self._completed.check()
        self._writer.validate_publication_attachment(root)
        self._parent.check()


def seal_completed_callback_tree(root: Path) -> BoundedInputTree:
    """Census trusted output metadata, then seal that exact ordinary namespace.

    This does not admit untrusted inputs or bound the preceding callback. Empty
    directories are retained; later growth, aliases and replacement are refused.
    """
    files: dict[str, tuple[int, ...]] = {}
    directories: dict[str, tuple[int, int, int]] = {}
    total = 0
    with DirectoryAnchor(root) as anchor:
        directories[""] = anchor.identity

        def census(descriptor: int, prefix: str) -> None:
            nonlocal total
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    name = prefix + entry.name
                    OwnedTreeWriter._parts(name)
                    node = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(node.st_mode):
                        child = os.open(entry.name, DIRECTORY_FLAGS, dir_fd=descriptor)
                        try:
                            if identity(os.fstat(child)) != identity(node):
                                raise ValueError("Completed callback directory changed")
                            directories[name] = identity(node)
                            census(child, name + "/")
                            attached = os.stat(
                                entry.name, dir_fd=descriptor, follow_symlinks=False
                            )
                            if identity(attached) != identity(node):
                                raise ValueError(
                                    "Completed callback directory attachment changed"
                                )
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(node.st_mode) and node.st_nlink == 1:
                        total += node.st_size
                        files[name] = (
                            *identity(node),
                            node.st_nlink,
                            node.st_size,
                            node.st_mtime_ns,
                            node.st_ctime_ns,
                        )
                    else:
                        raise ValueError(
                            "Completed callback contains a nonregular or aliased member"
                        )

        census(anchor.fd, "")
        anchor.check()
    tree = BoundedInputTree(
        root,
        max_bytes=max(1, total),
        max_files=max(1, len(files), len(directories)),
    )
    try:
        if tree.files != files or tree.directories != directories:
            raise ValueError("Completed callback changed while sealing its namespace")
        tree.check()
        return tree
    except BaseException:
        tree.close()
        raise
