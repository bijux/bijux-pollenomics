"""Render compact retained numerical support without publishing raw count rows."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from .authority import DESCRIPTOR_SHA256, SOURCE_SHA256


def products(values: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive reader statistics from admitted captures, not a fresh model run."""
    account = values["source-account.json"]
    review = values["independent-source-review.json"]
    attempts = values["bridge-attempt-population.json"]
    cases = []
    for source in sorted(
        values["full-vector-source-account.json"],
        key=lambda row: row["native_sample_id"],
    ):
        diagnostic = source["diagnostic"]
        cases.append(
            {
                "native_sample_id": source["native_sample_id"],
                "curated_sample_id": source["curated_sample_id"],
                "native_entity_id": source["native_entity"]["ID_ENTITY"],
                "native_site_id": source["native_site"]["ID_SITE"],
                "entity_name": source["native_entity"]["entity_name"],
                "coordinates": diagnostic["native_coordinates"],
                "entire_reported_label_count": diagnostic["literal_common_label_count"],
                "all_reported_count_total": diagnostic["source_count_sum_all_labels"],
                "maximum_absolute_percentage_point_difference": diagnostic[
                    "max_abs_shared_percentage_point_difference"
                ],
                "entire_saved_vector_exact_rational_equal": diagnostic[
                    "entire_literal_vector_exact_rational_equal"
                ],
                "entire_vector_within_assumed_saved_decimal_quantum": diagnostic[
                    "entire_literal_vector_within_display_quantum"
                ],
                "zero_imputation_performed": False,
                "denominator_contains_polypodiales": any(
                    row["taxon_clean"] == "Polypodiales"
                    and Decimal(row["taxon_count"]) > 0
                    for row in source["original_native_pollen_rows"]
                ),
                "basin_category_2017": source["original2017_metadata"]["BASIN_SIZE"],
                "basin_category_2021": source["native_site"]["ID_BASIN_SIZE"],
            }
        )
    grouped = Counter((row["id_bridge_hypothesis"], row["result"]) for row in attempts)
    precision = "Nearest rounding to each saved decimal token's quantum is a declared diagnostic assumption; author rounding is unauthenticated."
    summary = {
        "schema_version": "embsecbio-literal-correspondence-account.v1",
        "producer_scope": "Replay a retained source-bound account; no fresh count scan, classifier or model execution.",
        "native_capture_authority": {
            "candidate": values["native-terminal.json"]["candidate"],
            "plan_sha256": values["native-terminal.json"]["plan_sha256"],
            "terminal_sha256": SOURCE_SHA256["native-terminal.json"],
            "descriptor_sha256": DESCRIPTOR_SHA256,
        },
        "native_taxon_labels_in_original_audit": 1184,
        "curated_source": {
            "samples": account["curated_samples"],
            "taxon_labels": account["curated_taxon_labels"],
        },
        "native_join_population": {
            "records": account["native_joined_records"],
            "eligible": review["native_eligible_population"],
            "refused": account["source_refusals"],
        },
        "bridge_attempts": {
            "attempted": account["bridge_attempts"],
            "outcomes": account["bridge_attempt_outcomes"],
            "by_hypothesis": [
                {"hypothesis": hypothesis, "outcome": outcome, "rows": count}
                for (hypothesis, outcome), count in sorted(grouped.items())
            ],
        },
        "conditional_support": {
            "coordinate_equal": review["coordinate_equal"],
            "shared_literal_values": review["conditional_shared_literal_match"],
            "entire_reported_axes": review["conditional_entire_reported_axis_match"],
            "shared_matches_with_incomplete_reported_axes": 110,
            "entire_saved_vectors_exact_rational_equal": 0,
            "precision_assumption": precision,
        },
        "entire_reported_axis_cases": cases,
        "interpretation": {
            "entire_axis": "All12 or13 reported labels in the two cases, not all242 model taxa or all1184 native labels.",
            "denominator": "Sum of all reported native counts; spore presence prevents assuming terrestrial pollen.",
            "offset": "ID+20000 has zero coordinate-consistent cases in this430-candidate cohort; no general crosswalk admitted.",
            "geometry": "Khodzal basin categories LARG and SMAL differ across releases; coordinates/name agreement is not physical basin authority.",
            "chronology": "No new age selector, age-scale transfer or calendar-modernity claim.",
        },
        "private_raw_rows_promoted": False,
        "authenticated_pipeline_or_historical_reproduction": False,
    }
    access = values["supplement-access-account.json"]
    refusals = {
        "schema_version": "embsecbio-literal-correspondence-source-refusals.v1",
        "source_refused_rows": account["source_refusals"],
        "supplement": {
            "url": access["requested_url"],
            "http_status": access["http_status"],
            "complete_response_body_bytes": access["retained_body_bytes"],
            "body_sha256": access["retained_body_sha256"],
            "DOCX_admitted": False,
        },
        "scoped_alternate_discovery": {
            "exact_named_S1_found": values["alternate-source-discovery.json"][
                "local_scope"
            ]["exact_named_S1_found"],
            "scope": "Inspected primary Reading, institutional, author-repository and local bundles; no exhaustive worldwide absence claim.",
        },
        "unsettled_inputs": account["missing_inputs"],
        "unauthenticated_claims": [
            "full taxon amalgamation",
            "historical author crosswalk",
            "general pollen denominator",
            "missing-row measurement zeros",
            "original release/age selector",
            "taxonomy review",
            "rights",
        ],
        "conditional_literal_evidence_retained": True,
        "external_outreach_sent": False,
    }
    return {"report.json": summary, "source-refusals.json": refusals}
