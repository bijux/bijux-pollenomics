from __future__ import annotations

from collections.abc import Iterable

from .merging import merge_neotoma_site_rows
from .source_projection import build_neotoma_site_row_from_download
from .summaries import populate_neotoma_site_summary_fields


def build_neotoma_site_rows_from_downloads(
    download_rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Aggregate full dataset downloads into one enriched site row per Neotoma site."""
    site_rows = []
    for item in download_rows:
        row = build_neotoma_site_row_from_download(item)
        if row is not None:
            site_rows.append(row)
    merged_rows = merge_neotoma_site_rows(site_rows)
    for row in merged_rows:
        populate_neotoma_site_summary_fields(row)
    return merged_rows
