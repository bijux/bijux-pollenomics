from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)

from tests.support.sead_evidence import write_sead_projection_fixture


def write_geojson(
    path: Path,
    layer_key: str,
    layer_label: str,
    category: str,
    *,
    record_id: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                "properties": {
                    "layer_key": layer_key,
                    "layer_label": layer_label,
                    "category": category,
                    "country": "Sweden",
                    "name": f"{layer_label} Record",
                    "subtitle": f"{layer_label} subtitle",
                    "description": "",
                    "source_url": "https://example.com",
                    "record_id": record_id,
                    "popup_rows": [{"label": "Source", "value": layer_label}],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_neotoma_context(context_root: Path) -> None:
    write_geojson(
        context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        layer_key="neotoma-pollen",
        layer_label="Neotoma pollen sites",
        category="Pollen",
        record_id="1",
    )
    surface_names = (
        "collection_units",
        "datasets",
        "chronologies",
        "chronology_controls",
        "samples",
        "age_claims",
        "variables",
        "observations",
        "conflicts",
        "orphans",
    )
    country_fields = (
        "sites",
        "collection_units",
        "datasets",
        "chronologies",
        "chronology_controls",
        "samples",
        "age_claim_rows",
        "observation_rows",
    )
    country_counts = {
        country_code: dict.fromkeys(country_fields, 0)
        for country_code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }
    country_counts["SE"]["sites"] = 1
    snapshot: dict[str, object] = {
        "schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:" + ("1" * 64),
        "build_id": "sha256:" + ("2" * 64),
        "sites": [
            {
                "site_id": "neotoma:site:1",
                "source_site_id": 1,
                "country_code": "SE",
                "country_decision_status": "assigned",
                "country_propagation_eligible": True,
            }
        ],
        **dict.fromkeys(surface_names, []),
        "reconciliation": {
            "normalized_row_counts": {
                surface_name: 1 if surface_name == "sites" else 0
                for surface_name in (
                    "sites",
                    "collection_units",
                    "datasets",
                    "chronologies",
                    "chronology_controls",
                    "samples",
                    "age_claims",
                    "variables",
                    "observations",
                )
            },
            "conflict_count": 0,
            "orphan_count": 0,
            "country_counts": country_counts,
            "country_attribution_counts": {
                "decision_statuses": {"assigned": 1},
                "final_country_codes": {"SE": 1},
                "propagation_eligibility": {"eligible": 1},
            },
        },
    }
    materialize_neotoma_relational_snapshot(
        (context_root / "neotoma" / "relational").absolute(), snapshot
    )


def write_sead_context(context_root: Path) -> tuple[str, str]:
    """Write a governed four-country SEAD projection fixture."""
    return write_sead_projection_fixture(context_root)
