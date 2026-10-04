"""Distinguish training exposure proxies and model-derived reference agreement."""

from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from .cohorts import entities, original_matrices, rates
from .numerical import ORDER
from .source import keyed, number, rows

CATEGORIES = (
    "direct_training_sample_id",
    "other_sample_same_recorded_training_coordinate",
    "other_coordinate_same_opaque_training_entity_name",
    "no_matching_training_id_coordinate_or_opaque_name",
)


def category(sid, coordinates, names, training):
    """Ordered proxies do not establish biological independence or site identity."""
    ids, points, tokens = training
    if sid in ids:
        return CATEGORIES[0]
    if coordinates[sid] in points:
        return CATEGORIES[1]
    if names[sid] in tokens:
        return CATEGORIES[2]
    return CATEGORIES[3]


def measures(records):
    result = rates(records)
    counts = Counter(r["dominant"] for r in records)
    recall = {
        biome: sum(r["dominant"] == biome and r["prediction"] == biome for r in records)
        / n
        for biome, n in sorted(counts.items())
    }
    matrix = Counter((r["dominant"], r["prediction"]) for r in records)
    return {
        **result,
        "reference_class_counts": dict(sorted(counts.items())),
        "balanced_dominant_agreement_present_classes": sum(recall.values())
        / len(recall)
        if recall
        else None,
        "reference_row_prediction_column_matrix": [
            {"reference": ref, "prediction": pred, "n": n}
            for (ref, pred), n in sorted(matrix.items())
        ],
    }


def filtered(records):
    return [
        r
        for r in records
        if r["dominant"] not in ("TUND", "CENF")
        and r["prediction"] not in ("TUND", "CENF")
    ]


def partition(records, exposure):
    groups = {name: [] for name in CATEGORIES}
    for record in records:
        categories = {exposure[s] for s in record["sample_ids"]}
        groups[next(name for name in CATEGORIES if name in categories)].append(record)
    return groups


def profile(samples, labels, predictions, selection, exposure, *, entity=True):
    records = (
        entities(samples, labels, predictions, selection)
        if entity
        else [
            {
                "sample_ids": [sid],
                "entity_name": samples[sid]["metadata"]["entity_name"],
                "dominant": labels[sid]["Dominant"],
                "subdominant": labels[sid]["Subdominant"],
                "prediction": predictions[sid],
            }
            for sid in sorted(selection)
            if labels[sid]["Dominant"] in ORDER
        ]
    )
    subset = filtered(records)
    return {
        "source_samples": len(selection),
        "eligible_label_samples": sum(len(r["sample_ids"]) for r in records),
        "sample_exposure_categories": dict(
            sorted(Counter(exposure[s] for s in selection).items())
        ),
        "all_class_agreement": measures(records),
        "exposure_partition_agreement": {
            name: measures(group)
            for name, group in partition(records, exposure).items()
        },
        "source_TUND_CENF_filtered_agreement": measures(subset),
        "TUND_CENF_excluded_rows": len(records) - len(subset),
        "grouping": "literal opaque entity-name token modes with lexicographic class ties"
        if entity
        else "individual native sample IDs",
    }


def sub_agreement(records):
    n = len(records)
    correct = sum(r["prediction"] == r["subdominant"] for r in records)
    return {
        "denominator": n,
        "subdominant_correct": correct,
        "subdominant_agreement": correct / n if n else None,
    }


def validated_members(directory, samples, labels, coordinates):
    training = keyed(directory, "rejection-training-samples.csv")
    downsample = keyed(directory, "rejection-downsampled-samples.csv")
    selected_rows = rows(directory / "selected-location-samples.csv", opaque_names=True)
    selected = {r["ID_SAMPLE"]: r for r in selected_rows}
    if len(selected) != len(selected_rows):
        raise ValueError("duplicate selected native sample key")
    if (len(training), len(downsample), len(selected)) != (678, 970, 4398):
        raise ValueError("training/downsample/location population differs")
    if not set(training) <= set(downsample) <= set(selected) <= set(samples):
        raise ValueError("native training/downsample membership differs")
    for members in (training, downsample):
        if any(
            r["Dominant"] != labels[sid]["Dominant"] or r["Dominant"] not in ORDER
            for sid, r in members.items()
        ):
            raise ValueError("native training/downsample reference class differs")
    for sid, row in selected.items():
        if (number(row["latitude"]), number(row["longitude"])) != coordinates[
            sid
        ] or any(row[k] != labels[sid][k] for k in ("Dominant", "Subdominant")):
            raise ValueError("selected native coordinate/reference label differs")
    trainpoints = {coordinates[sid] for sid in training}
    remainder = set(downsample) - set(training)
    if (
        len(trainpoints) != 678
        or len({coordinates[sid] for sid in selected}) != 4398
        or {coordinates[sid] for sid in remainder} & trainpoints
    ):
        raise ValueError("declared nontraining coordinate separation differs")
    return set(training), set(downsample), set(selected)


def exposure_product(
    directory: Path, capture: dict, samples: dict, labels: dict, predictions: dict
) -> dict:
    if capture["schema_version"] != "qualified-embsecbio-training-exposure-capture.v1":
        raise ValueError("training exposure capture schema differs")
    for name, expected in capture["source_sha256"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError("training exposure captured source dependency changed")
    if (
        len(samples) != 5765
        or set(samples) != set(labels)
        or set(samples) != set(predictions)
        or not set(predictions.values()) <= set(ORDER)
    ):
        raise ValueError("training exposure source/prediction population differs")
    coordinates = {
        sid: (number(r["metadata"]["latitude"]), number(r["metadata"]["longitude"]))
        for sid, r in samples.items()
    }
    names = {sid: r["metadata"]["entity_name"] for sid, r in samples.items()}
    training, downsample, selected = validated_members(
        directory, samples, labels, coordinates
    )
    proxies = training, {coordinates[s] for s in training}, {names[s] for s in training}
    exposure = {sid: category(sid, coordinates, names, proxies) for sid in samples}
    selections = {
        "complete_curated_cohort": set(samples),
        "emb_complete_coordinate_window": {
            s
            for s, (lat, lon) in coordinates.items()
            if 28 < lat < 49.25 and 20 < lon < 62
        },
        "northern_europe_coordinate_screen": {
            s
            for s, (lat, lon) in coordinates.items()
            if 54 <= lat <= 72 and -25 <= lon <= 32
        },
        "original_emb_selected_cohort": {
            s
            for s in selected
            if labels[s]["Dominant"] in ORDER
            and 28 < coordinates[s][0] < 49.25
            and 20 < coordinates[s][1] < 62
        },
        "author_nontraining_downsample_PNV_samples": downsample - training,
        "regenerated_training_PNV_samples": training,
    }
    reports = {
        name: profile(
            samples,
            labels,
            predictions,
            selection,
            exposure,
            entity=name
            not in (
                "author_nontraining_downsample_PNV_samples",
                "regenerated_training_PNV_samples",
            ),
        )
        for name, selection in selections.items()
    }
    original = entities(
        samples, labels, predictions, selections["original_emb_selected_cohort"]
    )
    matrices = original_matrices(directory, original)
    if len(original) != 917 or not all(r["all_cells_exact"] for r in matrices.values()):
        raise ValueError("training exposure original matrix cells differ")
    subrows = [r for r in original if r["subdominant"] in ORDER]
    submembers = {s for r in subrows for s in r["sample_ids"]}
    subreport = profile(samples, labels, predictions, submembers, exposure)
    subreport["original_subdominant_target_agreement"] = sub_agreement(subrows)
    subreport["subdominant_target_exposure_partition"] = {
        name: sub_agreement(group)
        for name, group in partition(subrows, exposure).items()
    }
    reports["original_emb_subdominant_matrix_members"] = subreport
    if reports != capture["expected_profiles"]:
        raise ValueError("training exposure admitted denominators/partitions differ")
    counts = rows(directory / "training-cohort-counts.csv")
    return {
        "schema_version": "embsecbio-training-evaluation-exposure.v1",
        "profiles": reports,
        "actual_training_samples": len(training),
        "actual_downsample_samples": len(downsample),
        "actual_nontraining_downsample_samples": len(downsample - training),
        "training_coordinate_count": len(proxies[1]),
        "training_opaque_name_count": len(proxies[2]),
        "native_source_samples": len(samples),
        "downsampling_class_counts": counts,
        "active_location_seed": 2501,
        "active_downsampling_seed": 2468,
        "commented_seed_124_activated": False,
        "downsampling_source_interpretation": "Operative ratio GRAM134/DESE97 times minority TUND82 floors to113; seven113+97+82=970. Per-class rounded0.7 gives seven79+68+57=678; globalround0.7*970=679 is not the operative selection. The source comment about reaching GRAM differs from executed source code.",
        "original_matrix_reuse_authentication": matrices,
        "native_entity_wire_transport": {
            **capture["native_wire_capture"],
            "publication_scope": "Retained admitted actual917native-wire capture; current producer does not read the absent original-entity CSV or repeat its byte comparison",
        },
        "capture_authority": capture["authority"],
        "prediction_scope": "Use admitted native predicted classes; exposure-only execution repeats no distances, fitting, R sampling or training statistics",
        "limits": capture["limits"],
    }
