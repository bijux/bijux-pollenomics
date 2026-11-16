"""Literal native variable fixtures pass through the maintained source producers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.boundaries import country_decisions


def generated_pair(
    root: Path,
    dimension: str,
    *,
    charcoal: bool = False,
    native_provenance: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], Path, Path, list[dict[str, Any]]]:
    """Publish a finite generated archive and its verified relational projection."""
    row = cast(dict[str, Any], download_row())
    sample = row["site"]["collectionunit"]["dataset"]["samples"][0]
    first = {
        **sample["datum"][0],
        "variableid": 501,
        "value": 2,
        "context": "unmodified",
        "symmetry": "radial",
        "taphonomics": None,
    }
    if charcoal:
        first.update(ecologicalgroup="CHAR", element="charcoal", elementtype="charcoal")
    second = {**first, "variableid": 502, "value": 3}
    if dimension == "units":
        second["units"] = "percent"
    elif dimension == "context":
        second["context"] = "prepared"
    elif dimension == "element":
        second.update(element="stomate", elementtype="stomate")
    elif dimension == "symmetry":
        second["symmetry"] = "bilateral"
    elif dimension == "taphonomics":
        second["taphonomics"] = "corroded"
    elif dimension != "native_id":
        raise AssertionError(dimension)
    if native_provenance is not None:
        for datum, provenance in zip((first, second), native_provenance, strict=True):
            for field in ("variableid", "symmetry", "taphonomics"):
                datum.pop(field, None)
            datum.update(provenance)
    sample["datum"] = [first, second]
    raw = root / "raw"
    raw.mkdir(parents=True)

    def write(path: Path, value: object) -> bytes:
        content = (
            json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode()
        path.write_bytes(content)
        return content

    parts = []
    for number in range(1, 10):
        part_rows = [row] if number == 1 else []
        ids = [201] if number == 1 else []
        part = {
            "generated_on": "2026-11-16",
            "source": "Neotoma",
            "endpoint_template": "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
            "datasettype": "pollen",
            "part_number": number,
            "part_count": 9,
            "row_count": len(part_rows),
            "downloaded_dataset_count": len(ids),
            "downloaded_dataset_ids": ids,
            "rows": part_rows,
        }
        name = f"part-{number:03d}.json"
        content = write(raw / name, part)
        parts.append(
            {
                "filename": name,
                "part_number": number,
                "row_count": len(part_rows),
                "downloaded_dataset_count": len(ids),
                "downloaded_dataset_ids": ids,
                "sha256": sha256(content).hexdigest(),
            }
        )
    write(
        raw / "manifest.json",
        {
            "generated_on": "2026-11-16",
            "source": "Neotoma",
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
            "endpoint_template": part["endpoint_template"],
            "datasettype": "pollen",
            "requested_dataset_count": 1,
            "requested_dataset_ids": [201],
            "downloaded_dataset_count": 1,
            "downloaded_dataset_ids": [201],
            "row_count": 1,
            "rows_per_part": 1,
            "part_count": 9,
            "parts": parts,
        },
    )
    rows, source = load_validated_neotoma_raw_archive(raw)
    snapshot = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=source,
        build_id="sha256:" + sha256(b"generated-variable-context-review").hexdigest(),
        country_by_site_id=country_decisions(rows),
    )
    normalized = root / "neotoma/relational"
    normalized.parent.mkdir(parents=True)
    materialize_neotoma_relational_snapshot(normalized, snapshot, rows_per_part=2)
    return cast(dict[str, Any], snapshot), raw, normalized, [first, second]
