"""Verify published training statistics against admitted native sampling captures."""

from __future__ import annotations

from collections import Counter
import hashlib
import math
from pathlib import Path

from .numerical import ORDER
from .source import keyed, number, rows


def within(actual: float, reference: float) -> bool:
    return abs(actual - reference) <= 1e-12 + 1e-12 * abs(reference)


def member_labels(directory: Path, name: str) -> dict[str, str]:
    members = keyed(directory, name)
    if any(row["Dominant"] not in ORDER for row in members.values()):
        raise ValueError("training sample class is unsupported")
    return {sid: row["Dominant"] for sid, row in members.items()}


def statistics(values: list[float]) -> tuple[float, float]:
    """Use sample SD with n−1 and stable independent summation."""
    if len(values) < 2 or any(not math.isfinite(v) for v in values):
        raise ValueError("training statistic requires at least two finite values")
    mean = math.fsum(values) / len(values)
    sd = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))
    return mean, sd


def training_product(
    directory: Path,
    capture: dict,
    samples: dict,
    labels: dict,
    taxa: list[str],
    means: dict,
    sd: dict,
) -> dict:
    """Recompute means and SD from native IDs without rerunning R sampling."""
    if (
        capture["schema_version"]
        != "qualified-embsecbio-training-reconstruction-capture.v1"
    ):
        raise ValueError("training capture schema differs")
    for name, expected in capture["source_sha256"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError("captured training source dependency changed")
    expected = capture["expected_counts"]
    if len(taxa) != expected["taxa"] or len(ORDER) != expected["classes"]:
        raise ValueError("training model taxonomy or class population differs")
    count_rows = rows(directory / "training-cohort-counts.csv")
    counts = {r["Dominant"]: r for r in count_rows}
    if len(counts) != len(count_rows) or set(counts) != set(ORDER):
        raise ValueError("training cohort class counts differ")
    computed = {}
    for profile in ("rejection", "rounding"):
        location_name = (
            "selected-location-samples.csv"
            if profile == "rejection"
            else "rounding-location-samples.csv"
        )
        location = keyed(directory, location_name)
        if len(location) != expected["location_samples"] or not set(location) <= set(
            samples
        ):
            raise ValueError("training source location population differs")
        eligible = {}
        for sid, row in location.items():
            if any(
                number(row[f]) != number(samples[sid]["metadata"][f])
                for f in ("latitude", "longitude")
            ):
                raise ValueError("training source location coordinates differ")
            if any(row[f] != labels[sid][f] for f in ("Dominant", "Subdominant")):
                raise ValueError("training source location PNV labels differ")
            if row["Dominant"] in ORDER:
                eligible[sid] = row["Dominant"]
        if len(eligible) != expected["eligible_locations"]:
            raise ValueError("training eligible location denominator differs")
        downsampled = member_labels(directory, profile + "-downsampled-samples.csv")
        training = member_labels(directory, profile + "-training-samples.csv")
        if (
            len(downsampled) != expected["downsampled_samples"]
            or len(training) != expected["training_samples"]
        ):
            raise ValueError("training/downsample denominator differs")
        if any(eligible.get(sid) != biome for sid, biome in downsampled.items()):
            raise ValueError(
                "downsample member is absent from matching source location"
            )
        if any(downsampled.get(sid) != biome for sid, biome in training.items()):
            raise ValueError("training member is absent from matching downsample")
        observed_counts = {
            "location_n": Counter(eligible.values()),
            "downsample_n": Counter(downsampled.values()),
            "training_n": Counter(training.values()),
        }
        if any(
            number(counts[b][f]) != observed_counts[f][b]
            for b in ORDER
            for f in observed_counts
        ):
            raise ValueError("training class denominator differs")
        native = {}
        for row in rows(directory / (profile + "-parameters.csv")):
            key = row["taxon_name"], row["biome"]
            if key in native:
                raise ValueError("native training parameter is duplicated")
            native[key] = row
        if set(native) != {(taxon, biome) for taxon in taxa for biome in ORDER}:
            raise ValueError("native training parameter population differs")
        comparison_cells = matched = 0
        max_saved = max_native = 0.0
        for biome in ORDER:
            selected = [samples[sid] for sid, b in training.items() if b == biome]
            for index, taxon in enumerate(taxa):
                mean, sample_sd = statistics(
                    [sample["values"].get(taxon, 0.0) for sample in selected]
                )
                reference = native[taxon, biome]
                if number(reference["n"]) != len(selected):
                    raise ValueError("native training statistic denominator differs")
                for field, value, saved in (
                    ("mean", mean, means[biome][index]),
                    ("sample_sd", sample_sd, sd[biome][index]),
                ):
                    recorded = number(reference[field])
                    if recorded < 0 or not within(value, recorded):
                        raise ValueError(
                            "native training statistic differs from source samples"
                        )
                    max_native = max(max_native, abs(value - recorded))
                    max_saved = max(max_saved, abs(value - saved))
                    matched += within(value, saved)
                    comparison_cells += 1
        if comparison_cells != expected["parameter_cells"]:
            raise ValueError("training parameter comparison denominator differs")
        computed[profile] = {
            "source_profile": profile,
            "eligible_location_samples": len(eligible),
            "downsampled_samples": len(downsampled),
            "training_samples": len(training),
            "training_class_counts": dict(
                sorted(observed_counts["training_n"].items())
            ),
            "parameter_cells_compared": comparison_cells,
            "published_matching_cells": matched,
            "published_mismatching_cells": comparison_cells - matched,
            "maximum_absolute_published_difference": max_saved,
            "maximum_absolute_native_difference": max_native,
            "native_source_statistics_all_matched": True,
            "published_parameters_reproduced": matched == comparison_cells,
        }
    scenarios = []
    for scenario in capture["scenarios"]:
        result = computed[scenario["source_profile"]]
        if (
            result["published_matching_cells"] != scenario["published_matching_cells"]
            or result["published_parameters_reproduced"]
            != scenario["original_parameter_reproduced"]
        ):
            raise ValueError("retained training comparison outcome differs")
        scenarios.append(
            {
                "native_sampling_capture": scenario,
                "current_source_statistic_comparison": result,
            }
        )
    return {
        "schema_version": "embsecbio-published-training-reconstruction.v1",
        "publication_scope": "Current Python source-statistic replay from admitted actual native training IDs; original R sampling retained as capture",
        "scenarios": scenarios,
        "tolerance": capture["tolerance"],
        "native_capture_authority": capture["authority"],
        "metadata_adapter": capture["metadata_adapter"],
        "limits": capture["limits"],
    }
