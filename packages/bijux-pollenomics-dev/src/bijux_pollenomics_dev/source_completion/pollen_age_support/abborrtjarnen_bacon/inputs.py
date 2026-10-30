"""Bind the six native dates and frozen sample/count/prediction identities."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import numpy as np
from numpy.typing import NDArray

from .. import abborrtjarne_membership as ledger
from ..depth_order import abborrtjarne_prediction_sensitivity as frozen
from ..legacyage_run_inputs import ARCHIVE_SHA256, MEMBERS

PROTOCOL = Path(
    "reports/science/chronology/abborrtjarnen-bacon/physical-rate-protocol.json"
)
CURVE_SHA256 = "0e03064baac546e7b67fca62b8e2365deabd8ee0a66881ad93aeb83e1c423eed"
FULL_CURVE_SHA256 = "974a66649f2ac8a53e6c99e256b019ac6982f999b12dcf7193162d4c1c09168e"


@dataclass(frozen=True)
class CoreInputs:
    """One immutable native sample axis and its fixed evaluation quantities."""

    protocol: dict[str, Any]
    controls: tuple[dict[str, Any], ...]
    sample_ids: tuple[str, ...]
    depths: NDArray[np.float64]
    counts: NDArray[np.int64]
    predictions: NDArray[np.float64]
    fit_identities: list[dict[str, Any]]


def read_inputs(repository: Path, source_root: Path) -> CoreInputs:
    """Use original metadata and native counts without old marginal-age constraints."""
    protocol = json.loads((repository / PROTOCOL).read_text())
    buffers = {}
    for relative, expected in frozen.INPUTS.items():
        body = (repository / relative).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError(f"Frozen scientific input differs: {relative}")
        buffers[relative] = body
    if protocol["source_inputs"] != {str(k): v for k, v in frozen.INPUTS.items()}:
        raise ValueError("Protocol and frozen source identities differ")
    rows, _ = frozen._support(buffers[ledger.SUPPORT])
    # Only identity/count fields are used; the ledger's old S5 bounds never
    # constrain the new model or its draws.
    native = frozen._json(buffers[frozen.RAW])
    counts = frozen._native_counts(native, rows)
    rows.sort(key=lambda row: Decimal(row["depth_cm"]))
    ids = tuple(row["sample_id"] for row in rows)
    depths = np.asarray([float(row["depth_cm"]) for row in rows])
    sites = [
        row["site"]
        for row in native["rows"]
        if row["site"]["dataset"]["datasetid"] == 19913
    ]
    unit = sites[0]["collectionunit"]
    if unit["collectionunitid"] != 14910 or unit["handle"] != "ABBO":
        raise ValueError("Native physical collection unit differs")
    chronologies = unit["chronologies"]
    if len(chronologies) != 1 or chronologies[0]["chronology"]["chronologyid"] != 11516:
        raise ValueError("Native chronology-control owner differs")
    native_controls = chronologies[0]["chronology"]["chroncontrols"]
    dated = {
        row["geochron"]["labnumber"]: row
        for row in native_controls
        if row["geochron"]["labnumber"] is not None
    }
    archive = source_root / "legacyage/zenodo-5815192/input-metadata-tables.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("LegacyAge original metadata archive differs")
    selected = {}
    with ZipFile(archive) as zipped:
        for name in ("S1", "S3"):
            with (
                zipped.open(MEMBERS[name]) as stream,
                io.TextIOWrapper(stream, encoding="cp1252", newline="") as text,
            ):
                selected[name] = [
                    row
                    for row in csv.DictReader(text, delimiter=";")
                    if row["Dataset_ID"] == "19913"
                ]
    source = selected["S1"]
    expected_settings = {
        "Marine": "FALSE",
        "Memory": "0.3",
        "Add.surface": "TRUE",
        "Resolution.cm": "5",
        "Waterline": "648",
        "Starting.age": "-52",
        "Reservoir": "NA",
    }
    if len(selected["S3"]) != 1 or any(
        selected["S3"][0][key] != value for key, value in expected_settings.items()
    ):
        raise ValueError("Source chronology settings differ from the declared profile")
    if (
        len(source) != 6
        or len(dated) != 6
        or {row["Laboratory_Label"] for row in source} != dated.keys()
    ):
        raise ValueError("Exactly six original ABBO radiocarbon controls required")
    controls: list[dict[str, Any]] = []
    for row in source:
        lab = row["Laboratory_Label"]
        match = dated.get(lab)
        if match is None or row["Dating_Method"] != "Carbon-14":
            raise ValueError("Unmatched native ABBO radiocarbon control")
        geochron = match["geochron"]
        age = Decimal(row["Age_Uncalibrated (kyr BP)"]) * 1000
        older = Decimal(row["Dating Error_Older (kyr)"]) * 1000
        younger = Decimal(row["Dating Error_Younger (kyr)"]) * 1000
        depth = Decimal(row["Depth (cm)"])
        if (depth, age, older, younger) != tuple(
            Decimal(str(x))
            for x in (
                match["depth"],
                geochron["geochronage"],
                geochron["geochronerrorolder"],
                geochron["geochronerroryounger"],
            )
        ):
            raise ValueError("Original metadata and native dating values differ")
        controls.append(
            {
                "sample_id": lab,
                "age": float(age),
                "error": float((older + younger) / 2),
                "depth": float(depth),
                "cc": 1,
                "source_material": row["Material_Dated"],
            }
        )
    tops = [row for row in native_controls if row["chroncontroltype"] == "Core top"]
    if len(tops) != 1 or (tops[0]["depth"], tops[0]["chroncontrolage"]) != (648, -52):
        raise ValueError("Source-declared surface anchor differs")
    controls.append(
        {
            "sample_id": "source-surface-anchor",
            "age": -52.0,
            "error": 30.0,
            "depth": 648.0,
            "cc": 0,
            "source_material": "artificial calendar anchor, not radiocarbon measurement",
        }
    )
    controls.sort(key=lambda row: row["depth"])
    predictions, fits = frozen._predictions(
        frozen._json(buffers[frozen.PREDICTIONS]), frozen._json(buffers[ledger.CONFIG])
    )
    return CoreInputs(
        protocol,
        tuple(controls),
        ids,
        depths,
        np.asarray([counts[sample] for sample in ids], dtype=np.int64),
        np.asarray(
            [[predictions[b][method] for b in frozen.BINS] for method in frozen.METHODS]
        ),
        fits,
    )
