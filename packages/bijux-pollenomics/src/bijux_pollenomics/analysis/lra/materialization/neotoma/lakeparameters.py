"""Hash-bound source lake parameters for review, without basin admission."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, cast

from ..models import canonical_bytes
from ..reading import checked_directory, json_object
from .site_evidence import NeotomaSiteEvidence


@dataclass(frozen=True)
class NeotomaLakeparameterReview:
    """A source-observation projection, not accepted historical basin geometry."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent report copy."""
        return json_object(self.canonical_json)


def _page(root: Path, record: dict[str, Any], name: str) -> list[dict[str, Any]]:
    if record.get("path") != name or (root / name).is_symlink():
        raise ValueError("Lakeparameter capture page path is unsafe")
    content = (root / name).read_bytes()
    if (
        len(content) > 1_000_000
        or record.get("bytes") != len(content)
        or record.get("sha256") != hashlib.sha256(content).hexdigest()
    ):
        raise ValueError("Lakeparameter capture page bytes differ from manifest")
    document = json_object(content)
    rows = document.get("data")
    if (
        document.get("status") != "success"
        or not isinstance(rows, list)
        or record.get("rows") != len(rows)
        or any(not isinstance(row, dict) for row in rows)
    ):
        raise ValueError("Lakeparameter source response is malformed")
    return rows


def assess_neotoma_lakeparameters(
    site_evidence: NeotomaSiteEvidence,
    capture_root: Path,
    expected_capture_sha256: str,
) -> NeotomaLakeparameterReview:
    """Reconcile locally captured live source pages to refused candidate sites."""
    if (
        hashlib.sha256(site_evidence.canonical_json).hexdigest()
        != site_evidence.result_digest
    ):
        raise ValueError("Candidate site evidence digest differs")
    sites = site_evidence.as_dict()
    site_rows = sites.get("site_rows")
    if (
        sites.get("schema_version") != "neotoma-candidate-site-evidence.v1"
        or sites.get("lra_admission_status") != "refused"
        or sites.get("denominators", {}).get("lra_accepted_samples") != 0
        or not isinstance(site_rows, list)
    ):
        raise ValueError("Candidate site evidence is not a refused source review")
    by_site = {
        int(row["site_id"].removeprefix("neotoma:site:")): row for row in site_rows
    }
    if (
        len(by_site) != len(site_rows)
        or len(by_site) != sites["denominators"]["candidate_source_sites"]
    ):
        raise ValueError("Candidate source site IDs do not reconcile")

    root = checked_directory(capture_root)
    if (root / "capture.json").is_symlink():
        raise ValueError("Lakeparameter capture manifest is a symlink")
    page_root = checked_directory(root / "capture-pages")
    capture_bytes = (root / "capture.json").read_bytes()
    capture_sha = hashlib.sha256(capture_bytes).hexdigest()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected_capture_sha256)
        or capture_sha != expected_capture_sha256
    ):
        raise ValueError("Lakeparameter capture digest differs from pinned input")
    capture = json_object(capture_bytes)
    records = capture.get("pages")
    if (
        capture.get("schema_version") != "neotoma-live-lakeparameter-custody.v1"
        or capture.get("source_consistency")
        != "live_paginated_not_transactional_snapshot"
        or capture.get("basin_admission_status") != "not_evaluated"
        or not isinstance(records, list)
        or not 2 <= len(records) <= 31
    ):
        raise ValueError("Lakeparameter capture is not bound to candidate site review")
    capture_site_digest = capture.get("candidate_site_report_sha256")
    capture_sites = by_site
    if capture_site_digest != site_evidence.result_digest:
        original_path = root / "site-evidence.json"
        if original_path.is_symlink() or not original_path.is_file():
            raise ValueError("Original capture site review is unavailable")
        original_bytes = original_path.read_bytes()
        if hashlib.sha256(original_bytes).hexdigest() != capture_site_digest:
            raise ValueError("Original capture site review digest differs")
        original = json_object(original_bytes)
        original_rows = original.get("site_rows")
        if (
            original.get("schema_version") != "neotoma-candidate-site-evidence.v1"
            or original.get("lra_admission_status") != "refused"
            or original.get("denominators", {}).get("lra_accepted_samples") != 0
            or original.get("source_snapshot_id") != sites.get("source_snapshot_id")
            or original.get("raw_manifest_sha256") != sites.get("raw_manifest_sha256")
            or not isinstance(original_rows, list)
        ):
            raise ValueError(
                "Original capture site review has different source authority"
            )
        capture_sites = {
            int(row["site_id"].removeprefix("neotoma:site:")): row
            for row in original_rows
        }
        if (
            not capture_sites
            or len(capture_sites) != len(original_rows)
            or len(capture_sites) != original["denominators"]["candidate_source_sites"]
            or not capture_sites.keys() <= by_site.keys()
            or any(
                capture_sites[key]["country_code"] != by_site[key]["country_code"]
                or capture_sites[key]["source_site_name"]
                != by_site[key]["source_site_name"]
                for key in capture_sites
            )
        ):
            raise ValueError("Original capture sites do not match current source sites")

    source_rows: list[tuple[dict[str, Any], dict[str, Any], int]] = []
    keys: set[tuple[int, int]] = set()
    for index, record in enumerate(records[:-1]):
        if not isinstance(record, dict):
            raise ValueError("Lakeparameter page manifest is malformed")
        offset = index * 1000
        if (
            record.get("offset") != offset
            or record.get("url")
            != f"https://api.neotomadb.org/v2.0/data/dbtables/lakeparameters?limit=1000&offset={offset}"
        ):
            raise ValueError("Lakeparameter page sequence or URL differs")
        rows = _page(page_root, record, f"lakeparameters-{index:03d}.json")
        if (index < len(records) - 2 and len(rows) != 1000) or (
            index == len(records) - 2 and not 0 < len(rows) < 1000
        ):
            raise ValueError("Lakeparameter pagination is incomplete")
        for row_index, row in enumerate(rows):
            key = (row.get("siteid"), row.get("lakeparameterid"))
            if (
                type(key[0]) is not int
                or type(key[1]) is not int
                or type(row.get("value")) not in (int, float)
                or key in keys
            ):
                raise ValueError("Lakeparameter source row key or value is invalid")
            keys.add(cast(tuple[int, int], key))
            source_rows.append((row, record, row_index))

    types_record = records[-1]
    if (
        not isinstance(types_record, dict)
        or types_record.get("offset") != 0
        or types_record.get("url")
        != "https://api.neotomadb.org/v2.0/data/dbtables/lakeparametertypes?limit=100&offset=0"
    ):
        raise ValueError("Lakeparameter type page differs")
    types = _page(page_root, types_record, "lakeparametertypes.json")
    by_type = {row.get("lakeparameterid"): row for row in types}
    if (
        not 0 < len(types) < 100
        or len(by_type) != len(types)
        or any(type(key) is not int for key in by_type)
        or any(key[1] not in by_type for key in keys)
    ):
        raise ValueError("Lakeparameter source type IDs do not reconcile")
    matched_capture = [
        (row, record, index)
        for row, record, index in source_rows
        if row["siteid"] in capture_sites
    ]
    matched = [
        (row, record, index)
        for row, record, index in source_rows
        if row["siteid"] in by_site
    ]
    if (
        capture.get("table_rows") != len(source_rows)
        or capture.get("type_rows") != len(types)
        or capture.get("candidate_site_ids") != len(capture_sites)
        or capture.get("candidate_site_ids_with_parameter_rows")
        != len({row["siteid"] for row, _, _ in matched_capture})
        or capture.get("candidate_parameter_rows") != len(matched_capture)
        or capture.get("candidate_rows") != [row for row, _, _ in matched_capture]
        or capture.get("parameter_types") != types
    ):
        raise ValueError("Lakeparameter capture summary differs from raw pages")
    rows = [
        {
            "site_id": by_site[row["siteid"]]["site_id"],
            "country_code": by_site[row["siteid"]]["country_code"],
            "source_site_name": by_site[row["siteid"]]["source_site_name"],
            "source_parameter_id": row["lakeparameterid"],
            "source_parameter_code": by_type[row["lakeparameterid"]].get(
                "lakeparametercode"
            ),
            "source_parameter_label": by_type[row["lakeparameterid"]].get(
                "lakeparameter"
            ),
            "source_value": row["value"],
            "source_row_locator": {
                "page": record["path"],
                "page_sha256": record["sha256"],
                "row_index": index,
            },
            "basin_admission_status": "not_reviewed",
        }
        for row, record, index in matched
    ]
    rows.sort(key=lambda row: (row["site_id"], row["source_parameter_id"]))
    counts = Counter(row["country_code"] for row in rows)
    payload = {
        "schema_version": "neotoma-lakeparameter-source-review.v1",
        "site_evidence_sha256": site_evidence.result_digest,
        "capture_site_evidence_sha256": capture_site_digest,
        "capture_sha256": capture_sha,
        "source_consistency": "live_paginated_not_transactional_snapshot",
        "source_table_rows": len(source_rows),
        "source_type_rows": len(types),
        "candidate_source_sites": len(by_site),
        "candidate_sites_with_observed_parameter_rows": len(
            {row["site_id"] for row in rows}
        ),
        "candidate_sites_without_observed_parameter_rows": len(by_site)
        - len({row["site_id"] for row in rows}),
        "absence_interpretation": "not_certified_by_live_offset_pagination",
        "country_observed_parameter_rows": {
            country: counts[country] for country in sites["country_denominators"]
        },
        "source_rows": rows,
        "basin_admission_status": "not_reviewed",
        "lra_admitted_samples": 0,
    }
    content = canonical_bytes(payload)
    return NeotomaLakeparameterReview(content, hashlib.sha256(content).hexdigest())
