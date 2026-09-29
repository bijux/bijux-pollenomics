"""Bind EMPD2–NFI spatial leads to source rows and explicit pair refusals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from pyproj import Geod, Transformer

from bijux_pollenomics_dev.source_completion.empd2_nfi import _nfi_rows
from bijux_pollenomics_dev.source_completion.empd2_nfi_reference import (
    build_empd2_nfi_decision_projection,
)

SOURCE_INPUTS = {
    "source-dossier.json": (
        Path("reference-sources/empd2-nfi/pairing/source-provenance.json"),
        "bcab3834980f6934143f3a2bf4e2a0155bf3c7024850989de4f0f28f89584c31",
    ),
    "spatial-screen.json": (
        Path("reference-sources/empd2-nfi/pairing/spatial-feasibility.json"),
        "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
    ),
    "slu-calibration-guide.pdf": (
        Path(
            "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
        ),
        "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8",
    ),
}
EMPD2_SHA256 = "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2"
NFI_SHA256 = "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294"
SOURCE_FIELDS = (
    "candidate_id",
    "empd2_sample",
    "empd2_source_sha256",
    "empd2_source_agebp",
    "empd2_source_age_code",
    "empd2_collection_time_status",
    "empd2_longitude_wgs84",
    "empd2_latitude_wgs84",
    "nfi_tract",
    "nfi_plot",
    "nfi_year",
    "nfi_inventory_date_source_native",
    "nfi_easting_sweref99tm",
    "nfi_northing_sweref99tm",
    "nfi_longitude_wgs84",
    "nfi_latitude_wgs84",
    "nfi_source_sha256",
    "distance_m_wgs84",
    "coordinate_comparability",
    "time_comparability",
    "measurement_comparability",
    "footprint_comparability",
    "source_identity_status",
    "missing_or_unreviewed_fields",
    "current_benchmark_decision",
    "scientific_admission",
)
NFI_LOCATION_FIELDS = frozenset(
    {
        "nfi_tract",
        "nfi_plot",
        "nfi_year",
        "nfi_inventory_date_source_native",
        "nfi_easting_sweref99tm",
        "nfi_northing_sweref99tm",
        "nfi_longitude_wgs84",
        "nfi_latitude_wgs84",
    }
)
PUBLIC_FIELDS = (
    "candidate_id",
    "nfi_row_identity_sha256",
    *(
        field
        for field in SOURCE_FIELDS
        if field not in NFI_LOCATION_FIELDS and field != "candidate_id"
    ),
)
COMMON_GAPS = (
    "authenticated_pollen_collection_date",
    "nfi_tree_measurement_values_and_units",
    "nfi_plot_effective_area_and_vegetation_denominator",
    "pollen_taxon_count_denominator_and_tree_taxon_crosswalk",
    "pollen_basin_or_local_vegetation_footprint",
    "plot_to_reconstruction_support_rule",
    "independent_source_and_leakage_review",
    "reviewed_nonnull_benchmark_minimum_and_thresholds",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def review_inputs(
    repository: Path, private_source_store: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Authenticate private review inputs and the tracked public guide."""
    source_bytes = {
        name: (
            (
                repository
                if name == "slu-calibration-guide.pdf"
                else private_source_store
            )
            / path
        ).read_bytes()
        for name, (path, _) in SOURCE_INPUTS.items()
    }
    for name, (_, expected) in SOURCE_INPUTS.items():
        if _sha(source_bytes[name]) != expected:
            raise ValueError(f"EMPD2–NFI review input digest changed: {name}")
    projection = build_empd2_nfi_decision_projection(
        dossier_bytes=source_bytes["source-dossier.json"],
        dossier_sha256=SOURCE_INPUTS["source-dossier.json"][1],
        spatial_bytes=source_bytes["spatial-screen.json"],
        spatial_sha256=SOURCE_INPUTS["spatial-screen.json"][1],
        guide_bytes=source_bytes["slu-calibration-guide.pdf"],
        guide_sha256=SOURCE_INPUTS["slu-calibration-guide.pdf"][1],
        workbook_sha256=NFI_SHA256,
    )
    dossier = cast(dict[str, Any], json.loads(source_bytes["source-dossier.json"]))
    spatial = cast(dict[str, Any], json.loads(source_bytes["spatial-screen.json"]))
    if (
        projection["source_identities"]["empd2_source"] != EMPD2_SHA256
        or projection["source_identities"]["nfi_workbook"] != NFI_SHA256
        or spatial["swedish_pollen_samples"] != 132
        or spatial["nfi_plot_year_rows"] != 43_892
        or spatial["nfi_distinct_plots"] != 6_018
        or spatial["thresholds_descriptive_only"]["1000"]
        != {
            "candidate_plot_year_sample_pairs": 53,
            "nfi_plot_years": 47,
            "nfi_plots": 46,
            "pollen_samples": 16,
        }
    ):
        raise ValueError("EMPD2–NFI retained source denominator changed")
    return projection, dossier, spatial


def decision_rows(
    projection: dict[str, Any],
    dossier: dict[str, Any],
    nfi_rows: list[tuple[str, str, str, str, float, float]],
) -> list[dict[str, object]]:
    """Bind each lead to one real plot row while keeping outcomes sealed."""
    if (
        projection.get("candidate_count") != 16
        or projection.get("admitted_pair_count") != 0
        or dossier.get("selected_lead_count") != 16
        or len(nfi_rows) != 43_892
    ):
        raise ValueError("EMPD2–NFI candidate or NFI source denominator changed")
    by_sample = {row["spatial_lead"]["pollen_sample"]: row for row in dossier["rows"]}
    by_plot = {(row[1], row[2], row[0]): row for row in nfi_rows}
    if len(by_sample) != 16 or len(by_plot) != len(nfi_rows):
        raise ValueError("EMPD2–NFI source identity is not unique")
    transform = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)
    geod = Geod(ellps="WGS84")
    decisions: list[dict[str, object]] = []
    for candidate in projection["candidate_rows"]:
        sample = candidate["pollen_sample"]
        source = by_sample[sample]
        metadata = source["source_metadata_excluding_vegdescription"]
        key = (candidate["nfi_tract"], candidate["nfi_plot"], candidate["nfi_year"])
        nfi = by_plot[key]
        if nfi[3] != candidate["nfi_inventory_date_source_native"]:
            raise ValueError(f"NFI native inventory date changed: {key}")
        nfi_lon, nfi_lat = transform.transform(nfi[4], nfi[5])
        _, _, distance = geod.inv(
            float(candidate["pollen_longitude"]),
            float(candidate["pollen_latitude"]),
            nfi_lon,
            nfi_lat,
        )
        if abs(distance - float(candidate["distance_m_wgs84"])) > 0.00001:
            raise ValueError(f"EMPD2–NFI geodesic source match changed: {sample}")
        gaps = list(COMMON_GAPS)
        if candidate["cross_source_identity_status"] == "unresolved":
            gaps.append("physical_pollen_sample_cross_source_identity")
        if source["collection_time_status"] == "source_note_requires_review":
            gaps.append("source_collection_note_authentication")
        decisions.append(
            {
                "candidate_id": candidate["record_id"],
                "empd2_sample": sample,
                "empd2_source_sha256": EMPD2_SHA256,
                "empd2_source_agebp": metadata["agebp"],
                "empd2_source_age_code": metadata["ageuncertainty"],
                "empd2_collection_time_status": source["collection_time_status"],
                "empd2_longitude_wgs84": candidate["pollen_longitude"],
                "empd2_latitude_wgs84": candidate["pollen_latitude"],
                "nfi_tract": nfi[1],
                "nfi_plot": nfi[2],
                "nfi_year": nfi[0],
                "nfi_inventory_date_source_native": nfi[3],
                "nfi_easting_sweref99tm": nfi[4],
                "nfi_northing_sweref99tm": nfi[5],
                "nfi_longitude_wgs84": nfi_lon,
                "nfi_latitude_wgs84": nfi_lat,
                "nfi_source_sha256": NFI_SHA256,
                "distance_m_wgs84": distance,
                "coordinate_comparability": "source_crs_transformed_geodesic_proximity_only",
                "time_comparability": "unresolved_pollen_collection_time",
                "measurement_comparability": "nfi_tree_outcomes_sealed_and_pollen_target_unmapped",
                "footprint_comparability": "lake_or_sediment_vs_tree_plot_support_unmatched",
                "source_identity_status": candidate["cross_source_identity_status"],
                "missing_or_unreviewed_fields": ";".join(gaps),
                "current_benchmark_decision": "refused_missing_pair_evidence",
                "scientific_admission": "false",
            }
        )
    if len(decisions) != 16 or len({row["candidate_id"] for row in decisions}) != 16:
        raise ValueError("EMPD2–NFI pair candidate closure changed")
    return decisions


def public_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep plot identities and coordinates in the ignored source-bound ledger."""
    public: list[dict[str, object]] = []
    for row in rows:
        source_row = [row[field] for field in sorted(NFI_LOCATION_FIELDS)]
        identity = _sha(
            json.dumps(
                {"nfi_source_sha256": NFI_SHA256, "row": source_row},
                separators=(",", ":"),
            ).encode("utf-8")
        )
        item = {
            field: row[field]
            for field in PUBLIC_FIELDS
            if field not in {"candidate_id", "nfi_row_identity_sha256"}
        }
        item["candidate_id"] = f"empd2-nfi:{row['empd2_sample']}:{identity[:16]}"
        item["nfi_row_identity_sha256"] = identity
        public.append(item)
    if len({row["candidate_id"] for row in public}) != len(public):
        raise ValueError("Public EMPD2–NFI candidate identity collision")
    return public


def build(
    repository: Path, private_source_store: Path, output: Path
) -> dict[str, object]:
    """Write a deterministic, source-checked refusal ledger at an absent path."""
    if output.exists():
        raise ValueError("Absent output destination required")
    repository, private_source_store, output = (
        path.resolve() for path in (repository, private_source_store, output)
    )
    source_root = private_source_store / "reference-sources/empd2-nfi"
    empd2_source = source_root / "empd2/source.sqlite3"
    nfi_workbook = source_root / "nfi/swedish-plot-data.xlsx"
    if _file_sha(empd2_source) != EMPD2_SHA256 or _file_sha(nfi_workbook) != NFI_SHA256:
        raise ValueError("EMPD2 or NFI original source identity changed")
    projection, dossier, spatial = review_inputs(repository, private_source_store)
    rows = decision_rows(projection, dossier, _nfi_rows(nfi_workbook))
    if _file_sha(empd2_source) != EMPD2_SHA256 or _file_sha(nfi_workbook) != NFI_SHA256:
        raise ValueError("EMPD2 or NFI source changed during pairing")
    output.mkdir(parents=True)
    source_ledger = output / "pairs-source-bound.csv"
    with source_ledger.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, SOURCE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    ledger = output / "pairs.csv"
    with ledger.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, PUBLIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(public_rows(rows))
    report: dict[str, object] = {
        "schema_version": "empd2-nfi-pair-decision.v1",
        "status": "zero_measured_pairs_refused_for_current_benchmark",
        "input_sha256": {
            **{path.as_posix(): digest for path, digest in SOURCE_INPUTS.values()},
            "empd2_original_source": EMPD2_SHA256,
            "nfi_original_workbook": NFI_SHA256,
            "producer": _file_sha(Path(__file__)),
        },
        "source_provenance": {
            "empd2_doi": "https://doi.org/10.1594/PANGAEA.909130",
            "empd2_source_license": "CC BY 4.0 per PANGAEA source page",
            "nfi_provider": "Swedish University of Agricultural Sciences, National Forest Inventory",
            "nfi_guide_url": "https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf",  # codespell:ignore dokument
            "nfi_guide_license": "CC0 1.0 per SLU calibration guide",
            "nfi_source_crs": "SWEREF99 TM / EPSG:3006",
            "distance_method": "WGS84 inverse geodesic; unrounded source values",
            "nfi_outcomes_opened": False,
            "raw_sources_copied": False,
            "nfi_row_level_location_published": False,
        },
        "denominators": {
            "swedish_empd2_metadata_samples": spatial["swedish_pollen_samples"],
            "nfi_plot_year_source_rows": spatial["nfi_plot_year_rows"],
            "nfi_distinct_tract_plot_keys": spatial["nfi_distinct_plots"],
            "all_plot_year_sample_pairs_within_1km": spatial[
                "thresholds_descriptive_only"
            ]["1000"]["candidate_plot_year_sample_pairs"],
            "nearest_plot_candidates_within_1km": 16,
            "distinct_selected_nfi_plot_years": len(
                {(row["nfi_tract"], row["nfi_plot"], row["nfi_year"]) for row in rows}
            ),
            "measured_pairs_admitted": 0,
            "current_benchmark_refusals": len(rows),
        },
        "missing_or_unreviewed_fields_all_pairs": list(COMMON_GAPS),
        "pair_specific_extra_gaps": {
            "cross_source_identity_unresolved": sum(
                row["source_identity_status"] == "unresolved" for row in rows
            ),
            "collection_note_requires_review": sum(
                row["empd2_collection_time_status"] == "source_note_requires_review"
                for row in rows
            ),
        },
        "decision": {
            "observed_tree_vegetation_measurement_pair_admitted": False,
            "regional_reconstruction_validation_supported": False,
            "local_plot_validation_supported": False,
            "benchmark_policy_frozen": False,
            "evaluation_performed": False,
            "scientific_acceptance": "not_evaluated",
            "review_state": "awaiting_qualified_source_review",
        },
        "pairs_csv": {"bytes": ledger.stat().st_size, "sha256": _file_sha(ledger)},
        "local_source_bound_ledger_sha256": _file_sha(source_ledger),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.repository, args.private_source_store, args.output)
    print(json.dumps(result["denominators"]))


if __name__ == "__main__":
    main()
