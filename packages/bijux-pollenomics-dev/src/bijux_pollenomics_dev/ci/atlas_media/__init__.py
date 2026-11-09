"""Deterministic no-basemap media for governed atlas storyboards."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .contracts import AtlasMediaError, AtlasMediaPlan, SelectedStory, StorySelection

if TYPE_CHECKING:
    from .gallery import build_gallery_manifest, write_gallery_manifest
    from .run_evidence import build_run_evidence_index, write_run_evidence_index
    from .storyboards import load_storyboard_manifest, select_stories

_LAZY_EXPORTS = {
    "build_gallery_manifest": ".gallery",
    "write_gallery_manifest": ".gallery",
    "build_run_evidence_index": ".run_evidence",
    "write_run_evidence_index": ".run_evidence",
    "load_storyboard_manifest": ".storyboards",
    "select_stories": ".storyboards",
}


def __getattr__(name: str) -> Any:
    """Load source-aware media helpers only when their public API is requested."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(_LAZY_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


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
