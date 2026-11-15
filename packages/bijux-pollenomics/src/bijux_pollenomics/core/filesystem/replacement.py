"""Preserve predecessors while attaching descriptor-owned replacement trees."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
import os
from pathlib import Path
from typing import Any, TypeVar

from .anchors import DirectoryAnchor, identity
from .owned_writes import OwnedTreeWriter
from .owned_writes import _rename_directory as _rename_directory
from .regular_inputs import BoundedInputTree

_Result = TypeVar("_Result")


def _attached(parent: DirectoryAnchor, name: str) -> tuple[int, int, int] | None:
    parent.check()
    try:
        return identity(os.stat(name, dir_fd=parent.fd, follow_symlinks=False))
    except FileNotFoundError:
        return None


def _move(
    source: DirectoryAnchor,
    name: str,
    target: DirectoryAnchor,
    attached_name: str,
    expected: tuple[int, int, int],
) -> None:
    source.check()
    target.check()
    if _attached(source, name) != expected:
        raise ValueError("Replacement source attachment identity changed")
    _rename_directory(source.fd, name, attached_name, destination_descriptor=target.fd)
    if _attached(target, attached_name) != expected:
        raise ValueError("Replacement target attachment identity changed")


def publish_owned_replacement(
    writer: OwnedTreeWriter,
    *,
    final: Path,
    prior: BoundedInputTree | None,
    recovery: DirectoryAnchor,
    validate: Callable[[Path], _Result],
    record: Callable[[str, dict[str, Any]], None] | None = None,
) -> _Result:
    """Publish and validate one candidate, retaining all recoverable failed state.

    The caller owns a private recovery directory on the destination filesystem.
    No operation deletes an entry. No-replace protects destination attachment;
    source checks are boundary seals, not an OS inode compare-and-swap primitive.
    """
    final = Path(final).absolute()
    with (
        DirectoryAnchor(final.parent) as parent,
        DirectoryAnchor(writer.root.parent) as stage_parent,
    ):
        writer.validate_attachment()
        with DirectoryAnchor(writer.root) as candidate:
            if (
                len(
                    {
                        os.fstat(anchor.fd).st_dev
                        for anchor in (parent, stage_parent, recovery)
                    }
                )
                != 1
            ):
                raise ValueError("Owned replacement requires one rename filesystem")
            if (prior is None) != (_attached(parent, final.name) is None):
                raise ValueError("Replacement destination differs from prior authority")
            if (
                prior is not None
                and _attached(parent, final.name) != prior.anchor.identity
            ):
                raise ValueError("Replacement prior directory identity changed")
            candidate_id = candidate.identity
            prior_id = None if prior is None else prior.anchor.identity
            try:
                writer.validate_closed_attachment(writer.root)
                validate(writer.root)
                writer.validate_closed_attachment(writer.root)
                if prior is not None:
                    prior.validate()
                    _move(parent, final.name, recovery, "prior", prior.anchor.identity)
                    prior.rebind(recovery.path / "prior")
                    prior.validate()
                writer.validate_attachment()
                _move(stage_parent, writer.root.name, parent, final.name, candidate_id)
                writer.validate_closed_attachment(final)
                result = validate(final)
                writer.validate_closed_attachment(final)
                parent.check()
                recovery.check()
                if record is not None:
                    record("published", {"retained_predecessor": prior is not None})
                writer.validate_closed_attachment(final)
                parent.check()
                recovery.check()
                return result
            except BaseException as primary_error:
                parent.check()
                recovery.check()
                # A competing final stays at its user path; never move it for cleanup.
                if _attached(parent, final.name) == candidate_id:
                    with suppress(ValueError, FileExistsError):
                        writer.validate_closed_attachment(final)
                        _move(
                            parent,
                            final.name,
                            recovery,
                            "refused-publication",
                            candidate_id,
                        )
                restored = False
                if (
                    prior is not None
                    and _attached(recovery, "prior") == prior_id
                    and _attached(parent, final.name) is None
                ):
                    prior.rebind(recovery.path / "prior")
                    prior.validate()
                    try:
                        _move(
                            recovery, "prior", parent, final.name, prior.anchor.identity
                        )
                    except FileExistsError:
                        pass
                    else:
                        prior.rebind(final)
                        restored = True
                if record is not None:
                    current = _attached(parent, final.name)
                    try:
                        record(
                            "refused",
                            {
                                "predecessor_restored": restored,
                                "retained_predecessor": _attached(recovery, "prior")
                                == prior_id
                                if prior is not None
                                else False,
                                "foreign_destination_preserved": current is not None
                                and current not in {candidate_id, prior_id},
                            },
                        )
                    except Exception as receipt_error:
                        primary_error.add_note(
                            f"Refusal receipt failed: {type(receipt_error).__name__}: "
                            f"{receipt_error}; retained recovery: {recovery.path}"
                        )
                raise
