"""Independently reconstruct source observations from hash-bound paginated pages."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import hashlib
import json
import math
import re
from typing import Any

COUNTRIES = {"DK", "FI", "NO", "SE", "UNASSIGNED"}


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def decode(raw: bytes) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in rows:
            if key in value:
                raise ValueError("Ambiguous duplicate source JSON key")
            value[key] = item
        return value

    def constant(value: str) -> None:
        raise ValueError("Nonfinite source JSON scalar: " + value)

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(value, dict):
        raise ValueError("Source response must be a JSON object")
    canonical(value)
    return value


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def reconstruct(
    capture_raw: bytes,
    site_raw: bytes,
    read_page: Callable[[str], bytes],
    expected_capture: str,
    expected_site: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    capture_sha = hashlib.sha256(capture_raw).hexdigest()
    site_sha = hashlib.sha256(site_raw).hexdigest()
    require(
        capture_sha == expected_capture and site_sha == expected_site,
        "Exact original capture/site source bytes required",
    )
    capture, sites = decode(capture_raw), decode(site_raw)
    require(
        all(
            type(capture.get(name)) is int
            for name in (
                "table_rows",
                "type_rows",
                "candidate_site_ids",
                "candidate_site_ids_with_parameter_rows",
                "candidate_parameter_rows",
            )
        ),
        "Capture summary counts must be native integers",
    )
    require(
        capture.get("schema_version") == "neotoma-live-lakeparameter-custody.v1"
        and capture.get("candidate_site_report_sha256") == site_sha,
        "Capture and original candidate site report differ",
    )
    require(
        capture.get("source_consistency") == "live_paginated_not_transactional_snapshot"
        and capture.get("basin_admission_status") == "not_evaluated",
        "Capture was relabelled as basin or transactional authority",
    )
    require(
        sites.get("schema_version") == "neotoma-candidate-site-evidence.v1"
        and sites.get("lra_admission_status") == "refused"
        and type(sites["denominators"].get("lra_accepted_samples")) is int
        and sites["denominators"]["lra_accepted_samples"] == 0,
        "Candidate sites must retain source-only refusal",
    )
    by_site: dict[int, dict[str, Any]] = {}
    for row in sites["site_rows"]:
        name = row["site_id"]
        require(
            isinstance(name, str) and re.fullmatch(r"neotoma:site:[0-9]+", name),
            "Native site identity required",
        )
        site_key = int(name.removeprefix("neotoma:site:"))
        require(
            site_key not in by_site
            and row["country_code"] in COUNTRIES
            and isinstance(row["source_site_name"], str),
            "Duplicate site, unknown country or untyped name",
        )
        by_site[site_key] = row
    require(
        type(sites["denominators"].get("candidate_source_sites")) is int
        and len(by_site) == sites["denominators"]["candidate_source_sites"]
        and set(sites["country_denominators"]) == COUNTRIES,
        "Candidate site/country denominators differ",
    )
    records = capture["pages"]
    require(
        isinstance(records, list) and 2 <= len(records) <= 31,
        "Finite complete page declaration required",
    )

    def page(
        record: dict[str, Any], name: str, url: str, offset: int
    ) -> list[dict[str, Any]]:
        require(
            record.get("path") == name
            and record.get("url") == url
            and type(record.get("offset")) is int
            and record["offset"] == offset,
            "Page path, URL or offset changed",
        )
        raw = read_page(name)
        require(
            len(raw) <= 1_000_000
            and type(record.get("bytes")) is int
            and record["bytes"] == len(raw)
            and record["sha256"] == hashlib.sha256(raw).hexdigest(),
            "Source page digest/size differs",
        )
        value = decode(raw)
        rows = value.get("data")
        require(
            value.get("status") == "success"
            and isinstance(rows, list)
            and type(record.get("rows")) is int
            and record["rows"] == len(rows)
            and all(isinstance(row, dict) for row in rows),
            "Source page response shape/count differs",
        )
        assert isinstance(rows, list)
        return rows

    indexed: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for index, record in enumerate(records[:-1]):
        offset = index * 1000
        name = f"lakeparameters-{index:03d}.json"
        rows = page(
            record,
            name,
            f"https://api.neotomadb.org/v2.0/data/dbtables/lakeparameters?limit=1000&offset={offset}",
            offset,
        )
        require(
            len(rows) == 1000 if index < len(records) - 2 else 0 < len(rows) < 1000,
            "Offset pages incomplete; absence remains uncertified",
        )
        for row_index, row in enumerate(rows):
            site, parameter, value = (
                row.get("siteid"),
                row.get("lakeparameterid"),
                row.get("value"),
            )
            require(
                type(site) is int
                and type(parameter) is int
                and type(value) in (int, float),
                "Typed finite source site/type/value required",
            )
            assert isinstance(site, int) and isinstance(parameter, int)
            assert isinstance(value, (int, float))
            require(math.isfinite(value), "Finite source value required")
            native_key = (site, parameter)
            require(
                native_key not in seen, "Duplicate native site/parameter source key"
            )
            seen.add(native_key)
            indexed.append(
                {
                    "native": row,
                    "page": name,
                    "page_sha256": record["sha256"],
                    "row_index": row_index,
                }
            )
    types = page(
        records[-1],
        "lakeparametertypes.json",
        "https://api.neotomadb.org/v2.0/data/dbtables/lakeparametertypes?limit=100&offset=0",
        0,
    )
    by_type: dict[int, dict[str, Any]] = {}
    for row in types:
        type_key = row.get("lakeparameterid")
        require(
            type(type_key) is int and type_key not in by_type,
            "Duplicate/untyped parameter type",
        )
        assert isinstance(type_key, int)
        by_type[type_key] = row
    require(
        0 < len(types) < 100 and all(parameter in by_type for _, parameter in seen),
        "Source parameter type closure differs",
    )
    for row in indexed:
        row["parameter_type"] = by_type[row["native"]["lakeparameterid"]]
    matched = [row for row in indexed if row["native"]["siteid"] in by_site]
    native_matches = [row["native"] for row in matched]
    require(
        capture.get("table_rows") == len(indexed)
        and capture.get("type_rows") == len(types)
        and capture.get("candidate_site_ids") == len(by_site)
        and capture.get("candidate_site_ids_with_parameter_rows")
        == len({row["siteid"] for row in native_matches})
        and capture.get("candidate_parameter_rows") == len(matched)
        and canonical(capture.get("candidate_rows")) == canonical(native_matches)
        and canonical(capture.get("parameter_types")) == canonical(types),
        "Capture summaries differ from complete original source pages",
    )
    rows = []
    for row in matched:
        source = row["native"]
        site = by_site[source["siteid"]]
        kind = by_type[source["lakeparameterid"]]
        rows.append(
            {
                "site_id": site["site_id"],
                "country_code": site["country_code"],
                "source_site_name": site["source_site_name"],
                "source_parameter_id": source["lakeparameterid"],
                "source_parameter_code": kind.get("lakeparametercode"),
                "source_parameter_label": kind.get("lakeparameter"),
                "source_value": source["value"],
                "source_row_locator": {
                    "page": row["page"],
                    "page_sha256": row["page_sha256"],
                    "row_index": row["row_index"],
                },
                "basin_admission_status": "not_reviewed",
            }
        )
    rows.sort(key=lambda row: (row["site_id"], row["source_parameter_id"]))
    counts = Counter(row["country_code"] for row in rows)
    observed = len({row["site_id"] for row in rows})
    report = {
        "schema_version": "neotoma-lakeparameter-source-review.v1",
        "site_evidence_sha256": site_sha,
        "capture_site_evidence_sha256": site_sha,
        "capture_sha256": capture_sha,
        "source_consistency": "live_paginated_not_transactional_snapshot",
        "source_table_rows": len(indexed),
        "source_type_rows": len(types),
        "candidate_source_sites": len(by_site),
        "candidate_sites_with_observed_parameter_rows": observed,
        "candidate_sites_without_observed_parameter_rows": len(by_site) - observed,
        "absence_interpretation": "not_certified_by_live_offset_pagination",
        "country_observed_parameter_rows": {
            country: counts[country] for country in sites["country_denominators"]
        },
        "source_rows": rows,
        "basin_admission_status": "not_reviewed",
        "lra_admitted_samples": 0,
    }
    return report, indexed
