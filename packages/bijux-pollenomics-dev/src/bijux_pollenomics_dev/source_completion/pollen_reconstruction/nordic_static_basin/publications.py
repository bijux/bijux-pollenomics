"""Bind returned native publication relations to the exact Nordic source cores."""

from __future__ import annotations

from .authority import CAPTURE_PINS, FAMILY, PUBLICATION_AUTHORITY

PREFIX = "verification/publication-metadata/"


def assess_publications(payload: object, dataset_id: int, site_id: int) -> dict:
    """Preserve native primary, secondary, empty and refused relation populations."""
    if (
        not isinstance(payload, dict)
        or payload.get("status") != "success"
        or not isinstance(payload.get("data"), list)
    ):
        return {
            "attribution_complete": False,
            "refusals": ["response is not native success/data-list"],
            "primary": [],
            "secondary": [],
            "publication_decisions": [],
        }
    publications = payload["data"]
    seen = set()
    duplicate_ids = set()
    for item in publications:
        publication = item.get("publication") if isinstance(item, dict) else None
        pid = (
            publication.get("publicationid") if isinstance(publication, dict) else None
        )
        if type(pid) is int and pid > 0:
            if pid in seen:
                duplicate_ids.add(pid)
            seen.add(pid)
    decisions = []
    for ordinal, item in enumerate(publications):
        publication = item.get("publication") if isinstance(item, dict) else None
        row = {
            "source_row_ordinal": ordinal,
            "native_publication": publication,
            "refusals": [],
        }
        if not isinstance(publication, dict):
            row["refusals"].append("publication wrapper missing or not object")
            decisions.append(row)
            continue
        pid = publication.get("publicationid")
        if type(pid) is not int or pid <= 0:
            row["refusals"].append("publication ID is not positive native integer")
        elif pid in duplicate_ids:
            row["refusals"].append(
                "publication ID repeats within exact dataset response"
            )
        relations = publication.get("datasets")
        matches = (
            [
                relation
                for relation in relations
                if isinstance(relation, dict)
                and type(relation.get("datasetid")) is int
                and relation["datasetid"] == dataset_id
            ]
            if isinstance(relations, list)
            else []
        )
        if len(matches) != 1:
            row["refusals"].append("exact native dataset relation absent or ambiguous")
        else:
            relation = matches[0]
            row["native_dataset_relation"] = relation
            if type(relation.get("siteid")) is not int or relation["siteid"] != site_id:
                row["refusals"].append("native relation site differs or is missing")
            if type(relation.get("primary")) is not bool:
                row["refusals"].append("primary status is not native boolean")
            else:
                row["actual_native_primary"] = relation["primary"]
                if relation["primary"] and (
                    not isinstance(publication.get("citation"), str)
                    or not publication["citation"].strip()
                ):
                    row["refusals"].append("primary citation absent or blank")
        row["admitted_as_returned_native_relation"] = not row["refusals"]
        decisions.append(row)
    return {
        "attribution_complete": any(
            row.get("admitted_as_returned_native_relation")
            and row.get("actual_native_primary") is True
            for row in decisions
        )
        and not any(row["refusals"] for row in decisions),
        "primary": [
            row
            for row in decisions
            if row.get("admitted_as_returned_native_relation")
            and row.get("actual_native_primary") is True
        ],
        "secondary": [
            row
            for row in decisions
            if row.get("admitted_as_returned_native_relation")
            and row.get("actual_native_primary") is False
        ],
        "refusals": [row for row in decisions if row["refusals"]],
        "publication_decisions": decisions,
        "returned_native_publication_count": len(publications),
        "empty_publication_response": not publications,
        "scope": "Attribution of returned native records only; not historical equivalence, chronology accuracy or independently checked original article identity.",
    }


def _native_output(receipt: dict, authority: dict, output_sha256: str) -> None:
    if (
        receipt.get("status") != "PASS"
        or type(receipt.get("native_exit_code")) is not int
        or receipt["native_exit_code"] != 0
        or receipt.get("custody_after_checked") is not True
        or receipt.get("custody_after_unchanged") is not True
        or receipt.get("custody_errors") != []
        or receipt.get("owned_survivors") != {}
        or "resource_failure" not in receipt
        or receipt["resource_failure"] is not None
        or receipt.get("candidate") != authority["candidate"]
        or receipt.get("plan_sha256") != authority["plan_sha256"]
    ):
        raise ValueError("Nordic publication native terminal authority differs")
    product = receipt.get("product_files", {}).get("consumer-result.json", {})
    if product.get("sha256") != output_sha256:
        raise ValueError("Nordic publication terminal output identity differs")


def publication_inventory(inputs: dict) -> dict[int, dict]:
    """Reconcile saved source bytes and classifications without any new retrieval."""
    required = [
        PREFIX + name
        for name in (
            "acquisition.json",
            "acquisition-terminal.json",
            "qualification.json",
            "qualification-terminal.json",
            "dataset-4445.json",
            "dataset-4446.json",
            "dataset-20034.json",
            "dataset-52082.json",
        )
    ]
    if any(name not in inputs for name in required):
        raise ValueError("Nordic primary publication source capture missing")
    acquisition = inputs[PREFIX + "acquisition.json"]
    qualification = inputs[PREFIX + "qualification.json"]
    acquisition_receipt = inputs[PREFIX + "acquisition-terminal.json"]
    qualification_receipt = inputs[PREFIX + "qualification-terminal.json"]
    acquisition_hash = CAPTURE_PINS[FAMILY + "/" + PREFIX + "acquisition.json"]
    qualification_hash = CAPTURE_PINS[FAMILY + "/" + PREFIX + "qualification.json"]
    _native_output(
        acquisition_receipt, PUBLICATION_AUTHORITY["acquisition"], acquisition_hash
    )
    _native_output(
        qualification_receipt,
        PUBLICATION_AUTHORITY["qualification"],
        qualification_hash,
    )
    if (
        acquisition.get("passed") is not True
        or qualification.get("passed") is not True
        or acquisition.get("actual_dataset_GET_count") != 4
        or acquisition.get("preferred_citation_additional_GET_count") != 0
        or qualification.get("actual_fresh_GETs") != 0
        or qualification.get("actual_acquisition_terminal_sha256")
        != CAPTURE_PINS[FAMILY + "/" + PREFIX + "acquisition-terminal.json"]
    ):
        raise ValueError("Nordic publication acquisition/qualification scope differs")
    census_hash = CAPTURE_PINS[FAMILY + "/verification/source-census.json"]
    if (
        acquisition.get("source_census_sha256") != census_hash
        or qualification.get("source_census_sha256") != census_hash
    ):
        raise ValueError("Nordic publication census identity differs")
    if acquisition.get("source_census_receipt_scope") != qualification.get(
        "original_census_receipt_scope"
    ):
        raise ValueError("Nordic publication original census scope differs")
    policies = acquisition.get("existing_policy_citation_account")
    if not isinstance(policies, dict) or policies != qualification.get(
        "existing_policy_citation_account"
    ):
        raise ValueError("Nordic publication preferred policy citations differ")
    captured_policies = inputs["verification/primary-policy-capture.json"]["records"]
    actual_policy = policies.get("existing_actual_HTTP200_policy_bytes", {})
    for record in captured_policies:
        preserved = actual_policy.get(record["policy_id"], {})
        if (
            preserved.get("sha256") != record["response_sha256"]
            or preserved.get("url") != record["url"]
        ):
            raise ValueError(
                "Nordic publication current public-policy identity differs"
            )
    if policies.get("policy_retrieval_fresh_in_this_job") is not False:
        raise ValueError(
            "Nordic publication reused policy was relabelled as new retrieval"
        )
    if [row.get("citation_key") for row in policies.get("preferred_citations", [])] != [
        "Williams_Grimm_2018",
        "Fyfe_2009",
        "Giesecke_2014",
    ]:
        raise ValueError("Nordic publication preferred citation inventory differs")
    census = inputs["verification/source-census.json"]
    cores = {row["source_core"]["native_dataset_id"]: row for row in census["cores"]}

    def indexed(records, source_key):
        if not isinstance(records, list) or len(records) != 4:
            raise ValueError("Nordic publication dataset population differs")
        indexed_records = {}
        for row in records:
            if not isinstance(row, dict):
                raise ValueError("Nordic publication dataset record differs")
            core = row.get(source_key)
            did = core.get("native_dataset_id") if isinstance(core, dict) else core
            if type(did) is not int or did not in cores or did in indexed_records:
                raise ValueError("Nordic publication native dataset axis differs")
            indexed_records[did] = row
        return indexed_records

    acquired = indexed(acquisition.get("records"), "native_dataset_id")
    qualified = indexed(qualification.get("records"), "source_core")
    results = {}
    for did, source in cores.items():
        request, assessed = acquired[did], qualified[did]
        if (
            assessed.get("source_core") != source["source_core"]
            or assessed.get("source_dataset_metadata")
            != source["raw_source_metadata"]["dataset"]
            or assessed.get("selected_named_chronology")
            != source["selected_named_calibrated_chronology"]
            or request.get("native_dataset_metadata")
            != source["raw_source_metadata"]["dataset"]
            or request.get("selected_named_chronology")
            != source["selected_named_calibrated_chronology"]
        ):
            raise ValueError("Nordic publication native core metadata differs")
        body_name = PREFIX + f"dataset-{did}.json"
        expected_hash = CAPTURE_PINS[FAMILY + "/" + body_name]
        if (
            request.get("transport_passed") is not True
            or request.get("actual_HTTP_status") != 200
            or request.get("actual_response_sha256") != expected_hash
            or assessed.get("actual_response_sha256") != expected_hash
            or acquisition_receipt.get("product_files", {})
            .get(f"dataset-{did}-publications.response", {})
            .get("sha256")
            != expected_hash
            or request.get("actual_native_response") != inputs[body_name]
        ):
            raise ValueError("Nordic publication returned-source identity differs")
        derived = assess_publications(
            inputs[body_name], did, source["source_core"]["native_site_id"]
        )
        if any(assessed.get(key) != value for key, value in derived.items()):
            raise ValueError("Nordic publication native relation assessment differs")
        results[did] = assessed
    expected_counts = {
        "native_dataset_count": len(results),
        "native_primary_publication_count": sum(
            len(row["primary"]) for row in results.values()
        ),
        "attribution_complete_dataset_count": sum(
            row["attribution_complete"] for row in results.values()
        ),
        "empty_dataset_count": sum(
            row["empty_publication_response"] for row in results.values()
        ),
        "attribution_complete": all(
            row["attribution_complete"] for row in results.values()
        ),
    }
    if any(qualification.get(key) != value for key, value in expected_counts.items()):
        raise ValueError("Nordic publication native summary population differs")
    return results
