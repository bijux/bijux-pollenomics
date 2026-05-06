from __future__ import annotations

from .reporting.models import CountryReport

__all__ = [
    "build_country_report_policy",
    "build_multi_country_map_policy",
    "build_sample_inventory_policy",
    "build_site_ranking_policy",
]


def build_country_report_policy(report: CountryReport) -> dict[str, str]:
    """Return the governed wording for one Homo sapiens country report."""
    return {
        "title": f"{report.country} Homo sapiens aDNA {report.version} Report",
        "summary_label": "Unique Homo sapiens aDNA samples",
        "intro": (
            f"This bundle was generated from Homo sapiens ancient-DNA release metadata "
            f"published in AADR `{report.version}` on `{report.generated_on}`."
        ),
        "scope": (
            f"It inventories only Homo sapiens aDNA sample rows that match the "
            f"`{report.country}` country filter. Environmental and archaeology context "
            "layers are published in the shared map bundle, not duplicated here."
        ),
        "empty_result_note": (
            "This country bundle is valid even when the filter returns zero Homo sapiens "
            "aDNA samples. In that case the CSV, GeoJSON, and markdown exports remain "
            "present so downstream checks can distinguish an empty result from a "
            "missing artifact."
        ),
        "dedup_note": (
            f"The report deduplicates samples by `genetic_id` across datasets. Dataset "
            f"row counts can differ by coverage, but the combined inventory for "
            f"`{report.country}` contains `{report.total_unique_samples}` unique "
            f"Homo sapiens aDNA samples in AADR `{report.version}`."
        ),
    }


def build_sample_inventory_policy(report: CountryReport) -> dict[str, str]:
    """Return the governed wording for the full Homo sapiens sample inventory."""
    return {
        "title": f"{report.country} Homo sapiens aDNA {report.version} Sample Inventory",
        "summary": (
            f"Generated on `{report.generated_on}`. Total Homo sapiens aDNA samples: "
            f"`{report.total_unique_samples}`."
        ),
    }


def build_multi_country_map_policy(
    *,
    title: str,
    version: str,
    generated_on: str,
) -> dict[str, str]:
    """Return the governed wording for the shared Homo sapiens atlas bundle."""
    return {
        "title": title,
        "intro": (
            f"This shared interactive map bundle was generated on `{generated_on}`."
        ),
        "scope": (
            f"It combines Homo sapiens aDNA records from AADR `{version}` with whichever "
            "contextual datasets are present in the repository at generation time and "
            "copies those derived artifacts into this directory."
        ),
        "count_note": (
            "Country sample counts in this README refer to Homo sapiens aDNA records "
            "derived from AADR. Context layers can have different geographic scope and "
            "record counts inside the map."
        ),
    }


def build_site_ranking_policy(*, title: str) -> dict[str, str]:
    """Return the governed wording for candidate-site ranking outputs."""
    return {
        "title": f"{title} Candidate Site Ranking",
        "intro": (
            "This ranking is an atlas-adjacent heuristic for comparing current Homo "
            "sapiens aDNA localities derived from AADR metadata against nearby "
            "contextual layers."
        ),
        "boundary": (
            "It is not yet a lake-selection or sampling recommendation engine."
        ),
    }
