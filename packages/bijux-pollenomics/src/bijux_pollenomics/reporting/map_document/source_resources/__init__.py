"""Authenticate and adapt native resource metadata without numerical admission."""

from .ancillary.models import AtlasAncillaryFederationInput, AtlasAncillaryMetadata
from .catalogue import load_atlas_resource_catalogue
from .models import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogue,
    AtlasResourceCatalogueInput,
)

__all__ = [
    "AtlasAncillaryFederationInput",
    "AtlasAncillaryMetadata",
    "AtlasResourceArchiveInput",
    "AtlasResourceCatalogue",
    "AtlasResourceCatalogueInput",
    "load_atlas_resource_catalogue",
]
