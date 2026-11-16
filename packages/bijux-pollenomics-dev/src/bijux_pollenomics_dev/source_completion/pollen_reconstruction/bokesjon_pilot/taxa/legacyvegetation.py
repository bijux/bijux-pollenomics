"""Preserve the 2025 parameter reference as source rows, never automatic model axes."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from copy import deepcopy
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import io
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree, DirectoryAnchor

DIRECTORY = Path("data/validation/pollen-productivity/legacyvegetation-2025")
SOURCE_SHA256 = "0c52e45ad13ce91d2683e5d78a985869d19e948affc20d563997492e13c4323b"
TABLES = ("original-study-estimates.csv", "synthesized-estimates.csv")
REGIONS = ("Asia", "Europe", "North America", "Northern Hemisphere")


def _available(text: str, *, positive: bool) -> bool:
    try:
        number = Decimal(text)
    except InvalidOperation:
        return False
    return number.is_finite() and (number > 0 if positive else number >= 0)


def _records(
    rows: Sequence[dict[str, str]], *, synthesis: bool
) -> list[dict[str, Any]]:
    workbook = "originals/" + (
        "synthesized-rpp.xlsx" if synthesis else "original-rpp.xlsx"
    )
    region_field, uncertainty = (
        ("region", "rpp_sd") if synthesis else ("continent", "rpp_se")
    )
    seen: set[tuple[str, ...]] = set()
    output = []
    for row in rows:
        required = {
            "taxon",
            "rpp",
            uncertainty,
            region_field,
            "source_workbook",
            "source_sheet",
            "source_row",
        }
        if not required <= set(row) or any(
            type(value) is not str for value in row.values()
        ):
            raise ValueError(
                "Literal source strings and required source locators are required"
            )
        identity = tuple(
            row[name]
            for name in ("source_workbook", "source_sheet", "source_row", region_field)
        )
        if (
            identity in seen
            or row["source_workbook"] != workbook
            or row["source_sheet"] != "Worksheet 1"
            or re.fullmatch(r"[1-9][0-9]*", row["source_row"]) is None
            or not (3 if synthesis else 2)
            <= int(row["source_row"])
            <= (133 if synthesis else 370)
            or row[region_field] not in (REGIONS if synthesis else REGIONS[:3])
            or not row["taxon"]
            or (
                synthesis
                and (
                    not row.get("taxonomic_level")
                    or "fall_speed" not in row
                    or "n_estimates" not in row
                )
            )
        ):
            raise ValueError(
                "Reference row identity is duplicated or outside the 2025 source table"
            )
        seen.add(identity)
        output.append(
            {
                **deepcopy(row),
                "source_row_identity": list(identity),
                "uncertainty_semantics": "source_label_SD"
                if synthesis
                else "source_label_SE",
                "nominal_rpp_available": _available(row["rpp"], positive=True),
                "uncertainty_available": _available(row[uncertainty], positive=False),
                "fall_speed_unit_status": "unqualified_native_vg"
                if synthesis
                else "not_supplied",
                "nominal_rpp_fsp_available": False,
                "uncertainty_model_admitted": False,
            }
        )
    return output


def adapt_reference(
    source: dict[str, Any],
    original_rows: Sequence[dict[str, str]],
    synthesized_rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    """Retain full row identity and literal availability without interpreting SD or vg."""
    if (
        source.get("schema_version") != "pollen-productivity-reference.v1"
        or source.get("paper", {}).get("doi") != "10.5194/essd-17-2007-2025"
        or "statistical_semantics" not in source
    ):
        raise ValueError("The declared 2025 parameter reference is required")
    original = _records(original_rows, synthesis=False)
    synthesis = _records(synthesized_rows, synthesis=True)
    return {
        "schema_version": "legacyvegetation-2025-parameter-coverage.v1",
        "paper": deepcopy(source["paper"]),
        "source_originals": deepcopy(source["source_originals"]),
        "statistical_semantics": deepcopy(source["statistical_semantics"]),
        "source_discrepancies": deepcopy(source.get("source_discrepancies", [])),
        "original_rows": original,
        "synthesized_rows": synthesis,
        "regional_coverage": [
            {
                "region": region,
                "source_rows": sum(r["region"] == region for r in synthesis),
                "nominal_rpp_rows": sum(
                    r["region"] == region and r["nominal_rpp_available"]
                    for r in synthesis
                ),
                "taxonomic_level_rows": dict(
                    Counter(
                        r["taxonomic_level"] for r in synthesis if r["region"] == region
                    )
                ),
            }
            for region in REGIONS
        ],
        "coverage_interpretation": "Counts describe literal source rows, not disjoint vegetation axes or independent parameter realizations. Genus/family and duplicate labels require explicit selection; no automatic panel is assembled.",
        "reference_normalization": source["statistical_semantics"]["rpp_units"],
        "missingness": "Blank and en-dash strings remain distinct; no European productivity is filled from another region.",
        "model_axes_selected": [],
        "scientific_admission": False,
        "automatic_parameter_replacement": False,
    }


def _table(raw: bytes, count: int) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("Reference CSV header is ambiguous")
    rows: list[dict[str, str]] = []
    for row in reader:
        if (
            len(rows) >= 1024
            or None in row
            or any(value is None for value in row.values())
        ):
            raise ValueError(
                "Reference CSV rows are unbounded or structurally ambiguous"
            )
        rows.append(row)
    if len(rows) != count:
        raise ValueError("Reference CSV population differs from its declaration")
    return rows


def read_reference(directory: Path, *, expected_source_sha256: str) -> dict[str, Any]:
    """Read three independently bound metadata files; workbooks and siblings stay opaque."""
    if re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256) is None:
        raise ValueError("Independent source metadata digest required")
    directory = directory.absolute()
    pins = []
    with DirectoryAnchor(directory) as anchor:

        def read(name: str, limit: int = 65536) -> bytes:
            anchor.check()
            with BoundedInputTree(
                directory, selected=name, max_bytes=limit, max_files=1
            ) as inputs:
                raw = inputs.read(directory / name, max_bytes=limit)
            anchor.check()
            pins.append(
                {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            )
            return raw

        raw = read("source.json")
        if sha256(raw).hexdigest() != expected_source_sha256:
            raise ValueError("Parameter metadata authority differs")
        source = json.loads(raw)
        declarations = source.get("reference_tables", [])
        if len(declarations) != 2 or {row["path"] for row in declarations} != set(
            TABLES
        ):
            raise ValueError("Exactly the two declared reference tables are required")
        tables = {}
        for name in TABLES:
            declaration = next(row for row in declarations if row["path"] == name)
            if (
                type(declaration["bytes"]) is not int
                or not 0 < declaration["bytes"] <= 65536
                or type(declaration["rows"]) is not int
                or not 0 <= declaration["rows"] <= 1024
            ):
                raise ValueError("Reference table declaration exceeds its finite bound")
            body = read(name, declaration["bytes"])
            if (
                len(body) != declaration["bytes"]
                or sha256(body).hexdigest() != declaration["sha256"]
            ):
                raise ValueError(
                    "Reference table bytes differ from the source authority"
                )
            tables[name] = _table(body, declaration["rows"])
        result = adapt_reference(source, tables[TABLES[0]], tables[TABLES[1]])
        anchor.check()
    result["source_pins"] = pins
    return result
