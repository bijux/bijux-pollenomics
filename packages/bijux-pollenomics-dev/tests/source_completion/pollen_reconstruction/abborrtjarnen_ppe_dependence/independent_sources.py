"""Reconstruct the native ABBO panel and public PPE facts from original sources."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from .independent_moments import Rational, _fraction, _require

AXIS = ("Betula", "Cyperaceae", "Juniperus communis", "Pinus sylvestris", "Poaceae")
TAXON_IDS = (29, 74, 4416, 1287, 417)
BINS = (3, 4, 5, 9)
PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-ppe-dependence/protocol.json"
)


def _native_inputs(
    repository: Path,
    source_root: Path,
    protocol: dict[str, Any],
    result: dict[str, Any],
) -> tuple[dict[int, tuple[int, ...]], Rational, Rational]:
    """Rebuild the four native panels from the captured provider response."""
    expected_hashes = {}
    for namespace, root, pins in (
        ("repository", repository, protocol["repository_files"]),
        ("source-store", source_root, protocol["source_store_files"]),
    ):
        for relative, pin in pins.items():
            member = Path(relative)
            _require(
                not member.is_absolute() and ".." not in member.parts,
                "Unsafe source member",
            )
            body = (root / member).read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            _require(
                len(body) == pin["bytes"] and digest == pin["sha256"],
                "Source identity changed",
            )
            expected_hashes[f"{namespace}/{relative}"] = digest
    _require(
        result["input_sha256"] == expected_hashes, "Result source identities differ"
    )
    with (
        repository / "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    ).open(newline="") as stream:
        reader = csv.DictReader(stream)
        _require(
            reader.fieldnames is not None and reader.fieldnames[-1] == "PPE (SD)",
            "Source uncertainty header differs",
        )
        rows = list(reader)
    published = {
        r["Plant taxa/Pollen-morphological types"]: (i + 2, r)
        for i, r in enumerate(rows)
    }
    _require(len(published) == len(rows) == 31, "Public parameter identities differ")
    for actual, name, taxon_id in zip(
        result["parameters"], AXIS, TAXON_IDS, strict=True
    ):
        line, row = published[name]
        pair = re.fullmatch(r"([\d.]+) \(([\d.]+)\)", row["PPE (SD)"])
        _require(pair is not None, "Literal PPE/SD token differs")
        assert pair is not None
        expected = {
            "name": name,
            "native_taxon_id": taxon_id,
            "ppe": float(pair[1]),
            "published_sd": float(pair[2]),
            "fall_speed_m_s": float(row["FSP (m/s)"]),
            "source_row": line,
            "literal_ppe_sd": row["PPE (SD)"],
            "literal_fall_speed": row["FSP (m/s)"],
        }
        _require(actual == expected, "Literal parameter pairing or magnitude differs")
    ppe = tuple(_fraction(r["ppe"]) for r in result["parameters"])
    sd = tuple(_fraction(r["published_sd"]) for r in result["parameters"])
    capture = "neotoma/dataset-19913/2026-10-26T185139Z/dataset-19913.download.json"
    source = json.loads((source_root / capture).read_text())
    _require(
        source["status"] == "success" and len(source["data"]) == 1,
        "Native response differs",
    )
    site = source["data"][0]["site"]
    unit = site["collectionunit"]
    _require(
        (
            site["siteid"],
            unit["collectionunitid"],
            unit["handle"],
            unit["dataset"]["datasetid"],
        )
        == (13338, 14910, "ABBO", 19913),
        "Native physical identities differ",
    )
    samples = unit["dataset"]["samples"]
    _require(
        len(samples) == len({r["sampleid"] for r in samples}) == 107,
        "Native sample population differs",
    )
    account = {r["sample_id"]: r for r in result["sample_account"]}
    _require(
        len(account) == len(result["sample_account"]) == 107
        and set(account) == {r["sampleid"] for r in samples},
        "Saved sample population differs",
    )
    grouped: dict[int, list[tuple[dict[str, Any], tuple[int, ...], dict[str, Any]]]] = {
        b: [] for b in BINS
    }
    common = set(published)
    for sample in samples:
        pollen = [
            d for d in sample["datum"] if d["element"] == d["elementtype"] == "pollen"
        ]
        _require(
            all(
                d["units"] == "NISP" and type(d["value"]) is int and d["value"] >= 0
                for d in pollen
            ),
            "Native pollen measurement differs",
        )
        by_name = {d["variablename"]: d for d in pollen}
        _require(len(by_name) == len(pollen), "Duplicate pollen label")
        missing = [name for name in AXIS if name not in by_name]
        for name, taxon_id in zip(AXIS, TAXON_IDS, strict=True):
            _require(
                name not in by_name or by_name[name]["taxonid"] == taxon_id,
                "Native taxon identity differs",
            )
        subtotal = sum(by_name[name]["value"] for name in AXIS if name in by_name)
        nisp = sum(d["value"] for d in pollen)
        ages = [a for a in sample["ages"] if a["chronologyid"] == 11516]
        age = (
            ages[0]
            if len(ages) == 1
            and ages[0]["agetype"] == "Calibrated radiocarbon years BP"
            and type(ages[0]["age"]) in (int, float)
            and math.isfinite(ages[0]["age"])
            else None
        )
        value = age["age"] if age is not None else None
        bins = [
            b for b in BINS if value is not None and 500 * b <= value < 500 * (b + 1)
        ]
        _require(len(bins) <= 1, "Requested time support overlaps")
        window = bins[0] if bins else None
        status = (
            "refused_named_source_age"
            if age is None
            else "outside_requested_windows"
            if window is None
            else "refused_missing_explicit_panel"
            if missing
            else "refused_zero_panel"
            if not subtotal
            else "selected_complete_panel"
        )
        expected = {
            "sample_id": sample["sampleid"],
            "depth_native": sample["depth"],
            "depth_unit": "native_depth_unit_not_explicit_in_payload",
            "source_age_bp": value,
            "chronology_id": 11516 if age is not None else None,
            "source_age_type": age["agetype"] if age is not None else None,
            "assumed_age_reference_year_ce": 1950 if age is not None else None,
            "raw_age_bounds": {"younger": age["ageyounger"], "older": age["ageolder"]}
            if age is not None
            else None,
            "status": status,
            "window_id": window,
            "panel_missing_taxa": missing,
            "panel_count_total": None if missing else subtotal,
            "reported_panel_subtotal": subtotal,
            "all_reported_pollen_nisp": nisp,
            "omitted_reported_pollen_nisp": nisp - subtotal,
            "excluded_nonpollen_rows": len(sample["datum"]) - len(pollen),
        }
        _require(
            account[sample["sampleid"]] == expected,
            "Saved native sample disposition differs",
        )
        if status == "selected_complete_panel":
            assert window is not None
            common.intersection_update(by_name)
            vector = tuple(by_name[name]["value"] for name in AXIS)
            grouped[window].append((sample, vector, expected))
    _require(
        common == set(AXIS) and [len(grouped[b]) for b in BINS] == [7, 9, 8, 5],
        "Maximal literal panel or selected population differs",
    )
    pooled = {}
    _require(
        [w["window_id"] for w in result["windows"]] == list(BINS),
        "Window order differs",
    )
    for row in result["windows"]:
        b = row["window_id"]
        members = sorted(grouped[b], key=lambda item: item[0]["sampleid"])
        n = tuple(sum(vector[j] for _, vector, _ in members) for j in range(len(AXIS)))
        support = [
            {
                "sample_id": s["sampleid"],
                "datum": s["datum"],
                "ages": s["ages"],
                "depth": s["depth"],
            }
            for s, _, _ in members
        ]
        identity = hashlib.sha256(
            json.dumps(
                support,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest()
        expected = {
            "window_id": b,
            "edges_cal_bp": [500 * b, 500 * (b + 1)],
            "sample_ids": [s["sampleid"] for s, _, _ in members],
            "native_sample_support_sha256": identity,
            "pooled_panel_counts": list(n),
            "panel_count_total": sum(n),
            "all_reported_pollen_nisp": sum(
                r["all_reported_pollen_nisp"] for _, _, r in members
            ),
            "omitted_reported_pollen_nisp": sum(
                r["omitted_reported_pollen_nisp"] for _, _, r in members
            ),
        }
        _require(
            all(row[k] == v for k, v in expected.items()),
            "Saved window source support differs",
        )
        pooled[b] = n
    return pooled, ppe, sd
