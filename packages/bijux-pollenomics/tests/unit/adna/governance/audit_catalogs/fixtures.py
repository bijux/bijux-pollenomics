"""Typed writers for public animal report fixtures."""

from __future__ import annotations

import json
from pathlib import Path


def write_world_summary(report_root: Path, *, sheep_locality_count: int = 1) -> None:
    atlas_root = report_root / "world"
    atlas_root.mkdir(parents=True, exist_ok=True)
    (atlas_root / "README.md").write_text(
        "# World Evidence Surface\n", encoding="utf-8"
    )
    payload = {
        "animal_atlas": {
            "species_layers": [
                {
                    "latin_name": "Ovis aries",
                    "common_name": "sheep",
                    "animal_scope": "domesticated_core",
                    "locality_count": sheep_locality_count,
                },
                {
                    "latin_name": "Rangifer tarandus",
                    "common_name": "reindeer",
                    "animal_scope": "comparator",
                    "locality_count": 1,
                },
            ]
        }
    }
    (atlas_root / "world_summary.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def write_country_summary(report_root: Path) -> None:
    sweden_root = report_root / "countries" / "sweden"
    sweden_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "country-animal-adna-summary.v1",
        "country": "Sweden",
        "species_rows": [
            {
                "species_latin_name": "Ovis aries",
                "species_common_name": "sheep",
                "support_class": "accepted",
                "nordic_relevance": "nordic_lead",
            }
        ],
    }
    (sweden_root / "sweden_animal_adna_v66_summary.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
