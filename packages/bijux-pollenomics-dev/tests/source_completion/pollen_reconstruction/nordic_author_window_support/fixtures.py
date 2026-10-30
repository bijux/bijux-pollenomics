"""Portable native owners and coherent author sources without real count reads."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast


def protocol() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[6]
    result: dict[str, Any] = json.loads(
        (
            repository
            / "reports/science/pollen-reconstruction/nordic-author-window-support/protocol.json"
        ).read_bytes()
    )
    result["scope"] = result["scientific_consumer"]
    result["suppression_semantics"] = "Unavailable aggregate is not a measured zero"
    return result


def cell(name: str, code: int, value: object) -> dict[str, Any]:
    return {
        "variablename": name,
        "taxonid": code,
        "value": value,
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "context": None,
    }


def native_fixture(
    index: int = 0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = protocol()
    core = profile["cores"][index]
    owner, age = core["identity"], core["chronology"]
    samples = []
    for i in range(owner["source_sample_count"]):
        point = [2700, 3200, 3700, 4200, 4700, 5200, 5700, -1, 7][i % 9]
        ages = [
            {
                "chronologyid": age["selected_id"],
                "chronologyname": age["selected_name"],
                "agetype": age["selected_native_type"],
                "age": point,
            }
        ]
        if age["selected_id"] != age["native_collection_default_reference"]:
            ages.append(
                {
                    "chronologyid": age["native_collection_default_reference"],
                    "chronologyname": "synthetic radiocarbon alternative",
                    "agetype": "Radiocarbon years BP",
                    "age": 720,
                }
            )
        samples.append(
            {
                "sampleid": 100000 * (index + 1) + i,
                "analysisunitid": 5000000 + 1000 * index + i,
                "depth": i,
                "thickness": None,
                "ages": ages,
                "datum": [
                    cell(a["source_name"], a["taxon_id"], v)
                    for a, v in zip(core["native_axes"], [4, 2], strict=True)
                ]
                + [
                    cell("Unmapped source label", 99999, 3),
                    {
                        **cell("Volume", 99998, 0.5),
                        "element": "volume",
                        "elementtype": "volume",
                        "units": "cm3",
                    },
                ],
            }
        )
    declarations = []
    for key, flag in age["source_default_flags"].items():
        code = int(key)
        metadata = {
            "isdefault": flag,
            "chronologyname": age["selected_name"]
            if code == age["selected_id"]
            else "synthetic alternate",
            "modelagetype": age["selected_native_type"]
            if code == age["selected_id"]
            else "Radiocarbon years BP",
        }
        declarations.append(
            {
                "chronology": {
                    "chronologyid": code,
                    "chronology": metadata,
                    "chroncontrols": [{"preserved": "synthetic control"}],
                }
            }
        )
    unit = {
        "collectionunitid": owner["collection_unit_id"],
        "handle": owner["handle"],
        "defaultchronology": age["native_collection_default_reference"],
        "chronologies": declarations,
        "dataset": {
            "datasetid": owner["dataset_id"],
            "datasettype": "pollen",
            "datasetpi": [{"contactname": "Synthetic contributor"}],
            "samples": samples,
        },
    }
    site = {
        "siteid": owner["site_id"],
        "sitename": "Synthetic core",
        "dataset": {"datasetid": owner["dataset_id"], "doi": "synthetic:source"},
        "collectionunit": unit,
    }
    return {"rows": [{"site": site}]}, core, profile


def native_samples(source: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        source["rows"][0]["site"]["collectionunit"]["dataset"]["samples"],
    )


def lookup_fixture() -> list[dict[str, Any]]:
    return [
        {"row_number": i + 2, "oldvar": name, "author_target": target}
        for i, (name, target) in enumerate(
            [
                ("Betula", "Betula"),
                ("Betula", "Betula"),
                ("Pinus", "Pinus"),
                ("Pinus", "Pinus"),
                ("Pinus sylvestris", "Pinus"),
            ]
        )
    ]


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("latin-1")


def parameter_fixture() -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    names = [f"Author target {i}" for i in range(31)]
    names[4], names[20] = "Betula", "Pinus"
    means = [{"A.series": name, "alpha": "1", "vg": "0.1"} for name in names]
    means[4].update(alpha="5.10571", vg="0.024")
    means[20].update(alpha="6.05833", vg="0.031")
    cov = [
        {
            "A.series": name,
            **{other: "1" if i == j else "0" for j, other in enumerate(names)},
        }
        for i, name in enumerate(names)
    ]
    cov[4]["Betula"], cov[20]["Pinus"] = "0.092006056", "0.056016002"
    base = [
        {"oldvar": n, "RPP.LANDCLIMII": t}
        for n, t in (
            ("Betula", "Betula"),
            ("Pinus", "Pinus"),
            ("Pinus sylvestris", "Pinus"),
        )
    ]
    base += [
        {"oldvar": f"Synthetic source {i}", "RPP.LANDCLIMII": names[i % 31]}
        for i in range(9728)
    ]
    rows = base + [deepcopy(base[i % len(base)]) for i in range(1057)]
    report = {
        "schema_version": "swedish-landclim-author-parameter-binding.v1",
        "author_target_count": 31,
        "covariance_nonzero_offdiagonal_cells": 0,
        "scientific_admission_allowed": False,
        "parameters": [
            {
                "author_target": name,
                "alpha_source_text": means[i]["alpha"],
                "fall_speed_source_text": means[i]["vg"],
                "alpha_variance_source_text": cov[i][name],
            }
            for i, name in enumerate(names)
        ],
    }
    return (
        csv_bytes(["oldvar", "RPP.LANDCLIMII"], rows),
        csv_bytes(["A.series", "alpha", "vg"], means),
        csv_bytes(["A.series", *names], cov),
        report,
    )


def saved_inputs(repository: Path, originals: Path) -> tuple[dict[str, Any], Path]:
    profile = protocol()

    def store(root: Path, name: str, value: Any, raw: bool = False) -> dict[str, Any]:
        body = value if raw else json.dumps(value).encode()
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {
            "path": name,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }

    parts: dict[str, dict[str, Any]] = {}
    chronologies, units = [], []
    for index, core in enumerate(profile["cores"]):
        source, _, _ = native_fixture(index)
        parts.setdefault(core["source"]["path"], {"rows": []})["rows"].extend(
            source["rows"]
        )
        site = source["rows"][0]["site"]
        unit = site["collectionunit"]
        uid = f"neotoma:collection-unit:{core['identity']['collection_unit_id']}"
        common = {
            "collection_unit_id": uid,
            "site_id": core["physical_family"],
            "country_code": {
                "Sweden": "SE",
                "Denmark": "DK",
                "Finland": "FI",
                "Norway": "NO",
            }[core["country"]],
        }
        units.append(
            {
                **common,
                "source_collection_unit_id": unit["collectionunitid"],
                "source_payload": {"handle": unit["handle"]},
            }
        )
        for wrapper in unit["chronologies"]:
            row = wrapper["chronology"]
            chronologies.append(
                {
                    **common,
                    "source_chronology_id": row["chronologyid"],
                    "source_is_default_assertion": row["chronology"]["isdefault"],
                    "selected_by_collection_unit_reference": row["chronologyid"]
                    == unit["defaultchronology"],
                    "source_payload": {
                        k: v for k, v in row.items() if k != "chroncontrols"
                    },
                }
            )
    pins = {name: store(repository, name, body) for name, body in parts.items()}
    for core in profile["cores"]:
        core["source"] = pins[core["source"]["path"]]
    manifest = {
        "parts": [
            {
                "filename": Path(name).name,
                "downloaded_dataset_ids": [
                    r["site"]["dataset"]["datasetid"] for r in parts[name]["rows"]
                ],
            }
            for name in parts
        ]
    }
    profile["provenance"]["raw_manifest"] = store(repository, "manifest.json", manifest)
    baseline = {
        "input_artifacts": {
            "raw_archive": {
                "path": "data/neotoma/raw/neotoma_pollen_dataset_downloads",
                "manifest_sha256": profile["provenance"]["raw_manifest"]["sha256"],
                "part_sha256": {Path(k).name: v["sha256"] for k, v in pins.items()},
            }
        }
    }
    for key, value in (
        ("relational_baseline", baseline),
        (
            "count_policy",
            {
                "schema_version": "krageholm-regional-literal-panel-protocol.v1",
                "windows": profile["windows"],
                "suppression_semantics": profile["suppression_semantics"],
            },
        ),
        ("chronology_metadata", {"rows": chronologies}),
        ("collection_metadata", {"rows": units}),
    ):
        profile["provenance"][key] = store(repository, key + ".json", value)
    lookup, mean, cov, report = parameter_fixture()
    for key, body in (
        ("lookup", lookup),
        ("mean", mean),
        ("covariance", cov),
        ("driver", b"synthetic driver metadata; never execute"),
    ):
        profile["author_sources"][key] = store(
            originals, profile["author_sources"][key]["path"], body, True
        )
    report["inputs"] = [
        {
            **profile["author_sources"][key],
            "path": profile["author_sources"][key]["path"].removeprefix(
                "landclim/author-reference/"
            ),
        }
        for key in ("mean", "covariance", "driver")
    ]
    profile["provenance"]["author_parameter_binding"] = store(
        repository, "binding.json", report
    )
    path = repository / "protocol.json"
    path.write_text(json.dumps(profile))
    return profile, path
