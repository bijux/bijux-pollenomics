"""Read native ABBO measurements and reconstruct every age-defined window."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

AXIS = ("Betula", "Cyperaceae", "Juniperus communis", "Pinus sylvestris", "Poaceae")
TAXON_IDS = (29, 74, 4416, 1287, 417)
BINS = (3, 4, 5, 9)


@dataclass(frozen=True)
class Sample:
    sample_id: int
    depth: float
    panel: tuple[int | None, ...]
    reported_nisp: int
    point_age: float | None = None


@dataclass(frozen=True)
class Membership:
    sample_ids: tuple[int, ...]
    missing: dict[int, tuple[str, ...]]
    reported_nisp: int
    panel_subtotal: int
    pooled: tuple[int, ...] | None
    status: str


def native_samples(source_root: Path) -> dict[int, Sample]:
    """Use the captured provider body, not producer-created selected matrices."""
    path = (
        source_root
        / "neotoma/dataset-19913/2026-10-26T185139Z/dataset-19913.download.json"
    )
    body = json.loads(path.read_text())
    site = body["data"][0]["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    if (
        body["status"] != "success"
        or len(body["data"]) != 1
        or (
            site["siteid"],
            unit["collectionunitid"],
            unit["handle"],
            dataset["datasetid"],
        )
        != (13338, 14910, "ABBO", 19913)
    ):
        raise ValueError("Native physical identities differ")
    result = {}
    for source in dataset["samples"]:
        sample_id = source["sampleid"]
        pollen = [
            d for d in source["datum"] if d["element"] == d["elementtype"] == "pollen"
        ]
        if (
            type(sample_id) is not int
            or sample_id in result
            or any(
                d["units"] != "NISP" or type(d["value"]) is not int or d["value"] < 0
                for d in pollen
            )
        ):
            raise ValueError("Native sample or pollen measurement differs")
        named = {d["variablename"]: d for d in pollen}
        if len(named) != len(pollen) or any(
            name in named and named[name]["taxonid"] != taxon_id
            for name, taxon_id in zip(AXIS, TAXON_IDS, strict=True)
        ):
            raise ValueError("Native taxon identity is ambiguous")
        depth = source["depth"]
        if type(depth) not in (int, float) or not np.isfinite(depth):
            raise ValueError("Native sample depth is unresolved")
        ages = [a for a in source["ages"] if a["chronologyid"] == 11516]
        point_age = (
            ages[0]["age"]
            if len(ages) == 1
            and ages[0]["agetype"] == "Calibrated radiocarbon years BP"
            and type(ages[0]["age"]) in (int, float)
            and np.isfinite(ages[0]["age"])
            else None
        )
        result[sample_id] = Sample(
            sample_id,
            depth,
            tuple(named[name]["value"] if name in named else None for name in AXIS),
            sum(d["value"] for d in pollen),
            point_age,
        )
    if len(result) != 107:
        raise ValueError("Native sample census differs")
    return result


def check_accounts(saved: list[dict[str, Any]], samples: dict[int, Sample]) -> None:
    """Validate the complete native census without importing a selection mask."""
    if len(saved) != len(samples) or {r["sample_id"] for r in saved} != set(samples):
        raise ValueError("Saved native sample census differs")
    for actual in saved:
        sample = samples[actual["sample_id"]]
        missing = [
            name for name, n in zip(AXIS, sample.panel, strict=True) if n is None
        ]
        subtotal = sum(n for n in sample.panel if n is not None)
        expected = {
            "sample_id": sample.sample_id,
            "depth_native": sample.depth,
            "source_point_age_bp": sample.point_age,
            "source_chronology_id": 11516,
            "missing_taxa": missing,
            "reported_panel_subtotal": subtotal,
            "panel_mass": None if missing else subtotal,
            "all_reported_pollen_nisp": sample.reported_nisp,
            "omitted_reported_pollen_nisp": sample.reported_nisp - subtotal,
        }
        if actual != expected:
            raise ValueError("Saved native sample measurement account differs")


def public_parameters(
    repository: Path, saved: list[dict[str, Any]]
) -> tuple[np.ndarray, np.ndarray]:
    """Validate literal published means and marginal SDs without fitting a law."""
    with (
        repository / "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    ).open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or reader.fieldnames[-1] != "PPE (SD)":
            raise ValueError("Published uncertainty heading differs")
        rows = list(reader)
    by_name = {
        r["Plant taxa/Pollen-morphological types"]: (i + 2, r)
        for i, r in enumerate(rows)
    }
    if len(rows) != len(by_name) or len(saved) != len(AXIS):
        raise ValueError("Published parameter axis differs")
    ppe, sd = [], []
    for actual, name, taxon_id in zip(saved, AXIS, TAXON_IDS, strict=True):
        line, row = by_name[name]
        token = re.fullmatch(r"([\d.]+) \(([\d.]+)\)", row["PPE (SD)"])
        if token is None:
            raise ValueError("Published PPE/SD token differs")
        expected = {
            "name": name,
            "native_taxon_id": taxon_id,
            "ppe": float(token[1]),
            "published_sd": float(token[2]),
            "fall_speed_m_s": float(row["FSP (m/s)"]),
            "source_row": line,
            "literal_ppe_sd": row["PPE (SD)"],
            "literal_fall_speed": row["FSP (m/s)"],
        }
        if actual != expected:
            raise ValueError("Published parameter pairing differs")
        ppe.append(float(token[1]))
        sd.append(float(token[2]))
    return np.asarray(ppe), np.asarray(sd)


def memberships(
    ages: np.ndarray, sample_ids: tuple[int, ...], samples: dict[int, Sample]
) -> tuple[Membership, ...]:
    """Retain all native members; missing axes invalidate rather than disappear."""
    if (
        ages.shape != (len(sample_ids),)
        or not np.all(np.isfinite(ages))
        or len(set(sample_ids)) != len(sample_ids)
        or set(sample_ids) != set(samples)
    ):
        raise ValueError("Native age/sample axis differs")
    result = []
    for window in BINS:
        selected = [
            samples[sample_id]
            for sample_id, age in zip(sample_ids, ages, strict=True)
            if 500 * window <= age < 500 * (window + 1)
        ]
        missing = {
            sample.sample_id: tuple(
                name for name, n in zip(AXIS, sample.panel, strict=True) if n is None
            )
            for sample in selected
            if any(n is None for n in sample.panel)
        }
        subtotal = sum(n for sample in selected for n in sample.panel if n is not None)
        pooled = (
            None
            if missing
            else tuple(
                sum(sample.panel[j] or 0 for sample in selected)
                for j in range(len(AXIS))
            )
        )
        status = (
            "refused_empty_window"
            if not selected
            else "refused_missing_explicit_panel"
            if missing
            else "refused_zero_panel"
            if not subtotal
            else "defined"
        )
        result.append(
            Membership(
                tuple(sample.sample_id for sample in selected),
                missing,
                sum(sample.reported_nisp for sample in selected),
                subtotal,
                pooled,
                status,
            )
        )
    return tuple(result)
