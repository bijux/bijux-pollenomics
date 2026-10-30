"""Authenticate the explicitly projected BOKE/BUS source cohort."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import csv
import io
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)

from ..physical_forward import inputs
from ..physical_forward.inputs import Core, digest, require

TAXA = ("Betula", "Ulmus")
CORES = ("BOKE", "BUS")
FULL_TAXA = ("Betula", "Fraxinus", "Ulmus")
SWEDISH_REPORT = (
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/report.json"
)
RAW = "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
PARAMETERS = "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"


def _support(value: object) -> str:
    return digest(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    )


def project_count_core(
    native: dict[str, Any], saved: dict[str, Any], core: Core, edges: list[int]
) -> list[dict[str, Any]]:
    """Reconcile the original measured panel without selecting positive B/U effort."""
    site = native["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    require(
        (site["siteid"], unit["collectionunitid"], dataset["datasetid"], unit["handle"])
        == (core.site, core.collection_unit, core.dataset, core.id),
        "Native physical core identity differs",
    )
    chronology = saved["chronology_id"]
    models = [
        x["chronology"]
        for x in unit["chronologies"]
        if x["chronology"]["chronologyid"] == chronology
    ]
    require(
        len(models) == 1
        and models[0]["chronology"]["modelagetype"] == sources.CALIBRATED_BP
        and models[0]["chronology"] == saved["selected_chronology"]["model"]
        and len(models[0]["chroncontrols"])
        == saved["selected_chronology"]["raw_control_count"]
        and unit.get("defaultchronology") == saved["source_default_chronology"]
        and {k: v for k, v in dataset.items() if k != "samples"}
        == saved["source_dataset"],
        "Original source chronology/dataset metadata differs",
    )
    controls = json.dumps(
        models[0]["chroncontrols"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    require(
        digest(controls) == saved["selected_chronology"]["raw_control_sha256"],
        "Native chronology controls differ",
    )
    require(
        len(dataset["samples"]) == saved["native_sample_count"],
        "Native sample population differs",
    )
    require(
        len(edges) >= 2
        and all(a < b for a, b in zip(edges[:-1], edges[1:], strict=True)),
        "Strict original age edges required",
    )
    grouped: dict[tuple[float, float], list[dict[str, Any]]] = {}
    excluded = []
    seen: set[int] = set()
    for row in dataset["samples"]:
        sample = sources.pollen_counts(row)
        sid = sample["sample_id"]
        require(type(sid) is int and sid not in seen, "Duplicate native sample")
        seen.add(sid)
        age, reason = sources.selected_age(sample, chronology)
        if reason is None:
            assert age is not None
            if not edges[0] <= age["age"] < edges[-1]:
                reason = "point_age_outside_declared_windows"
        if reason is None:
            _, reason = sources.explicit_panel(sample, list(core.axis))
        if reason:
            excluded.append({"sample_id": sid, "reason": reason})
            continue
        assert age is not None
        bounds = next(
            (a, b)
            for a, b in zip(edges[:-1], edges[1:], strict=True)
            if a <= age["age"] < b
        )
        grouped.setdefault(bounds, []).append(sample)
    require(
        dict(Counter(x["reason"] for x in excluded)) == saved["exclusions_by_reason"]
        and _support(excluded) == saved["local_native_exclusions_sha256"]
        and sum(map(len, grouped.values())) == saved["included_sample_count"]
        and len(grouped) == saved["occupied_window_count"]
        and set(grouped) == {c.window for c in core.cells},
        "Original native admission/exclusion population differs",
    )
    originals = {
        inputs.window(r): r
        for r in saved["results"]
        if r["profile"] == "metadata_radius_wind_3"
    }
    require(len(originals) == len(core.cells), "Duplicate original baseline window")
    output = []
    for cell in core.cells:
        samples = grouped[cell.window]
        original = originals[cell.window]
        counts = [sum(s["counts"][name] for s in samples) for name in core.axis]
        support = [
            {
                k: s[k]
                for k in (
                    "sample_id",
                    "analysis_unit_id",
                    "depth",
                    "ages",
                    "datum_rows",
                )
            }
            for s in samples
        ]
        ages = [sources.selected_age(s, chronology)[0] for s in samples]
        missing = sum(
            a is not None and a.get("ageolder") is None and a.get("ageyounger") is None
            for a in ages
        )
        total_pollen = sum(s["reported_all_pollen_NISP_sum"] for s in samples)
        require(
            tuple(counts) == cell.counts
            and _support(support) == cell.source_support_sha256
            and len(samples) == original["native_sample_count"]
            and missing == original["raw_age_bounds_missing"]
            and total_pollen == original["reported_all_pollen_NISP_sum"],
            "Native window support/counts/denominators differ",
        )
        require(
            all(name in s["counts"] for s in samples for name in TAXA),
            "Projected taxon is unmeasured; absence cannot become zero",
        )
        projected = [counts[core.axis.index(name)] for name in TAXA]
        discarded = {
            name: counts[i] for i, name in enumerate(core.axis) if name not in TAXA
        }
        require(
            sum(counts) == sum(projected) + sum(discarded.values())
            and total_pollen >= sum(counts),
            "Panel denominator conservation failed",
        )
        output.append(
            {
                "core": core.id,
                "window_cal_bp": list(cell.window),
                "original_axis": list(core.axis),
                "original_counts": counts,
                "original_panel_N": sum(counts),
                "projected_counts": projected,
                "projected_panel_N": sum(projected),
                "discarded_original_panel_counts": discarded,
                "Fraxinus_original_panel_count": discarded.get("Fraxinus"),
                "reported_all_pollen_NISP_N": total_pollen,
                "outside_original_panel_N": total_pollen - sum(counts),
                "outside_projected_panel_N": total_pollen - sum(projected),
                "sample_ids": [s["sample_id"] for s in samples],
                "raw_age_bounds_missing": missing,
                "original_native_support_sha256": cell.source_support_sha256,
                "taxon_measured": [True, True],
            }
        )
    return output


def project_core(
    native: dict[str, Any], saved: dict[str, Any], core: Core, edges: list[int]
) -> list[dict[str, Any]]:
    """Retain the positive projected-effort contract of the point-study intake."""
    rows = project_count_core(native, saved, core, edges)
    require(
        all(row["projected_panel_N"] > 0 for row in rows),
        "Projected panel has no counted grains",
    )
    return rows


def _load_groups(
    repository: Path,
    project: Callable[
        [dict[str, Any], dict[str, Any], Core, list[int]], list[dict[str, Any]]
    ],
) -> dict[str, Any]:
    """Admit the original matched native windows without fitting new cover."""
    cores, protocol, pins = inputs.load(repository)
    selected = tuple(c for name in CORES for c in cores if c.id == name)
    require(
        len(selected) == 2
        and len({c.site for c in selected}) == 2
        and all(c.country == "SE" for c in selected),
        "Two distinct named Swedish physical places required",
    )
    pin = protocol["inputs"]["swedish_report"]
    saved = inputs.decode(
        inputs.buffer(repository / pin["path"], pin["sha256"], pin["bytes"])
    )
    declaration = saved["source_files"]
    raw = inputs.decode(sources.read_bound(repository, RAW, declaration[RAW]))
    require(raw["row_count"] == len(raw["rows"]), "Native raw row population differs")
    parameters = list(
        csv.DictReader(
            io.StringIO(
                sources.read_bound(
                    repository, PARAMETERS, declaration[PARAMETERS]
                ).decode()
            )
        )
    )
    require(len(parameters) == 31, "Original public parameter population differs")
    projected: dict[str, list[dict[str, Any]]] = {}
    metadata = []
    for core in selected:
        source = [
            r
            for r in raw["rows"]
            if r["site"]["collectionunit"]["dataset"]["datasetid"] == core.dataset
        ]
        recorded = [r for r in saved["cores"] if r["metadata_code"] == core.id]
        require(len(source) == len(recorded) == 1, "Unique native/saved core required")
        row = recorded[0]
        require(tuple(row["parameter_taxa"]) == core.axis, "Original axis differs")
        indices = [core.axis.index(name) for name in TAXA]
        ppe = [core.ppe[i] for i in indices]
        kernels = [core.kernels[i] for i in indices]
        for i, name in enumerate(TAXA):
            parameter = [
                r
                for r in parameters
                if r["Plant taxa/Pollen-morphological types"] == name
            ]
            require(len(parameter) == 1, "Literal parameter row ambiguous")
            value = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", parameter[0]["PPE (SD)"])
            require(value is not None, "Public PPE annotation unsupported")
            assert value is not None
            require(
                (float(value[1]), float(value[2]), float(parameter[0]["FSP (m/s)"]))
                == (ppe[i], core.sd[indices[i]], row["fall_speed_m_s"][indices[i]]),
                "Saved fixed parameter differs from literal source",
            )
        projected[core.id] = project(
            source[0], row, core, saved["protocol"]["age_window_edges_cal_bp"]
        )
        metadata.append(
            {
                "core": core.id,
                "native_site_id": core.site,
                "native_dataset_id": core.dataset,
                "native_collection_unit_id": core.collection_unit,
                "ppe": ppe,
                "saved_K": kernels,
                "response_PPE_times_K": [
                    e * k for e, k in zip(ppe, kernels, strict=True)
                ],
                **{
                    k: row[k]
                    for k in (
                        "chronology_id",
                        "selected_chronology",
                        "metadata_static_radius_m",
                        "metadata_disk_area_m2",
                        "historical_metadata_access_flag",
                        "native_sample_count",
                        "included_sample_count",
                        "exclusions_by_reason",
                        "local_native_exclusions_sha256",
                    )
                },
            }
        )
    require(metadata[0]["ppe"] == metadata[1]["ppe"], "Common literal PPE axis differs")
    by_core = {
        name: {tuple(r["window_cal_bp"]): r for r in rows}
        for name, rows in projected.items()
    }
    shared = sorted(set(by_core["BOKE"]) & set(by_core["BUS"]))
    groups = [
        {"window_cal_bp": list(w), "sites": [by_core[name][w] for name in CORES]}
        for w in shared
    ]
    unmatched = [
        {**row, "status": "unmatched_window_no_fit"}
        for name in CORES
        for w, row in by_core[name].items()
        if w not in shared
    ]
    require(
        len(groups) == 13
        and len(unmatched) == 6
        and all(r["core"] == "BUS" for r in unmatched),
        "Original 13 matched/six unmatched windows differ",
    )
    sample_sets = [
        {sid for g in groups for sid in g["sites"][i]["sample_ids"]} for i in range(2)
    ]
    require(
        not sample_sets[0] & sample_sets[1], "Native sample identities overlap places"
    )
    return {
        "groups": groups,
        "unmatched": unmatched,
        "cores": metadata,
        "scientific_inputs": pins
        + [{"path": name, **declaration[name]} for name in (RAW, PARAMETERS)],
        "original_source_epochs": protocol["source_epochs"],
    }


def load_groups(repository: Path) -> dict[str, Any]:
    """Admit the original positive B/U point-study input, without changing its shape."""
    return _load_groups(repository, project_core)


def load_count_groups(repository: Path) -> dict[str, Any]:
    """Read full measured counts directly; no fitted report or positive B/U selection.

    Original full-panel sample eligibility, native supports and fixed window
    membership remain in force. A Fraxinus-only BOKE window retains its positive
    full-panel effort even though its conditional B/U experiment has zero trials.
    """
    loaded = _load_groups(repository, project_count_core)
    boke = read_full_response(repository, loaded)
    bus = loaded["cores"][1]
    loaded["full_panel_responses"] = [
        {"core": "BOKE", **boke},
        {
            "core": "BUS",
            "taxa": list(TAXA),
            **{k: bus[k] for k in ("ppe", "saved_K", "response_PPE_times_K")},
        },
    ]
    for row in [*loaded["groups"], *loaded["unmatched"]]:
        for site in row.get("sites", [row]):
            site["original_taxon_measured"] = [True] * len(site["original_axis"])
            site["taxon_measured_on_common_axis"] = (
                [True, True, True] if site["core"] == "BOKE" else [True, False, True]
            )
    return loaded


def _read_pin(repository: Path, admitted: dict[str, Any], relative: str) -> bytes:
    pins = [
        p
        for p in admitted["scientific_inputs"]
        if Path(p["path"]) in (Path(relative), repository / relative)
    ]
    require(len(pins) == 1, "One original scientific source identity required")
    return sources.read_bound(repository, relative, pins[0])


def read_full_response(repository: Path, admitted: dict[str, Any]) -> dict[str, Any]:
    """Reuse the original full BOKE response and literal public Fraxinus row."""
    saved = inputs.decode(_read_pin(repository, admitted, SWEDISH_REPORT))
    cores = [c for c in saved["cores"] if c["metadata_code"] == "BOKE"]
    require(
        len(cores) == 1 and cores[0]["parameter_taxa"] == list(FULL_TAXA),
        "Original BOKE3 axis required",
    )
    core = cores[0]
    quadrature = [
        q for q in core["quadrature"] if q["profile"] == "metadata_radius_wind_3"
    ]
    require(
        len(quadrature) == 1 and len(quadrature[0]["factors"]) == 1,
        "Original saved kernel required",
    )
    ppe = inputs.numbers(core["ppe"], 3, positive=True)
    sd = inputs.numbers(core["ppe_standard_deviation"], 3, positive=False)
    speeds = inputs.numbers(core["fall_speed_m_s"], 3, positive=True)
    kernels = inputs.numbers(quadrature[0]["factors"][0], 3, positive=True)
    require(all(k <= 1 for k in kernels), "Receiver probabilities exceed one")
    require(
        admitted["cores"][0]["core"] == "BOKE"
        and admitted["cores"][0]["ppe"] == [ppe[0], ppe[2]]
        and admitted["cores"][0]["saved_K"] == [kernels[0], kernels[2]],
        "Original projected response differs",
    )
    rows = list(
        csv.DictReader(
            io.StringIO(_read_pin(repository, admitted, PARAMETERS).decode())
        )
    )
    rows = [r for r in rows if r["Plant taxa/Pollen-morphological types"] == "Fraxinus"]
    require(len(rows) == 1, "Unique literal Fraxinus parameter row required")
    match = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", rows[0]["PPE (SD)"])
    require(match is not None, "Literal Fraxinus PPE annotation unsupported")
    assert match is not None
    require(
        (float(match[1]), float(match[2]), float(rows[0]["FSP (m/s)"]))
        == (ppe[1], sd[1], speeds[1]),
        "Original Fraxinus parameter differs",
    )
    return {
        "taxa": list(FULL_TAXA),
        "ppe": ppe,
        "saved_K": kernels,
        "response_PPE_times_K": list(
            inputs.numbers(
                [e * k for e, k in zip(ppe, kernels, strict=True)], 3, positive=True
            )
        ),
        "saved_quadrature": quadrature[0],
        "source_report": SWEDISH_REPORT,
        "source_parameters": PARAMETERS,
    }
