"""Preserve every native aliquot and refuse absent literal measurements."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

DATASETS = {"53995": "28869", "54001": "28872"}
TAXA = ("Alnus", "Plantago lanceolata")
SOURCE = "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
SOURCE_SHA256 = "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134"


def decode_sample(sample: dict[str, Any], dataset: str, pointer: str) -> dict[str, Any]:
    """Return all selection reasons without silently completing native fields."""
    reasons: list[str] = []
    ages = sample.get("ages")
    age = None
    bin_id = None
    if not isinstance(ages, list) or len(ages) != 1 or not isinstance(ages[0], dict):
        reasons.append("native_age_row_not_unique")
    else:
        row = ages[0]
        value = row.get("age")
        if row.get("agetype") != "Calibrated radiocarbon years BP":
            reasons.append("native_age_type_unsupported")
        elif (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            reasons.append("native_age_not_finite_numeric")
        else:
            age = value
            bin_id = math.floor(value / 500)
            if bin_id not in range(-1, 12):
                reasons.append("native_point_outside_declared_bins")
    datum = sample.get("datum")
    counts: list[int | None] = []
    pair_rows: list[Any] = []
    for taxon in TAXA:
        matches = (
            [
                row
                for row in datum
                if isinstance(row, dict) and row.get("variablename") == taxon
            ]
            if isinstance(datum, list)
            else []
        )
        pair_rows.extend(matches)
        count_value: int | None = None
        if len(matches) != 1:
            reasons.append(
                taxon
                + (":absent_native_datum" if not matches else ":duplicate_native_axis")
            )
        else:
            row = matches[0]
            raw = row.get("value")
            if row.get("units") != "NISP" or row.get("elementtype") != "pollen":
                reasons.append(taxon + ":unsupported_measure")
            elif type(raw) is not int or raw < 0:
                reasons.append(taxon + ":nonnegative_integer_count_required")
            else:
                count_value = raw
        counts.append(count_value)
    total = (
        sum(value for value in counts if value is not None)
        if all(value is not None for value in counts)
        else None
    )
    if total is not None and not 1 <= total <= 10000:
        reasons.append("pair_total_outside_interval_domain")
    return {
        "dataset_id": dataset,
        "site_id": DATASETS[dataset],
        "source_pointer": pointer,
        "native_sample_id": sample.get("sampleid"),
        "native_age_rows": ages,
        "native_pair_datum": pair_rows,
        "point_age_bp": age,
        "bin_id": bin_id,
        "counts": counts,
        "pair_total": total,
        "refusal_reasons": reasons,
        "admitted": not reasons,
    }


def read_population(repository: Path) -> list[dict[str, Any]]:
    """Bind the original source bytes before inspecting two named source datasets."""
    path = repository / SOURCE
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Native source hash differs")
    payload = json.loads(path.read_bytes())
    found: set[str] = set()
    population: list[dict[str, Any]] = []
    for row_index, row in enumerate(payload["rows"]):
        site = row["site"]
        dataset = site.get("dataset", {})
        identifier = str(dataset.get("datasetid"))
        if identifier not in DATASETS:
            continue
        if (
            identifier in found
            or str(site["siteid"]) != DATASETS[identifier]
            or dataset.get("datasettype") != "pollen"
            or dataset.get("database") != "European Pollen Database"
        ):
            raise ValueError("Ambiguous native dataset/site/source identity")
        found.add(identifier)
        nested = site["collectionunit"]["dataset"]
        samples = nested["samples"]
        if not isinstance(samples, list) or any(
            not isinstance(sample, dict) for sample in samples
        ):
            raise ValueError("Native sample population must be explicit objects")
        for index, sample in enumerate(samples):
            pointer = f"/rows/{row_index}/site/collectionunit/dataset/samples/{index}"
            population.append(decode_sample(sample, identifier, pointer))
    if found != set(DATASETS) or not population:
        raise ValueError("Both native datasets and their sample population required")
    return population
