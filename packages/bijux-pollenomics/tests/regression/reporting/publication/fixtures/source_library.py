"""Declare contextual source authority for generated publication fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

CONTEXT_PROVIDERS = (
    "bijux_pollenomics.adna.projects.evidence.sites",
    "bijux_pollenomics.adna.projects.evidence.coordinates",
    "bijux_pollenomics.adna.projects.registry.samples",
    "bijux_pollenomics.adna.projects.registry.localities",
    "bijux_pollenomics.adna.workflow.normalization.samples",
)


@contextmanager
def generated_source_library(data_root: Path) -> Iterator[Path]:
    """Declare no contextual library while retaining real availability checks."""
    data_root.mkdir(parents=True)
    assert not any(data_root.iterdir()), "Generated contextual input must be empty"
    with ExitStack() as stack:
        for module in CONTEXT_PROVIDERS:
            stack.enter_context(
                patch(module + ".repository_data_root", return_value=data_root)
            )
        yield data_root
    assert not any(data_root.iterdir()), "Generated contextual input must stay empty"
