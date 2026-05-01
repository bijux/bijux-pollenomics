from __future__ import annotations

from .models import SourceReplacementRule
from .pipeline.staging import build_staging_output_dir

__all__ = ["build_source_replacement_rules"]


def build_source_replacement_rules(
    *,
    selected_sources: tuple[str, ...],
    source_output_roots: dict[str, str],
) -> dict[str, SourceReplacementRule]:
    """Describe destructive refresh behavior for every selected source."""
    rules: dict[str, SourceReplacementRule] = {}
    for source in selected_sources:
        final_output_root = source_output_roots[source]
        rules[source] = SourceReplacementRule(
            source=source,
            refresh_mode="staging_swap",
            final_output_root=final_output_root,
            staging_output_root=str(build_staging_output_dir(final_output_root)),
            destructive_refresh=True,
            preserves_previous_on_failure=True,
        )
    return rules
