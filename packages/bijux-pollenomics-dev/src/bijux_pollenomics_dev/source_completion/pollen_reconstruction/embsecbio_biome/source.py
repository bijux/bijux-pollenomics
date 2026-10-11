"""Read exact curated values and preserve opaque entity-name byte tokens."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import TypedDict

from .numerical import ORDER


class PollenSample(TypedDict):
    """Preserve native metadata separately from taxon percentage values."""

    metadata: dict[str, str]
    values: dict[str, float]


def rows(path: Path, *, opaque_names: bool = False) -> list[dict[str, str]]:
    """Latin1 transports bytes bijectively; it does not repair source encoding."""
    with path.open(
        encoding="latin1" if opaque_names else "utf-8-sig", newline=""
    ) as stream:
        reader = csv.DictReader(stream)
        result = list(reader)
    if not result or any(
        None in row or any(value is None for value in row.values()) for row in result
    ):
        raise ValueError("CSV row width or population differs")
    return result


def number(value: str) -> float:
    """Read a finite literal ASCII model value."""
    if not value.isascii():
        raise ValueError("model-critical numerical fields must be literal ASCII")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("model-critical numerical field must be finite")
    return result


def model(
    directory: Path,
) -> tuple[list[str], dict[str, list[float]], dict[str, list[float]]]:
    """Read unique source taxa and their saved class parameters."""
    values = rows(directory / "Train_dataset.csv")
    taxa = [r["taxon_name"] for r in values]
    if len(set(taxa)) != len(taxa) or any(not t or not t.isascii() for t in taxa):
        raise ValueError("saved taxonomy must be unique literal ASCII")
    means = {b: [number(r["Mean_" + b]) for r in values] for b in ORDER}
    sd = {b: [number(r["Stdev_" + b]) for r in values] for b in ORDER}
    return taxa, means, sd


def pollen(directory: Path, taxa: list[str]) -> tuple[dict[str, PollenSample], int]:
    """Retain native sample metadata and bounded taxon percentages."""
    samples: dict[str, PollenSample] = {}
    values = rows(directory / "Modern_pollen_perc_emb_smpds.csv", opaque_names=True)
    for row in values:
        sid, taxon = row["ID_SAMPLE"], row["taxon_name"]
        if not sid or not sid.isascii() or not taxon.isascii():
            raise ValueError("native sample and taxon fields must be literal ASCII")
        amount = number(row["taxon_percent"])
        if not 0 <= amount <= 100:
            raise ValueError("pollen percentages must be in [0,100]")
        metadata = {k: row[k] for k in ("entity_name", "latitude", "longitude")}
        number(metadata["latitude"])
        number(metadata["longitude"])
        sample = samples.setdefault(sid, {"metadata": metadata, "values": {}})
        if sample["metadata"] != metadata:
            raise ValueError("native sample metadata is inconsistent")
        if taxon in sample["values"]:
            raise ValueError("duplicate native sample/taxon pair")
        if taxon not in taxa and amount != 0:
            raise ValueError("unsupported positive source taxonomy")
        sample["values"][taxon] = amount
    return samples, len(values)


def keyed(directory: Path, name: str) -> dict[str, dict[str, str]]:
    """Index unique native sample rows without changing source labels."""
    values = rows(directory / name)
    result = {r["ID_SAMPLE"]: r for r in values}
    if len(result) != len(values):
        raise ValueError("duplicate native sample key")
    return result
