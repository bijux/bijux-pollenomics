"""Register shared native source and immutable context fixtures."""

from ...resource_catalogue.native_captures import catalogue_sources as catalogue_sources
from ...resource_catalogue.reading.catalogue_publication import (
    publish_catalogue as publish_catalogue,
)
from ...resource_catalogue.reading.source_archive.original_metadata.historical_catalogues import (
    original_catalogue as original_catalogue,
)
from .native_context import context_inputs as context_inputs
