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
        "variablename": f"Taxon {taxon}",
        "element": "pollen",
        "units": unit,
        "value": value,
    }


def authorities(
    root: Path, *, context_only_sample: int | None = None
) -> tuple[Path, Path]:
    raw, normalized = root / "raw", root / "normalized"
    parts = []
    ids = list(range(1, 10))
    for identity in ids:
        missing = datum(None, taxon=12)
        del missing["value"]
        sample = {
            "sampleid": identity * 100,
            "datum": [
                datum(0),
                datum(None, taxon=11),
                missing,
                datum(9007199254740993, taxon=13),
                datum(10.5, unit="percent", taxon=14),
            ],
            "ages": [
                {"chronologyid": 999, "agetype": "Calendar years BP", "age": 100},
                {"chronologyid": 998, "agetype": "Radiocarbon years BP", "age": 110},
            ],
        }
        if identity * 100 == context_only_sample:
            sample["ages"] = [
                {"chronologyid": 998, "agetype": "Radiocarbon years BP", "age": 110}
            ]
        row = {
            "site": {
                "siteid": identity,
                "sitename": f"Synthetic site {identity}",
                "geography": json.dumps({"type": "Point", "coordinates": [15.0, 60.0]}),
                "geopolitical": ["Sweden"],
                "collectionunit": {
                    "collectionunitid": identity,
                    "dataset": {"datasetid": identity, "samples": [sample]},
                    "chronologies": [],
                    "defaultchronology": None,
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
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
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


def observation(
    value: object, *, unit: str = "NISP", family: str = "count"
) -> dict[str, object]:
    return {
        "source_value": value,
        "source_unit": unit,
        "unit_family": family,
        "detection_status": "source_null" if value is None else "reported_value",
        "source_payload": {"value": value, "units": unit},
    }
