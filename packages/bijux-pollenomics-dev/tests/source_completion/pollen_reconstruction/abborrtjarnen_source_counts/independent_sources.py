"""Independently read literal original counts and exact native depth owners."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from fractions import Fraction
import io
import json


@dataclass(frozen=True)
class SourceRow:
    physical_line: int
    depth_token: str
    depth_m: Fraction
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class NativeSample:
    sample_id: int
    depth_native: Fraction
    values: tuple[int | None, ...]


def literal_count(token: str) -> tuple[str, int | None]:
    """Keep empty, invalid, explicit zero and positive integer facts distinct."""
    if not token.strip():
        return "blank", None
    if "/" in token:
        return "invalid", None
    try:
        value = Fraction(token.strip())
    except (ValueError, ZeroDivisionError):
        return "invalid", None
    if value.denominator != 1 or value < 0:
        return "invalid", None
    return ("zero" if value == 0 else "positive"), value.numerator


def original_rows(
    body: bytes, columns: tuple[str, ...]
) -> tuple[str, tuple[str, ...], tuple[SourceRow, ...]]:
    """Read original TSV positions without a producer reader or float join."""
    lines = body.decode("utf-8").splitlines()
    end = [i for i, line in enumerate(lines) if line.strip() == "*/"]
    if len(end) != 1:
        raise ValueError("Original description terminator is ambiguous")
    header_index = end[0] + 1
    parsed = list(
        csv.reader(io.StringIO("\n".join(lines[header_index:])), delimiter="\t")
    )
    if not parsed:
        raise ValueError("Original table is empty")
    header = tuple(parsed[0])
    if (
        header[0] != "Depth sed [m]"
        or len(header) != len(set(header))
        or any(header.count(c) != 1 for c in columns)
    ):
        raise ValueError("Original source column is missing or duplicated")
    positions = [header.index(c) for c in columns]
    result = []
    depths: set[Fraction] = set()
    for offset, row in enumerate(parsed[1:], start=2):
        if len(row) != len(header):
            raise ValueError("Original source row has the wrong width")
        try:
            depth = Fraction(row[0].strip())
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError("Original depth is not an exact finite number") from error
        if depth in depths:
            raise ValueError("Original depth has multiple owners")
        depths.add(depth)
        result.append(
            SourceRow(
                header_index + offset, row[0], depth, tuple(row[p] for p in positions)
            )
        )
    return "\n".join(lines[:header_index]), header, tuple(result)


def native_samples(
    body: bytes, axis: tuple[tuple[str, int], ...]
) -> tuple[NativeSample, ...]:
    """Decode native decimal tokens exactly and reject ambiguous named counts."""
    document = json.loads(body, parse_float=Fraction)
    records = document.get("data")
    if (
        document.get("status") != "success"
        or not isinstance(records, list)
        or len(records) != 1
    ):
        raise ValueError("Native endpoint population differs")
    site = records[0]["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    if any(
        type(value) is not int
        for value in (site["siteid"], unit["collectionunitid"], dataset["datasetid"])
    ):
        raise ValueError("Native source identifier kind differs")
    if (
        site["siteid"],
        unit["collectionunitid"],
        unit["handle"],
        dataset["datasetid"],
    ) != (
        13338,
        14910,
        "ABBO",
        19913,
    ):
        raise ValueError("Native physical source identity differs")
    if dataset["database"] != "European Pollen Database" or dataset["doi"] != [
        "10.21233/2vzb-bg61"
    ]:
        raise ValueError("Native publication/database identity differs")
    names = {name for name, _ in axis}
    taxon_ids = {taxon_id for _, taxon_id in axis}
    if len(names) != len(axis) or len(taxon_ids) != len(axis):
        raise ValueError("Declared native taxon axis is ambiguous")
    owners: set[int] = set()
    depths: set[Fraction] = set()
    result = []
    for row in dataset["samples"]:
        sample_id = row["sampleid"]
        depth = row["depth"]
        if type(sample_id) is not int or sample_id in owners:
            raise ValueError("Native sample owner is invalid or duplicated")
        if type(depth) not in (int, Fraction):
            raise ValueError("Native depth is not an exact finite number")
        depth = Fraction(depth)
        if depth in depths:
            raise ValueError("Native depth has multiple owners")
        owners.add(sample_id)
        depths.add(depth)
        values: dict[str, int] = {}
        for datum in row["datum"]:
            name, taxon_id = datum["variablename"], datum["taxonid"]
            if name not in names and taxon_id not in taxon_ids:
                continue
            if (
                type(taxon_id) is not int
                or (name, taxon_id) not in axis
                or name in values
                or datum["element"] != "pollen"
                or datum["elementtype"] != "pollen"
                or datum["units"] != "NISP"
                or type(datum["value"]) is not int
                or datum["value"] < 0
            ):
                raise ValueError("Native named measurement is ambiguous or invalid")
            values[name] = datum["value"]
        result.append(
            NativeSample(sample_id, depth, tuple(values.get(n) for n, _ in axis))
        )
    return tuple(result)


def depth_pairs(
    original: tuple[SourceRow, ...], native: tuple[NativeSample, ...]
) -> tuple[tuple[SourceRow, NativeSample], ...]:
    """Require an exact bijection after the declared metre-to-centimetre scale."""
    by_depth = {row.depth_m * 100: row for row in original}
    if len(by_depth) != len(original) or len({r.depth_native for r in native}) != len(
        native
    ):
        raise ValueError("Depth mapping is not one-to-one")
    if set(by_depth) != {row.depth_native for row in native}:
        raise ValueError("Original and native depth populations differ")
    return tuple(
        (by_depth[row.depth_native], row)
        for row in sorted(native, key=lambda r: (r.depth_native, r.sample_id))
    )
