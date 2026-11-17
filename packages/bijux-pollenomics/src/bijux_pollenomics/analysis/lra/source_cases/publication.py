"""Retain complete conditional design outcomes when analytical execution refuses."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ....core.errors.cleanup import add_cleanup_note
from ....core.filesystem import OwnedTreeWriter
from .contracts import canonical
from .results import design_summaries


@contextmanager
def retain_failed_design(
    directory: Path, rows: list[dict[str, Any]], *, weighted: bool
) -> Iterator[None]:
    """Retain all unattempted mass privately without replacing a native failure."""
    try:
        yield
    except BaseException as primary:
        add_cleanup_note(
            primary,
            lambda: (
                f"Private conditional analytical evidence originally allocated at {directory.parent}; original source members are not embedded in the public derived view"
            ),
        )
        try:
            moments = design_summaries(rows, weighted=weighted)
            for value in moments.values():
                value.update(mean=None, population_covariance=None, complete=False)
            receipt = {
                "schema_version": "lra-source-case-failure.v1",
                "cases": rows,
                "summaries": moments,
                "status": "refused",
                "full_law_moments_available": False,
            }
            with OwnedTreeWriter(
                directory, max_bytes=64 * 1024 * 1024, max_files=1
            ) as writer:
                writer.write_bytes("failure-ledger.json", canonical(receipt))
        except Exception as secondary:

            def receipt_note(error: Exception = secondary) -> str:
                return f"Private source-case failure ledger refused: {type(error).__name__}"

            add_cleanup_note(primary, receipt_note)
        raise
