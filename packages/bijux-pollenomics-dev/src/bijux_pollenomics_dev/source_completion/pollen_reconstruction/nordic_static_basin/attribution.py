"""Preserve native DOI, investigator, constituent and captured policy scope."""

from .authority import PUBLICATION_AUTHORITY
from .publications import PREFIX, publication_inventory


def attribution(inputs: dict) -> dict:
    policy = inputs["verification/primary-policy-capture.json"]
    terminal = inputs["verification/primary-policy-native-terminal.json"]
    if (
        not policy["passed"]
        or terminal["native_exit_code"] != 0
        or not terminal["custody_after_unchanged"]
    ):
        raise ValueError("Nordic primary policy native authority differs")
    if len(policy["records"]) != 2 or any(
        row["http_status"] != 200
        or not row["transport_passed"]
        or not row["cc_by_4_0_marker_observed"]
        for row in policy["records"]
    ):
        raise ValueError("Nordic original primary policy capture differs")
    publications = publication_inventory(inputs)
    records = []
    for source in inputs["verification/source-census.json"]["cores"]:
        native = source["raw_source_metadata"]
        dataset = native["dataset"]
        if (
            dataset["datasetid"] != source["source_core"]["native_dataset_id"]
            or not dataset["doi"]
            or not dataset["datasetpi"]
        ):
            raise ValueError("Nordic original dataset attribution differs")
        records.append(
            {
                "native_dataset_id": dataset["datasetid"],
                "native_collection_unit_id": native["collection_unit"][
                    "collectionunitid"
                ],
                "dataset_name": dataset["datasetname"],
                "constituent_database": dataset["database"],
                "original_doi_tokens": dataset["doi"],
                "original_investigator_records": dataset["datasetpi"],
                "original_contribution_notes": dataset["datasetnotes"],
                "source_handle": native["collection_unit"]["handle"],
                "historical_workbook_access_marker": source["raw_metadata_fields"][
                    "DataRestricted/NotRestriced"
                ],
                "historical_marker_applied_as_current_public_source_permission": False,
                "native_site_id": source["source_core"]["native_site_id"],
                "returned_native_publication_inventory": publications[
                    dataset["datasetid"]
                ],
            }
        )
    return {
        "schema_version": "nordic-retained-source-attribution.v1",
        "datasets": sorted(records, key=lambda row: row["native_dataset_id"]),
        "attribution_complete": all(
            row["attribution_complete"] for row in publications.values()
        ),
        "attribution_scope": "Complete attribution of the four returned native dataset publication inventories only; no article-content authentication, historical replay, chronology accuracy or rights upgrade.",
        "pending_primary_publication_dataset_ids": sorted(
            did for did, row in publications.items() if not row["attribution_complete"]
        ),
        "primary_publication_inventory_status": "Four native primary dataset relations to three distinct publication IDs qualified from saved HTTP200 responses. Secondary records and DOI nulls remain native.",
        "native_primary_dataset_relation_count": sum(
            len(row["primary"]) for row in publications.values()
        ),
        "distinct_primary_publication_ids": sorted(
            {
                decision["native_publication"]["publicationid"]
                for row in publications.values()
                for decision in row["primary"]
            }
        ),
        "native_secondary_dataset_relation_count": sum(
            len(row["secondary"]) for row in publications.values()
        ),
        "empty_native_publication_response_count": sum(
            row["empty_publication_response"] for row in publications.values()
        ),
        "refused_native_publication_relation_count": sum(
            len(row["refusals"]) for row in publications.values()
        ),
        "publication_capture_authority": PUBLICATION_AUTHORITY,
        "existing_policy_citation_account": inputs[PREFIX + "qualification.json"][
            "existing_policy_citation_account"
        ],
        "original_source_census_receipt_status": inputs[
            "verification/source-census-terminal.json"
        ]["status"],
        "original_articles_acquired_or_authenticated": False,
        "preferred_policy_citations": [
            {
                "scope": "Neotoma Paleoecology Database",
                "reference": (
                    "Williams, Grimm et al. (2018). The Neotoma Paleoecology "
                    "Database: A multi-proxy, international community-curated "
                    "data resource. Quaternary Research 89, 156-177."
                ),
                "database_pid": "https://doi.org/10.17616/R3PD38",
                "policy_body_sha256": (
                    "f5ae5e79f7dd1a4d6dd846fa9a63a14129dc8b0ea9c21ed484289304be01b85e"
                ),
            },
            {
                "scope": "European Pollen Database",
                "reference": (
                    "Fyfe et al. (2009). The European Pollen Database: past "
                    "efforts and current activities. Vegetation History and "
                    "Archaeobotany 18, 417-424."
                ),
                "policy_body_sha256": (
                    "f5ae5e79f7dd1a4d6dd846fa9a63a14129dc8b0ea9c21ed484289304be01b85e"
                ),
            },
            {
                "scope": "Named MADCAP chronologies used for the two Solsoe cores",
                "reference": (
                    "Giesecke et al. (2014). Towards mapping the late "
                    "Quaternary vegetation change of Europe. Vegetation History "
                    "and Archaeobotany 23, 75-86."
                ),
                "selected_chronology_ids": [25732, 25740],
                "policy_body_sha256": (
                    "f5ae5e79f7dd1a4d6dd846fa9a63a14129dc8b0ea9c21ed484289304be01b85e"
                ),
                "scope_limit": (
                    "Policy-preferred citation and named model attribution; "
                    "no article acquisition, chronology refit or age accuracy "
                    "is established by this account."
                ),
            },
        ],
        "source_provider": "Neotoma Paleoecology Database",
        "constituent": "European Pollen Database",
        "captured_primary_policy_records": policy["records"],
        "policy_scope": "Actual recorded HTTP200 bodies/CCBY markers, with constituent and original investigator/dataset attribution. A separate later403 lookup does not replace these bytes. This account does not grant blanket historical author/PANGAEA rights or per-dataset embargo authority.",
        "rights_and_raw_redistribution_admitted": False,
        "raw_counts_or_sample_age_masks_included": False,
        "raw_source_support_remains_local": True,
    }
