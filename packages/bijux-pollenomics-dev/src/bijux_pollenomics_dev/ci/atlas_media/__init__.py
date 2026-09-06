"""Deterministic no-basemap media for governed atlas storyboards."""

from .contracts import AtlasMediaError, AtlasMediaPlan, SelectedStory, StorySelection
from .gallery import (
    build_gallery_manifest,
    write_gallery_manifest,
)
from .run_evidence import build_run_evidence_index, write_run_evidence_index
from .storyboards import load_storyboard_manifest, select_stories


def materialize_atlas_media(plan: AtlasMediaPlan) -> dict[str, object]:
    """Load the subprocess-owning runner only when materialization is requested."""
    from .runner import materialize_atlas_media as run

    return run(plan)


__all__ = [
    "AtlasMediaError",
    "AtlasMediaPlan",
    "SelectedStory",
    "StorySelection",
    "build_gallery_manifest",
    "build_run_evidence_index",
    "load_storyboard_manifest",
    "materialize_atlas_media",
    "select_stories",
    "write_gallery_manifest",
    "write_run_evidence_index",
]
