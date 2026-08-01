"""Governed discovery surface for Swedish archaeology sites represented by SEAD."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
import csv
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

from ....core.files import write_json
from ....core.temporal_semantics import build_temporal_semantics
from ...exports.context_points import write_context_points_geojson
from ...models import ContextPointRecord

DISCOVERY_LAYER_KEY = "sweden-archaeology-site-discovery"
DISCOVERY_LAYER_LABEL = "Sweden archaeology site discovery"
DISCOVERY_JSON_NAME = "sweden_archaeology_site_discovery.json"
DISCOVERY_CSV_NAME = "sweden_archaeology_site_discovery.csv"
DISCOVERY_GEOJSON_NAME = "sweden_archaeology_site_discovery.geojson"
DISCOVERY_MARKDOWN_NAME = "sweden_archaeology_site_discovery.md"

_READINESS_ORDER = {
    "chronology_and_bibliography_ready": 0,
    "chronology_ready": 1,
    "bibliography_ready": 2,
    "inventory_only": 3,
}


@dataclass(frozen=True)
class SwedenArchaeologySiteDiscovery:
    """Auditable site registry and time-aware map records for Sweden."""

    summary: dict[str, object]
    ranking_contract: dict[str, object]
    site_rows: tuple[dict[str, object], ...]
    map_records: tuple[ContextPointRecord, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "sweden-archaeology-site-discovery.v1",
            "generated_on": date.today().isoformat(),
            "summary": self.summary,
            "ranking_contract": self.ranking_contract,
            "sites": list(self.site_rows),
        }


def build_sweden_archaeology_site_discovery(
    *,
    site_records: Iterable[ContextPointRecord],
    temporal_records: Iterable[ContextPointRecord],
    raw_rows: Iterable[Mapping[str, object]],
    raa_density_geojson: Mapping[str, object] | None = None,
) -> SwedenArchaeologySiteDiscovery:
    """Build a complete Sweden-only discovery registry without invented dates."""
    sweden_sites = {
        record.record_id: record for record in site_records if record.country == "Sweden"
    }
    temporal_by_site: dict[str, list[ContextPointRecord]] = defaultdict(list)
    for record in temporal_records:
        site_id = record.record_id.partition(":")[0]
        if record.country == "Sweden" and site_id in sweden_sites:
            temporal_by_site[site_id].append(record)
    raw_by_site = {
        str(row.get("site_id", "")).strip(): row
        for row in raw_rows
        if str(row.get("site_id", "")).strip() in sweden_sites
    }

    unranked: list[dict[str, object]] = []
    for site_id, record in sweden_sites.items():
        raw = raw_by_site.get(site_id, {})
        chronology = temporal_by_site.get(site_id, [])
        bibliography_count = _list_count(raw.get("bibliography_rows"))
        chronology_kinds = sorted(
            {
                str((item.temporal_semantics or {}).get("evidence_class", ""))
                .removeprefix("sead_")
                .strip()
                for item in chronology
                if str((item.temporal_semantics or {}).get("evidence_class", "")).strip()
            }
        )
        chronology_record_count = sum(item.record_count for item in chronology)
        readiness = _readiness_tier(bool(chronology), bibliography_count > 0)
        raa_count = _density_count_for_point(
            record.longitude, record.latitude, raa_density_geojson
        )
        unranked.append(
            {
                "site_id": site_id,
                "site_name": record.name,
                "country": "Sweden",
                "latitude": record.latitude,
                "longitude": record.longitude,
                "source_url": record.source_url,
                "discovery_readiness": readiness,
                "chronology_resolved": bool(chronology),
                "chronology_interval_count": len(chronology),
                "chronology_record_count": chronology_record_count,
                "chronology_kind_count": len(chronology_kinds),
                "chronology_kinds": chronology_kinds,
                "bibliography_count": bibliography_count,
                "dataset_count": _integer(raw.get("dataset_count")),
                "sample_group_count": _integer(raw.get("sample_group_count")),
                "physical_sample_count": _integer(raw.get("physical_sample_count")),
                "analysis_entity_count": _integer(raw.get("analysis_entity_count")),
                "raa_density_context_count": raa_count,
                "raa_context_role": "coarse_spatial_context_only",
                "current_activity_status": "not_captured_by_repository_sources",
            }
        )

    ordered = sorted(unranked, key=_ranking_key)
    ranked = tuple({**row, "discovery_rank": rank} for rank, row in enumerate(ordered, 1))
    rank_by_site = {str(row["site_id"]): row for row in ranked}
    map_records = tuple(
        record
        for site_id in sorted(sweden_sites, key=lambda value: rank_by_site[value]["discovery_rank"])
        for record in _map_records_for_site(
            sweden_sites[site_id],
            temporal_by_site.get(site_id, []),
            rank_by_site[site_id],
        )
    )
    resolved_count = sum(bool(row["chronology_resolved"]) for row in ranked)
    summary = {
        "country": "Sweden",
        "site_count": len(ranked),
        "chronology_resolved_site_count": resolved_count,
        "chronology_unresolved_site_count": len(ranked) - resolved_count,
        "bibliography_linked_site_count": sum(
            int(row["bibliography_count"]) > 0 for row in ranked
        ),
        "map_feature_count": len(map_records),
        "numeric_temporal_feature_count": sum(
            record.time_mean_bp is not None for record in map_records
        ),
        "unresolved_temporal_feature_count": sum(
            record.time_mean_bp is None for record in map_records
        ),
        "raa_density_context_available": any(
            row["raa_density_context_count"] is not None for row in ranked
        ),
        "current_activity_status": "not_captured_by_repository_sources",
    }
    ranking_contract = {
        "purpose": "repository discovery readiness, not archaeological significance",
        "coverage_rule": "every geolocated Swedish SEAD site is retained",
        "tier_order": list(_READINESS_ORDER),
        "within_tier_order": [
            "chronology kind count descending",
            "chronology source-record count descending",
            "bibliography count descending",
            "dataset count descending",
            "site name and SEAD site identifier ascending",
        ],
        "raa_density_role": (
            "context only; RAÄ density never changes rank, identifies no individual site, "
            "and supplies no chronology"
        ),
        "temporal_rule": (
            "linked numeric SEAD intervals are published individually; sites without "
            "linked numeric chronology remain explicitly unresolved"
        ),
        "activity_rule": (
            "the repository sources do not establish current excavation, sampling, "
            "or research activity"
        ),
    }
    return SwedenArchaeologySiteDiscovery(
        summary=summary,
        ranking_contract=ranking_contract,
        site_rows=ranked,
        map_records=map_records,
    )


def write_sweden_archaeology_site_discovery(
    output_root: Path, discovery: SwedenArchaeologySiteDiscovery
) -> dict[str, Path]:
    """Write registry, tabular, spatial, and human-readable discovery products."""
    derived_root = Path(output_root) / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": derived_root / DISCOVERY_JSON_NAME,
        "csv": derived_root / DISCOVERY_CSV_NAME,
        "geojson": derived_root / DISCOVERY_GEOJSON_NAME,
        "markdown": derived_root / DISCOVERY_MARKDOWN_NAME,
    }
    write_json(paths["json"], discovery.as_dict())
    _write_site_csv(paths["csv"], discovery.site_rows)
    write_context_points_geojson(paths["geojson"], discovery.map_records)
    paths["markdown"].write_text(
        render_sweden_archaeology_site_discovery(discovery), encoding="utf-8"
    )
    return paths


def render_sweden_archaeology_site_discovery(
    discovery: SwedenArchaeologySiteDiscovery,
) -> str:
    """Render the discovery contract and its highest-readiness sites."""
    summary = discovery.summary
    lines = [
        "# Sweden archaeology site discovery",
        "",
        "This governed surface publishes every geolocated Swedish SEAD site. Its order measures repository discovery readiness, not archaeological importance or present-day field activity.",
        "",
        "## Coverage",
        "",
        f"- Sites: {summary['site_count']:,}",
        f"- Sites with linked numeric chronology: {summary['chronology_resolved_site_count']:,}",
        f"- Sites with unresolved chronology: {summary['chronology_unresolved_site_count']:,}",
        f"- Sites with linked bibliography: {summary['bibliography_linked_site_count']:,}",
        f"- Time-aware and explicitly unresolved map features: {summary['map_feature_count']:,}",
        "",
        "## Interpretation contract",
        "",
        "1. Linked SEAD chronology is shown at its real numeric interval; no dates are inferred from place, density, or rank.",
        "2. A site without linked numeric chronology remains visible with an unresolved temporal posture.",
        "3. RAÄ density is coarse context only. It neither identifies a site nor changes discovery rank.",
        "4. Current excavation, sampling, and research activity are not captured by these repository sources.",
        "",
        "## Highest discovery readiness",
        "",
        "| Rank | Site | Readiness | Chronology intervals | Bibliography | Datasets |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for row in discovery.site_rows[:40]:
        lines.append(
            "| {discovery_rank} | [{site_name}]({source_url}) | {discovery_readiness} | "
            "{chronology_interval_count} | {bibliography_count} | {dataset_count} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "The JSON and CSV companions contain the complete ranked registry; the GeoJSON companion contains every temporal interval plus one unresolved feature for each site lacking linked numeric chronology.",
            "",
        ]
    )
    return "\n".join(lines)


def _map_records_for_site(
    site: ContextPointRecord,
    chronology: Sequence[ContextPointRecord],
    registry_row: Mapping[str, object],
) -> list[ContextPointRecord]:
    popup = (
        ("Discovery rank", str(registry_row["discovery_rank"])),
        ("Discovery readiness", str(registry_row["discovery_readiness"]).replace("_", " ")),
        ("Linked bibliography records", str(registry_row["bibliography_count"])),
        ("Linked chronology kinds", str(registry_row["chronology_kind_count"])),
        ("RAÄ density context", str(registry_row["raa_density_context_count"] or "Unavailable")),
        ("Current activity", "Not captured by repository sources"),
    )
    if chronology:
        return [
            ContextPointRecord(
                source="SEAD",
                layer_key=DISCOVERY_LAYER_KEY,
                layer_label=DISCOVERY_LAYER_LABEL,
                category="Archaeology site discovery",
                country="Sweden",
                record_id=f"{item.record_id}:discovery",
                name=site.name,
                latitude=site.latitude,
                longitude=site.longitude,
                geometry_type="Point",
                subtitle="Governed Swedish archaeology discovery",
                description="A linked SEAD chronology interval for this archaeology site.",
                source_url=site.source_url,
                record_count=item.record_count,
                popup_rows=(
                    ("SEAD site ID", site.record_id),
                    *popup,
                    (
                        "Chronology kind",
                        str(
                            (item.temporal_semantics or {}).get(
                                "evidence_class", "linked chronology"
                            )
                        )
                        .removeprefix("sead_")
                        .replace("_", " "),
                    ),
                    ("Date coverage", item.time_label),
                    ("Grouped source records", str(item.record_count)),
                ),
                time_start_bp=item.time_start_bp,
                time_end_bp=item.time_end_bp,
                time_mean_bp=item.time_mean_bp,
                time_label=item.time_label,
                temporal_semantics=item.temporal_semantics,
            )
            for item in chronology
        ]
    semantics = build_temporal_semantics(
        source_family="sead",
        evidence_class="sead_site_inventory",
        precision_posture="no_linked_numeric_chronology",
        comparability_posture="unresolved",
        time_start_bp=None,
        time_end_bp=None,
        summary_label="Chronology unresolved in repository sources",
        comparison_note=(
            "This site remains discoverable but cannot participate in numeric time filtering "
            "until linked chronology is available."
        ),
        provenance_locator=f"site/{site.record_id}",
        uncertainty_notes=("No linked numeric SEAD chronology was captured.",),
    ).as_dict()
    return [
        ContextPointRecord(
            source="SEAD",
            layer_key=DISCOVERY_LAYER_KEY,
            layer_label=DISCOVERY_LAYER_LABEL,
            category="Archaeology site discovery",
            country="Sweden",
            record_id=f"{site.record_id}:unresolved:discovery",
            name=site.name,
            latitude=site.latitude,
            longitude=site.longitude,
            geometry_type="Point",
            subtitle="Governed Swedish archaeology discovery",
            description="This site is retained with explicitly unresolved chronology.",
            source_url=site.source_url,
            record_count=1,
            popup_rows=(("SEAD site ID", site.record_id),) + popup + (("Time", "Unresolved"),),
            temporal_semantics=semantics,
        )
    ]


def _readiness_tier(has_chronology: bool, has_bibliography: bool) -> str:
    if has_chronology and has_bibliography:
        return "chronology_and_bibliography_ready"
    if has_chronology:
        return "chronology_ready"
    if has_bibliography:
        return "bibliography_ready"
    return "inventory_only"


def _ranking_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _READINESS_ORDER[str(row["discovery_readiness"])],
        -int(row["chronology_kind_count"]),
        -int(row["chronology_record_count"]),
        -int(row["bibliography_count"]),
        -int(row["dataset_count"]),
        str(row["site_name"]).casefold(),
        str(row["site_id"]),
    )


def _density_count_for_point(
    longitude: float,
    latitude: float,
    payload: Mapping[str, object] | None,
) -> int | None:
    if payload is None:
        return None
    features = payload.get("features", [])
    if not isinstance(features, list):
        return None
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or not coordinates:
            continue
        ring = coordinates[0]
        if not isinstance(ring, list) or not ring:
            continue
        xs = [float(point[0]) for point in ring if isinstance(point, list) and len(point) >= 2]
        ys = [float(point[1]) for point in ring if isinstance(point, list) and len(point) >= 2]
        if xs and ys and min(xs) <= longitude < max(xs) and min(ys) <= latitude < max(ys):
            return _integer(properties.get("count"))
    return None


def _write_site_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (list, dict))
                    else value
                    for key, value in row.items()
                }
            )


def _list_count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _integer(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value))
    except ValueError:
        return 0


__all__ = [
    "DISCOVERY_CSV_NAME",
    "DISCOVERY_GEOJSON_NAME",
    "DISCOVERY_JSON_NAME",
    "DISCOVERY_LAYER_KEY",
    "DISCOVERY_LAYER_LABEL",
    "DISCOVERY_MARKDOWN_NAME",
    "SwedenArchaeologySiteDiscovery",
    "build_sweden_archaeology_site_discovery",
    "render_sweden_archaeology_site_discovery",
    "write_sweden_archaeology_site_discovery",
]
