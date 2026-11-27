"""Compare candidate identities with independently selected source declarations."""

from datetime import datetime
import re
from typing import Any


def _table(table: Any) -> list[dict[str, Any]]:
    if not isinstance(table, dict):
        raise ValueError("Candidate table is unavailable")
    fields, records = table.get("fields"), table.get("records")
    if (
        not isinstance(fields, list)
        or not all(type(x) is str for x in fields)
        or len(set(fields)) != len(fields)
        or not isinstance(records, list)
        or type(table.get("record_count")) is not int
        or table["record_count"] != len(records)
    ):
        raise ValueError("Candidate table structure differs")
    if any(not isinstance(row, list) or len(row) != len(fields) for row in records):
        raise ValueError("Candidate row width differs")
    return [dict(zip(fields, row, strict=True)) for row in records]


def reconcile(
    records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    declarations: list[dict[str, Any]],
    *,
    expected_sites: int,
    expected_datasets: int,
    expected_selected: int,
) -> list[dict[str, Any]]:
    """Require each selected identity to match actual candidate and source evidence.

    Input source declarations are locally receipt-bound, not execution attestation.
    The returned private rows contain no native body, citation, publication flag or
    count. An empty body does not prove a publication-site relation.
    """
    if (
        any(
            type(n) is not int or not 0 < n <= 20000
            for n in (expected_sites, expected_datasets, expected_selected)
        )
        or len(records) != expected_sites
        or len(selected) != expected_selected
        or len(declarations) != expected_selected
    ):
        raise ValueError("Candidate or selection population differs")
    sites: set[int] = set()
    datasets: dict[int, int] = {}
    statuses: dict[int, dict[str, Any]] = {}
    for record in records:
        rid = record.get("record_id")
        if (
            not isinstance(rid, str)
            or not rid.startswith("neotoma:site:")
            or not rid[13:].isascii()
            or not rid[13:].isdigit()
        ):
            raise ValueError("Candidate site identity differs")
        site = int(rid[13:])
        if site <= 0 or rid != f"neotoma:site:{site}" or site in sites:
            raise ValueError("Candidate site identity repeats")
        sites.add(site)
        tabs = record["tabs"]
        rows = _table(tabs["samples"]["datasets"])
        capture = tabs["provenance"]["publication_capture"]
        if (
            not isinstance(capture, dict)
            or capture.get("source_id") != "neotoma/publication-links/2026-09-29"
            or capture.get("manifest_sha256")
            != "d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da"
            or capture.get("epoch_posture")
            != "separate_provider_capture_not_original_pollen_snapshot"
        ):
            raise ValueError("Candidate historical capture identity differs")
        captures = _table(capture["datasets"])
        local: set[int] = set()
        for row in rows:
            dataset = row.get("source_dataset_id")
            payload = row.get("source_payload")
            if (
                type(dataset) is not int
                or dataset <= 0
                or row.get("dataset_id") != f"neotoma:dataset:{dataset}"
                or not isinstance(payload, dict)
                or type(payload.get("datasetid")) is not int
                or payload["datasetid"] != dataset
                or dataset in datasets
            ):
                raise ValueError("Candidate native dataset identity differs")
            datasets[dataset] = site
            local.add(dataset)
        for row in captures:
            value = row.get("dataset_id")
            if (
                not isinstance(value, str)
                or not value.startswith("neotoma:dataset:")
                or not value[16:].isascii()
                or not value[16:].isdigit()
            ):
                raise ValueError("Candidate capture identity differs")
            dataset = int(value[16:])
            if (
                value != f"neotoma:dataset:{dataset}"
                or dataset not in local
                or dataset in statuses
                or not isinstance(row.get("status"), str)
            ):
                raise ValueError("Candidate capture identity repeats or differs")
            statuses[dataset] = row
    if len(datasets) != expected_datasets or set(datasets) != set(statuses):
        raise ValueError("Candidate dataset population differs")
    by_dataset: dict[int, dict[str, Any]] = {}
    for row in declarations:
        key = row.get("dataset_id")
        if type(key) is not int or key in by_dataset:
            raise ValueError("Source declaration identity repeats")
        by_dataset[key] = row
    seen: set[int] = set()
    observations: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in selected:
        dataset, selected_site, observation = (
            item.get("dataset_id"),
            item.get("site_id"),
            item.get("observation_id"),
        )
        if (
            type(dataset) is not int
            or type(selected_site) is not int
            or not isinstance(observation, str)
            or any(
                not isinstance(item.get(k), str)
                or re.fullmatch(r"[0-9a-f]{64}", item[k]) is None
                for k in (
                    "capsule_sha256",
                    "capture_sha256",
                    "receipt_sha256",
                    "body_sha256",
                )
            )
            or re.fullmatch(
                re.escape(item["capture_sha256"]) + r":/facets/(0|[1-9][0-9]*)",
                observation,
            )
            is None
            or dataset in seen
            or observation in observations
            or datasets.get(dataset) != selected_site
            or statuses.get(dataset, {}).get("status") != "not_captured"
            or any(
                key not in statuses.get(dataset, {})
                or statuses[dataset][key] is not None
                for key in (
                    "publication_count",
                    "source_primary_count",
                    "request_url",
                    "retrieved_at_utc",
                    "response_sha256",
                    "response_byte_count",
                )
            )
        ):
            raise ValueError("Selected candidate identity or capture status differs")
        seen.add(dataset)
        observations.add(observation)
        declaration = by_dataset.get(dataset)
        if (
            declaration is None
            or type(declaration.get("site_id")) is not int
            or any(
                declaration.get(key) != value
                for key, value in {
                    "site_id": selected_site,
                    "observation_id": observation,
                    "capsule_manifest_sha256": item.get("capsule_sha256"),
                    "capture_manifest_sha256": item.get("capture_sha256"),
                    "receipt_sha256": item.get("receipt_sha256"),
                    "body_sha256": item.get("body_sha256"),
                }.items()
            )
            or declaration.get("capture_terminal_status")
            != "received_complete_unqualified_facet"
            or declaration.get("derived_source_qualification")
            != "qualified_source_schema"
            or declaration.get("scientific_admission") != "not_asserted"
        ):
            raise ValueError("Selected source declaration differs")
        proof = declaration.get("source_declarations")
        if (
            not isinstance(proof, dict)
            or set(proof)
            != {
                "schema_version",
                "capture_utc_start",
                "capture_utc_end",
                "request_utc_start",
                "request_utc_end",
                "request_url",
                "original_parent_scope",
                "original_scope_role",
                "current_scope_role",
                "scientific_admission",
            }
            or any(type(value) is not str for value in proof.values())
            or proof.get("request_url")
            != f"https://api.neotomadb.org/v2.0/data/datasets/{dataset}/publications"
            or proof.get("schema_version") != "neotoma-scoped-facet-declarations.v1"
            or proof.get("original_parent_scope")
            != "authenticated_original_parent_scope"
            or proof.get("original_scope_role") != "development_resource_discovery"
            or proof.get("current_scope_role") != "development_resource_discovery"
            or proof.get("scientific_admission") != "not_asserted"
        ):
            raise ValueError("Selected source posture differs")
        try:
            capture_start, request_start, request_end, capture_end = (
                datetime.fromisoformat(proof[key])
                for key in (
                    "capture_utc_start",
                    "request_utc_start",
                    "request_utc_end",
                    "capture_utc_end",
                )
            )
            if (
                any(
                    t.utcoffset() is None
                    for t in (capture_start, request_start, request_end, capture_end)
                )
                or not capture_start <= request_start <= request_end <= capture_end
            ):
                raise ValueError("Selected source timing differs")
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Selected source timing differs") from error
        output.append(
            {
                "dataset_id": dataset,
                "site_id": selected_site,
                "observation_id": observation,
                "capsule_sha256": item["capsule_sha256"],
                "capture_sha256": item["capture_sha256"],
                "receipt_sha256": item["receipt_sha256"],
                "body_sha256": item["body_sha256"],
                "source_declarations": dict(proof),
            }
        )
    if seen != set(by_dataset) or seen != {
        dataset
        for dataset, status in statuses.items()
        if status["status"] == "not_captured"
    }:
        raise ValueError("Selected source population differs")
    return output
