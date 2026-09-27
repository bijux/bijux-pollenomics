"""Reconcile governed SEAD joins and source UUIDs through the Nordic map input."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    validate_governed_sead_admission,
)
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)

RAW_BASE = Path("data/sead/raw/acquisitions") / SEAD_GOVERNED_EVIDENCE_RUN_ID
PUBLIC_PATH = Path("data/sead/normalized/nordic_environmental_sites.geojson")
TRACE_PATH = Path("docs/report/regions/nordic/nordic_point_traceability.json")
COUNTRIES = {"Sweden": "SE", "Denmark": "DK", "Norway": "NO", "Finland": "FI"}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _indexed(
    rows: list[dict[str, Any]], key: str, label: str
) -> dict[str, dict[str, Any]]:
    result = {str(row[key]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate {label} identities")
    return result


def reconcile(
    raw_sites: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    joins: list[dict[str, Any]],
    features: list[dict[str, Any]],
    trace_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Require lossless assigned-site identity and explicit excluded decisions."""
    if len(joins) != 86 or len({edge["edge"] for edge in joins}) != len(joins):
        raise ValueError("Complete 86-edge relation inventory required")
    for edge in joins:
        if (
            edge["status"] != "complete"
            or edge["orphan_child_ids"]
            or edge["duplicate_child_ids"]
            or edge["duplicate_parent_ids"]
            or edge["unexplained_loss_count"] != 0
        ):
            raise ValueError(f"Unreconciled source relation: {edge['edge']}")
    raw = _indexed(raw_sites, "site_id", "raw site")
    if len({row["site_uuid"] for row in raw_sites}) != len(raw_sites):
        raise ValueError("Raw site UUIDs are not unique")
    assigned = _indexed(
        [row for row in decisions if row["decision"]["decision_status"] == "assigned"],
        "site_id",
        "assigned country decision",
    )
    excluded = _indexed(
        [row for row in decisions if row["decision"]["decision_status"] != "assigned"],
        "site_id",
        "excluded country decision",
    )
    if set(raw) != set(assigned) or set(raw) & set(excluded):
        raise ValueError("Raw sites and assigned country decisions diverge")
    public = _indexed(
        [feature["properties"] for feature in features], "record_id", "public site"
    )
    trace = _indexed(trace_records, "record_id", "map traceability site")
    if set(public) != set(raw) or set(trace) != set(raw):
        raise ValueError("Source, public and map-traceability site sets diverge")
    geometry_by_id = {
        str(feature["properties"]["record_id"]): feature["geometry"]
        for feature in features
    }
    countries: Counter[str] = Counter()
    bindings: list[tuple[str, str, str]] = []
    for site_id in sorted(raw, key=int):
        source, decision, published, map_row = (
            raw[site_id],
            assigned[site_id],
            public[site_id],
            trace[site_id],
        )
        uuid_rows = [
            row["value"]
            for row in published["popup_rows"]
            if row["label"] == "Site UUID"
        ]
        site_id_rows = [
            row["value"] for row in published["popup_rows"] if row["label"] == "Site ID"
        ]
        country = decision["decision"]["derived_country"]
        if (
            uuid_rows != [source["site_uuid"]]
            or decision["site_uuid"] != source["site_uuid"]
            or site_id_rows != [site_id]
            or published["country"] != country
            or map_row["country"] != country
            or published["name"] != map_row["title"]
            or published["source_url"] != f"https://browser.sead.se/site/{site_id}"
            or geometry_by_id[site_id]["type"] != "Point"
            or geometry_by_id[site_id]["coordinates"]
            != [source["longitude_dd"], source["latitude_dd"]]
        ):
            raise ValueError(f"Source-to-public SEAD site binding diverges: {site_id}")
        if (
            country not in COUNTRIES
            or decision["governed_country_code"] != COUNTRIES[country]
        ):
            raise ValueError(f"Unexpected governed SEAD country: {site_id}")
        countries[country] += 1
        bindings.append((site_id, source["site_uuid"], country))
    if (
        len(raw) != 2069
        or len(excluded) != 126
        or dict(countries)
        != {"Sweden": 1925, "Denmark": 59, "Norway": 45, "Finland": 40}
    ):
        raise ValueError("Current governed SEAD population changed")
    excluded_statuses = Counter(
        row["decision"]["decision_status"] for row in excluded.values()
    )
    if dict(excluded_statuses) != {"review": 103, "unassigned": 23}:
        raise ValueError("Excluded SEAD decision population changed")
    edges = [
        {
            "edge": edge["edge"],
            "child_row_count": edge["child_row_count"],
            "referenced_child_row_count": edge["referenced_child_row_count"],
            "matched_child_count": edge["matched_child_count"],
            "null_reference_child_count": edge["null_reference_child_count"],
            "orphan_child_count": len(edge["orphan_child_ids"]),
            "unexplained_loss_count": edge["unexplained_loss_count"],
        }
        for edge in sorted(joins, key=lambda row: row["edge"])
    ]
    return {
        "schema_version": "sead-public-source-custody.v1",
        "posture": "source-to-Nordic-map identity and relation replay; no scientific admission",
        "raw_and_public_site_count": len(raw),
        "country_counts": dict(sorted(countries.items())),
        "excluded_decision_count": len(excluded),
        "excluded_status_counts": dict(sorted(excluded_statuses.items())),
        "site_uuid_country_bindings_sha256": _sha(
            json.dumps(bindings, separators=(",", ":"), ensure_ascii=False).encode()
        ),
        "join_edge_count": len(edges),
        "join_null_reference_count": sum(
            edge["null_reference_child_count"] for edge in edges
        ),
        "join_edges": edges,
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    data_root = repository / "data"
    raw_root = repository / RAW_BASE
    snapshot = validate_governed_sead_admission(raw_root, data_root=data_root)
    selected = {
        (RAW_BASE / path).as_posix(): snapshot.copied_files[path]
        for path in (
            "manifest.json",
            "payloads/tbl_sites.json",
            "country-decisions.json",
            "reconciliation/joins.json",
        )
    }
    selected[(RAW_BASE / "admission.json").as_posix()] = (
        raw_root / "admission.json"
    ).read_bytes()
    if (
        _sha(selected[(RAW_BASE / "admission.json").as_posix()])
        != SEAD_GOVERNED_ADMISSION_SHA256
    ):
        raise ValueError("Governed SEAD admission changed after validation")
    for path in (PUBLIC_PATH, TRACE_PATH):
        selected[path.as_posix()] = (repository / path).read_bytes()
    raw_sites = json.loads(selected[(RAW_BASE / "payloads/tbl_sites.json").as_posix()])[
        "rows"
    ]
    decisions = json.loads(selected[(RAW_BASE / "country-decisions.json").as_posix()])[
        "decisions"
    ]
    joins = json.loads(selected[(RAW_BASE / "reconciliation/joins.json").as_posix()])[
        "edges"
    ]
    features = json.loads(selected[PUBLIC_PATH.as_posix()])["features"]
    trace_document = json.loads(selected[TRACE_PATH.as_posix()])
    trace_layers = [
        layer
        for layer in trace_document["layers"]
        if layer["layer_key"] == "sead-sites"
    ]
    if len(trace_layers) != 1 or trace_layers[0]["source_artifact"] != PUBLIC_PATH.name:
        raise ValueError("Map traceability SEAD source artifact changed")
    result = reconcile(
        raw_sites, decisions, joins, features, trace_layers[0]["records"]
    )
    if trace_layers[0]["row_count"] != result["raw_and_public_site_count"]:
        raise ValueError("Map traceability count changed")
    result["source_run_id"] = snapshot.admission["run_id"]
    result["acquisition_bundle_sha256"] = snapshot.admission[
        "acquisition_bundle_sha256"
    ]
    result["inputs_sha256"] = {
        path: _sha(payload) for path, payload in sorted(selected.items())
    }
    for path in (PUBLIC_PATH, TRACE_PATH):
        if (
            _sha((repository / path).read_bytes())
            != result["inputs_sha256"][path.as_posix()]
        ):
            raise ValueError(f"Public SEAD input changed during replay: {path}")
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
