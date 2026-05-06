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


def build_site_ranking_policy(
    *, title: str, profile_name: str = "atlas_exploration"
) -> dict[str, str]:
    """Return the governed wording for candidate-site ranking outputs."""
    profile_policies = {
        "atlas_exploration": {
            "intro": (
                "This ranking is an atlas-adjacent heuristic for comparing current "
                "ancient-DNA locality anchors against nearby contextual layers with "
                "explicit evidence and missingness signals."
            ),
            "profile_warning": (
                "Atlas exploration favors interpretable descriptive ordering, not "
                "fieldwork commitment."
            ),
            "recommendation_gate": (
                "Sampling recommendation disabled: use fieldwork triage plus stronger "
                "cross-species and non-metadata evidence before promoting any locality."
            ),
        },
        "chronology_first": {
            "intro": (
                "This ranking stresses chronology agreement to expose how much of the "
                "atlas remains coherent when date overlap matters most."
            ),
            "profile_warning": (
                "Chronology-first ordering can still overrate thin evidence if source "
                "metadata are sparse or inconsistent."
            ),
            "recommendation_gate": (
                "Sampling recommendation disabled: chronology-heavy ordering is still "
                "a comparison aid, not a lake-selection decision."
            ),
        },
        "context_first": {
            "intro": (
                "This ranking stresses contextual support so the atlas shows how much "
                "candidate order depends on nearby non-aDNA evidence."
            ),
            "profile_warning": (
                "Context-first ordering can flatter busy neighborhoods even when "
                "direct ancient-DNA evidence remains weak."
            ),
            "recommendation_gate": (
                "Sampling recommendation disabled: context-heavy ordering is not a "
                "substitute for stronger direct evidence."
            ),
        },
        "fieldwork_triage": {
            "intro": (
                "This ranking uses a stricter pre-recommendation profile that treats "
                "missing chronology, single-species direct evidence, and metadata-only "
                "inputs as blockers for serious fieldwork posture."
            ),
            "profile_warning": (
                "Fieldwork triage is still a governed readiness screen, not a final "
                "sampling plan."
            ),
            "recommendation_gate": (
                "Sampling recommendation remains off unless chronology, context overlap, "
                "cross-species direct evidence, and non-metadata direct evidence all clear."
            ),
        },
    }
    profile_policy = profile_policies[profile_name]
    return {
        "title": f"{title} Candidate Site Ranking",
        "intro": profile_policy["intro"],
        "boundary": (
            "It does not collapse atlas convenience into scientific certainty, and it "
            "must not be read as a recommendation unless the explicit gate says so."
        ),
        "profile_warning": profile_policy["profile_warning"],
        "recommendation_gate": profile_policy["recommendation_gate"],
    }
