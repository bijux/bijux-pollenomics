"""Synthetic source receipts built by the existing source-owned producers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)


def write_json(path: Path, value: object) -> bytes:
    content = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def datum(value: object, *, unit: str = "NISP", taxon: int = 10) -> dict[str, Any]:
    return {
        "taxonid": taxon,
        "variablename": "Alnus" if taxon == 10 else "Betula",
        "element": "pollen",
        "elementtype": "pollen",
        "units": unit,
        "value": value,
    }


def authorities(
    root: Path,
    *,
    synthetic: bool = True,
    omitted_marker_part: int | None = None,
    first_value: object = 0,
    unit: str = "NISP",
    age_type: str = "Calendar years BP",
) -> tuple[Path, Path]:
    raw, normalized = root / "raw", root / "normalized"
    parts = []
    ids = list(range(1, 10))
    for identity in ids:
        sample = {
            "sampleid": identity * 100,
            "datum": [
                datum(first_value if identity == 1 else 70, unit=unit),
                datum(100 if identity == 1 else 30, taxon=11),
            ],
            "ages": [
                {
                    "chronologyid": 999,
                    "agetype": age_type,
                    "ageyounger": 5400,
                    "ageolder": 5600,
                },
            ],
        }
        row = {
            "site": {
                "siteid": identity,
                "sitename": f"Synthetic site {identity}",
                "geography": json.dumps({"type": "Point", "coordinates": [15.0, 60.0]}),
                "geopolitical": ["Sweden"],
                "collectionunit": {
                    "collectionunitid": identity,
                    "dataset": {"datasetid": identity, "samples": [sample]},
                    "chronologies": [
                        {
                            "chronology": {
                                "chronologyid": 999,
                                "chronology": {"isdefault": True},
                            }
                        }
                    ],
                    "defaultchronology": 999,
                },
                "dataset": {"datasetid": identity},
            }
        }
        filename = f"part-{identity:03d}.json"
        part = {
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "endpoint_template": "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
            "datasettype": "pollen",
            "part_number": identity,
            "part_count": 9,
            "row_count": 1,
            "downloaded_dataset_count": 1,
            "downloaded_dataset_ids": [identity],
            "rows": [row],
        }
        if synthetic and identity != omitted_marker_part:
            part.update(
                data_kind="synthetic", synthetic_fixture_id="neotoma-lra-fixture.v1"
            )
        content = write_json(raw / filename, part)
        parts.append(
            {
                "filename": filename,
                "part_number": identity,
                "row_count": 1,
                "downloaded_dataset_count": 1,
                "downloaded_dataset_ids": [identity],
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    write_json(
        raw / "manifest.json",
        {
            **(
                {
                    "data_kind": "synthetic",
                    "synthetic_fixture_id": "neotoma-lra-fixture.v1",
                }
                if synthetic
                else {}
            ),
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
            "synthetic_country_by_site_id": {str(identity): "SE" for identity in ids},
            "endpoint_template": "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
            "datasettype": "pollen",
            "requested_dataset_count": 9,
            "requested_dataset_ids": ids,
            "downloaded_dataset_count": 9,
            "downloaded_dataset_ids": ids,
            "row_count": 9,
            "rows_per_part": 1,
            "part_count": 9,
            "parts": parts,
        },
    )
    rows, source_id = load_validated_neotoma_raw_archive(raw)
    snapshot = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=source_id,
        build_id="synthetic-test-build",
        country_by_site_id=dict.fromkeys(ids, "SE"),
    )
    materialize_neotoma_relational_snapshot(normalized, snapshot, rows_per_part=3)
    return raw, normalized
