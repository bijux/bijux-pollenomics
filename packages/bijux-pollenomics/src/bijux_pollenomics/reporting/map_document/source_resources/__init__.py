"""Authenticate and adapt native resource metadata without numerical admission."""

from .ancillary.models import (
    AtlasAncillaryArchivesInput,
    AtlasAncillaryFederationInput,
    AtlasAncillaryMetadata,
    AtlasAncillarySupportingMetadata,
    AtlasContextArchiveInput,
    AtlasSourceArchiveInput,
    AtlasTaxonAncestryArchiveInput,
)
from .catalogue import load_atlas_resource_catalogue
from .models import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogue,
    AtlasResourceCatalogueInput,
)

__all__ = [
    "AtlasAncillaryArchivesInput",
    "AtlasAncillarySupportingMetadata",
    "AtlasContextArchiveInput",
    "AtlasSourceArchiveInput",
    "AtlasTaxonAncestryArchiveInput",
    "AtlasAncillaryFederationInput",
    "AtlasAncillaryMetadata",
    "AtlasResourceArchiveInput",
    "AtlasResourceCatalogue",
    "AtlasResourceCatalogueInput",
    "load_atlas_resource_catalogue",
]
