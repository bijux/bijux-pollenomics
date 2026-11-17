"""Describe source replacement rules from their actual publication owners."""

from __future__ import annotations

from pathlib import Path

from ..contracts.models import SourceReplacementRule
from ..workflow.materialization.staging import build_staging_output_dir
from ..workflow.planning.source_registry import CONTEXT_SOURCE_SPECS

__all__ = ["build_source_replacement_rules"]


def build_source_replacement_rules(
    *,
    selected_sources: tuple[str, ...],
    source_output_roots: dict[str, str],
) -> dict[str, SourceReplacementRule]:
    """Describe the actual publication owner for each selected source."""
    rules: dict[str, SourceReplacementRule] = {}
    for source in selected_sources:
        final_output_root = source_output_roots[source]
        spec = CONTEXT_SOURCE_SPECS.get(source)
        callback_owned = source in {"aadr", "boundaries"} or (
            spec is not None and not spec.owns_output_publication
        )
        rules[source] = SourceReplacementRule(
            source=source,
            refresh_mode="owned_callback_replacement"
            if callback_owned
            else "staging_swap",
            final_output_root=final_output_root,
            staging_output_root=(
                None
                if callback_owned
                else str(build_staging_output_dir(Path(final_output_root)))
            ),
            destructive_refresh=True,
            preserves_previous_on_failure=True,
        )
    return rules
