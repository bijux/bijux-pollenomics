"""Bind Rootsi metadata candidates to LandClim site coverage without admitting truth."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast

ROOTSI = Path("data/landclim/review/rootsi-candidate-inputs")
SITES = Path("data/landclim/normalized/nordic_pollen_site_sequences.csv")
RAW_METADATA = Path("data/landclim/raw/landclim_ii_site_metadata.xlsx")
SOURCE_RECEIPT = Path("data/landclim/raw/landclim_sources.json")
EXPECTED_PAIR_SHA = "ca94f04342f5c54212dc3ef9acfa0cbeea6e92419878f951ec23b2a0acf5cfd6"
EXPECTED_CANDIDATE_SHA256 = {
    "manifest.json": "714f60289143e38f38a9e6acb75d4a150be79ba6637f6c222d89998c291b5ffe",
    "publication-candidates.jsonl": "d54b2266c4b7c7386edef9d5694c49a20c1cc1eadab3155358aca4dd386a79c3",
    "rootsi-crosswalk.csv": "ee76ac6af9d79ce4d81224a566e8edd7dc71eb940402b352fda809bba7e93588",
    "requirement-status.csv": "7852bb8ca7a7c064844b23a71e385030ae35d8e0b5031994eefe71253e3b7362",
    "report.json": "10ddc1d588411d1eb55d369d7a886ef0846acbe92fb1f6698e631fc82363c70d",
}
DOI = "https://doi.org/10.1594/PANGAEA.937075"
FIELDS = (
    "publication_row",
    "publication_locator",
    "rootsi_row",
    "rootsi_locator",
    "publication_sequence",
    "rootsi_sequence",
    "site_record_id",
    "site_name",
    "match_reasons",
    "publication_samples",
    "rootsi_samples",
    "site_samples",
    "samples_agree",
    "typed_workbook_member",
    "typed_workbook_sha256",
    "access_marker",
    "chronology_source_label",
    "site_coverage_start_bp",
    "site_coverage_end_bp",
    "source_top_bp",
    "source_bottom_bp",
    "coverage_comparability",
    "coverage_refusal_reason",
    "site_window_count",
    "site_grid_id",
    "candidate_overlap",
    "authenticated_workbook_identity",
    "per_sequence_rights",
    "independent_ground_truth",
    "exact_grid_window_contribution",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def _identity(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": _sha(data),
    }


def verify_candidate_inputs(candidate_dir: Path) -> dict[str, Any]:
    """Require the complete byte-identical derived candidate closure."""
    if (
        candidate_dir.is_symlink()
        or not candidate_dir.is_dir()
        or {path.name for path in candidate_dir.iterdir()}
        != set(EXPECTED_CANDIDATE_SHA256)
    ):
        raise ValueError("Rootsi review input set changed")
    for name, expected_sha in EXPECTED_CANDIDATE_SHA256.items():
        path = candidate_dir / name
        if (
            path.is_symlink()
            or not path.is_file()
            or _sha(path.read_bytes()) != expected_sha
        ):
            raise ValueError(f"Rootsi review input digest changed: {name}")
    manifest = json.loads((candidate_dir / "manifest.json").read_bytes())
    if (
        manifest["output_contract"]["candidate_pair_identity_sha256"]
        != EXPECTED_PAIR_SHA
        or manifest["output_contract"]["output_file_count"] != 5
        or manifest["claims"]["rootsi_is_authenticated_historical_input"] is not False
        or manifest["claims"]["per_sequence_rights_cleared"] is not False
        or manifest["claims"]["scientifically_accepted"] is not False
    ):
        raise ValueError("Rootsi manifest changed scientific posture")
    if {entry["path"] for entry in manifest["artifacts"]} != (
        set(EXPECTED_CANDIDATE_SHA256) - {"manifest.json"}
    ):
        raise ValueError("Rootsi manifest artifact set changed")
    for artifact in manifest["artifacts"]:
        path = candidate_dir / artifact["path"]
        data = path.read_bytes()
        if _sha(data) != artifact["sha256"] or len(data) != artifact["byte_count"]:
            raise ValueError(f"Rootsi candidate artifact changed: {path.name}")
    return cast(dict[str, Any], manifest)


def reconcile(
    publication: list[dict[str, Any]],
    crosswalk: list[dict[str, str]],
    sites: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Require a complete, one-to-one metadata/consumer join and retain refusals."""
    if len(publication) != 1128 or len(crosswalk) != 81:
        raise ValueError("Rootsi source denominators changed")
    status = Counter(row["candidate_status"] for row in publication)
    if status != {
        "unique_rootsi_metadata_candidate": 79,
        "no_rootsi_metadata_candidate": 1049,
    }:
        raise ValueError("Rootsi candidate inventory changed")
    cross_status = Counter(row["publication_candidate_status"] for row in crosswalk)
    if cross_status != {
        "unique_rootsi_metadata_candidate": 79,
        "no_rootsi_metadata_candidate": 2,
    }:
        raise ValueError("Rootsi crosswalk inventory changed")
    rootsi = {int(row["rootsi_source_row"]): row for row in crosswalk}
    if len(rootsi) != 81:
        raise ValueError("Duplicate Rootsi metadata row")
    site_index: dict[str, list[dict[str, str]]] = {}
    for site in sites:
        if site["record_id"].startswith("937075:"):
            site_index.setdefault(
                site["record_id"].split(":", 1)[1].casefold(), []
            ).append(site)
    if sum(map(len, site_index.values())) != 223:
        raise ValueError("LandClim II site inventory changed")
    rows: list[dict[str, object]] = []
    used_rootsi: set[int] = set()
    used_sites: set[str] = set()
    used_publication: set[int] = set()
    for source in publication:
        if source["candidate_status"] != "unique_rootsi_metadata_candidate":
            continue
        candidates = source["metadata_candidates"]
        if len(candidates) != 1 or source["reproduction_ready"] is not False:
            raise ValueError("Candidate status or scientific admission changed")
        candidate = candidates[0]
        row_id = int(candidate["rootsi_source_row"])
        publication_row = int(source["publication_worksheet_row"])
        if row_id in used_rootsi or publication_row in used_publication:
            raise ValueError("Candidate mapping is not one-to-one")
        used_rootsi.add(row_id)
        used_publication.add(publication_row)
        cross = rootsi[row_id]
        if (
            cross["publication_candidate_status"] != "unique_rootsi_metadata_candidate"
            or json.loads(cross["publication_candidate_rows_json"]) != [publication_row]
            or json.loads(cross["match_reasons_json"]) != [candidate["match_reasons"]]
            or json.loads(cross["sample_count_agrees_json"])
            != [candidate["sample_count_agrees"]]
            or cross["rootsi_source_locator"] != candidate["rootsi_source_locator"]
            or cross["rootsi_sequence_label_raw"]
            != candidate["rootsi_sequence_label_raw"]
            or not cross["typed_workbook_member"].startswith("rootsi/")
            or len(cross["typed_workbook_sha256"]) != 64
            or cross["historical_primary_input_identity_status"] != "not_authenticated"
            or cross["reproduction_ready"] != "false"
            or candidate["historical_primary_input_identity_verified"] is not False
            or candidate["reported_country_agrees"] is not True
            or source["publication_country_raw"] != "Sweden"
            or cross["rootsi_country_raw"] != "SWE"
        ):
            raise ValueError("Rootsi candidate ownership or refusal changed")
        sequence = source["publication_sequence_raw"]
        matched = site_index.get(sequence.casefold(), [])
        if len(matched) != 1:
            raise ValueError(f"LandClim site join is not unique: {sequence}")
        site = matched[0]
        if site["record_id"] in used_sites:
            raise ValueError("LandClim site reused by multiple candidates")
        used_sites.add(site["record_id"])
        popup = dict(json.loads(site["popup_rows_json"]))
        temporal = json.loads(site["temporal_semantics_json"])
        if (
            site["source_url"] != DOI
            or site["country"] != "Sweden"
            or popup["Sequence file"] != sequence
            or popup["Pollen samples"] != source["publication_sample_count_raw"]
            or popup["Access posture"] != source["publication_access_marker_raw"]
            or popup["Chronology basis"] != source["publication_chronology_source_raw"]
            or temporal["original_labels"]
            != [
                f"{label}: {popup[label]}"
                for label in ("Top BP", "Bottom BP")
                if label in popup
            ]
            or popup["Time windows"] != site["record_count"]
            or temporal["evidence_class"] != "pollen_site_sequence_coverage"
            or temporal["provenance_path"] != RAW_METADATA.as_posix()
            or (
                temporal["comparability_posture"] == "numeric_interval"
                and (
                    temporal["time_start_bp"] != int(site["time_start_bp"])
                    or temporal["time_end_bp"] != int(site["time_end_bp"])
                    or temporal["refusal_reason_code"] != ""
                )
            )
            or (
                temporal["comparability_posture"] == "refused"
                and (
                    site["time_start_bp"] != ""
                    or site["time_end_bp"] != ""
                    or temporal["time_start_bp"] is not None
                    or temporal["time_end_bp"] is not None
                    or temporal["refusal_reason_code"]
                    not in {"negative_bp", "partial_interval"}
                )
            )
            or temporal["comparability_posture"] not in {"numeric_interval", "refused"}
            or candidate["sample_count_agrees"]
            != (
                str(candidate["rootsi_sample_count_claim"])
                == source["publication_sample_count_raw"]
            )
        ):
            raise ValueError(
                f"LandClim site metadata or temporal meaning changed: {sequence}"
            )
        rows.append(
            {
                "publication_row": publication_row,
                "publication_locator": source["publication_source_locator"],
                "rootsi_row": row_id,
                "rootsi_locator": cross["rootsi_source_locator"],
                "publication_sequence": sequence,
                "rootsi_sequence": cross["rootsi_sequence_label_raw"],
                "site_record_id": site["record_id"],
                "site_name": site["name"],
                "match_reasons": ";".join(candidate["match_reasons"]),
                "publication_samples": source["publication_sample_count_raw"],
                "rootsi_samples": cross["rootsi_sample_count_claim"],
                "site_samples": popup["Pollen samples"],
                "samples_agree": str(candidate["sample_count_agrees"]).lower(),
                "typed_workbook_member": cross["typed_workbook_member"],
                "typed_workbook_sha256": cross["typed_workbook_sha256"],
                "access_marker": popup["Access posture"],
                "chronology_source_label": popup["Chronology basis"],
                "site_coverage_start_bp": site["time_start_bp"],
                "site_coverage_end_bp": site["time_end_bp"],
                "source_top_bp": popup.get("Top BP", ""),
                "source_bottom_bp": popup.get("Bottom BP", ""),
                "coverage_comparability": temporal["comparability_posture"],
                "coverage_refusal_reason": temporal["refusal_reason_code"],
                "site_window_count": site["record_count"],
                "site_grid_id": popup["LCGRID_ID"],
                "candidate_overlap": "yes_metadata_only",
                "authenticated_workbook_identity": "unresolved",
                "per_sequence_rights": "unresolved",
                "independent_ground_truth": "refused_candidate_overlap",
                "exact_grid_window_contribution": "unresolved",
            }
        )
    if len(rows) != 79 or len(used_rootsi) != 79 or len(used_sites) != 79:
        raise ValueError("Incomplete candidate overlap ledger")
    coverage = Counter(
        (str(row["coverage_comparability"]), str(row["coverage_refusal_reason"]))
        for row in rows
    )
    if coverage != {
        ("numeric_interval", ""): 35,
        ("refused", "negative_bp"): 36,
        ("refused", "partial_interval"): 8,
    } or Counter(row["samples_agree"] for row in rows) != {"true": 78, "false": 1}:
        raise ValueError("Sample or chronology refusal inventory changed")
    rows.sort(key=lambda row: int(str(row["publication_row"])))
    return rows


def build(repository: Path, output: Path) -> dict[str, object]:
    """Write a deterministic source-bound review at an explicit destination."""
    repository = repository.resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError("Absent destination required")
    candidate_dir = repository / ROOTSI
    manifest_path = candidate_dir / "manifest.json"
    manifest = verify_candidate_inputs(candidate_dir)
    metadata_path = repository / RAW_METADATA
    if (
        _sha(metadata_path.read_bytes())
        != manifest["sources"]["publication_inventory"]["workbook_sha256"]
    ):
        raise ValueError("Publication workbook identity changed")
    receipt_path = repository / SOURCE_RECEIPT
    if (
        _sha(receipt_path.read_bytes())
        != manifest["sources"]["publication_inventory"]["receipt_sha256"]
    ):
        raise ValueError("LandClim source receipt identity changed")
    receipt = json.loads(receipt_path.read_text())
    if not any(
        dataset["dataset_id"] == "937075"
        and dataset["doi"] == DOI
        and RAW_METADATA.name in dataset["files"]
        for dataset in receipt["datasets"]
    ):
        raise ValueError("LandClim II source receipt changed")
    publication_path = candidate_dir / "publication-candidates.jsonl"
    crosswalk_path = candidate_dir / "rootsi-crosswalk.csv"
    publication = [
        json.loads(line) for line in publication_path.read_text().splitlines()
    ]
    rows = reconcile(
        publication,
        _read_csv(crosswalk_path.read_bytes()),
        _read_csv((repository / SITES).read_bytes()),
    )
    output.mkdir(parents=True)
    with (output / "overlap.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report: dict[str, object] = {
        "schema_version": "rootsi-landclim-overlap.v1",
        "source": DOI,
        "matching_profile": manifest["output_contract"]["matching_profile"],
        "candidate_pair_identity_sha256": EXPECTED_PAIR_SHA,
        "denominators": {
            "publication_metadata_rows": 1128,
            "rootsi_metadata_rows": 81,
            "landclim_ii_site_features": 223,
            "unique_metadata_candidate_pairs": 79,
            "unmatched_publication_rows": 1049,
            "unmatched_rootsi_rows": 2,
            "sample_count_agreement": 78,
            "sample_count_disagreement": 1,
            "numeric_site_coverage_intervals": 35,
            "refused_site_coverage_intervals": 44,
            "negative_bp_coverage_refusals": 36,
            "partial_coverage_refusals": 8,
        },
        "dependency_edges": [
            {
                "from": "Rootsi typed workbook claim",
                "to": "Rootsi metadata row",
                "status": "member_and_hash_only",
            },
            {
                "from": "Rootsi metadata row",
                "to": "LandClim II publication metadata row",
                "status": "unique_metadata_candidate",
            },
            {
                "from": "LandClim II publication metadata row",
                "to": "normalized LandClim II site feature",
                "status": "exact_sequence_and_source_metadata_join",
            },
            {
                "from": "LandClim II site feature",
                "to": "REVEALS grid/window/value/SE",
                "status": "dataset_context_only_exact_contributor_lineage_unresolved",
            },
        ],
        "admission": {
            "independent_vegetation_ground_truth": False,
            "raw_pollen_independence_from_landclim_model": False,
            "historical_workbook_identity_authenticated": False,
            "per_sequence_rights_cleared": False,
            "sample_chronology_admitted": False,
            "grid_window_contributor_lineage_resolved": False,
        },
        "notes": [
            "Pairing is metadata candidate overlap, not authenticated identity of historical input cells.",
            "Site BP bounds describe sequence coverage; they are not sample ages or event times.",
            "Shared site metadata creates a possible circular comparison; LandClim model output is not independent vegetation truth for these candidates.",
            "LCGRID_ID and site time coverage do not prove which site contributed to a modeled grid/window or its value and standard error.",
            "EKE reports 25 Rootsi samples and 42 LandClim publication/site samples; its candidate status does not erase this disagreement.",
            "Only 35 site coverage intervals remain numerically comparable; 36 negative-BP and 8 partial source intervals are refused.",
        ],
        "inputs": [
            _identity(path, repository)
            for path in (
                manifest_path,
                publication_path,
                crosswalk_path,
                candidate_dir / "requirement-status.csv",
                candidate_dir / "report.json",
                metadata_path,
                receipt_path,
                repository / SITES,
            )
        ],
        "overlap_csv": {
            "bytes": (output / "overlap.csv").stat().st_size,
            "sha256": _sha((output / "overlap.csv").read_bytes()),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
