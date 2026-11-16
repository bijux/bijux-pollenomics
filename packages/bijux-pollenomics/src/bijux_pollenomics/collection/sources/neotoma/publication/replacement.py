"""Owned source replacement and format-specific bounded preservation profiles."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
import json
import os
from pathlib import Path
import secrets
from typing import Any, TypeVar

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note
from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor
from bijux_pollenomics.core.filesystem.regular_inputs import BoundedInputTree
from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement
from bijux_pollenomics.core.repository import (
    RepositoryRootNotFoundError,
    find_repository_root,
)
from bijux_pollenomics.evidence.sources.neotoma.validation import (
    RELATIONAL_MATERIALIZATION_MAX_BYTES as RELATIONAL_MATERIALIZATION_MAX_BYTES,
)

SOURCE_MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MANIFEST_MAX_BYTES = 16 * 1024 * 1024
_Result = TypeVar("_Result")


def _same_filesystem(left: DirectoryAnchor, right: DirectoryAnchor) -> bool:
    return os.fstat(left.fd).st_dev == os.fstat(right.fd).st_dev


def _destination_repository(parent: Path) -> Path | None:
    for candidate in (parent, *parent.parents):
        if not (
            os.path.lexists(candidate / "pyproject.toml")
            or os.path.lexists(candidate / "packages" / "bijux-pollenomics")
        ):
            continue
        try:
            repository = find_repository_root(candidate)
        except RepositoryRootNotFoundError:
            return None
        return repository if parent.is_relative_to(repository) else None
    return None


def replace_neotoma_tree(
    final: Path,
    *,
    build: Callable[[OwnedTreeWriter], None],
    validate: Callable[[Path], _Result],
    max_bytes: int,
) -> _Result:
    """Retain failed candidates and predecessors without changing source formats.

    The nearest recognized destination repository owns central artifact receipts.
    Another volume retains its recovery tree locally. Standalone destinations
    use private local recovery and receipts without borrowing a source checkout.
    """
    final = Path(final).absolute()
    if max_bytes not in {SOURCE_MAX_BYTES, RELATIONAL_MATERIALIZATION_MAX_BYTES}:
        raise ValueError("Neotoma replacement profile is not established")
    for kind in ("staging", "recovery"):
        collision = final.parent / f".{final.name}.{kind}"
        if os.path.lexists(collision):
            raise FileExistsError(f"Neotoma {kind} path collision: {collision}")
    with ExitStack() as stack:
        parent = stack.enter_context(DirectoryAnchor(final.parent, create=True))
        repository = _destination_repository(parent.path)
        prior = None
        if os.path.lexists(final):
            prior = stack.enter_context(
                BoundedInputTree(
                    final,
                    max_bytes=max_bytes,
                    max_files=MAX_FILES,
                    member_limits={"manifest.json": MANIFEST_MAX_BYTES},
                )
            )
            validate(final)
            prior.validate()
        local = False
        receipt_root = None
        if repository is not None:
            artifacts = repository / "artifacts" / "neotoma-publication"
            storage = stack.enter_context(DirectoryAnchor(artifacts, create=True))
            token = "replacement-" + secrets.token_hex(16)
            os.mkdir(token, 0o700, dir_fd=storage.fd)
            receipt_root = artifacts / token
            local = _same_filesystem(parent, storage)
        if local:
            assert receipt_root is not None
            recovery_path = receipt_root
        else:
            recovery_name = ".neotoma-recovery-" + secrets.token_hex(16)
            os.mkdir(recovery_name, 0o700, dir_fd=parent.fd)
            recovery_path = final.parent / recovery_name
        if receipt_root is None:
            receipt_root = recovery_path
        recovery = stack.enter_context(DirectoryAnchor(recovery_path))
        receipts = stack.enter_context(
            OwnedTreeWriter(
                receipt_root / "receipts", max_bytes=1024 * 1024, max_files=8
            )
        )

        def record(status: str, fields: dict[str, Any]) -> None:
            payload = {
                "status": status,
                "destination": str(final),
                "recovery_root": str(recovery_path),
                "destination_volume_recovery": not local,
                "owning_repository": None if repository is None else str(repository),
                "max_bytes": max_bytes,
                "max_files": MAX_FILES,
                **fields,
            }
            receipts.write_bytes(
                status + ".json",
                (json.dumps(payload, sort_keys=True, allow_nan=False) + "\n").encode(),
            )

        record("prepared", {"prior_present": prior is not None})
        writer = stack.enter_context(
            OwnedTreeWriter(
                recovery_path / "candidate", max_bytes=max_bytes, max_files=MAX_FILES
            )
        )
        try:
            build(writer)
        except BaseException as error:
            try:
                record("refused-build", {"prior_preserved": prior is not None})
            except Exception as receipt_error:

                def receipt_note(failure: Exception = receipt_error) -> str:
                    return (
                        "Neotoma refusal receipt could not be written: "
                        + type(failure).__name__
                    )

                add_cleanup_note(error, receipt_note)
            add_cleanup_note(
                error, lambda: f"Neotoma recovery state retained at {recovery_path}"
            )
            raise
        try:
            return publish_owned_replacement(
                writer,
                final=final,
                prior=prior,
                recovery=recovery,
                validate=validate,
                record=record,
            )
        except BaseException as error:
            add_cleanup_note(
                error, lambda: f"Neotoma recovery state retained at {recovery_path}"
            )
            raise
