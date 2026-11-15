"""Authenticate and adapt native resource metadata without numerical admission."""

from .catalogue import load_atlas_resource_catalogue
from .models import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogue,
    AtlasResourceCatalogueInput,
)

__all__ = [
    "AtlasResourceArchiveInput",
    "AtlasResourceCatalogue",
    "AtlasResourceCatalogueInput",
    "load_atlas_resource_catalogue",
]
