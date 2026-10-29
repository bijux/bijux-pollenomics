"""Prepare a closed author taxon composition for constrained LOVE folds."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)

Json = dict[str, Any]
TAXA31 = (
    "Abies.alba",
    "Alnus.glutinosa",
    "Amanranthaceae.Chenopodiaceae",
    "Artemisia",
    "Betula",
    "Buxus.sempervirens",
    "Calluna.vulgaris",
    "Carpinus.betulus",
    "Carpinus.orientalis",
    "Castanea",
    "Cerealia.t",
    "Corylus.avellana",
    "Cyperaceae",
    "Ericaceae",
    "Fagus.sylvatica",
    "Filipendula",
    "Fraxinus",
    "Juniperus",
    "Phillyrea",
    "Picea",
    "Pinus",
    "Pistacia",
    "Plantago.lanceolata.type",
    "Poaceae",
    "Quercus.deciduous",
    "Quercus.evergreen",
    "Rumex.acetosa.t",
    "Salix",
    "Secale",
    "Tilia",
    "Ulmus",
)
PARAMETER_DIGEST = "bf54e69f37db5baf3ea85dab33b1df6edc5f0028266d5543f86a830ff1b037bd"
NATIVE_IDS = (
    "BECKHAM",
    "BROADOWN",
    "COMERSLA",
    "CUTHILL2",
    "EXEBRID",
    "GOURTEMIRES",
    "HANGINGS",
    "HARESDOWN",
    "LARKBARR",
    "LOBBSBOG",
    "LONGBREACH",
    "MOLECHAM",
    "NTWITCHEN",
    "WHH05",
    "WHH11",
    "WINDMILL",
    "WINNEYS",
)
SOURCE_MANIFEST = "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
CROSSWALK = "3a0f598ba5e550ca39da52b2047b7020b013dad013d15f79bef8e1c3c1a979c3"
PARAMETER_SOURCES = {
    "means_sha256": "066ebadbe6ab10aead80c74a184284e05b9db3cd1f5daff04249596170a663e2",
    "covariance_sha256": "8821de94682c454e3a751897b487c8bf1612cf60994dc6246fb33284a73e9918",
}
WINDOWS = {
    4: (22582, 518, 750, 1250, "1000", ("COMERSLA", "EXEBRID", "WHH05", "WHH11")),
    5: (20732, 159, 1250, 1750, "1500", ("EXEBRID", "WHH11")),
    6: (23009, 167, 1750, 2250, "2000", ("EXEBRID", "WHH05", "WHH11")),
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()


def checksum(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_digest(value: object) -> str:
    return checksum(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


def project_documents(
    bodies: dict[str, bytes], *, window: int = 5
) -> tuple[dict[str, bytes], Json]:
    """Project only a finite admitted native window; never fill an absent site."""
    require(
        type(window) is int and window in WINDOWS,
        "Declared source window4/5/6 required",
    )
    native_total, excluded_total, younger, older, label, unavailable = WINDOWS[window]
    original = json.loads(bodies["experiment.json"])
    report = json.loads(bodies["source-report.json"])
    SourceExperimentSpec(original)
    require(
        report["experiment_sha256"] == checksum(bodies["experiment.json"]),
        "Native experiment identity changed",
    )
    template = original["request_template"]
    require(
        tuple(template["taxa"]) == TAXA31 and TAXA31[15] == "Filipendula",
        "Original31 taxon order required",
    )
    require(
        [row["taxon"] for row in template["parameters"]] == list(TAXA31)
        and canonical_digest(template["parameters"]) == PARAMETER_DIGEST,
        "Original PPE/SD/species/fall-speed mapping required",
    )
    require(
        template["pollen_unit"] == "count"
        and template["data_kind"] == "source_observations",
        "Native source count units required",
    )
    require(
        template["method_profile"] == "disqover-0.9.14-source-compatible"
        and template["configuration"]
        == {
            "seed": 7,
            "love": {
                "method": "analytical",
                "stochastic": False,
                "max_ring": 2,
                "repeats": 2,
                "distance_weighting": "gpm neutral",
                "fall_speed_profile": "landclimii-2016-gpm-neutral-analytical-v1",
            },
            "reveals": {
                "stochastic": False,
                "iterations": 2,
                "distance_weighting": "gpm neutral",
                "fall_speed_profile": "landclimii-2016-gpm-neutral-analytical-v1",
            },
        },
        "Original native analytical source profile required",
    )
    sites = original["sites"]
    eligible = [site["site_id"] for site in sites]
    require(
        len(eligible) == len(set(eligible)) == 17 - len(unavailable)
        and set(eligible) == set(NATIVE_IDS) - set(unavailable)
        and all(site["record_id"] == "author:" + site["site_id"] for site in sites),
        "Original window-specific eligible identities required",
    )
    require(
        report["eligible_sites"] == eligible
        and report["zero_count_sites"] == sorted(unavailable)
        and set(eligible) | set(unavailable) == set(NATIVE_IDS)
        and report["selected_window"] == window
        and report["total_count"] == native_total
        and report["age_support_bp"] == [younger, older]
        and report["source_manifest_sha256"] == SOURCE_MANIFEST,
        "Native window availability or source denominator changed",
    )
    if window != 5:
        availability = report["source_window_availability"]
        require(
            availability["unavailable_sites"] == sorted(unavailable)
            and availability["source_taxa"] == 31,
            "Unavailable formatter-filled windows must remain explicit",
        )
    expected_bin = {
        "bin_id": "author-TW" + str(window),
        "younger_bp": younger,
        "older_bp": older,
    }
    require(
        template["temporal_matching"]["bins"] == [expected_bin],
        "Original selected temporal bin required",
    )
    chronology = json.loads(bodies["chronology.json"])
    require(
        chronology
        == {
            "source": "author bins.csv/TWlookup.csv",
            "window": window,
            "bounds_cal_bp": [younger, older],
            "label_bp": label,
        },
        "Source chronology/window units differ",
    )
    references = [site[role] for site in sites for role in ("raw", "geometry")]
    references += template["evidence"]
    expected_names = {"experiment.json", "source-report.json"} | {
        row["path"] for row in references
    }
    require(
        set(bodies) == expected_names and len(bodies) == 2 * len(sites) + 7,
        "Exact native scientific file namespace required",
    )
    require(
        all(Path(name).name == name and name not in (".", "..") for name in bodies),
        "Flat confined native member paths required",
    )
    for row in references:
        require(
            checksum(bodies[row["path"]]) == row["sha256"],
            "Native raw/geometry/evidence identity changed",
        )
    taxonomy = json.loads(bodies["taxa.json"])
    require(
        taxonomy == {"source_sha256": CROSSWALK, "prepared_taxa": list(TAXA31)},
        "Native prepared-name crosswalk changed",
    )
    require(
        json.loads(bodies["parameters.json"]) == PARAMETER_SOURCES,
        "Original parameter source identities required",
    )
    result = dict(bodies)
    native_mass = excluded_mass = 0
    for site in sites:
        raw = json.loads(bodies[site["raw"]["path"]])
        counts = raw["sample"]["counts"]
        require(
            raw["data_kind"] == "source_observations"
            and raw["taxa"] == list(TAXA31)
            and isinstance(counts, list)
            and len(counts) == 31
            and all(type(value) is int and value >= 0 for value in counts)
            and sum(counts) > counts[15],
            "Positive retained source counts required; missing/negative/fractional values are not zeros",
        )
        sample = raw["sample"]
        require(
            sample["site_id"] == site["site_id"]
            and sample["sample_id"] == site["site_id"] + ":TW" + str(window)
            and sample["age_type"] == "calendar_bp"
            and sample["age_support_bp"] == [[younger, older]]
            and sample["coordinate"] == int(label)
            and sample["bin_id"] == expected_bin["bin_id"],
            "Original site/sample/temporal support required",
        )
        native_mass += sum(counts)
        excluded_mass += counts[15]
        counts.pop(15)
        raw["taxa"].pop(15)
        result[site["raw"]["path"]] = encoded(raw)
        site["raw"]["sha256"] = checksum(result[site["raw"]["path"]])
        geometry = json.loads(bodies[site["geometry"]["path"]])
        require(
            geometry["sample_metadata"]
            == {k: v for k, v in sample.items() if k != "counts"}
            and len(geometry["inversion_rings"]) == 2
            and len(geometry["forward_rings"]) == 4
            and (
                geometry["forward_rings"][2]["inner_m"],
                geometry["forward_rings"][2]["outer_m"],
            )
            == (1000, 10000),
            "Native geometry and declared regional annulus required",
        )
        require(
            all(
                type(geometry[key]) in (int, float) and math.isfinite(geometry[key])
                for key in ("latitude", "longitude")
            ),
            "Finite source site coordinates required",
        )
        geometry["inversion_rings"].append(deepcopy(geometry["forward_rings"][2]))
        result[site["geometry"]["path"]] = encoded(geometry)
        site["geometry"]["sha256"] = checksum(result[site["geometry"]["path"]])
    require(
        (native_mass, excluded_mass) == (native_total, excluded_total),
        "Window-specific31/30 count mass differs",
    )
    template["taxa"].pop(15)
    template["parameters"].pop(15)
    template["method_profile"] = "ring-taxon-preserving"
    for method in ("love", "reveals"):
        template["configuration"][method]["fall_speed_profile"] = (
            "disqover-0.9.14-wrapper-v1"
        )
    template["configuration"]["love"].update(
        method="optimized",
        optimized_profile="ring-taxon-preserving",
        optimizer_backend="scipy.slsqp-simplex-uniform",
        optimizer_iterations=300,
        optimizer_max_evaluations=16000,
        optimizer_tolerance=1e-8,
        repeats=1,
    )
    taxonomy["prepared_taxa"].pop(15)
    taxonomy.update(
        excluded_taxon="Filipendula",
        excluded_nisp=excluded_total,
        original_nisp=native_total,
    )
    result["taxa.json"] = encoded(taxonomy)
    decision = json.loads(bodies["decision.json"])
    decision["constrained_love_design"] = {
        "study": "prior-exposed author English development",
        "closed_taxon_axis": "30 of 31 author targets; Filipendula excluded",
        "optimizer": "uniform-start SLSQP simplex; 300 iterations; 16000 evaluations; ftol 1e-8",
        "evidence_limit": "fold-specific LRA-derived vegetation, not independent measured vegetation",
    }
    result["decision.json"] = encoded(decision)
    for evidence in template["evidence"]:
        evidence["sha256"] = checksum(result[evidence["path"]])
    SourceExperimentSpec(original)
    result["experiment.json"] = encoded(original)
    report.update(
        experiment_sha256=checksum(result["experiment.json"]),
        closed_taxon_count=30,
        excluded_taxon="Filipendula",
        excluded_taxon_nisp=excluded_total,
        original_count_denominator=native_total,
        optimizer_backend="scipy.slsqp-simplex-uniform",
    )
    if window != 5:
        report["constrained_projection"] = {
            "native_input_report_sha256": checksum(bodies["source-report.json"]),
            "native_taxa": 31,
            "retained_taxa": 30,
            "excluded_index": 15,
            "native_original_nisp": native_total,
            "excluded_nisp": excluded_total,
            "retained_nisp": native_total - excluded_total,
            "native_ids": list(NATIVE_IDS),
            "eligible_sites": eligible,
            "unavailable_sites": sorted(unavailable),
            "total_count_meaning": "The inherited total_count is the original31taxon source denominator; retained_nisp declares this30taxon projection.",
            "missingness": "Original formatter-filled unavailable windows remain unavailable, not observed ecological zeros. Retained individual zero taxon counts remain zeros.",
            "age_scale": "Original source-declared calibrated/calendarBP support; no epoch, calibration or uncertainty requalification.",
        }
    result["source-report.json"] = encoded(report)
    return result, {
        "source_manifest_sha256": SOURCE_MANIFEST,
        "experiment_sha256": report["experiment_sha256"],
        "eligible_sites": len(sites),
        "excluded_nisp": excluded_total,
        "original_nisp": native_total,
        "retained_nisp": native_total - excluded_total,
        "window": window,
        "source_files": len(bodies),
    }


def prepare(source: Path, destination: Path, *, window: int = 5) -> Json:
    """Validate the whole scientific input scope before exclusively writing it."""
    require(
        not source.is_symlink() and not destination.is_symlink(),
        "Linked source or destination refused",
    )
    source, destination = source.resolve(), destination.resolve()
    require(
        source.is_dir()
        and not destination.exists()
        and not destination.is_relative_to(source),
        "Distinct source and absent output required",
    )
    entries = list(source.iterdir())
    require(
        len(entries) <= 37
        and all(
            p.is_file()
            and not p.is_symlink()
            and p.stat().st_nlink == 1
            and p.stat().st_size <= 1024 * 1024
            for p in entries
        ),
        "Bounded regular flat source files required",
    )
    bodies = {p.name: p.read_bytes() for p in entries}
    require(
        sum(map(len, bodies.values())) <= 8 * 1024 * 1024,
        "Native scientific input bound exceeded",
    )
    projected, summary = project_documents(bodies, window=window)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.with_name("." + destination.name + ".pending")
    stage.mkdir()
    try:
        for name, body in projected.items():
            with (stage / name).open("xb") as stream:
                stream.write(body)
        os.replace(stage, destination)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--window", type=int, choices=WINDOWS, default=5)
    args = parser.parse_args()
    print(
        json.dumps(
            prepare(args.source, args.destination, window=args.window), sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
