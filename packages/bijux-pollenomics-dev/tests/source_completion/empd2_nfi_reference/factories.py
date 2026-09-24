"""NFI-outcome-blind source and review-return factories for focused tests."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from bijux_pollenomics_dev.source_completion.empd2_nfi_reference import (
    build_empd2_nfi_decision_projection,
)
from pyproj import Geod


def json_bytes(value: object) -> bytes:
    """Serialize deterministic fixture bytes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    """Hash canonical fixture JSON."""
    return sha256(json_bytes(value)).hexdigest()


def nfi_schema() -> tuple[bytes, str]:
    """Build the separately pinned structural NFI column schema."""
    headers = [
        "Year",
        "TractID",
        "PlotID",
        "Inventory_Date",
        "Easting",
        "Northing",
        "PlotArea",
        "LandUseClass",
        "Treelayers",
        "Fully_layered",
        "MeanHeight",
        "SiteIndex",
        "SISpecies",
        "StandAge",
        "Maturityclass",
        "Stand_density",
        "Stand_gaps",
        "DwStem",
        "DwBranch",
        "DwRootStump",
        "VolPine",
        "VolContorta",
        "VolSpruce",
        "VolBirch",
        "VolOtherDec",
        "BaPine",
        "BaContorta",
        "BaSpruce",
        "BaBirch",
        "BaOtherDec",
        "MeanDbhAll",
        "MeanDbhPine",
        "MeanDbhContorta",
        "MeanDbhSpruce",
        "MeanDbhBirch",
        "MeanDbhOtherDec",
        "NoStemsPine",
        "NoStemsContorta",
        "NoStemsSpruce",
        "NoStemsBirch",
        "NoStemsOtherDec",
        "Soilmoisture_code",
        "Soiltype_code",
        "Soiltexture_code",
        "Soildepth_code",
        "Bottomlayertype_code",
        "Fieldlayertype_code",
    ]
    content = json_bytes(
        {
            "acquisition_receipt_sha256": "1" * 64,
            "candidate_estimand": "matched point/plot tree composition or structure only",
            "data_dimension_declared_not_counted": "A1:AU43893",
            "data_rows_opened": 0,
            "final_test_labels_opened": False,
            "header_count": 47,
            "headers": headers,
            "readme_dimension": "A1:N109",
            "regional_area_cover_truth_admitted": False,
            "schema_version": "nfi-workbook-schema-review.v1",
            "selected_readme_descriptions": {
                "BaBirch": "Basal area of birch (m2/ha)",
                "BaPine": "Basal area of pine (m2/ha)",
                "BaSpruce": "Basal area of spruce (m2/ha)",
                "Easting": "Meters. Sweref99TM",
                "Inventory_Date": "YYYY-MM-DD",
                "LandUseClass": (
                    "National classification according to table. Only plots from "
                    "Forestland according to FAO-definitions included."
                ),
                "NoStemsPine": "No of stems of pine (no/ha)",
                "Northing": "Meters. Sweref99TM",
                "PlotArea": (
                    "Circular plot r=7 => 153.94 m2 (only un-divided plots included)"
                ),
                "VolBirch": "Volume of birch (m3/ha)",
                "VolPine": "Volume of pine (m3/ha)",
                "VolSpruce": "Volume of spruce (m3/ha)",
                "Year": "Year of inventory (2007-2025)",
            },
            "sheet_names": ["ReadMe", "2007-2025"],
            "source_byte_count": 1,
            "source_sha256": "8" * 64,
        }
    )
    return content, sha256(content).hexdigest()


def sources() -> dict[str, Any]:
    """Build exact source-shaped bytes for 16 spatial leads."""
    workbook = "8" * 64
    source = "5" * 64
    spatial_rows = []
    dossier_rows = []
    for index in range(16):
        sample = f"sample-{index:02d}"
        nfi_index = index - 1 if index in {1, 3, 5} else index
        year = "2011" if index == 1 else str(2010 + nfi_index % 10)
        lead = {
            "distance_m_wgs84": float(nfi_index + 0.125),
            "mechanical_count_candidate": True,
            "nearest_row_selection": "distance_only; NFI year is not temporally matched",
            "nfi_inventory_date_source_native": f"date-{nfi_index}",
            "nfi_plot": str(200 + nfi_index),
            "nfi_tract": str(1000 + nfi_index),
            "nfi_year": year,
            "pair_admission": "candidate_only",
            "pollen_agebp_source_native": -20,
            "pollen_ageuncertainty_source_native": "A",
            "pollen_review_reason_codes": ["cross_source_identity_unresolved"]
            if index == 0
            else [],
            "pollen_sample": sample,
            "time_support": "unresolved_collection_time",
        }
        spatial_rows.append(lead)
        dossier_rows.append(
            {
                "collection_time_source_note": None,
                "collection_time_status": "not_authenticated_from_source_fields",
                "independent_vegetation_pair_admission": False,
                "publication_link_count": 0,
                "source_age_uncertainty_lookup": {
                    "source_age_range_label": "fixture",
                    "source_description": "fixture",
                },
                "source_metadata_excluding_vegdescription": {
                    "samplename": sample,
                    "originalsamplename": sample,
                    "sitename": f"site-{index:02d}",
                    "country": "Sweden",
                    "latitude": 60.0 + nfi_index / 100,
                    "longitude": 15.0 + nfi_index / 100,
                    "locationreliability": "fixture-reviewed",
                    "locationnotes": "fixture",
                    "areaofsite": "fixture",
                    "samplecontext": "surface",
                    "sampletype": "surface",
                    "samplemethod": "fixture",
                    "agebp": -20,
                    "ageuncertainty": "A",
                    "notes": "fixture",
                    "empd_version": "EMPD2",
                },
                "source_publications": [],
                "spatial_lead": lead,
            }
        )
    _, schema_sha = nfi_schema()
    spatial = {
        "schema_version": "empd2-nfi-spatial-feasibility.v2",
        "evidence_role": "candidate_spatial_leads_only",
        "scientific_admission": "candidate_only",
        "independent_vegetation_pair_count": 0,
        "nfi_plot_year_rows": 16,
        "nfi_distinct_plots": 14,
        "swedish_pollen_samples": 16,
        "pollen_invalid_coordinate_count": 0,
        "thresholds_descriptive_only": {
            key: {
                "candidate_plot_year_sample_pairs": 16,
                "nfi_plot_years": 14,
                "nfi_plots": 14,
                "pollen_samples": 16,
            }
            for key in ("1000", "5000", "10000")
        },
        "thresholds_mechanical_count_candidates_only": {
            key: {
                "candidate_plot_year_sample_pairs": 16,
                "nfi_plot_years": 14,
                "nfi_plots": 14,
                "pollen_samples": 16,
            }
            for key in ("1000", "5000", "10000")
        },
        "nfi_source_crs": "SWEREF99TM (source ReadMe); EPSG:3006 for candidate transform",
        "distance_method": "unrounded WGS84 inverse geodesic on transformed NFI and source EMPD2 points",
        "collection_time_comparability": "unresolved_for_all_pollen_samples",
        "worksheet_access": "entire XML streamed; only first six identity/geometry cells selected, no tree measurements displayed or scored",
        "source_hashes": {
            "empd2_screen": "6" * 64,
            "empd2_source": source,
            "nfi_eligibility": "a" * 64,
            "nfi_schema": schema_sha,
            "nfi_workbook": workbook,
        },
        "nearest_nfi_row_by_pollen_sample": spatial_rows,
    }
    spatial_bytes = json_bytes(spatial)
    dossier = {
        "schema_version": "empd2-nfi-source-dossier.v1",
        "spatial_report_sha256": sha256(spatial_bytes).hexdigest(),
        "scientific_admission": "candidate_only",
        "independent_vegetation_pair_count": 0,
        "selected_lead_count": 16,
        "source_sha256": source,
        "selection": "unrounded distance_m_wgs84 <= 1000; descriptive source review only",
        "source_metadata_columns": [
            "samplename",
            "originalsamplename",
            "sitename",
            "country",
            "longitude",
            "latitude",
            "locationreliability",
            "locationnotes",
            "areaofsite",
            "samplecontext",
            "sampletype",
            "samplemethod",
            "agebp",
            "ageuncertainty",
            "notes",
            "empd_version",
        ],
        "source_explicit_collection_date_column": None,
        "samples_with_publication_links": 0,
        "samples_with_collection_note_cues": 0,
        "source_age_uncertainty_counts": {"A": 16},
        "source_age_value_kinds": {"numeric": 16},
        "rows": list(reversed(dossier_rows)),
    }
    dossier_bytes = json_bytes(dossier)
    guide = b"%PDF-1.7\nsource-bound fixture"
    return {
        "dossier_bytes": dossier_bytes,
        "dossier_sha256": sha256(dossier_bytes).hexdigest(),
        "spatial_bytes": spatial_bytes,
        "spatial_sha256": sha256(spatial_bytes).hexdigest(),
        "guide_bytes": guide,
        "guide_sha256": sha256(guide).hexdigest(),
        "workbook_sha256": workbook,
    }


def projection() -> dict[str, Any]:
    """Build the deterministic fixture projection."""
    return build_empd2_nfi_decision_projection(**sources())


def parameter_manifest(
    value: dict[str, Any],
) -> tuple[bytes, str, list[dict[str, Any]]]:
    """Build exact PPE and fall-speed rows for every accepted taxon."""
    rows = []
    for taxon, name, ppe, fall in (
        ("taxon:birch", "Betula", 1.0, 0.024),
        ("taxon:pine", "Pinus", 2.0, 0.031),
    ):
        row = {
            "taxon_id": taxon,
            "accepted_taxon_name": name,
            "accepted_taxon_rank": "genus",
            "lra_model_taxon_id": taxon,
            "ppe_binding": _parameter_binding(taxon, "ppe", ppe),
            "fall_speed_binding": _parameter_binding(taxon, "fall_speed", fall),
            "evidence_reference_ids": [f"evidence:parameters:{taxon}"],
        }
        row["parameter_row_sha256"] = digest(row)
        rows.append(row)
    manifest = {
        "schema_version": "empd2-lra-taxon-parameters.v1",
        "pollen_source_sha256": value["source_identities"]["empd2_source"],
        "accepted_taxon_ids": ["taxon:birch", "taxon:pine"],
        "ppe_reference_taxon": "taxon:birch",
        "rows": rows,
    }
    content = json_bytes(manifest)
    return content, sha256(content).hexdigest(), rows


def _parameter_binding(taxon: str, kind: str, value: float) -> dict[str, Any]:
    normalized_units = "dimensionless_pollen_productivity" if kind == "ppe" else "m/s"
    units = "relative_to_reference_taxon" if kind == "ppe" else "m/s"
    return {
        "parameter_record_id": f"parameter:{taxon}:{kind}",
        "parameter_record_sha256": digest([taxon, kind, "record"]),
        "parameter_candidate_id": f"candidate:{taxon}:{kind}",
        "parameter_candidate_sha256": digest([taxon, kind, "candidate"]),
        "source_value_text": str(value),
        "source_value": value,
        "source_units": units,
        "source_uncertainty_text": None,
        "source_uncertainty_value": None,
        "normalized_value": value,
        "normalized_units": normalized_units,
        "normalization_profile": (
            "identity-relative-ppe-to-dimensionless.v1"
            if kind == "ppe"
            else "identity-m-per-second.v1"
        ),
        "reference_taxon": "taxon:birch" if kind == "ppe" else None,
        "applicability_domain": "empd2-nfi-reference",
        "normalization_rationale": "Exact reviewed source value and units.",
    }


def taxon_receipt(
    value: dict[str, Any], parameter_sha256: str
) -> tuple[dict[str, Any], str]:
    """Build a receipt and its independently supplied content identity."""
    receipt = {
        "schema_version": "empd2-nfi-taxon-ppe-admission.v1",
        "pollen_source_sha256": value["source_identities"]["empd2_source"],
        "accepted_taxon_ids": ["taxon:birch", "taxon:pine"],
        "parameter_binding_sha256": parameter_sha256,
        "reviewer_id": "reviewer:taxon-ppe",
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "evidence_reference_ids": ["evidence:parameter-review"],
        "disposition": "accepted_for_reference_contract",
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
    }
    return receipt, digest(receipt)


def mapping_manifest(
    value: dict[str, Any], parameter_sha: str, parameter_rows: list[dict[str, Any]]
) -> tuple[bytes, str]:
    """Build exact source-native p_vars rows with reviewed mapping intent."""
    parameter_shas = {
        row["taxon_id"]: row["parameter_row_sha256"] for row in parameter_rows
    }
    rows = []
    for source_var in range(1, 5231):
        canonical_var = (
            source_var if source_var <= 1901 else 1 + (source_var - 1902) % 1901
        )
        taxon = {1: "taxon:birch", 2: "taxon:pine"}.get(canonical_var)
        native = {
            "var_": source_var,
            "acc_var_": canonical_var,
            "original_varname": f"source-taxon-{source_var}",
            "acc_varname": f"accepted-source-taxon-{canonical_var}",
            "groupid": "TRSH" if taxon else "HERB",
        }
        row = {
            **native,
            "mapping_disposition": "accepted" if taxon else "refused_unmapped",
            "taxon_id": taxon,
            "parameter_row_sha256": parameter_shas.get(taxon),
            "reason_codes": ["reviewed-parameter-mapping"]
            if taxon
            else ["outside-accepted-taxa"],
            "p_vars_row_sha256": digest(
                {
                    "pollen_source_sha256": value["source_identities"]["empd2_source"],
                    **native,
                }
            ),
        }
        rows.append(row)
    manifest = {
        "schema_version": "empd2-p-vars-taxon-mapping.v1",
        "pollen_source_sha256": value["source_identities"]["empd2_source"],
        "taxon_parameter_binding_sha256": parameter_sha,
        "source_row_count": 5230,
        "rows": rows,
    }
    content = json_bytes(manifest)
    return content, sha256(content).hexdigest()


def pollen_count_index(
    value: dict[str, Any], mapping_sha: str, parameter_sha: str
) -> tuple[bytes, str, bytes, str, list[dict[str, Any]]]:
    """Build a non-quantitative index; quantitative sample bytes stay sealed."""
    attestation = {
        "schema_version": "empd2-pollen-count-producer-attestation.v1",
        "pollen_source_sha256": value["source_identities"]["empd2_source"],
        "sample_count": 16,
        "source_row_count": 476,
        "closure_status": "externally_attested_not_runtime_verified",
        "producer_id": "producer:fixture-pinned-sqlite",
        "evidence_reference_ids": ["evidence:pinned-sqlite-count-export"],
        "source_table_schema": {
            "table": "p_counts",
            "columns": [
                {
                    "name": "samplename",
                    "declared_type": "VARCHAR(25)",
                    "not_null": True,
                },
                {"name": "var_", "declared_type": "INTEGER", "not_null": True},
                {
                    "name": "count",
                    "declared_type": "NUMERIC(12,6)",
                    "not_null": False,
                },
            ],
            "primary_key": ["samplename", "var_"],
        },
        "query_contract": {
            "selected_columns": ["samplename", "var_", "count"],
            "sample_denominator": sorted(
                row["pollen_sample"] for row in value["candidate_rows"]
            ),
            "predicate": {
                "column": "samplename",
                "operator": "in",
                "value_source": "sample_denominator",
            },
            "order_by": ["samplename", "var_"],
        },
        "null_source_row_count": 0,
        "duplicate_source_row_count": 0,
        "noninteger_count_row_count": 0,
        "negative_count_row_count": 0,
        "out_of_mapping_var_row_count": 0,
        "nonpositive_mapped_denominator_sample_count": 0,
        "taxon_mapping_manifest_sha256": mapping_sha,
    }
    rows = []
    for candidate in value["candidate_rows"]:
        sample = candidate["pollen_sample"]
        payload = json_bytes({"sealed_fixture_only": sample})
        row = {
            "pollen_sample": sample,
            "pollen_source_sha256": value["source_identities"]["empd2_source"],
            "sample_payload_sha256": sha256(payload).hexdigest(),
            "sample_payload_size": len(payload),
            "payload_schema_id": "empd2-p-counts-sample.v1",
            "taxon_mapping_manifest_sha256": mapping_sha,
            "taxon_parameter_binding_sha256": parameter_sha,
        }
        row["index_row_sha256"] = digest(row)
        rows.append(row)
    attestation["ordered_payload_set_sha256"] = digest(
        [
            {
                "pollen_sample": row["pollen_sample"],
                "sample_payload_sha256": row["sample_payload_sha256"],
                "sample_payload_size": row["sample_payload_size"],
                "payload_schema_id": row["payload_schema_id"],
            }
            for row in rows
        ]
    )
    attestation_bytes = json_bytes(attestation)
    attestation_sha = sha256(attestation_bytes).hexdigest()
    index = {
        "schema_version": "empd2-pollen-count-sealed-index.v1",
        "pollen_source_sha256": value["source_identities"]["empd2_source"],
        "taxon_mapping_manifest_sha256": mapping_sha,
        "taxon_parameter_binding_sha256": parameter_sha,
        "producer_attestation_sha256": attestation_sha,
        "sample_count": 16,
        "rows": rows,
    }
    index_bytes = json_bytes(index)
    return (
        index_bytes,
        sha256(index_bytes).hexdigest(),
        attestation_bytes,
        attestation_sha,
        rows,
    )


def evidence_manifest(
    value: dict[str, Any],
    count_index_sha256: str,
    producer_attestation_sha256: str,
    count_index_rows: list[dict[str, Any]],
) -> tuple[bytes, str]:
    """Build externally pinnable evidence without opening sealed count payloads."""
    rows = []
    geod = Geod(ellps="WGS84")
    for index, candidate in enumerate(value["candidate_rows"]):
        longitude, latitude, _ = geod.fwd(
            candidate["pollen_longitude"],
            candidate["pollen_latitude"],
            90.0,
            candidate["distance_m_wgs84"],
        )
        pollen_period = {
            "younger_bp": -100,
            "older_bp": 25,
            "age_type": "BP",
            "evidence_reference_ids": ["evidence:pollen-collection-interval"],
        }
        vegetation_period = {
            "younger_bp": 1949 - int(candidate["nfi_year"]),
            "older_bp": 1951 - int(candidate["nfi_year"]),
            "age_type": "BP",
            "evidence_reference_ids": ["evidence:nfi-date-conversion"],
        }
        pollen_support = {
            "latitude": candidate["pollen_latitude"],
            "longitude": candidate["pollen_longitude"],
            "radius_m": 100.0,
            "coordinate_uncertainty_m": 10.0,
            "younger_bp": pollen_period["younger_bp"],
            "older_bp": pollen_period["older_bp"],
            "coordinate_crs": "EPSG:4326",
            "spatial_profile": "bounded-footprint-radius-v1",
            "temporal_profile": "typed-bp-interval-v1",
        }
        vegetation_support = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_m": 50.0,
            "coordinate_uncertainty_m": 5.0,
            "younger_bp": vegetation_period["younger_bp"],
            "older_bp": vegetation_period["older_bp"],
            "coordinate_crs": "EPSG:4326",
            "spatial_profile": "bounded-footprint-radius-v1",
            "temporal_profile": "typed-bp-interval-v1",
        }
        pollen_support["footprint_sha256"] = digest(pollen_support)
        vegetation_support["footprint_sha256"] = digest(vegetation_support)
        count_index_row = count_index_rows[index]
        rows.append(
            {
                "record_id": candidate["record_id"],
                "source_row_sha256": candidate["source_row_sha256"],
                "pollen_collection_period": pollen_period,
                "pollen_support": pollen_support,
                "vegetation_support": vegetation_support,
                "paired_footprint": {
                    "source_distance_m_wgs84": candidate["distance_m_wgs84"],
                    "reviewed_max_pair_distance_m": 1000.0,
                    "relation": "reviewed_proximity_support_compatible",
                    "evidence_reference_ids": ["evidence:pair-support-review"],
                },
                "nfi_inventory_date_source_native": candidate[
                    "nfi_inventory_date_source_native"
                ],
                "inventory_time_binding": {
                    "native_inventory_date": candidate[
                        "nfi_inventory_date_source_native"
                    ],
                    "conversion_profile": "reviewed-native-date-to-bp-interval.v1",
                    "converted_interval_sha256": digest(vegetation_period),
                    "evidence_reference_ids": ["evidence:nfi-date-conversion"],
                },
                "vegetation_observation_period": vegetation_period,
                "pollen_source_binding": {
                    "index_row": count_index_row,
                    "pollen_count_index_sha256": count_index_sha256,
                    "producer_attestation_sha256": producer_attestation_sha256,
                    "payload_access_status": "sealed_unopened",
                    "count_closure_status": "externally_attested_not_runtime_verified",
                },
                "estimand": {
                    "estimand_id": "nfi:point-plot-tree-basal-area",
                    "rows": [
                        {
                            "taxon_id": "taxon:birch",
                            "source_column": "BaBirch",
                            "variable_id": "variable:birch-basal-area",
                            "unit": "unit:m2-per-ha",
                        },
                        {
                            "taxon_id": "taxon:pine",
                            "source_column": "BaPine",
                            "variable_id": "variable:pine-basal-area",
                            "unit": "unit:m2-per-ha",
                        },
                    ],
                    "support_role": "point_plot_tree_measurement_not_area_cover",
                },
                "nfi_rights_evidence_reference_ids": ["evidence:cc0-guide"],
                "independence_status": "reviewed_independent",
                "independence_evidence_reference_ids": ["evidence:independence-review"],
            }
        )
    manifest = {
        "schema_version": "empd2-nfi-reference-evidence.v1",
        "projection_sha256": value["projection_sha256"],
        "reviewer_id": "reviewer:declared",
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "rows": rows,
    }
    content = json_bytes(manifest)
    return content, sha256(content).hexdigest()


def admission(evidence_row: dict[str, Any], receipt_sha256: str) -> dict[str, Any]:
    """Select one exact row of externally pinned reviewed evidence."""
    return {
        "evidence_row_sha256": digest(evidence_row),
        "taxon_ppe_receipt_sha256": receipt_sha256,
    }


def returned(
    *, admit_first: bool
) -> tuple[dict[str, Any], str | None, bytes | None, str | None]:
    """Build one canonical complete return."""
    value = projection()
    parameter_bytes, parameter_sha, parameter_rows = parameter_manifest(value)
    del parameter_bytes
    receipt, receipt_sha = taxon_receipt(value, parameter_sha)
    _, mapping_sha = mapping_manifest(value, parameter_sha, parameter_rows)
    index_bytes, index_sha, attestation_bytes, attestation_sha, index_rows = (
        pollen_count_index(value, mapping_sha, parameter_sha)
    )
    del index_bytes, attestation_bytes
    evidence_bytes, evidence_sha = evidence_manifest(
        value, index_sha, attestation_sha, index_rows
    )
    evidence = json.loads(evidence_bytes)["rows"]
    decisions = []
    for index, candidate in enumerate(value["candidate_rows"]):
        admitted = admit_first and index == 0
        decisions.append(
            {
                "record_id": candidate["record_id"],
                "source_row_sha256": candidate["source_row_sha256"],
                "disposition": "declared_inclusion" if admitted else "refused",
                "reason_codes": [
                    "reviewed_identity_support_and_estimand"
                    if admitted
                    else "collection_time_not_authenticated"
                ],
                "evidence_reference_ids": [f"evidence:{candidate['record_id']}"],
                "admission": admission(evidence[index], receipt_sha)
                if admitted
                else None,
            }
        )
    return (
        {
            "schema_version": "empd2-nfi-reference-decisions.v1",
            "projection_sha256": value["projection_sha256"],
            "admission_id": "review:empd2-nfi",
            "reviewer_id": "reviewer:declared",
            "reviewer_authority": "declared_not_authenticated",
            "decision_date": "2026-09-24",
            "rationale": "Every source lead was reviewed without outcome access.",
            "outcome_access_status": "not_started",
            "taxon_ppe_receipt": receipt if admit_first else None,
            "decisions": decisions,
        },
        receipt_sha if admit_first else None,
        evidence_bytes if admit_first else None,
        evidence_sha if admit_first else None,
    )
