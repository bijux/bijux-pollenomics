"""Admit the native FLINK record and preserve literal count-row states."""

from __future__ import annotations

from copy import deepcopy
import json
import math
from typing import Any, cast

from ..physical_forward.inputs import require

SOURCE: dict[str, Any] = {
    "path": "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json",
    "sha256": "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134",
    "bytes": 24477671,
}
IDENTITY = {
    "site_id": 28889,
    "dataset_id": 54024,
    "collection_unit_id": 39258,
    "default_chronology_id": 38438,
}
TAXA = ({"label": "Betula", "taxon_id": 29}, {"label": "Ulmus", "taxon_id": 310})
WINDOWS = tuple((n, n + 500) for n in range(2700, 5700, 500))
AGE_TYPE = "Calibrated radiocarbon years BP"
NEGATIVE_SAMPLES = (552982, 552983, 552996)


def encoded(value: object) -> bytes:
    """Identify projected support without changing any native numeric type."""
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def _object(value: object) -> dict[str, Any]:
    require(
        type(value) is dict and all(type(k) is str for k in value),
        "Native object required",
    )
    return cast(dict[str, Any], value)


def _rows(value: object) -> list[dict[str, Any]]:
    require(type(value) is list, "Native row array required")
    return [_object(v) for v in cast(list[object], value)]


def _integer(value: object) -> int:
    require(
        type(value) is int and value >= 0,
        "Nonnegative integer count or identifier required",
    )
    return cast(int, value)


def _number(value: object) -> int | float:
    require(
        type(value) in (int, float) and math.isfinite(cast(float, value)),
        "Finite native age/depth required",
    )
    return cast(int | float, value)


def _age(sample: dict[str, Any], name: str) -> dict[str, Any]:
    claims = _rows(sample["ages"])
    for claim in claims:
        _integer(claim["chronologyid"])
        require(type(claim["agetype"]) is str, "Typed native age required")
        _number(claim["age"])
        for key in ("ageolder", "ageyounger"):
            if claim[key] is not None:
                _number(claim[key])
    selected = [c for c in claims if c["chronologyid"] == 38438]
    require(len(selected) == 1, "Missing or duplicate default-chronology age")
    claim = selected[0]
    require(
        claim["agetype"] == AGE_TYPE and claim["chronologyname"] == name,
        "Native age type/chronology differs",
    )
    if claim["ageyounger"] is not None:
        require(
            claim["ageyounger"] <= claim["age"], "Native younger bound exceeds point"
        )
    if claim["ageolder"] is not None:
        require(claim["ageolder"] >= claim["age"], "Native older bound precedes point")
    return deepcopy(claim)


def pollen_rows(sample: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate literal count-role cells without any count aggregation."""
    datum = _rows(sample["datum"])
    pollen: list[dict[str, Any]] = []
    for index, row in enumerate(datum):
        require(type(row["variablename"]) is str, "Literal native label required")
        _integer(row["taxonid"])
        if row["element"] != "pollen":
            continue
        require(
            row["units"] == "NISP"
            and row["elementtype"] == "pollen"
            and row["context"] is None,
            "Pollen denominator requires literal uncontextualized pollen/NISP rows",
        )
        count = _integer(row["value"])
        pollen.append(
            {
                "datum_index": index,
                **{
                    k: row[k]
                    for k in (
                        "taxonid",
                        "variablename",
                        "units",
                        "element",
                        "elementtype",
                        "context",
                    )
                },
                "value": count,
            }
        )
    return pollen


def _panel(sample: dict[str, Any]) -> dict[str, Any]:
    datum = _rows(sample["datum"])
    pollen = pollen_rows(sample)
    keys = [(row["taxonid"], row["variablename"]) for row in pollen]
    duplicate_pollen = len(set(keys)) != len(keys)
    states = []
    counts: list[int | None] = []
    for taxon in TAXA:
        matches = [
            {
                "datum_index": i,
                **{
                    k: row[k]
                    for k in (
                        "taxonid",
                        "variablename",
                        "units",
                        "element",
                        "elementtype",
                        "context",
                        "value",
                    )
                },
            }
            for i, row in enumerate(datum)
            if row["variablename"] == taxon["label"]
        ]
        selected_count: int | None = None
        if not matches:
            status = "missing_literal"
        elif len(matches) != 1:
            status = "duplicate_literal"
        else:
            row = matches[0]
            if (
                row["taxonid"] != taxon["taxon_id"]
                or row["units"] != "NISP"
                or row["element"] != "pollen"
                or row["elementtype"] != "pollen"
                or row["context"] is not None
            ):
                status = "incompatible_literal"
            else:
                selected_count = _integer(row["value"])
                status = "measured_zero" if selected_count == 0 else "measured"
        states.append({**taxon, "status": status, "native_matches": matches})
        counts.append(selected_count)
    complete = all(n is not None for n in counts) and not duplicate_pollen
    pollen_n = None if duplicate_pollen else sum(row["value"] for row in pollen)
    panel_n = sum(cast(list[int], counts)) if complete else None
    return {
        "literal_states": states,
        "panel_complete": complete,
        "panel_counts": counts,
        "panel_N": panel_n,
        "native_pollen_NISP_rows": pollen,
        "pollen_denominator_status": "duplicate_native_pollen_rows"
        if duplicate_pollen
        else "complete",
        "pollen_N": pollen_n,
        "excluded_pollen_N": pollen_n - panel_n
        if pollen_n is not None and panel_n is not None
        else None,
    }


def read_native(
    source_object: dict[str, Any], protocol: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Admit the exact native record/typed cells without projection arithmetic."""
    require(
        protocol["schema_version"] == "flink-native-panel-projection.v1",
        "Wrong projection protocol",
    )
    require(
        protocol["source"] == SOURCE and protocol["identity"] == IDENTITY,
        "Exact FLINK source identity required",
    )
    require(
        protocol["taxa"] == list(TAXA)
        and protocol["windows"] == [list(w) for w in WINDOWS],
        "Literal panel/window axis differs",
    )
    require(
        protocol["age"]["native_type"] == AGE_TYPE
        and protocol["age"]["reference_epoch_ad"] == 1950,
        "Explicit source BP convention required",
    )
    expected = protocol["sample_ids"]
    require(
        type(expected) is list
        and len(expected) == 109
        and all(type(n) is int for n in expected)
        and len(set(expected)) == 109,
        "Exact native sample axis required",
    )
    require(
        protocol["negative_age_sample_ids"] == list(NEGATIVE_SAMPLES),
        "Native negative-age axis differs",
    )
    sites = [_object(row["site"]) for row in _rows(source_object["rows"])]
    selected = [s for s in sites if _object(s["dataset"])["datasetid"] == 54024]
    require(len(selected) == 1, "Missing or duplicate selected dataset")
    site = selected[0]
    require(
        type(site["siteid"]) is int and site["siteid"] == 28889,
        "Selected native site differs",
    )
    unit = _object(site["collectionunit"])
    require(
        type(unit["collectionunitid"]) is int
        and unit["collectionunitid"] == 39258
        and unit["handle"] == "FLINK",
        "Selected collection unit differs",
    )
    dataset = _object(unit["dataset"])
    require(
        type(dataset["datasetid"]) is int
        and dataset["datasetid"] == 54024
        and dataset["datasettype"] == "pollen",
        "Nested dataset differs",
    )
    require(
        type(unit["defaultchronology"]) is int and unit["defaultchronology"] == 38438,
        "Native default chronology differs",
    )
    chronologies = [_object(row["chronology"]) for row in _rows(unit["chronologies"])]
    selected_chronologies = [c for c in chronologies if c["chronologyid"] == 38438]
    defaults = [
        c for c in chronologies if _object(c["chronology"])["isdefault"] is True
    ]
    require(
        len(selected_chronologies) == len(defaults) == 1
        and defaults[0] == selected_chronologies[0],
        "Missing or ambiguous native default chronology",
    )
    chronology = _object(selected_chronologies[0]["chronology"])
    require(
        chronology["modelagetype"] == AGE_TYPE
        and type(chronology["chronologyname"]) is str,
        "Native model age type differs",
    )
    samples = _rows(dataset["samples"])
    require(
        [s["sampleid"] for s in samples] == expected
        and all(type(s["sampleid"]) is int for s in samples),
        "Native sample population/order differs",
    )
    for sample in samples:
        _age(sample, chronology["chronologyname"])
        _integer(sample["analysisunitid"])
        _number(sample["depth"])
        if sample["thickness"] is not None:
            _number(sample["thickness"])
        pollen_rows(sample)
    return selected_chronologies[0], samples
