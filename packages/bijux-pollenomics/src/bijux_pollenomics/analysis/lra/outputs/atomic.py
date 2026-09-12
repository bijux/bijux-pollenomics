"""Translate shared exclusive-publication errors into the LRA refusal contract."""

from __future__ import annotations

import errno
from pathlib import Path

from ....core.owned_tree import publish_new_output_tree
from ..engine.errors import LRARefusal


def publish_directory(stage: Path, destination: Path) -> None:
    """Publish one new LRA product using the shared no-replace tree primitive."""
    try:
        publish_new_output_tree(
            final_output_root=destination, staging_output_root=stage
        )
    except FileExistsError as exc:
        raise LRARefusal("lra_output_exists", str(destination)) from exc
    except ValueError as exc:
        raise LRARefusal("invalid_lra_output_path", str(exc)) from exc
    except OSError as exc:
        if exc.errno == errno.ENOTSUP:
            raise LRARefusal("atomic_publication_unavailable", str(exc)) from exc
        raise
