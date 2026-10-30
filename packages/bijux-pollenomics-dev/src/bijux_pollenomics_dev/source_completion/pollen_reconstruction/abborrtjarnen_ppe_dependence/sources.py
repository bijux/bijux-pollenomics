"""Bind the current ABBO source, public parameters and declared protocol."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Any

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-ppe-dependence/protocol.json"
)
CAPTURE = "neotoma/dataset-19913/2026-10-26T185139Z/"
PARAMETERS = "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
TAXA = ("Betula", "Cyperaceae", "Juniperus communis", "Pinus sylvestris", "Poaceae")
TAXON_IDS = (29, 74, 4416, 1287, 417)
WINDOWS = (3, 4, 5, 9)


def require(condition: bool, reason: str) -> None:
    """Refuse source/analytical ambiguity before a numerical result exists."""
    if not condition:
        raise ValueError(reason)


def bound_files(root: Path, declarations: dict[str, Any]) -> dict[str, bytes]:
    """Read exact contained original files without making a dataset copy."""
    root = root.resolve(strict=True)
    result = {}
    for relative, identity in declarations.items():
        path = root / relative
        require(
            not Path(relative).is_absolute() and ".." not in Path(relative).parts,
            "Invalid source locator",
        )
        require(
            not path.is_symlink() and path.resolve(strict=True).is_relative_to(root),
            "Source escapes its owning root",
        )
        body = path.read_bytes()
        require(
            len(body) == identity["bytes"]
            and hashlib.sha256(body).hexdigest() == identity["sha256"],
            f"Changed source bytes: {relative}",
        )
        result[relative] = body
    return result


def parameter_rows(
    body: bytes, names: tuple[str, ...] = TAXA, ids: tuple[int, ...] = TAXON_IDS
) -> tuple[list[dict[str, Any]], set[str]]:
    """Use literal public row labels and unaltered bracketed SD magnitudes."""
    reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
    rows = list(reader)
    require(
        reader.fieldnames is not None and "PPE (SD)" in reader.fieldnames,
        "Published uncertainty header differs",
    )
    by_name = {
        row["Plant taxa/Pollen-morphological types"]: (i + 2, row)
        for i, row in enumerate(rows)
    }
    require(
        len(rows) == len(by_name) == 31 and len(names) == len(ids),
        "Public parameter axis differs",
    )
    parameters = []
    for name, taxon_id in zip(names, ids, strict=True):
        require(name in by_name, "Literal source parameter pairing missing")
        line, row = by_name[name]
        match = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", row["PPE (SD)"])
        require(
            match is not None
            and re.fullmatch(r"[0-9.]+", row["FSP (m/s)"]) is not None,
            "Annotated parameter needs a declared interpretation",
        )
        assert match is not None
        mean, sd, fall = float(match[1]), float(match[2]), float(row["FSP (m/s)"])
        require(
            all(math.isfinite(x) for x in (mean, sd, fall))
            and mean > 0
            and sd >= 0
            and fall > 0,
            "Invalid public parameter domain",
        )
        parameters.append(
            {
                "name": name,
                "native_taxon_id": taxon_id,
                "ppe": mean,
                "published_sd": sd,
                "fall_speed_m_s": fall,
                "source_row": line,
                "literal_ppe_sd": row["PPE (SD)"],
                "literal_fall_speed": row["FSP (m/s)"],
            }
        )
    require(
        parameters[-1]["name"] == "Poaceae"
        and parameters[-1]["ppe"] == 1
        and parameters[-1]["published_sd"] == 0,
        "Fixed relative reference differs",
    )
    return parameters, set(by_name)


def load_sources(repository: Path, source_store: Path) -> dict[str, Any]:
    """Authenticate the one current official core and its use/parameter context."""
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    require(
        tuple(protocol["taxon_axis"]) == TAXA
        and tuple(protocol["native_taxon_ids"]) == TAXON_IDS
        and tuple(protocol["window_ids"]) == WINDOWS,
        "Declared analytical axis differs",
    )
    require(
        protocol["window_width_years"] == 500
        and protocol["window_sample_counts"] == [7, 9, 8, 5]
        and protocol["physical"]["source_reported_area_ha"] == 3,
        "Declared window/area support differs",
    )
    require(
        protocol["core"]
        == {
            "dataset_id": 19913,
            "site_id": 13338,
            "collection_unit_id": 14910,
            "handle": "ABBO",
            "chronology_id": 11516,
            "native_samples": 107,
            "selected_samples": 29,
        },
        "Declared physical core differs",
    )
    original = bound_files(source_store, protocol["source_store_files"])
    public = bound_files(repository, protocol["repository_files"])
    capture = json.loads(original[CAPTURE + "capture-manifest.json"])
    require(
        capture["status"] == "complete" and len(capture["records"]) == 4,
        "Current HTTP capture is incomplete",
    )
    for record in capture["records"]:
        body = original[CAPTURE + record["body_file"]]
        require(
            record["http_status"] == 200
            and record["body_complete"] is True
            and hashlib.sha256(body).hexdigest() == record["retained_body_sha256"],
            "Current HTTP body identity differs",
        )
    download = json.loads(original[CAPTURE + "dataset-19913.download.json"])
    require(
        download["status"] == "success" and len(download["data"]) == 1,
        "Single-core source response differs",
    )
    site = download["data"][0]["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    require(
        (site["siteid"], unit["collectionunitid"], unit["handle"], dataset["datasetid"])
        == (13338, 14910, "ABBO", 19913),
        "Current native physical owner differs",
    )
    require(
        site["dataset"] == {k: v for k, v in dataset.items() if k != "samples"},
        "Current dataset metadata views differ",
    )
    metadata = json.loads(original[CAPTURE + "dataset-19913.metadata.json"])["data"][0][
        "site"
    ]
    require(
        metadata["siteid"] == 13338
        and metadata["collectionunitid"] == 14910
        and metadata["datasets"][0]["datasetid"] == 19913,
        "Current metadata physical owner differs",
    )
    require(
        dataset["database"] == "European Pollen Database"
        and dataset["doi"] == ["10.21233/2vzb-bg61"]
        and dataset["datasetpi"][0]["contactname"] == "Giesecke, Thomas",
        "Attribution source differs",
    )
    profile = (
        original["epd/pangaea/abbo-pollen-profile-pangaea-738429.tsv"]
        .split(b"*/", 1)[0]
        .decode()
    )
    require("Area: 3 ha." in profile, "Reported event-area evidence differs")
    parameters, labels = parameter_rows(public[PARAMETERS])
    return {
        "protocol": protocol,
        "site": site,
        "parameters": parameters,
        "parameter_labels": labels,
        "input_sha256": {
            **{
                f"source-store/{k}": v["sha256"]
                for k, v in protocol["source_store_files"].items()
            },
            **{
                f"repository/{k}": v["sha256"]
                for k, v in protocol["repository_files"].items()
            },
        },
    }
