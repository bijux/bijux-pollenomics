"""Public reporting API for country, atlas, and published report builds."""

from ..adna import AdnaLocalitySummary, AdnaSampleRecord
from .adna import SchemaError, load_country_samples, summarize_localities
from .models import (
    AnimalFoundationRefreshReport,
    CountryReport,
    MultiCountryMapReport,
    PublishedReportsReport,
)
from .presentation.text import slugify
from .service import (
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
    refresh_animal_adna_foundation,
)

__all__ = [
    "AdnaLocalitySummary",
    "AdnaSampleRecord",
    "AnimalFoundationRefreshReport",
    "CountryReport",
    "MultiCountryMapReport",
    "PublishedReportsReport",
    "SchemaError",
    "generate_country_report",
    "generate_multi_country_map",
    "generate_published_reports",
    "load_country_samples",
    "refresh_animal_adna_foundation",
    "slugify",
    "summarize_localities",
]
