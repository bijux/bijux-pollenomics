"""Independently join Swedish source membership, integer pollen mass and scores."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from fractions import Fraction
import gzip
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from typing import Any

from contracts import ROOT, exact, load, pin, require

METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
EXCLUDED = {"zz.do not use", "aage.cal.BP"}


def compressed(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()))


def taxonomy(raw: bytes) -> tuple[dict[str, str], list[str]]:
    rows = list(csv.DictReader(io.StringIO(raw.decode("latin-1"))))
    require(
        bool(rows) and set(rows[0]) == {"oldvar", "RPP.LANDCLIMII"}, "Lookup columns"
    )
    mapping: dict[str, str] = {}
    for row in rows:
        source, target = row["oldvar"], row["RPP.LANDCLIMII"]
        require(bool(source) and bool(target), "Empty lookup label")
        require(
            source not in mapping or mapping[source] == target, "Ambiguous lookup label"
        )
        mapping[source] = target
    return mapping, sorted(set(mapping.values()) - EXCLUDED)


def source_rows(manifest: dict[str, Any], surface: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    entry = manifest["surfaces"][surface]
    for part in entry["parts"]:
        path = ROOT / "data/neotoma/relational" / part["path"]
        require(pin(path)["sha256"] == part["sha256"], "Source part SHA differs")
        value = load(path)
        require(
            value["source_snapshot_id"] == manifest["source_snapshot_id"]
            and value["build_id"] == manifest["build_id"],
            "Source table epoch differs",
        )
        rows = value["rows"]
        require(
            type(rows) is list
            and len(rows) == part["row_count"]
            and all(type(x) is dict for x in rows),
            "Source table rows differ",
        )
        result.extend(rows)
    require(len(result) == entry["row_count"], "Source surface count differs")
    return result


def selected_claims(ages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in ages:
        if (
            row["subject_type"] != "sample"
            or row["country_code"] != "SE"
            or row["source_age_type"] != "Calibrated radiocarbon years BP"
            or row["is_default_chronology"] is not True
            or row["comparability_status"] != "comparable"
            or row["calibration_status"] != "calibrated"
        ):
            continue
        age = row["source_age_value"]
        require(
            type(age) in (int, float) and math.isfinite(age) and age >= 0,
            "Invalid selected source age",
        )
        key = row["subject_id"]
        require(key not in result, "Duplicate selected age")
        result[key] = row
    return result


def source_coordinate(geography: Any) -> dict[str, float]:
    geometry = json.loads(geography) if type(geography) is str else geography
    kind, coordinates = geometry["type"], geometry["coordinates"]
    if kind == "Point":
        longitude, latitude = coordinates[:2]
    else:
        require(kind in ("Polygon", "MultiPolygon"), "Unreviewed geometry type")
        polygons = [coordinates] if kind == "Polygon" else coordinates
        weighted_area = weighted_x = weighted_y = 0.0
        for polygon in polygons:
            for index, ring in enumerate(polygon):
                cross_sum = x_sum = y_sum = 0.0
                for current, following in zip(ring, ring[1:] + ring[:1], strict=True):
                    cross = current[0] * following[1] - following[0] * current[1]
                    cross_sum += cross
                    x_sum += (current[0] + following[0]) * cross
                    y_sum += (current[1] + following[1]) * cross
                require(abs(cross_sum) >= 1e-15, "Zero source polygon area")
                area = abs(cross_sum) / 2 * (1 if index == 0 else -1)
                weighted_area += area
                weighted_x += area * (x_sum / (3 * cross_sum))
                weighted_y += area * (y_sum / (3 * cross_sum))
        require(weighted_area > 0, "No source exterior area")
        longitude, latitude = weighted_x / weighted_area, weighted_y / weighted_area
    require(
        type(longitude) in (int, float)
        and type(latitude) in (int, float)
        and math.isfinite(longitude)
        and math.isfinite(latitude)
        and -180 <= longitude <= 180
        and -90 <= latitude <= 90,
        "Invalid WGS84 source point",
    )
    return {"latitude": float(latitude), "longitude": float(longitude)}


def direct_count(row: dict[str, Any]) -> bool:
    return (
        all(
            row.get(key) == value
            for key, value in {
                "source_element": "pollen",
                "source_element_type": "pollen",
                "source_unit": "NISP",
                "unit_family": "count",
                "detection_status": "reported_value",
            }.items()
        )
        and type(row.get("source_value")) is int
        and row["source_value"] >= 0
        and type(row.get("source_reported_name")) is str
        and bool(row["source_reported_name"].strip())
    )


def allocate(
    native: dict[str, int], mapping: dict[str, str], axis: list[str]
) -> dict[str, Any]:
    values = dict.fromkeys(axis, 0)
    excluded = unmapped = 0
    for name, value in native.items():
        require(type(value) is int and value >= 0, "Invalid native integer mass")
        target = mapping.get(name)
        if target is None:
            unmapped += value
        elif target in EXCLUDED:
            excluded += value
        else:
            require(target in values, "Target outside explicit axis")
            values[target] += value
    return {
        "counts": values,
        "closed_nisp": sum(values.values()),
        "all_pollen_nisp": sum(native.values()),
        "author_excluded_nisp": excluded,
        "unmapped_nisp": unmapped,
    }


def verify_preparation(
    family: str, study: dict[str, Any], prepared: Path
) -> dict[str, Any]:
    protocol = study["protocol"]
    source = load(ROOT / protocol["source_identity"]["relational_manifest_path"])
    sites = {x["site_id"]: x for x in source_rows(source, "sites")}
    datasets = {x["dataset_id"]: x for x in source_rows(source, "datasets")}
    samples = source_rows(source, "samples")
    claims = selected_claims(source_rows(source, "age_claims"))
    holdout_ids: set[str] = set()
    by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in samples:
        if row["country_code"] == "SE":
            by_site[row["site_id"]].append(row)
    if family == "swedish-lake-transfer":
        targets = protocol["targets"]
        claim_sites = Counter(row["site_id"] for row in claims.values())
        eligible = {
            key
            for key, rows in by_site.items()
            if key not in protocol["previous_swedish_target_site_ids"]
            and len({x["dataset_id"] for x in rows}) == 1
            and len({x["collection_unit_id"] for x in rows}) == 1
            and (sites[key]["source_payload"].get("sitedescription") or "")
            .lower()
            .startswith(("lake", "small lake"))
            and claim_sites[key] >= 50
            and datasets[rows[0]["dataset_id"]]["source_payload"].get("datasettype")
            == "pollen"
            and datasets[rows[0]["dataset_id"]]["source_payload"].get("database")
            == "European Pollen Database"
        }
        require(
            eligible == {x["site_id"] for x in targets},
            "Full eligible source cohort differs",
        )
        units = {
            x["collection_unit_id"]: x for x in source_rows(source, "collection_units")
        }
        for target in targets:
            rows = by_site[target["site_id"]]
            require(
                len(rows) == target["source_samples"]
                and {x["dataset_id"] for x in rows} == {target["dataset_id"]}
                and {x["collection_unit_id"] for x in rows}
                == {target["collection_unit_id"]}
                and units[target["collection_unit_id"]]["source_payload"]["handle"]
                == target["source_handle"],
                "Lake source identities differ",
            )
    else:
        target = protocol["target"]
        selected = [
            x for x in samples if x["dataset_id"] == target["selected_dataset_id"]
        ]
        parallel = [
            x
            for x in samples
            if x["dataset_id"] == target["excluded_parallel_dataset_id"]
        ]
        holdout_ids = {row["sample_id"] for row in selected}
        require(
            len(selected) == target["selected_sample_count"]
            and len(parallel) == target["parallel_dataset_sample_count"],
            "Parallel source count differs",
        )
        relevant = {
            key: value
            for key, value in datasets.items()
            if value["site_id"] == target["site_id"]
        }
        require(
            set(relevant)
            == {target["selected_dataset_id"], target["excluded_parallel_dataset_id"]}
            and all(
                x["collection_unit_id"] == target["collection_unit_id"]
                and x["source_payload"].get("datasettype") == "pollen"
                and x["source_payload"].get("database") == "European Pollen Database"
                for x in relevant.values()
            ),
            "Parallel dataset/core identity differs",
        )
        depths = [
            {
                x["source_depth"]: claims[x["sample_id"]]["source_age_value"]
                for x in rows
            }
            for rows in (selected, parallel)
        ]
        require(
            exact(depths[0], depths[1])
            and len(depths[0]) == target["shared_depths_with_equal_calibrated_age"],
            "Parallel core depth/age evidence differs",
        )
        targets = [
            {
                **target,
                "selected_samples": target["selected_sample_count"],
                "selected_age_min_bp": target["source_age_min_bp"],
                "selected_age_max_bp": target["source_age_max_bp"],
            }
        ]
    expected_sites = []
    memberships: dict[str, tuple[str, str]] = {}
    native: dict[tuple[str, str], Counter[str]] = {}
    for target in targets:
        key = target["site_id"]
        selected = [
            x
            for x in claims.values()
            if x["site_id"] == key
            and (family == "swedish-lake-transfer" or x["subject_id"] in holdout_ids)
        ]
        ids = sorted(x["subject_id"] for x in selected)
        require(
            len(ids) == target["selected_samples"]
            and sha256(("\n".join(ids) + "\n").encode()).hexdigest()
            == target["selected_sample_ids_sha256_newline_utf8"],
            "Exact selected native IDs differ",
        )
        require(
            min(x["source_age_value"] for x in selected)
            == target["selected_age_min_bp"]
            and max(x["source_age_value"] for x in selected)
            == target["selected_age_max_bp"]
            and sites[key]["source_payload"]["sitename"] == target["site_name"],
            "Selected source age/name differs",
        )
        bins = set()
        for row in selected:
            sample, bin_id = (
                row["subject_id"],
                str(math.floor(row["source_age_value"] / 500)),
            )
            require(sample not in memberships, "Sample in multiple targets")
            memberships[sample] = (key, bin_id)
            bins.add(bin_id)
            native.setdefault((key, bin_id), Counter())
        expected_sites.append(
            {
                "site_id": key,
                "site_name": target["site_name"],
                "group_id": key,
                "coordinate": source_coordinate(
                    sites[key]["source_payload"]["geography"]
                ),
                "candidate_bin_ids": sorted(bins, key=int),
                "candidate_sample_ids": ids,
            }
        )
    # Bound memory to one complete source part; never collect the observation surface.
    observed: set[str] = set()
    covered: set[str] = set()
    for part in source["surfaces"]["observations"]["parts"]:
        single = {
            **source,
            "surfaces": {
                "observations": {"parts": [part], "row_count": part["row_count"]}
            },
        }
        for row in source_rows(single, "observations"):
            member = memberships.get(row["sample_id"])
            if member is None or not direct_count(row):
                continue
            require(
                row["site_id"] == member[0] and row["observation_id"] not in observed,
                "Observation ownership/duplicate differs",
            )
            observed.add(row["observation_id"])
            covered.add(row["sample_id"])
            native[member][row["source_reported_name"]] += row["source_value"]
    require(covered == set(memberships), "Selected source samples lack direct counts")
    raw_lookup = Path(study["taxonomy_lookup"]["path"]).read_bytes()
    mapping, axis = taxonomy(raw_lookup)
    require(
        len(list(csv.DictReader(io.StringIO(raw_lookup.decode("latin-1"))))) == 10788
        and len(mapping) == 9731
        and len(axis) == 31,
        "Qualified taxonomy dimensions differ",
    )
    require(
        exact(
            compressed(prepared / "inputs/metadata-SE.json.gz"),
            {"country": "SE", "sites": expected_sites},
        ),
        "Prepared target metadata differs",
    )
    expected_outcomes: dict[str, dict[str, Any]] = defaultdict(dict)
    for (key, bin_id), counts in native.items():
        allocated = allocate(counts, mapping, axis)
        require(allocated["all_pollen_nisp"] > 0, "Empty native target bin")
        expected_outcomes["SE:" + key][bin_id] = {
            "sample_count": sum(
                value == (key, bin_id) for value in memberships.values()
            ),
            **allocated,
        }
    outcomes = compressed(prepared / "sealed-outcomes/outcomes-SE.json.gz")
    require(
        exact(outcomes, dict(expected_outcomes)),
        "Complete native count/taxonomy mass differs",
    )
    training = Path(study["actual_protocol_training"]["path"])
    require(
        (prepared / "inputs/training-SE.json.gz").read_bytes() == training.read_bytes(),
        "Training copy differs",
    )
    training_rows = compressed(training)
    require(
        len(training_rows) == protocol["training"]["site_groups"]
        and {x["country"] for x in training_rows.values()}
        == set(protocol["training"]["country_codes"])
        and not (
            {x["site_id"] for x in training_rows.values()}
            & {x["site_id"] for x in expected_sites}
        ),
        "Training country/target exclusion differs",
    )
    return {
        "selected_samples": len(memberships),
        "selected_sites": len(expected_sites),
        "selected_observation_rows": len(observed),
        "target_bins": len(native),
        "axis": axis,
        "outcomes": outcomes,
    }


def verify_scores(prepared: Path, predicted: Path, scored: Path) -> dict[str, int]:
    manifest = load(prepared / "input-manifest.json")
    metadata = compressed(prepared / "inputs/metadata-SE.json.gz")
    training = compressed(prepared / "inputs/training-SE.json.gz")
    outcomes = compressed(prepared / "sealed-outcomes/outcomes-SE.json.gz")
    predictions = compressed(predicted / "predictions-SE.json.gz")
    axis = manifest["axis"]
    require(
        predictions["country"] == "SE" and predictions["axis"] == axis,
        "Prediction country/axis differs",
    )
    candidates = {
        (site["site_id"], int(b))
        for site in metadata["sites"]
        for b in site["candidate_bin_ids"]
    }
    rows = predictions["predictions"]
    keys = [(x["site_id"], x["bin_id"], x["method"]) for x in rows]
    require(len(keys) == len(set(keys)), "Duplicate prediction method/bin")
    refused = {(x["site_id"], x["bin_id"]) for x in predictions["refusals"]}
    produced = {(x["site_id"], x["bin_id"]) for x in rows}
    require(
        not produced & refused and produced | refused == candidates,
        "Prediction denominator differs",
    )
    scores = list(csv.DictReader((scored / "scores.csv").open(newline="")))
    require(len(scores) == len(rows), "Score/prediction coverage differs")
    for prediction, result in zip(rows, scores, strict=True):
        key = (prediction["site_id"], prediction["bin_id"])
        eligible = [
            x
            for x in training.values()
            if str(key[1]) in x["bins"] and x["bins"][str(key[1])]["closed_nisp"] > 0
        ]
        require(
            len({x["group_id"] for x in eligible}) >= 2
            and key[0] not in {x["site_id"] for x in eligible}
            and prediction["training_site_ids"]
            == sorted(x["site_id"] for x in eligible)
            and prediction["target_pollen_counts_read"] is False,
            "Prediction training/leakage claim differs",
        )
        require(
            {x["method"] for x in rows if (x["site_id"], x["bin_id"]) == key}
            == set(METHODS),
            "Incomplete methods",
        )
        fractions = prediction["fractions"]
        require(
            set(fractions) == set(axis)
            and all(
                type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1
                for x in fractions.values()
            )
            and math.isclose(sum(fractions.values()), 1, rel_tol=0, abs_tol=1e-9),
            "Unclosed prediction",
        )
        target = outcomes["SE:" + key[0]][str(key[1])]
        observed = {
            taxon: target["counts"][taxon] / target["closed_nisp"] for taxon in axis
        }
        mae = sum(
            abs(fractions[taxon] - observed[taxon]) for taxon in sorted(axis)
        ) / len(axis)
        hellinger = math.sqrt(
            0.5
            * sum(
                (math.sqrt(fractions[taxon]) - math.sqrt(observed[taxon])) ** 2
                for taxon in fractions
            )
        )
        require(
            (result["site_id"], int(result["bin_id"]), result["method"])
            == (key[0], key[1], prediction["method"])
            and result["country"] == "SE"
            and result["status"] == "scored",
            "Score row identity differs",
        )
        require(
            float(result["mae_fraction"]) == mae
            and float(result["hellinger_distance"]) == hellinger
            and int(result["target_sample_count"]) == target["sample_count"]
            and int(result["target_assigned_nisp"]) == target["closed_nisp"]
            and int(result["target_native_nisp"]) == target["all_pollen_nisp"],
            "Score arithmetic or count differs",
        )
        require(
            result["prediction_sha256"]
            == pin(predicted / "predictions-SE.json.gz")["sha256"],
            "Score source hash differs",
        )
    for key in refused:
        eligible = [
            x
            for x in training.values()
            if str(key[1]) in x["bins"] and x["bins"][str(key[1])]["closed_nisp"] > 0
        ]
        require(len({x["group_id"] for x in eligible}) < 2, "Unsupported refusal")
    report = load(scored / "report.json")
    require(
        report["score_rows"] == len(scores)
        and report["axis"] == axis
        and report["methods"] == list(METHODS),
        "Summary scope differs",
    )
    cells = [cell for bins in outcomes.values() for cell in bins.values()]
    denominators = {
        "sites": len(metadata["sites"]),
        "selected_samples": sum(
            len(site["candidate_sample_ids"]) for site in metadata["sites"]
        ),
        "native_nisp": sum(cell["all_pollen_nisp"] for cell in cells),
        "assigned_nisp": sum(cell["closed_nisp"] for cell in cells),
        "author_excluded_nisp": sum(cell["author_excluded_nisp"] for cell in cells),
        "unmapped_nisp": sum(cell["unmapped_nisp"] for cell in cells),
    }
    require(
        exact(report["country_source_denominators"], {"SE": denominators}),
        "Complete reported source denominator differs",
    )
    for method in METHODS:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in scores:
            if row["method"] == method:
                grouped[row["site_id"]].append(row)
        for field, summary in (
            ("mae_fraction", "site_macro_mae_fraction"),
            ("hellinger_distance", "site_macro_hellinger_distance"),
        ):
            means = [
                float(
                    sum(
                        (Fraction.from_float(float(x[field])) for x in group),
                        Fraction(),
                    )
                    / len(group)
                )
                for group in grouped.values()
            ]
            expected = float(
                sum((Fraction.from_float(x) for x in means), Fraction()) / len(means)
            )
            require(
                report[summary]["SE"][method] == expected,
                "Site-macro arithmetic differs",
            )
    return {
        "predicted_bins": len(produced),
        "refused_bins": len(refused),
        "prediction_rows": len(rows),
        "score_rows": len(scores),
    }
