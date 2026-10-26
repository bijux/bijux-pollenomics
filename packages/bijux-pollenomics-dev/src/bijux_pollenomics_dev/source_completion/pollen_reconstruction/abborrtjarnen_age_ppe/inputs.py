"""Keep original five-taxon measurements distinct from age-dependent membership."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ..abborrtjarnen_ppe_dependence.inputs import native_counts, source_age
from ..abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    WINDOWS,
    load_sources,
    require,
)
from .chronology import PROTOCOL, authority


def prepare(repository: Path, source_root: Path) -> dict[str, Any]:
    """Join all 107 exact native IDs/depths; do not import the closed16 mask."""
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    require(
        protocol["taxon_axis"] == list(TAXA)
        and protocol["native_taxon_ids"] == list(TAXON_IDS)
        and protocol["window_ids"] == list(WINDOWS),
        "Frozen five-taxon/window axes differ",
    )
    core, qualified = authority(repository, protocol)
    original = load_sources(repository, source_root)
    unit = original["site"]["collectionunit"]
    raw = unit["dataset"]["samples"]
    require(
        len(raw) == len({s["sampleid"] for s in raw}) == 107,
        "Native sample population differs",
    )
    selected = [
        c["chronology"]
        for c in unit["chronologies"]
        if c["chronology"]["chronologyid"] == 11516
    ]
    require(
        len(selected) == 1
        and selected[0]["chronology"]["modelagetype"]
        == "Calibrated radiocarbon years BP",
        "Original source point chronology differs",
    )
    by_id = {f"neotoma:sample:{s['sampleid']}": s for s in raw}
    ids = core["sample_ids"]
    require(
        len(ids) == len(set(ids)) == 107 and set(ids) == set(by_id),
        "Qualified chronology/native sample axes differ",
    )
    samples = []
    accounts = []
    for identifier, depth in zip(ids, core["depths"], strict=True):
        sample = by_id[identifier]
        require(
            type(sample["depth"]) in (int, float)
            and math.isfinite(sample["depth"])
            and float(sample["depth"]) == depth,
            "Sample depth/model axis differs",
        )
        counts, age = native_counts(sample), source_age(sample)
        record = {
            "sample_id": sample["sampleid"],
            "depth_native": sample["depth"],
            "source_point_age_bp": None if age is None else age["age"],
            "source_chronology_id": 11516,
            "missing_taxa": counts["missing"],
            "reported_panel_subtotal": counts["panel_subtotal"],
            "panel_mass": None if counts["vector"] is None else sum(counts["vector"]),
            "all_reported_pollen_nisp": counts["all_nisp"],
            "omitted_reported_pollen_nisp": counts["all_nisp"]
            - counts["panel_subtotal"],
        }
        accounts.append(record)
        samples.append({**record, "counts": counts["vector"]})
    require(
        sum(not r["missing_taxa"] for r in accounts) == 99
        and sum(bool(r["missing_taxa"]) for r in accounts) == 8,
        "Frozen explicit-panel source support differs",
    )
    old = json.loads((repository / protocol["physical_response_input"]).read_bytes())
    require(
        old["parameters"] == original["parameters"]
        and [r["taxon"] for r in old["physical_response"]] == list(TAXA),
        "Existing five-taxon physical input axes differ",
    )
    require(
        protocol["physical"] == original["protocol"]["physical"],
        "Fixed source geometry/transport differs",
    )
    return {
        "protocol": protocol,
        "source_protocol": original["protocol"],
        "parameters": original["parameters"],
        "physical_response": old["physical_response"],
        "deposition": np.array([r["factor"] for r in old["physical_response"]]),
        "sample_ids": ids,
        "samples": samples,
        "sample_accounts": accounts,
        "age_authority": qualified,
        "fixed_age_reference": old["windows"],
        "input_sha256": {
            **original["input_sha256"],
            **{
                f"repository/{k}": v["sha256"]
                for k, v in protocol["repository_inputs"].items()
            },
        },
    }


def membership(
    samples: list[dict[str, Any]], ages: list[float], bin_id: int
) -> tuple[dict[str, Any], tuple[int, ...] | None]:
    """A single missing-axis member refuses the whole bin, without zero fill."""
    require(
        len(samples) == len(ages) and all(math.isfinite(a) for a in ages),
        "Source/age axes differ",
    )
    members = [
        s
        for s, a in zip(samples, ages, strict=True)
        if 500 * bin_id <= a < 500 * (bin_id + 1)
    ]
    missing = {
        str(s["sample_id"]): s["missing_taxa"] for s in members if s["missing_taxa"]
    }
    subtotal = sum(s["reported_panel_subtotal"] for s in members)
    mass = None if missing else subtotal
    status = (
        "empty_native_window"
        if not members
        else "missing_explicit_five_taxon_member"
        if missing
        else "nonempty_zero_panel_mass"
        if mass == 0
        else "defined"
    )
    record = {
        "status": status,
        "sample_ids": [s["sample_id"] for s in members],
        "sample_count": len(members),
        "reported_panel_subtotal": subtotal,
        "panel_mass": mass,
        "all_reported_pollen_nisp": sum(s["all_reported_pollen_nisp"] for s in members),
        "omitted_reported_pollen_nisp": sum(
            s["omitted_reported_pollen_nisp"] for s in members
        ),
        "missing_members": missing,
    }
    counts = (
        None
        if status != "defined"
        else tuple(sum(s["counts"][i] for s in members) for i in range(5))
    )
    return record, counts
