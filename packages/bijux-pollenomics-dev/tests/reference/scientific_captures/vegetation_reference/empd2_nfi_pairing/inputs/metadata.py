"""Independently join metadata-only source fields and preserve every pair refusal."""

from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
import sqlite3
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from contracts import (
    FIELDS,
    GAPS,
    INPUTS,
    LOCATION_FIELDS,
    PUBLIC_FIELDS,
    csv_wire,
    exact,
    finite,
    load,
    pin,
    public_projection,
    require,
)

METADATA_FIELDS = (
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
)
NFI_HEADER = ("Year", "TractID", "PlotID", "Inventory_Date", "Easting", "Northing")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
TABLE_COLUMNS = {
    "metadata": set(METADATA_FIELDS),
    "ageuncertainties": {"ageuncertainty", "age", "description"},
    "metapubli": {"samplename", "publiid"},
    "publications": {"publiid", "doi", "reference"},
}


def authorizer(
    action: int,
    first: str | None,
    second: str | None,
    database: str | None,
    trigger: str | None,
) -> int:
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if (
        action == sqlite3.SQLITE_READ
        and database == "main"
        and (first in TABLE_COLUMNS)
        and (second in TABLE_COLUMNS[first])
        and (trigger is None)
    ):
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def nfi_metadata(
    path: Path,
) -> tuple[list[tuple[str, str, str, str, float, float]], dict[str, object]]:
    rows = []
    keys = set()
    selected_cells = 0
    seen_header = False
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = [
            "".join(t.text or "" for t in node.iter(NS + "t"))
            for node in root.findall(NS + "si")
        ]
        with archive.open("xl/worksheets/sheet2.xml") as stream:
            for _, node in ET.iterparse(stream, events=("end",)):
                if node.tag != NS + "row":
                    continue
                cells = {}
                for cell in node.findall(NS + "c"):
                    column = cell.get("r", "").rstrip("0123456789")
                    if column not in ("A", "B", "C", "D", "E", "F"):
                        continue
                    require(column not in cells, "Repeated selected NFI column")
                    value = cell.find(NS + "v")
                    text = None if value is None else value.text
                    if text is not None and cell.get("t") == "s":
                        text = strings[int(text)]
                    cells[column] = text
                    selected_cells += 1
                values = tuple(cells.get(c) for c in ("A", "B", "C", "D", "E", "F"))
                if node.get("r") == "1":
                    require(
                        not seen_header and values == NFI_HEADER,
                        "NFI six-column header differs",
                    )
                    seen_header = True
                else:
                    require(
                        seen_header
                        and all(isinstance(v, str) and v != "" for v in values),
                        "NFI metadata missing",
                    )
                    year, tract, plot, date, x, y = values
                    assert (
                        isinstance(year, str)
                        and isinstance(tract, str)
                        and isinstance(plot, str)
                        and isinstance(date, str)
                    )
                    a, b = (float(str(x)), float(str(y)))
                    require(
                        math.isfinite(a) and math.isfinite(b),
                        "Nonfinite NFI coordinates",
                    )
                    key = (tract, plot, year)
                    require(key not in keys, "Duplicate native NFI plot-year")
                    keys.add(key)
                    rows.append((year, tract, plot, date, a, b))
                node.clear()
    return (
        rows,
        {
            "selected_columns": list(NFI_HEADER),
            "selected_cells": selected_cells,
            "source_rows": len(rows),
            "outcome_columns_decoded": 0,
            "zip_members_semantically_selected": [
                "xl/sharedStrings.xml",
                "xl/worksheets/sheet2.xml",
            ],
            "physical_XML_and_shared_string_bytes_read": True,
            "raw_outcome_bytes_unread_claimed": False,
        },
    )


def source_metadata(
    path: Path, names: list[str]
) -> tuple[
    dict[str, dict[str, Any]],
    dict[object, dict[str, Any]],
    dict[str, list[dict[str, Any]]],
]:
    require(len(names) == len(set(names)), "Duplicate requested pollen identity")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        columns = {r[1] for r in db.execute("PRAGMA table_info(metadata)")}
        require(
            set(METADATA_FIELDS) <= columns
            and (
                not any(
                    w in c.casefold()
                    for c in columns
                    for w in ("collect", "date", "year")
                )
            ),
            "Metadata schema requires timing review",
        )
        db.set_authorizer(authorizer)
        uncertainty = {
            r["ageuncertainty"]: {
                "source_age_range_label": r["age"],
                "source_description": r["description"],
            }
            for r in db.execute(
                "SELECT ageuncertainty,age,description FROM ageuncertainties"
            )
        }
        records = {}
        citations = {}
        for name in names:
            values = db.execute(
                "SELECT "
                + ",".join(METADATA_FIELDS)
                + " FROM metadata WHERE samplename=?",
                (name,),
            ).fetchall()
            require(len(values) == 1, "Native metadata identity not unique: " + name)
            records[name] = dict(values[0])
            citations[name] = [
                dict(v)
                for v in db.execute(
                    "SELECT mp.publiid,p.doi,p.reference FROM metapubli AS mp LEFT JOIN publications AS p ON p.publiid=mp.publiid WHERE mp.samplename=? ORDER BY mp.publiid",
                    (name,),
                )
            ]
        return (records, uncertainty, citations)
    finally:
        db.close()


def checked_leads(
    dossier: dict[str, Any],
    spatial: dict[str, Any],
    records: dict[str, dict[str, Any]],
    uncertainty: dict[object, dict[str, Any]],
    citations: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    require(
        dossier["schema_version"] == "empd2-nfi-source-dossier.v1"
        and spatial["schema_version"] == "empd2-nfi-spatial-feasibility.v2",
        "Retained source schema differs",
    )
    require(
        dossier["source_sha256"] == INPUTS["sqlite"][1]
        and dossier["spatial_report_sha256"] == INPUTS["spatial"][1],
        "Dossier source bindings differ",
    )
    nearest = spatial["nearest_nfi_row_by_pollen_sample"]
    require(
        len(nearest) == 132 and len({r["pollen_sample"] for r in nearest}) == 132,
        "Retained132-row spatial denominator differs",
    )
    leads = {
        r["pollen_sample"]: r for r in nearest if finite(r["distance_m_wgs84"]) <= 1000
    }
    require(
        len(leads) == len(dossier["rows"]) == dossier["selected_lead_count"] == 16,
        "Complete16 lead set differs",
    )
    require(
        exact(dossier["source_metadata_columns"], list(METADATA_FIELDS))
        and dossier["source_explicit_collection_date_column"] is None,
        "Retained source field declarations differ",
    )
    require(
        dossier["scientific_admission"] == "candidate_only"
        and type(dossier["independent_vegetation_pair_count"]) is int
        and (dossier["independent_vegetation_pair_count"] == 0),
        "Measured pair admission changed",
    )
    seen = set()
    age_codes: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    with_citations = notes = 0
    for item in dossier["rows"]:
        lead = item["spatial_lead"]
        name = lead["pollen_sample"]
        require(name not in seen and name in leads, "Duplicate/missing selected sample")
        seen.add(name)
        require(
            exact(lead, leads[name])
            and exact(item["source_metadata_excluding_vegdescription"], records[name]),
            "Original native metadata/lead join differs",
        )
        raw = records[name]
        require(
            raw["country"] == "Sweden"
            and exact(raw["agebp"], lead["pollen_agebp_source_native"])
            and exact(
                raw["ageuncertainty"], lead["pollen_ageuncertainty_source_native"]
            ),
            "Native raw age/country changed",
        )
        require(
            exact(
                item["source_age_uncertainty_lookup"],
                uncertainty.get(raw["ageuncertainty"]),
            )
            and exact(item["source_publications"], citations[name]),
            "Native age code/citation join differs",
        )
        require(
            type(item["publication_link_count"]) is int
            and item["publication_link_count"] == len(citations[name]),
            "Publication link cardinality differs",
        )
        note = (
            raw["notes"]
            if isinstance(raw["notes"], str) and "collect" in raw["notes"].casefold()
            else None
        )
        status = (
            "source_note_requires_review"
            if note is not None
            else "not_authenticated_from_source_fields"
        )
        require(
            exact(item["collection_time_source_note"], note)
            and item["collection_time_status"] == status
            and (item["independent_vegetation_pair_admission"] is False),
            "Source collection cue was promoted",
        )
        require(
            lead["pair_admission"] == "candidate_only"
            and lead["mechanical_count_candidate"] is True
            and (lead["time_support"] == "unresolved_collection_time"),
            "Spatial lead was promoted",
        )
        age_codes[str(raw["ageuncertainty"])] += 1
        kinds[
            "numeric"
            if isinstance(raw["agebp"], (int, float))
            else "missing_or_source_text"
        ] += 1
        with_citations += bool(citations[name])
        notes += note is not None
    require(seen == set(leads) == set(records), "Selected sample membership differs")
    require(
        exact(dossier["source_age_uncertainty_counts"], dict(sorted(age_codes.items())))
        and exact(dossier["source_age_value_kinds"], dict(sorted(kinds.items()))),
        "Native raw-age denominator differs",
    )
    require(
        dossier["samples_with_publication_links"] == with_citations
        and dossier["samples_with_collection_note_cues"] == notes,
        "Collection/publication denominator differs",
    )
    return sorted(
        dossier["rows"],
        key=lambda item: (
            f"empd2-nfi:{item['spatial_lead']['pollen_sample']}:nfi-{item['spatial_lead']['nfi_tract']}-{item['spatial_lead']['nfi_plot']}-{item['spatial_lead']['nfi_year']}"
        ),
    )


def expected_rows(
    items: list[dict[str, Any]],
    nfi: list[tuple[str, str, str, str, float, float]],
    transform: Any,
    geod: Any,
) -> list[dict[str, object]]:
    by_key = {(r[1], r[2], r[0]): r for r in nfi}
    require(len(by_key) == len(nfi), "Duplicate NFI source key")
    rows = []
    for item in items:
        lead = item["spatial_lead"]
        raw = item["source_metadata_excluding_vegdescription"]
        name = lead["pollen_sample"]
        n = by_key[lead["nfi_tract"], lead["nfi_plot"], lead["nfi_year"]]
        require(
            n[3] == lead["nfi_inventory_date_source_native"],
            "Native inventory date differs",
        )
        lon, lat = transform.transform(n[4], n[5])
        lon, lat = (finite(lon), finite(lat))
        _, _, distance = geod.inv(
            finite(raw["longitude"]), finite(raw["latitude"]), lon, lat
        )
        distance = finite(distance)
        require(
            0 <= distance <= 1000
            and abs(distance - finite(lead["distance_m_wgs84"])) <= 1e-05,
            "Source geodesic changed beyond maintained1e-5m bound",
        )
        gaps = list(GAPS)
        identity = (
            "unresolved"
            if "cross_source_identity_unresolved" in lead["pollen_review_reason_codes"]
            else "not_established"
        )
        if identity == "unresolved":
            gaps.append("physical_pollen_sample_cross_source_identity")
        if item["collection_time_status"] == "source_note_requires_review":
            gaps.append("source_collection_note_authentication")
        row = {
            "candidate_id": f"empd2-nfi:{name}:nfi-{n[1]}-{n[2]}-{n[0]}",
            "empd2_sample": name,
            "empd2_source_sha256": INPUTS["sqlite"][1],
            "empd2_source_agebp": raw["agebp"],
            "empd2_source_age_code": raw["ageuncertainty"],
            "empd2_collection_time_status": item["collection_time_status"],
            "empd2_longitude_wgs84": float(raw["longitude"]),
            "empd2_latitude_wgs84": float(raw["latitude"]),
            "nfi_tract": n[1],
            "nfi_plot": n[2],
            "nfi_year": n[0],
            "nfi_inventory_date_source_native": n[3],
            "nfi_easting_sweref99tm": n[4],
            "nfi_northing_sweref99tm": n[5],
            "nfi_longitude_wgs84": lon,
            "nfi_latitude_wgs84": lat,
            "nfi_source_sha256": INPUTS["workbook"][1],
            "distance_m_wgs84": distance,
            "coordinate_comparability": "source_crs_transformed_geodesic_proximity_only",
            "time_comparability": "unresolved_pollen_collection_time",
            "measurement_comparability": "nfi_tree_outcomes_sealed_and_pollen_target_unmapped",
            "footprint_comparability": "lake_or_sediment_vs_tree_plot_support_unmatched",
            "source_identity_status": identity,
            "missing_or_unreviewed_fields": ";".join(gaps),
            "current_benchmark_decision": "refused_missing_pair_evidence",
            "scientific_admission": "false",
        }
        require(set(row) == set(FIELDS), "Independent row field closure differs")
        rows.append(row)
    return rows


def validate_products(
    output: Path, rows: list[dict[str, object]], tracked_report: dict[str, Any]
) -> dict[str, Any]:
    require(
        len(rows) == 16 and len({r["candidate_id"] for r in rows}) == 16,
        "Current16-row closure differs",
    )
    source = output / "pairs-source-bound.csv"
    public = output / "pairs.csv"
    report_path = output / "report.json"
    require(
        source.read_bytes() == csv_wire(rows, FIELDS),
        "Complete source-bound CSV differs from independently joined records",
    )
    public_rows = public_projection(rows)
    require(
        public.read_bytes() == csv_wire(public_rows, PUBLIC_FIELDS),
        "Public privacy projection differs",
    )
    actual = load(report_path)
    expected = dict(tracked_report)
    expected["pairs_csv"] = {
        "bytes": public.stat().st_size,
        "sha256": pin(public)["sha256"],
    }
    require(
        exact(actual, expected),
        "Complete current report differs outside authenticated new public CSV digest/size",
    )
    require(
        actual["denominators"]["measured_pairs_admitted"] == 0
        and type(actual["denominators"]["measured_pairs_admitted"]) is int,
        "Measured pair count promoted",
    )
    require(
        all(
            row["scientific_admission"] == "false"
            and row["current_benchmark_decision"] == "refused_missing_pair_evidence"
            for row in rows
        ),
        "A pair refusal was promoted",
    )
    require(
        actual["missing_or_unreviewed_fields_all_pairs"] == list(GAPS),
        "Complete eight shared gaps changed",
    )
    require(
        actual["pair_specific_extra_gaps"]
        == {
            "cross_source_identity_unresolved": sum(
                r["source_identity_status"] == "unresolved" for r in rows
            ),
            "collection_note_requires_review": sum(
                r["empd2_collection_time_status"] == "source_note_requires_review"
                for r in rows
            ),
        },
        "Pair-specific gaps changed",
    )
    require(
        actual["denominators"]["distinct_selected_nfi_plot_years"]
        == len(
            {tuple(r[k] for k in ("nfi_tract", "nfi_plot", "nfi_year")) for r in rows}
        ),
        "Selected plot-year count differs",
    )
    return {
        "complete_source_rows": len(rows),
        "all_source_fields_checked": len(FIELDS),
        "public_fields_checked": len(PUBLIC_FIELDS),
        "private_location_fields_excluded": len(LOCATION_FIELDS),
        "admitted_pairs": 0,
        "refusals": 16,
        "tree_outcome_cells_selected": 0,
        "geodesic_retained_agreement_tolerance_m": 1e-05,
        "static_report_oracle": "Authenticated canonical report metadata, with only current independent public CSV bytes/hash substituted. Complete source/private/public row values are independently reconstructed.",
        "retained_all_pairs_within1km_claim": 53,
        "full132_by43892_spatial_sweep_recomputed": False,
        "scientific_acceptance_claimed": False,
    }
