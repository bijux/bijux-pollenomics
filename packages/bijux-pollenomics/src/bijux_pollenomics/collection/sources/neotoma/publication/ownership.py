"""Keep one writer's inode anchored through source validation and publication."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import stat
from typing import TypeVar

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

_Result = TypeVar("_Result")


def _identity(root: Path) -> tuple[int, int]:
    if (
        not root.is_absolute()
        or root.resolve(strict=True) != root
        or any(member.is_symlink() for member in (root, *root.parents))
    ):
        raise ValueError("Source publication directory identity is redirected")
    node = root.stat(follow_symlinks=False)
    if not stat.S_ISDIR(node.st_mode):
        raise ValueError("Source publication inode is not an ordinary directory")
    return node.st_dev, node.st_ino


def _require_identity(root: Path, owned: tuple[int, int]) -> None:
    if _identity(root) != owned:
        raise ValueError(
            "Source publication directory identity differs from owned inode"
        )


def publish_owned_source_tree(
    writer: OwnedTreeWriter,
    *,
    staging: Path,
    final: Path,
    validate: Callable[[Path], _Result],
) -> _Result:
    """Validate both locations with the ownership descriptor still open.

    Byte equality does not establish ownership. Save identity before invoking
    validators, refuse replacement at either location, and retain all trees on
    failure. The caller keeps the writer open throughout this operation.
    """
    if writer.root != staging:
        raise ValueError("Source publication staging path differs from its writer")
    owned = _identity(staging)
    writer.validate_attachment()
    _require_identity(staging, owned)
    writer.validate_publication_attachment(staging)
    validate(staging)
    writer.validate_attachment()
    _require_identity(staging, owned)
    if final.name in {"", ".", ".."} or not final.is_absolute():
        raise ValueError("Source publication target is not a canonical path")
    writer.validate_publication_attachment(staging)
    _identity(final.parent)
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    _require_identity(final, owned)
    writer.validate_publication_attachment(final)
    result = validate(final)
    _require_identity(final, owned)
    writer.validate_publication_attachment(final)
    return result
