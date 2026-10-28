"""Bind primary pollen counts to source-labelled Neotoma rows without taxonomy claims."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

BASE = Path(
    "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
BASE_SHA = "92019a8331209d7247702193bbdfbe359807d7ee1df92566fcf31935f6b273d4"
PREFIX = BASE.parents[1]
COMMON_SHA = "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a"
PRODUCER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py"
FAMILY = "docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/"
OWNER = "countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report-products"
REPORT = FAMILY + "report.json"
SAMPLES = FAMILY + "samples.csv"
PRIMARY = "landclim/pangaea/solsoe/solsoe81-pollen-739834.txt"
MANIFEST = "data/neotoma/relational/manifest.json"
RELATIONAL = "data/neotoma/relational/"
UNIT = "neotoma:collection-unit:4303"
SITE = "neotoma:site:3432"
SOURCE = Path(__file__).resolve().parent


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file() and not path.is_symlink(),
        "Physical regular input required: " + str(path),
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def load(path: Path) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len({k for k, _ in rows}) == len(rows), "Duplicate JSON keys")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant
    )


def dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def input_catalog() -> list[dict[str, Any]]:
    value = load(SOURCE / "declared-inputs.json")["inputs"]
    require(
        isinstance(value, list)
        and len(value) == 12
        and len({row["path"] for row in value}) == 12,
        "Exact twelve declared source inputs required",
    )
    return list(value)


def owner_contract(inventory: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in inventory["owners"] if row.get("owner_id") == OWNER]
    require(len(rows) == 1, "Exactly one named pollen-lineage owner required")
    row = rows[0]
    require(
        set(row)
        == {
            "owner_id",
            "role",
            "paths",
            "producer_paths",
            "producer_inputs",
            "verification",
        },
        "Named owner fields differ",
    )
    expected = sorted(
        item["path"] for item in input_catalog() if item["path"].startswith(RELATIONAL)
    )
    require(
        row["role"] == "unresolved"
        and exact(row["paths"], [REPORT, SAMPLES])
        and exact(row["producer_paths"], [PRODUCER])
        and exact(row["producer_inputs"], expected),
        "Named two-product owner boundary differs",
    )
    require(
        type(row["verification"]) is str and bool(row["verification"]),
        "Owner source/rights limits required",
    )
    return dict(row)


def primary_table(raw: bytes) -> tuple[list[str], list[tuple[int, list[int]]]]:
    text = raw.decode("utf-8")
    require(
        all(
            marker in text
            for marker in (
                "10.1594/PANGAEA.739834",
                "Event(s):\tSOLSOE81",
                "Area: 2.5 ha.",
                "Creative Commons Attribution-NonCommercial 3.0 Unported",
            )
        )
        and text.count("*/\n") == 1,
        "Primary citation/event/rights/table boundary differs",
    )
    metadata, table = text.split("*/\n")
    axes = []
    for line in metadata.splitlines():
        if line.startswith("\t") and " [#] (" in line and ") * PI:" in line:
            name, remainder = line[1:].split(" [#] (", 1)
            axes.append((name, remainder.split(") * PI:", 1)[0]))
    parsed = list(csv.reader(io.StringIO(table), delimiter="\t"))
    require(
        bool(axes) and len({name for name, _ in axes}) == len(axes),
        "Primary parameter names duplicate or absent",
    )
    header, *rows = parsed
    require(
        header[0] == "Depth sed [m]"
        and len(header) == len(axes) + 1
        and len(set(header)) == len(header),
        "Primary column axes differ",
    )
    require(
        all(
            label.startswith(short + " [#]")
            for label, (_, short) in zip(header[1:], axes, strict=True)
        ),
        "Primary parameter order differs",
    )
    values = []
    for row in rows:
        require(len(row) == len(header), "Primary ragged count row")
        depth = Decimal(row[0]) * 100
        require(
            depth.is_finite() and depth == depth.to_integral_value(),
            "Primary depth must be exact integral centimetres",
        )
        require(
            all(value and value.isascii() and value.isdigit() for value in row[1:]),
            "Primary counts must be nonnegative integers",
        )
        values.append((int(depth), [int(value) for value in row[1:]]))
    require(
        bool(values) and len({depth for depth, _ in values}) == len(values),
        "Primary depths duplicate or absent",
    )
    return [name for name, _ in axes], sorted(values, key=lambda row: row[0])


def reconcile(
    raw: bytes, samples: list[dict[str, Any]], observations: Iterable[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    names, primary = primary_table(raw)
    selected = [row for row in samples if row["collection_unit_id"] == UNIT]
    require(
        bool(selected) and all(row["site_id"] == SITE for row in selected),
        "Selected source sample site differs",
    )
    require(
        all(type(row["sample_id"]) is str and row["sample_id"] for row in selected),
        "Native source sample IDs required",
    )
    by_depth = {Decimal(str(row["source_depth"])): row["sample_id"] for row in selected}
    require(
        len(by_depth) == len(selected) == len({row["sample_id"] for row in selected}),
        "Native source depths or sample IDs duplicate",
    )
    require(
        set(by_depth) == {Decimal(depth) for depth, _ in primary},
        "Primary/native source depth sets differ",
    )
    counts: dict[str, dict[str, int]] = {row["sample_id"]: {} for row in selected}
    for row in observations:
        if row["sample_id"] not in counts:
            continue
        require(
            row["collection_unit_id"] == UNIT
            and row["site_id"] == SITE
            and row["source_unit"] == "NISP"
            and row["unit_family"] == "count",
            "Native pollen observation source role differs",
        )
        value, name = row["source_value"], row["source_reported_name"]
        require(
            type(value) is int
            and value > 0
            and type(name) is str
            and bool(name)
            and name not in counts[row["sample_id"]],
            "Duplicate, mistyped or nonpositive sparse observation",
        )
        counts[row["sample_id"]][name] = value
    native_names = set().union(*(set(row) for row in counts.values()))
    same = set(names) & native_names
    source_only = sorted(set(names) - native_names)
    native_only = native_names - set(names)
    vectors: dict[tuple[int, ...], list[str]] = {}
    for name in native_only:
        signature = tuple(
            counts[by_depth[Decimal(depth)]].get(name, 0) for depth, _ in primary
        )
        vectors.setdefault(signature, []).append(name)
    mapping = {name: name for name in same}
    candidates = []
    for name in source_only:
        signature = tuple(row[names.index(name)] for _, row in primary)
        matches = vectors.get(signature, [])
        require(len(matches) == 1, "Renamed source count vector is absent or ambiguous")
        mapping[name] = matches[0]
        candidates.append(
            {
                "pangaea_parameter_name": name,
                "neotoma_source_reported_name": matches[0],
                "positive_sample_count": sum(value > 0 for value in signature),
                "source_count_sum": sum(signature),
                "vector_equal_at_all_66_depths": True,
                "status": "numeric_source_name_candidate_not_ecological_approval",
            }
        )
    require(
        len(mapping) == len(names) == len(native_names) == len(set(mapping.values())),
        "Source/native name mapping is not bijective",
    )
    ledger = []
    positive = 0
    total = 0
    for depth, values in primary:
        native = counts[by_depth[Decimal(depth)]]
        require(
            all(
                native.get(mapping[name], 0) == value
                for name, value in zip(names, values, strict=True)
            ),
            "A source/native count cell differs",
        )
        observed = sum(value > 0 for value in values)
        require(
            observed == len(native), "Native sparse absence/zero distinction differs"
        )
        positive += observed
        total += sum(values)
        ledger.append(
            {
                "depth_cm": depth,
                "neotoma_sample_id": by_depth[Decimal(depth)],
                "positive_source_taxa": observed,
                "source_count_sum": sum(values),
                "positive_counts_equal": True,
            }
        )
    derived = {
        "primary_profile_rows": len(primary),
        "primary_parameter_count": len(names),
        "primary_count_cells": len(primary) * len(names),
        "primary_positive_count_cells": positive,
        "primary_zero_count_cells": len(primary) * len(names) - positive,
        "primary_total_count": total,
        "neotoma_1981_sample_count": len(selected),
        "neotoma_positive_observation_count": sum(len(row) for row in counts.values()),
        "exact_same_name_parameter_count": len(same),
        "numeric_rename_candidate_count": len(candidates),
        "numeric_rename_candidates": candidates,
    }
    return derived, ledger


def part_rows(
    repository: Path, manifest: dict[str, Any], surface: str
) -> Iterator[dict[str, Any]]:
    declared = {row["path"]: row for row in input_catalog()}
    descriptor = manifest["surfaces"][surface]
    parts = descriptor["parts"]
    require(
        type(descriptor["part_count"]) is int
        and descriptor["part_count"] == len(parts)
        and len({part["path"] for part in parts}) == len(parts),
        "Relational part membership differs",
    )
    for part in parts:
        relative = part["path"]
        require(
            isinstance(relative, str)
            and PurePosixPath(relative).as_posix() == relative
            and not PurePosixPath(relative).is_absolute()
            and ".." not in PurePosixPath(relative).parts,
            "Unsafe relational part path",
        )
        name = RELATIONAL + relative
        require(name in declared, "Undeclared relational input")
        path = repository / name
        require(
            exact(pin(path), {**declared[name], "path": str(path)})
            and part["sha256"] == declared[name]["sha256"],
            "Relational part input differs",
        )
        rows = load(path)["rows"]
        require(
            type(part["row_count"]) is int and len(rows) == part["row_count"],
            "Relational row count differs",
        )
        yield from rows


def verify_products(
    report: dict[str, Any],
    expected: dict[str, Any],
    rows: list[dict[str, Any]],
    csv_raw: bytes,
    derived: dict[str, Any],
) -> None:
    require(exact(report, expected), "Complete canonical report typed fields differ")
    require(
        all(exact(report[key], value) for key, value in derived.items()),
        "Independent source count/depth/name joins differ",
    )
    require(
        exact(report["author_79_sample_selection_identified"], False)
        and exact(report["author_chronology_identified"], False)
        and exact(report["lra_admitted_samples"], 0),
        "Unresolved selection/chronology/LRA scope differs",
    )
    require(
        report["source_rights"]
        == "PANGAEA CC BY-NC 3.0; primary raw text remains external",
        "Primary rights scope differs",
    )
    for key in (
        "all_source_sample_depths_match_exactly_cm",
        "all_positive_source_counts_match_exactly",
        "neotoma_zero_cells_are_sparse_absences",
    ):
        require(exact(report[key], True), "Source equality/absence flag differs")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "depth_cm",
            "neotoma_sample_id",
            "positive_source_taxa",
            "source_count_sum",
            "positive_counts_equal",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    require(
        csv_raw == stream.getvalue().encode("utf-8"),
        "Complete ordered sample CSV differs from independent source ledger",
    )
