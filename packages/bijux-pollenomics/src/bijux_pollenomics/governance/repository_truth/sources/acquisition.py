"""Source-family acquisition and reader-truth queue construction."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

from .core_counts import _build_source_assessment_counts as _build_core_counts

__all__ = [
    "build_repository_source_acquisition_queue",
    "render_repository_source_acquisition_queue_markdown",
]

_AcquisitionRow = TypedDict(
    "_AcquisitionRow",
    {
        "source_family": str,
        "priority": str,
        "current_gap": str,
        "required_outcome": str,
    },
)
_AcquisitionPayload = TypedDict(
    "_AcquisitionPayload",
    {"row_count": int, "rows": list[_AcquisitionRow]},
)


def build_repository_source_acquisition_queue(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Publish the next real acquisition or reader-truth work across source families."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    animal_gap_row = {
        "queue_key": "animal_adna_repo_ingestion",
        "source_family": "animal_adna",
        "priority": "high",
        "current_gap": "local reference supplements exceed repository supplement capture",
        "required_outcome": "ingest staged paper and supplement assets into governed repo surfaces, then extract sample, site, and chronology rows",
        "evidence_anchor": "data/adna/governance/source_library/reference_stash_reconciliation.json",
    }
    if (
        counts["papers_with_local_reference_supplements"]
        <= counts["papers_with_archived_supplements"]
    ):
        animal_gap_row = {
            "queue_key": "animal_adna_sample_extraction",
            "source_family": "animal_adna",
            "priority": "high",
            "current_gap": "repository supplement capture now matches visible local staging, but sample, site, and chronology extraction still lags",
            "required_outcome": "use the archived paper supplements to publish sample-owned identity, locality, chronology, and coordinate evidence",
            "evidence_anchor": "data/adna/governance/source_library/project_source_evidence_matrix.json",
        }
    rows = [
        animal_gap_row,
    ]
    surface_to_source = {
        "landclim_site_count": "landclim",
        "landclim_grid_cell_count": "landclim",
        "neotoma_point_count": "neotoma",
        "sead_point_count": "sead",
        "raa_total_site_count": "raa",
        "raa_heritage_site_count": "raa",
    }
    for surface in counts["zero_collection_summary_surfaces"]:
        rows.append(
            {
                "queue_key": f"{surface}_collection_summary_repair",
                "source_family": surface_to_source.get(surface, "source_collection"),
                "priority": "medium",
                "current_gap": f"collection summary still reports `{surface}` as zero",
                "required_outcome": "rebuild the collection summary so public cross-domain counts stop understating the tracked source family",
                "evidence_anchor": "data/collection_summary.json",
            }
        )
    return {
        "schema_version": "repository-source-acquisition-queue.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_source_acquisition_queue_markdown(
    payload: dict[str, object],
) -> str:
    queue = cast(_AcquisitionPayload, payload)
    lines = [
        "# Repository source acquisition queue",
        "",
        "This queue names the source families whose current tracked capture still",
        "lags the public story. It is a recovery surface, not a vague wishlist:",
        "each row states the concrete source-family gap that still blocks a more",
        "credible publication posture.",
        "",
        f"- Queue rows: `{queue['row_count']}`",
        "",
        "| Source family | Priority | Current gap | Required outcome |",
        "| --- | --- | --- | --- |",
    ]
    for row in queue["rows"]:
        lines.append(
            f"| `{row['source_family']}` | `{row['priority']}` | {row['current_gap']} | {row['required_outcome']} |"
        )
    return "\n".join(lines) + "\n"
