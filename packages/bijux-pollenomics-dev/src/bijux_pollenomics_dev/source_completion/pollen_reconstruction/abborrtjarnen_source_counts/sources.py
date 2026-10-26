"""Literal original ABBO table fields and current native measurement identities."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class Axis:
    name: str
    column: str
    abbreviation: str
    epd_comment: str
    native_id: int


AXES = (
    Axis("Betula", "Bet [#]", "Bet", "Betula", 29),
    Axis("Cyperaceae", "Cypae [#]", "Cypae", "Cyperaceae", 74),
    Axis("Juniperus communis", "Jun.c [#]", "Jun.c", "Juniperus-type", 4416),
    Axis("Pinus sylvestris", "Pin.s [#]", "Pin.s", "Pinus diploxylon-type", 1287),
    Axis("Poaceae", "Poac [#]", "Poac", "Gramineae", 417),
)


@dataclass(frozen=True)
class OriginalRow:
    index: int
    depth_token: str
    depth_m: Decimal
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class OriginalTable:
    columns: tuple[str, ...]
    rows: tuple[OriginalRow, ...]


@dataclass(frozen=True)
class NativeSample:
    sample_id: int
    depth: Decimal
    observed: dict[str, int]


def read_original(text: str) -> OriginalTable:
    """Decode only the declared five count fields, preserving every literal cell."""
    parts = text.split("*/", 1)
    if len(parts) != 2:
        raise ValueError("Original description terminator is missing")
    description, body = parts
    for required in (
        "PANGAEA.738429",
        "Giesecke, Thomas (2010): Pollen profile ABBO, Abborrtjärnen, Sweden",
        "2010-05-11",
        "CC-BY-NC-3.0",
        "DEPTH, sediment/rock [m]",
    ):
        if required not in description:
            raise ValueError("Original descriptive source identity differs")
    for axis in AXES:
        matching = [
            line
            for line in description.splitlines()
            if f"{axis.name} [#] ({axis.abbreviation}) *" in line
        ]
        if (
            len(matching) != 1
            or matching[0].rsplit("* COMMENT:", 1)[-1].strip() != axis.epd_comment
        ):
            raise ValueError("Original parameter/comment identity differs")
    rows = list(
        csv.reader(
            body.lstrip("\r\n").splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE
        )
    )
    if not rows:
        raise ValueError("Original table is empty")
    columns = tuple(rows[0])
    if (
        len(set(columns)) != len(columns)
        or columns[0] != "Depth sed [m]"
        or any(axis.column not in columns for axis in AXES)
    ):
        raise ValueError("Original count/depth columns differ")
    positions = tuple(columns.index(axis.column) for axis in AXES)
    parsed = []
    for index, cells in enumerate(rows[1:]):
        if len(cells) != len(columns):
            raise ValueError("Original table row width differs")
        try:
            depth = Decimal(cells[0].strip())
        except InvalidOperation as exc:
            raise ValueError("Original depth is not an exact decimal") from exc
        if not depth.is_finite():
            raise ValueError("Original depth is not finite")
        parsed.append(
            OriginalRow(index, cells[0], depth, tuple(cells[j] for j in positions))
        )
    return OriginalTable(columns, tuple(parsed))


def read_native(document: dict[str, Any]) -> tuple[NativeSample, ...]:
    """Preserve native integer measurements; absent target records stay absent."""
    if document["status"] != "success" or len(document["data"]) != 1:
        raise ValueError("Native response population differs")
    site = document["data"][0]["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    if (
        site["siteid"],
        unit["collectionunitid"],
        unit["handle"],
        dataset["datasetid"],
    ) != (13338, 14910, "ABBO", 19913):
        raise ValueError("Native physical owner differs")
    if dataset["database"] != "European Pollen Database" or dataset["doi"] != [
        "10.21233/2vzb-bg61"
    ]:
        raise ValueError("Native dataset provenance differs")
    by_name = {axis.name: axis for axis in AXES}
    by_id = {axis.native_id: axis for axis in AXES}
    parsed = []
    identifiers = set()
    for sample in dataset["samples"]:
        sample_id, raw_depth = sample["sampleid"], sample["depth"]
        if (
            type(sample_id) is not int
            or sample_id in identifiers
            or type(raw_depth) not in (int, float, Decimal)
        ):
            raise ValueError("Native sample identity or depth type differs")
        depth = Decimal(str(raw_depth))
        if not depth.is_finite():
            raise ValueError("Native sample depth is not finite")
        identifiers.add(sample_id)
        observed = {}
        for datum in sample["datum"]:
            name = datum["variablename"]
            taxon_id = datum["taxonid"]
            if name not in by_name and taxon_id not in by_id:
                continue
            value = datum["value"]
            if (
                name not in by_name
                or type(taxon_id) is not int
                or taxon_id != by_name[name].native_id
                or datum["element"] != "pollen"
                or datum["elementtype"] != "pollen"
                or datum["units"] != "NISP"
                or type(value) is not int
                or value < 0
                or name in observed
            ):
                raise ValueError("Native target measurement identity/type differs")
            observed[name] = value
        parsed.append(NativeSample(sample_id, depth, observed))
    return tuple(parsed)


def classify_token(token: str) -> tuple[str, int | None, str | None]:
    """An explicit numeric zero is distinct from a blank or an invalid count."""
    if not token.strip():
        return "blank", None, "empty_cell"
    try:
        value = Decimal(token.strip())
    except InvalidOperation:
        return "invalid", None, "unparsed_count_token"
    if not value.is_finite():
        return "invalid", None, "nonfinite_count"
    if value < 0:
        return "invalid", None, "negative_count"
    if value != value.to_integral_value():
        return "invalid", None, "nonintegral_count"
    integer = int(value)
    return (
        ("explicit_zero" if integer == 0 else "explicit_positive_integer"),
        integer,
        None,
    )
