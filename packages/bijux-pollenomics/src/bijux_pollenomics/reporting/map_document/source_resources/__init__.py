"""Authenticate and adapt native resource metadata without numerical admission."""

from .catalogue import load_atlas_resource_catalogue
from .models import AtlasResourceCatalogue, AtlasResourceCatalogueInput

__all__ = [
    "AtlasResourceCatalogue",
    "AtlasResourceCatalogueInput",
    "load_atlas_resource_catalogue",
]
