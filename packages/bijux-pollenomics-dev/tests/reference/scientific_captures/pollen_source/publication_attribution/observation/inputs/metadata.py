"""Independently project raw provider and DataCite fields without calling maintained builders."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any
from urllib.parse import quote, urlsplit


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def native_progress(
    actual: list[dict[str, Any]], expected: list[dict[str, Any]]
) -> None:
    require(len(actual) == len(expected) == 2, "Exactly two maintained stages required")
    for left, right in zip(actual, expected, strict=True):
        require(
            left["id"] == right["id"]
            and exact(left["argv"], right["argv"])
            and type(left["actual_exit"]) is int
            and left["actual_exit"] == 0
            and left["timed_out"] is False,
            "Maintained native stage identity/argv/exit differs",
        )


def object_bytes(raw: bytes) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(rows) == len({key for key, _ in rows}), "Duplicate JSON key")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(isinstance(result, dict), "Raw JSON must be an object")
    assert isinstance(result, dict)
    return result


def provider_links(identity: int, raw: bytes) -> list[dict[str, Any]]:
    require(
        type(identity) is int and identity > 0,
        "Provider dataset identity is not a positive integer",
    )
    source = object_bytes(raw)
    require(
        source.get("status") == "success" and isinstance(source.get("data"), list),
        "Provider response is not a successful list",
    )
    result = {}
    for item in source["data"]:
        require(
            isinstance(item, dict) and isinstance(item.get("publication"), dict),
            "Malformed provider publication row",
        )
        value = item["publication"]
        token = value.get("publicationid")
        require(
            type(token) is int and token > 0 and token not in result,
            "Duplicate/invalid native publication ID",
        )
        relations = value.get("datasets")
        require(isinstance(relations, list), "Provider dataset relations absent")
        matches = [
            row
            for row in relations
            if isinstance(row, dict)
            and type(row.get("datasetid")) is int
            and row["datasetid"] == identity
        ]
        require(
            len(matches) == 1,
            "Provider publication does not uniquely join the native dataset",
        )
        primary = matches[0].get("primary")
        require(
            primary is None or type(primary) is bool,
            "Provider primary flag lost native type",
        )
        canonical = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        result[token] = {
            "publication_id": token,
            "source_primary_flag": primary,
            "source_citation": value.get("citation"),
            "source_doi": value.get("doi"),
            "source_year": value.get("year"),
            "source_publication_type": value.get("pubtype"),
            "source_authors": value.get("author"),
            "source_payload_sha256": digest(canonical),
        }
    return [result[key] for key in sorted(result)]


def publication_status(links: list[dict[str, Any]]) -> str:
    primary = sum(row["source_primary_flag"] is True for row in links)
    if not links:
        return "no_publication_link"
    if primary == 1:
        return "one_source_primary_publication"
    if primary > 1:
        return "multiple_source_primary_publications"
    return "no_source_primary_flag"


def expected_publication(
    entity_raw: bytes,
    dataset_raw: bytes,
    policy_raw: bytes,
    manifest_raw: bytes,
    responses: dict[int, bytes],
) -> dict[str, Any]:
    entity = object_bytes(entity_raw)
    dataset = object_bytes(dataset_raw)
    manifest = object_bytes(manifest_raw)
    require(
        entity.get("schema_version") == "neotoma-nordic-entity-decisions.v1"
        and type(entity.get("direct_pollen_included_datasets")) is int
        and entity["direct_pollen_included_datasets"] == 85,
        "Native entity denominator differs",
    )
    require(
        entity["inputs"]["data/neotoma/relational/surfaces/datasets/part-00001.json"]
        == digest(dataset_raw),
        "Entity dataset part linkage differs",
    )
    sources = {row["dataset_id"]: row for row in dataset["rows"]}
    require(
        len(sources) == len(dataset["rows"]) == 209, "Full209dataset identities differ"
    )
    used = [
        row
        for row in entity["decisions"]
        if row["direct_pollen_study_disposition"] == "included"
    ]
    require(
        len(used) == len({row["dataset_id"] for row in used}) == 85,
        "Used85dataset identities differ",
    )
    require(
        manifest.get("schema_version") == "neotoma-candidate-publication-capture.v1"
        and type(manifest.get("response_count")) is int
        and manifest["response_count"] == len(manifest["responses"]) == 169,
        "Current169provider manifest differs",
    )
    captured = {row["dataset_id"]: row for row in manifest["responses"]}
    require(
        len(captured) == 169 and all(type(k) is int and k > 0 for k in captured),
        "Provider native IDs differ",
    )
    require(
        set(responses) == set(captured), "Complete169provider response closure differs"
    )
    for token, raw in responses.items():
        row = captured[token]
        require(
            row["path"] == f"responses/dataset-{token}-publications.json"
            and type(row["http_status"]) is int
            and row["http_status"] == 200
            and row["sha256"] == digest(raw)
            and type(row["bytes"]) is int
            and row["bytes"] == len(raw),
            "Provider raw manifest byte/status linkage differs",
        )
    decisions = []
    for selected in sorted(used, key=lambda row: row["dataset_id"]):
        source = sources[selected["dataset_id"]]
        require(
            digest(json.dumps(source, sort_keys=True, separators=(",", ":")).encode())
            == selected["source_dataset_row_sha256"],
            "Native source dataset row identity differs",
        )
        native = source["source_dataset_id"]
        require(type(native) is int and native > 0, "Source dataset ID is not typed")
        raw = responses[native]
        links = provider_links(native, raw)
        status = publication_status(links)
        payload = source["source_payload"]
        dois = payload["doi"]
        investigators = [item["contactname"] for item in payload["datasetpi"]]
        require(
            payload["database"] == "European Pollen Database"
            and isinstance(dois, list)
            and dois
            and all(isinstance(v, str) and v and v.isascii() for v in dois)
            and investigators
            and all(isinstance(v, str) and v for v in investigators),
            "Source attribution field posture differs",
        )
        doi_status = (
            "one_source_doi"
            if len(dois) == 1
            else "ascii_case_equivalent_source_dois"
            if len({v.lower() for v in dois}) == 1
            else "distinct_source_dois"
        )
        if status == "one_source_primary_publication":
            primary = next(row for row in links if row["source_primary_flag"] is True)
            require(
                all(
                    primary.get(key)
                    for key in ("source_citation", "source_year", "source_authors")
                ),
                "Provider primary citation is incomplete",
            )
        decisions.append(
            {
                "dataset_id": selected["dataset_id"],
                "site_id": selected["site_id"],
                "country_code": selected["country_code"],
                "dataset_dois": dois,
                "dataset_doi_status": doi_status,
                "dataset_investigators": investigators,
                "constituent_database": payload["database"],
                "source_dataset_notes": payload["datasetnotes"],
                "provider_publication_status": status,
                "provider_publications": links,
                "provider_response_sha256": digest(raw),
                "direct_pollen_role": "used_in_selected_study",
                "lra_admission": "unresolved_source_requirements",
            }
        )
    country = {}
    for code in ("SE", "DK", "NO", "FI"):
        selected = [row for row in decisions if row["country_code"] == code]
        country[code] = {
            "used_datasets": len(selected),
            "one_source_primary_publication": sum(
                row["provider_publication_status"] == "one_source_primary_publication"
                for row in selected
            ),
            "primary_link_review_required": sum(
                row["provider_publication_status"] != "one_source_primary_publication"
                for row in selected
            ),
            "distinct_source_dois": sum(
                row["dataset_doi_status"] == "distinct_source_dois" for row in selected
            ),
            "either_citation_review": sum(
                row["provider_publication_status"] != "one_source_primary_publication"
                or row["dataset_doi_status"] == "distinct_source_dois"
                for row in selected
            ),
        }
    require(
        {key: value["used_datasets"] for key, value in country.items()}
        == {"SE": 3, "DK": 2, "NO": 52, "FI": 28},
        "Selected country denominator differs",
    )
    policy_sha = "ba75c8f22491f5b5e83a835f964aedea53b62e526cf6ea36bb10b376e774b3a4"
    require(policy_sha.encode() in policy_raw, "Declared governed policy marker absent")
    return {
        "schema_version": "nordic-neotoma-publication-readiness.v1",
        "entity_ledger_sha256": digest(entity_raw),
        "dataset_part_sha256": digest(dataset_raw),
        "provider_capture_manifest_sha256": digest(manifest_raw),
        "provider_policy": {
            "url": "https://www.neotomadb.org/data/data-use-and-embargo-policy",
            "captured_policy_sha256": policy_sha,
            "governed_review_sha256": digest(policy_raw),
            "version": "2025",
            "posture": "CC BY 4.0 with three-level attribution; source-specific review remains separate",
        },
        "used_dataset_count": len(decisions),
        "provider_publication_status_counts": dict(
            sorted(
                Counter(row["provider_publication_status"] for row in decisions).items()
            )
        ),
        "dataset_doi_status_counts": dict(
            sorted(Counter(row["dataset_doi_status"] for row in decisions).items())
        ),
        "doi_equivalence_rule": {
            "url": "https://www.doi.org/doi-handbook/html/",
            "section": "3.3.4 Case Insensitivity of the DOI Name",
            "application": "ASCII case equivalence only; preserve source DOI strings",
        },
        "country_denominators": country,
        "provider_primary_gap_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["provider_publication_status"] != "one_source_primary_publication"
        ],
        "distinct_doi_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["dataset_doi_status"] == "distinct_source_dois"
        ],
        "citation_review_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["provider_publication_status"] != "one_source_primary_publication"
            or row["dataset_doi_status"] == "distinct_source_dois"
        ],
        "decisions": decisions,
        "publication_ready": False,
        "lra_accepted_samples": 0,
    }


def landing_dataset(url: str) -> int | None:
    require(isinstance(url, str), "Registry landing URL is not literal text")
    parsed = urlsplit(url)
    token = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    return (
        int(token)
        if parsed.hostname == "data.neotomadb.org"
        and token.isascii()
        and token.isdecimal()
        else None
    )


def registry_record(doi: str, raw: bytes) -> dict[str, Any]:
    require(
        isinstance(doi, str) and bool(doi) and doi.isascii(),
        "Source DOI is not literal ASCII",
    )
    value = object_bytes(raw)
    data = value["data"]
    attrs = data["attributes"]
    require(
        data["type"] == "dois"
        and isinstance(attrs["doi"], str)
        and attrs["doi"].isascii()
        and attrs["doi"].lower() == doi.lower(),
        "Registry native DOI identity differs",
    )
    require(
        isinstance(attrs["titles"], list), "Registry titles are not an ordered list"
    )
    return {
        "source_doi": doi,
        "registry_doi": attrs["doi"],
        "registry_created": attrs["created"],
        "publication_year": attrs["publicationYear"],
        "titles": attrs["titles"],
        "landing_url": attrs["url"],
        "landing_dataset_id": landing_dataset(attrs["url"]),
        "version": attrs.get("version"),
        "related_identifiers": attrs.get("relatedIdentifiers", []),
        "response_sha256": digest(raw),
    }


def pair_status(
    dataset_id: int, records: list[dict[str, Any]]
) -> tuple[list[str], bool, str]:
    require(
        type(dataset_id) is int and dataset_id > 0 and len(records) == 2,
        "Registry pair identity differs",
    )
    first, second = records
    declared = []
    for record, other in ((first, second), (second, first)):
        for relation in record["related_identifiers"]:
            if (
                relation.get("relationType") == "IsIdenticalTo"
                and relation.get("relatedIdentifierType") == "DOI"
                and isinstance(relation.get("relatedIdentifier"), str)
                and relation["relatedIdentifier"].isascii()
                and relation["relatedIdentifier"].lower() == other["source_doi"].lower()
            ):
                declared.append(record["source_doi"])
                break
    same = all(
        type(row["landing_dataset_id"]) is int
        and row["landing_dataset_id"] == dataset_id
        for row in records
    )
    return (
        declared,
        same,
        "registry_declared_identical"
        if declared
        else "same_dataset_target_without_declared_equivalence"
        if same
        else "registry_target_mismatch",
    )


def expected_doi(
    attribution: dict[str, Any],
    attribution_raw: bytes,
    manifest_raw: bytes,
    responses: dict[str, bytes],
) -> dict[str, Any]:
    selected = [
        row
        for row in attribution["decisions"]
        if row["dataset_doi_status"] == "distinct_source_dois"
    ]
    require(
        len(selected) == 13 and all(len(row["dataset_dois"]) == 2 for row in selected),
        "Exact13native DOI pairs required",
    )
    manifest = object_bytes(manifest_raw)
    require(
        manifest.get("schema_version") == "neotoma-nordic-distinct-doi-capture.v1"
        and type(manifest.get("response_count")) is int
        and manifest["response_count"] == len(manifest["responses"]) == 26,
        "Exact26DataCite manifest rows required",
    )
    indexed = {
        (row["dataset_id"], row["source_doi"].lower()): row
        for row in manifest["responses"]
    }
    require(len(indexed) == 26, "DuplicateDataCite native identity")
    require(
        set(responses) == {row["path"] for row in manifest["responses"]},
        "Complete26DataCite response closure differs",
    )
    decisions = []
    for selected_row in sorted(selected, key=lambda row: row["dataset_id"]):
        token = int(selected_row["dataset_id"].rsplit(":", 1)[-1])
        records = []
        for position, doi in enumerate(selected_row["dataset_dois"], 1):
            row = indexed[(token, doi.lower())]
            path = f"responses/dataset-{token}-doi-{position}.json"
            raw = responses[path]
            require(
                row["path"] == path
                and row["url"] == "https://api.datacite.org/dois/" + quote(doi, safe="")
                and type(row["http_status"]) is int
                and row["http_status"] == 200
                and row["sha256"] == digest(raw)
                and type(row["bytes"]) is int
                and row["bytes"] == len(raw),
                "DataCite exactURL/status/rawbyte join differs",
            )
            records.append(registry_record(doi, raw))
        declared, same, status = pair_status(token, records)
        decisions.append(
            {
                "dataset_id": selected_row["dataset_id"],
                "site_id": selected_row["site_id"],
                "country_code": selected_row["country_code"],
                "source_doi_names": selected_row["dataset_dois"],
                "registry_records": records,
                "same_neotoma_dataset_target": same,
                "identity_relation_declared_by": declared,
                "doi_pair_status": status,
                "citation_selection": "source_owner_review_required"
                if status != "registry_declared_identical"
                else "equivalence_supported_citation_format_pending",
            }
        )
    return {
        "schema_version": "nordic-neotoma-distinct-doi-review.v1",
        "attribution_ledger_sha256": digest(attribution_raw),
        "registry_capture_manifest_sha256": digest(manifest_raw),
        "registry_relation_guidance": "https://support.datacite.org/docs/when-should-i-use-isidenticalto",
        "reviewed_dataset_count": len(decisions),
        "reviewed_doi_count": sum(len(row["source_doi_names"]) for row in decisions),
        "doi_pair_status_counts": dict(
            sorted(Counter(row["doi_pair_status"] for row in decisions).items())
        ),
        "decisions": decisions,
        "lra_accepted_samples": 0,
    }
