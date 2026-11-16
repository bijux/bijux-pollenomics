"""Publish complete report callbacks through exclusive operation-owned roots."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import shutil
import stat
from threading import RLock
from typing import TypeVar

from ...core.errors.cleanup import add_cleanup_note
from ...core.filesystem import OwnedTreeWriter
from ...core.filesystem.anchors import DIRECTORY_FLAGS, DirectoryAnchor, identity
from ...core.filesystem.recovery_storage import resolve_publication_workspace_parent
from ...core.filesystem.regular_inputs import BoundedInputTree
from ...core.filesystem.replacement import publish_owned_replacement
from ...core.owned_tree import (
    build_staging_output_dir,
    remove_output_tree,
)

T = TypeVar("T")


@dataclass
class _CallbackWorkspace:
    """Keep eager nested report recovery outside the active candidate namespace."""

    writer: OwnedTreeWriter
    recovery: DirectoryAnchor
    root_identity: tuple[int, int, int]
    process_id: int
    active: bool = True
    children: int = 0


_CALLBACK_WORKSPACE: ContextVar[_CallbackWorkspace | None] = ContextVar(
    "report_callback_workspace", default=None
)
_WORKSPACE_LOCK = RLock()
_WORKSPACES: dict[tuple[int, int, int], _CallbackWorkspace] = {}

__all__ = [
    "build_staging_output_dir",
    "publish_into_staging_dir",
    "reset_output_dir",
    "retain_existing_report_files",
]


def _find_workspace(final: Path) -> _CallbackWorkspace | None:
    """Find live report roots across threads without following moved authority."""
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
def _parent_workspace(final: Path) -> Iterator[_CallbackWorkspace | None]:
    with _WORKSPACE_LOCK:
        outer = _find_workspace(final)
        if outer is not None:
            if (
                not outer.active
                or outer.process_id != os.getpid()
                or final == outer.writer.root
            ):
                raise ValueError("Nested report callback workspace is unavailable")
            outer.writer.validate_attachment()
            outer.recovery.check()
            target_identity: tuple[int, int, int] | None
            try:
                target_identity = identity(final.stat(follow_symlinks=False))
            except FileNotFoundError:
                target_identity = None
            if target_identity == outer.root_identity:
                raise ValueError("Nested report callback workspace is unavailable")
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


def reset_output_dir(path: Path) -> None:
    """Remove one generated report directory so publication stays deterministic."""
    remove_output_tree(path)


def retain_existing_report_files(existing_root: Path, staging_root: Path) -> None:
    """Carry files outside the current publisher's output into its staged tree."""
    if not existing_root.is_dir():
        return
    for source in existing_root.rglob("*"):
        relative = source.relative_to(existing_root)
        destination = staging_root / relative
        if source.is_symlink():
            raise ValueError(f"report tree contains an unsupported symlink: {relative}")
        if source.is_dir():
            if destination.exists() and not destination.is_dir():
                raise ValueError(
                    f"report tree has a file-directory collision: {relative}"
                )
            continue
        if not source.is_file():
            raise ValueError(f"report tree contains an unsupported entry: {relative}")
        if destination.exists():
            if destination.is_symlink() or not destination.is_file():
                raise ValueError(
                    f"report tree has a file-directory collision: {relative}"
                )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def publish_into_staging_dir(
    final_output_root: Path,
    publish: Callable[[Path], T],
    *,
    validate: Callable[[Path], object] | None = None,
) -> T:
    """Publish a trusted, completed Path callback without borrowing another tree.

    Callback generation is not pre-budgeted. Its completed ordinary namespace
    supplies exact seals and finite bounds for subsequent attachment checks.
    Prior and refused trees remain in private recovery; no cleanup deletes them.
    Optional semantic validation runs before attachment and on final readback.
    """
    final = Path(final_output_root).absolute()
    with _parent_workspace(final) as outer, ExitStack() as stack:
        parent = stack.enter_context(
            DirectoryAnchor(final.parent, create=True, creation_mode=0o777)
        )
        prior = (
            stack.enter_context(_completed_report_tree(final))
            if os.path.lexists(final)
            else None
        )
        storage_path = (
            outer.recovery.path / "nested"
            if outer is not None
            else resolve_publication_workspace_parent(
                final, namespace="report-publication"
            )
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
                        "Report callback has incomplete child publications"
                    )
                parent.check()
                writer.validate_attachment()
                completed = stack.enter_context(_completed_report_tree(writer.root))
                candidate = _CompletedReportCandidate(writer, completed, parent)
                publish_owned_replacement(
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
                    f"Report publication evidence retained at {recovery.path}; "
                    f"expected directory identity {recovery.identity}; "
                    "current attachment must be verified"
                ),
            )
            raise


class _CompletedReportCandidate:
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


def _completed_report_tree(root: Path) -> BoundedInputTree:
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
                                raise ValueError("Completed report directory changed")
                            directories[name] = identity(node)
                            census(child, name + "/")
                            attached = os.stat(
                                entry.name, dir_fd=descriptor, follow_symlinks=False
                            )
                            if identity(attached) != identity(node):
                                raise ValueError(
                                    "Completed report directory attachment changed"
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
                            "Completed report contains a nonregular or aliased member"
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
            raise ValueError("Completed report changed while sealing its namespace")
        tree.check()
        return tree
    except BaseException:
        tree.close()
        raise
