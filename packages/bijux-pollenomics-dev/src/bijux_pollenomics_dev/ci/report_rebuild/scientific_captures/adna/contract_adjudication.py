"""Joint literal-clause metadata adjudication; no loader, exporter or engine imports."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any

COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
ACCEPTANCE = "no pollen semantics leakage"
LIFECYCLE_CLAUSE = "Actual human and animal source-to-country metadata lifecycle has no pollen semantics leakage."
LEGACY_FIELDS = (
    "schema_version",
    "species_latin_name",
    "species_common_name",
    "source_family",
    "sample_namespace",
    "genetic_id",
    "master_id",
    "group_id",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "publication",
    "year_first_published",
    "full_date",
    "date_mean_bp",
    "date_stddev_bp",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "time_label",
    "dating_basis",
    "coordinate_confidence",
    "data_type",
    "molecular_sex",
    "datasets",
    "accession_lineage",
)
CURRENT_FIELDS = (*LEGACY_FIELDS, "sample_chronology", "sample_identity")


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def parse_object(raw: bytes) -> dict[str, Any]:

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(values) == len({k for k, _ in values}), "Duplicate metadata key")
        return dict(values)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite metadata: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(isinstance(result, dict), "Metadata object required")
    assert isinstance(result, dict)
    return result


def identity(row: dict[str, Any]) -> dict[str, Any]:
    name = row["path"]
    checksum = row["sha256"]
    require(isinstance(name, str), "Text identity path required")
    path = PurePosixPath(name)
    require(
        path.is_absolute()
        and path.as_posix() == name
        and (".." not in path.parts)
        and ("\\" not in name),
        "Absolute normalized metadata identity required",
    )
    require(
        type(row["bytes"]) is int
        and row["bytes"] >= 0
        and isinstance(checksum, str)
        and (len(checksum) == 64)
        and all(c in "0123456789abcdef" for c in checksum),
        "Typed metadata SHA/size required",
    )
    return {key: row[key] for key in ("path", "sha256", "bytes")}


def exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            (exact(a, b) for a, b in zip(left, right, strict=True))
        )
    return left == right


def zero(value: object) -> bool:
    return type(value) is int and value == 0


def index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        item = identity(row)
        require(item["path"] not in result, "Duplicate expected input path")
        result[item["path"]] = item
    return result


def joined_legacy_inputs(
    raw: dict[str, Any], saved: dict[str, Any]
) -> list[dict[str, Any]]:
    raw_expected = raw["declared_inputs"]
    saved_expected = saved["declared_inputs"]["files"]
    require(
        len({r["path"] for r in raw_expected}) == len(raw_expected)
        and len({r["path"] for r in saved_expected}) == len(saved_expected),
        "Duplicate declaration path",
    )
    raw_pins, saved_pins = (index(raw["input_pins"]), index(saved["input_pins"]))
    joined = []
    for country in COUNTRIES:
        stem = country.casefold()
        name = f"docs/report/countries/{stem}/{stem}_aadr_v66_samples.csv"
        left = [r for r in raw_expected if r["path"] == name]
        right = [r for r in saved_expected if r["path"] == name]
        require(
            len(left) == len(right) == 1,
            "Exact four historical country CSV identities required in both declarations",
        )
        a = {**left[0], "path": str(PurePosixPath(raw["private_source_root"]) / name)}
        b = {**right[0], "path": str(PurePosixPath(saved["repository"]) / name)}
        a, b = (identity(a), identity(b))
        require(
            exact(a, b)
            and exact(raw_pins.get(a["path"]), a)
            and exact(saved_pins.get(b["path"]), b),
            "Historical country input identity differs between actual jobs",
        )
        joined.append(
            {
                "country": country,
                "expected_identity": a,
                "raw_producer_input_verified": True,
                "saved_observer_input_verified": True,
                "sample_body_read_by_callback": False,
            }
        )
    return joined


def qualify_raw(d: dict[str, Any], refs: dict[str, Any]) -> dict[str, Any]:
    plan, inner, outer, producer, review = [
        d[k]
        for k in ("raw_plan", "raw_inner", "raw_outer", "raw_producer", "raw_review")
    ]
    candidate = plan["candidate"]
    require(
        plan["schema_version"] == "adna-owned-sample-export-plan.v1"
        and plan["canonical_identity_at_source_freeze"]["candidate"] == candidate
        and (plan["canonical_identity_at_source_freeze"]["status"] == "")
        and (plan["countries"] == list(COUNTRIES)),
        "Raw source epoch/country plan differs",
    )
    for receipt in (inner, outer):
        require(
            zero(receipt["actual_exit"])
            and receipt["candidate"] == candidate
            and (receipt["plan_sha256"] == refs["raw_plan"]["sha256"]),
            "Raw native plan/whole status differs",
        )
    require(
        exact(outer["inner_terminal"], refs["raw_inner"])
        and zero(outer["child_native_exit"])
        and (outer["child_timed_out"] is False)
        and all(
            outer[k] is True
            for k in (
                "registered_plan_unchanged",
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_outer_wall_bound_pass",
            )
        ),
        "Raw outer custody/resources differ",
    )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and (inner["live_canonical_equality_claimed"] is False)
        and all(
            inner[k] is True
            for k in (
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_whole_wall_bound_pass",
            )
        ),
        "Raw inner custody/resources differ",
    )
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2,
        "Both current raw producer and independent observer required",
    )
    for declared, actual, name, action in zip(
        plan["stages"],
        inner["stages"],
        ("maintained-sample-producer", "independent-source-sample-observer"),
        ("producer", "observer"),
        strict=True,
    ):
        require(
            declared["id"] == actual["id"] == name
            and declared["action"] == actual["action"] == action
            and exact(declared["argv"], actual["argv"])
            and (type(declared["timeout_seconds"]) is int)
            and (declared["timeout_seconds"] == 180)
            and (type(actual["timeout_seconds"]) is int)
            and (actual["timeout_seconds"] == 180)
            and zero(actual["actual_exit"])
            and (actual["timed_out"] is False),
            "Raw native role/argv/typed exit differs",
        )
    for obj in (producer, review):
        require(
            zero(obj["actual_exit"]) and obj["candidate"] == candidate,
            "Raw native witness differs",
        )
    require(
        producer["numerical_import_attempts"] == []
        and producer["new_current_source_contract"] is True
        and (producer["legacy_v1_inverse_or_historical_reproduction_claimed"] is False)
        and (
            producer[
                "rich_native_provenance_recovered_or_genotype_rights_ecology_human_LRA_admitted"
            ]
            is False
        ),
        "Raw producer scope inflated",
    )
    manifest = producer["runtime_manifest"]
    species = manifest["species_manifest"]["species"]
    require(
        manifest["schema_version"] == "adna-runtime-manifest.v1"
        and species["latin_name"] == "Homo sapiens"
        and (species["modalities"] == ["metadata_only"])
        and (species["source_families"] == ["AADR"]),
        "Current producer escaped the human metadata domain",
    )
    bundles = manifest["source_bundles"]
    require(
        len(bundles) == 1
        and bundles[0]["source_family"] == "AADR"
        and (bundles[0]["source_release"] == "v66")
        and (bundles[0]["dataset_names"] == ["1240k", "ho"])
        and (bundles[0]["record_modality"] == "metadata_only"),
        "Current source bundle domain differs",
    )
    require(
        producer["maintained_public_calls"]
        == [
            "build_homo_sapiens_runtime_manifest_for_version_dir",
            "load_species_samples(AdnaSampleQuery(political_entity=country))",
            "write_samples_csv(default_v2)",
            "write_samples_geojson(default_v2)",
        ],
        "Actual maintained loader/exporter call roles differ",
    )
    for key in (
        "historical_byte_equality_required_or_assumed",
        "old_v1_inverse_or_original_missing_receipt_recovery",
        "genotype_biology_ecology_rights_calibration_or_LRA_acceptance",
        "independent_observer_calls_public_loader_or_exporter",
    ):
        require(review[key] is False, "Raw observer scope inflated")
    require(
        review["full_typed_metadata_and_both_default_v2_transports_verified"] is True
        and review[
            "software_interval_hull_does_not_validate_disjoint_scientific_support"
        ]
        is True
        and (review["disjoint_support_gaps_remain_scientifically_refused"] is True),
        "Raw current export/support scope differs",
    )
    require(
        [r["country_query"] for r in producer["countries"]]
        == [r["country_query"] for r in review["countries"]]
        == list(COUNTRIES),
        "Raw country witnesses differ",
    )
    summaries = []
    for produced, observed in zip(
        producer["countries"], review["countries"], strict=True
    ):
        require(
            type(produced["sample_count"]) is int
            and type(observed["current_unique_samples"]) is int
            and (produced["sample_count"] == observed["current_unique_samples"])
            and (observed["full_typed_and_v2_CSV_GeoJSON_equal"] is True)
            and exact(
                produced["dataset_row_counts"], observed["current_dataset_row_counts"]
            ),
            "Full raw typed/transport population mismatch",
        )
        require(
            set(produced["products"]) == {"csv", "geojson", "typed"},
            "Exactly twelve current native product roles required",
        )
        audit = observed["duplicate_native_chronology_support_audit"]
        require(
            audit["original_supports_preserved"] is True
            and audit["calibration_or_chronology_scientifically_validated"] is False,
            "Original chronology support authority inflated",
        )
        for row in audit["duplicates"]:
            require(
                row["software_merge_match_is_scientific_chronology_validation"] is False
                and row["scientific_support_refusal"]
                == (
                    "disjoint_native_support_hull"
                    if row["open_gaps_introduced_by_hull"]
                    else ""
                ),
                "Duplicate support gap refused result lost",
            )
        summaries.append(
            {
                "country": observed["country_query"],
                "published": observed["current_unique_samples"],
                "dataset_counts": observed["current_dataset_row_counts"],
                "chronology_refusals": observed["chronology_refusals"],
                "duplicate_support_counts": audit["counts"],
                "legacy_comparison": observed["legacy_v1_comparison"],
            }
        )
    return {
        "source_candidate": candidate,
        "actual_stages": [0, 0],
        "whole_exits": [0, 0],
        "current_human_default_v2_export_executed": True,
        "current_export_schema": "adna-sample-record-export.v2",
        "current_CSV_fields": list(CURRENT_FIELDS),
        "owned_extensions": ["sample_chronology", "sample_identity"],
        "source_modality": "metadata_only",
        "twelve_full_typed_CSV_GeoJSON_products": True,
        "country_summaries": summaries,
        "scientific_chronology_admitted": False,
    }


def qualify_saved(d: dict[str, Any], refs: dict[str, Any]) -> dict[str, Any]:
    plan, common, outer, review = [
        d[k] for k in ("saved_plan", "saved_common", "saved_outer", "saved_review")
    ]
    candidate = plan["candidate"]
    require(
        plan["requirement_id"] == review["requirement_id"] == "ADNA-001"
        and plan["literal_clause"] == review["literal_clause"] == LIFECYCLE_CLAUSE,
        "Saved literal clause differs",
    )
    for obj in (common, outer):
        require(
            zero(obj["actual_exit"])
            and obj["plan_sha256"] == refs["saved_plan"]["sha256"]
            and (obj["candidate"] == candidate),
            "Saved actual plan/status differs",
        )
    require(
        exact(outer["common_terminal"], refs["saved_common"])
        and exact(outer["independent_review"], refs["saved_review"])
        and zero(outer["common_actual_exit"])
        and exact(outer["actual_native_stage_exits"], [0])
        and (outer["timed_out"] is False)
        and (outer["error"] is None)
        and (outer["after_input_error"] is None)
        and (outer["completed_whole_wall_bound_pass"] is True)
        and (outer["memory_bound_pass"] is True)
        and (outer["scientific_or_publication_admission"] is False),
        "Saved outer scope/custody differs",
    )
    require(
        common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
        and common["absent_input_paths_unchanged"] is True
        and exact(common["canonical_before"], common["canonical_after"])
        and (common["canonical_before"]["candidate"] == candidate),
        "Saved source custody differs",
    )
    require(
        len(plan["stages"]) == len(common["stages"]) == 1,
        "Exactly saved independent observer required",
    )
    expected, actual = (plan["stages"][0], common["stages"][0])
    require(
        expected["id"] == actual["id"] == "independent-adna-domain-joins"
        and exact(expected["argv"], actual["argv"])
        and (expected["must_succeed"] is actual["must_succeed"] is True)
        and (type(expected["timeout_seconds"]) is int)
        and (expected["timeout_seconds"] == 45)
        and (type(actual["timeout_seconds"]) is int)
        and (actual["timeout_seconds"] == 45)
        and zero(actual["actual_exit"])
        and (actual["timed_out"] is False),
        "Saved native observer role differs",
    )
    require(
        zero(review["actual_exit"])
        and review["candidate"] == candidate
        and (review["saved_product_no_pollen_semantics_leakage"] is True)
        and (type(review["original_whole_actual_exit"]) is int)
        and (review["original_whole_actual_exit"] == 1)
        and exact(review["original_native_stage_exits"], [0, 1]),
        "Original failed saved scope lost",
    )
    for key in (
        "successful_inventory_repeated",
        "original_lifecycle_execution_requalified",
        "missing_old_literal_receipt_recovered",
        "old_normalization_or_export_producers_repeated",
        "current_default_v2_population_reproduced",
        "exact_whole_requirement_adjudicated",
        "rights_human_biology_LRA_or_ecological_admission",
    ):
        require(review[key] is False, "Saved individual partial flag was promoted")
    schema = review["source_contracts"]
    require(
        schema["human_legacy"] == list(LEGACY_FIELDS)
        and schema["current_default_schema"] == "adna-sample-record-export.v2"
        and (
            schema["owned_current_extensions"]
            == ["sample_chronology", "sample_identity"]
        )
        and (schema["current_v2_population_execution_claimed"] is False),
        "Owned current29/source27 schema correspondence differs",
    )
    evidence = review["complete_saved_scientific_joins"]
    for key in (
        "source_acquisition_reauthenticated",
        "pollen_measurement_field_leakage",
        "pollen_eligibility_promoted",
        "current_v2_human_population_export_executed",
        "rights_human_biology_LRA_or_pollen_event_admission",
    ):
        require(evidence[key] is False, "Saved domain boundary promoted")
    blocked = evidence["animal"]["blocked_source_taxon_witnesses"]
    require(
        len(blocked) == 4
        and len({r["native_sample_id"] for r in blocked}) == 4
        and all(
            r["cross_species_publication_admitted"] is False
            and r["wild_domestic_analytical_equivalence_claimed"] is False
            and (r["taxon_alignment_status"] == "project_species_mismatch")
            and (r["inclusion_status"] == "sample_context_blocked")
            for r in blocked
        ),
        "Exact four blocked native taxon witnesses differ",
    )
    joins = evidence["compound_source_pointer_joins"]
    components = {
        component for row in joins for component in row["exact_catalog_components"]
    }
    return {
        "source_candidate": candidate,
        "actual_observer_exit": 0,
        "whole_exits": [0, 0],
        "original_failed_whole": 1,
        "original_stage_exits": [0, 1],
        "individual_current_v2_population_reproduced": False,
        "human": evidence["human"],
        "animal": {
            k: evidence["animal"][k]
            for k in ("source_ids", "mapped", "excluded", "nordic", "species_contracts")
        },
        "country_CSVs": evidence["country_csvs_checked"],
        "full_saved_animal_bundles": evidence["full_saved_animal_bundles_checked"],
        "declared_backlinks": evidence["declared_backlinks"],
        "used_backlinks": evidence["actually_used_backlinks"],
        "compound_field_joins": len(joins),
        "unique_compound_components": len(components),
        "historical_missing_metadata_digests": evidence[
            "historical_missing_metadata_digest_count"
        ],
        "all_four_native_taxon_refusals_preserved": True,
        "fresh_current_animal_source_to_country_producer_executed": False,
    }


def evaluate(
    d: dict[str, Any], refs: dict[str, Any], requirement: dict[str, Any]
) -> dict[str, Any]:
    rows = [r for r in requirement["requirements"] if r.get("id") == "ADNA-001"]
    require(
        len(rows) == 1 and rows[0]["acceptance"] == ACCEPTANCE,
        "Exact current requirement acceptance differs",
    )
    raw = qualify_raw(d, refs)
    saved = qualify_saved(d, refs)
    identities = joined_legacy_inputs(d["raw_plan"], d["saved_plan"])
    require(
        raw["source_candidate"] == saved["source_candidate"],
        "The reviewed joint source epochs differ",
    )
    h = saved["human"]
    a = saved["animal"]
    require(
        type(h["source_ids"]) is int
        and h["source_ids"] == h["published"] + h["coordinate_excluded"]
        and (h["chronology_statuses"] == {"review_required": h["source_ids"]}),
        "Human full source/refusal denominator differs",
    )
    require(
        a["source_ids"] == a["mapped"] + a["excluded"]
        and saved["declared_backlinks"] == saved["used_backlinks"]
        and (saved["historical_missing_metadata_digests"] == 3),
        "Animal/refusal/backlink history differs",
    )
    for country in raw["country_summaries"]:
        require(
            country["published"] == h["countries"][country["country"]]["published"],
            "Identical country inputs have differing observed source populations",
        )
    require(
        sum(r["published"] for r in raw["country_summaries"]) == h["published"],
        "Current and saved human population differs",
    )
    return {
        "schema_version": "adna-joint-literal-clause-adjudication.v1",
        "requirement_id": "ADNA-001",
        "literal_acceptance": ACCEPTANCE,
        "actual_callback_exit": 0,
        "callback_is_metadata_only_not_new_native_producer": True,
        "authenticated_metadata_references": refs,
        "exact_four_country_input_identity_join": identities,
        "current_human_execution": raw,
        "saved_population_observation": saved,
        "observed_population_software_no_pollen_semantics_leakage_supported": True,
        "whole_ADNA_001_closed": False,
        "whole_current_lifecycle_reproduction_claimed": False,
        "precise_residual": "No fresh maintained current animal source-to-four-country API/export producer is established by these two jobs. The successful saved-product observer is not an animal production run, and its original whole1/current-v2 false flags remain literal. A separate bounded current consumer of the ten normalized animal sources can address that behavioral residual without repeating archive normalization.",
        "remaining_boundaries": {
            "human_chronology_review_required": h["source_ids"],
            "historical_backlink_metadata_digest_absences": 3,
            "biological_rights_genotype_ecological_pollen_or_PROP_004_acceptance": False,
            "original_missing_native_receipt_recovered": False,
            "disjoint_support_scientifically_admitted": False,
        },
        "no_pollen_findings_scope": "Original saved human/animal fields, false eligibility/leakage flags and native taxon refusals plus the genuine current human29-field typed/CSV/GeoJSON transport. This is population/software-domain evidence, not a biological or scientific chronology decision.",
    }
