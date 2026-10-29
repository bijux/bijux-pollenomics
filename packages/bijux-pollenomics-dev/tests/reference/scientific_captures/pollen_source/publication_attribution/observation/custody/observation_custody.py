"""Bind saved native execution to retained sources without inventing package imports."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

import contracts as c

ORIGINAL_PLAN_SHA = "ca4003d9c94379843d7803d8cc213c7fe89be4789615dce58fcc4a0c779fb11f"
RETENTION_SHA = "b0d4e5219f7f4d631e5f3125cfc6168cff765d6bcac527eef191daa127712c2c"
SOURCE_SHA = {
    "publication": "e884947655566a7eb6d4f0390d10dff80d4d285a2be32f720161d68b83346d1f",
    "doi": "a74034a8c21f7298183a7d89f625f1308fd3000b18a4d9105f00e547404424ec",
}
IMPORTS = {
    "publication": [
        "from __future__ import annotations",
        "import argparse",
        "from collections import Counter",
        "from hashlib import sha256",
        "import json",
        "from pathlib import Path",
        "from typing import Any",
        "from bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake import parse_dataset_publications",
    ],
    "doi": [
        "from __future__ import annotations",
        "import argparse",
        "from collections import Counter",
        "from hashlib import sha256",
        "import json",
        "from pathlib import Path",
        "from typing import Any",
        "from urllib.parse import quote, urlsplit",
    ],
}


def source_role(kind: str, raw: bytes, origins: Any, expected: Any) -> None:
    """A run-path CLI is authenticated separately from its imported module census."""
    c.require(kind in SOURCE_SHA, "Unknown maintained source role")
    c.require(
        hashlib.sha256(raw).hexdigest() == SOURCE_SHA[kind],
        "Executed source hash changed",
    )
    imports = [
        ast.unparse(node)
        for node in ast.walk(ast.parse(raw))
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    c.require(
        c.exact(imports, IMPORTS[kind]), "Maintained source import contract changed"
    )
    c.require(
        type(origins) is list and c.exact(origins, expected),
        "Complete saved package-origin census differs",
    )
    c.require(
        all(
            type(row) is dict
            and set(row) == {"module", "path", "sha256", "bytes"}
            and type(row["module"]) is str
            for row in origins
        ),
        "Malformed package origin",
    )
    names = [row["module"] for row in origins]
    c.require(names == sorted(set(names)), "Package origins must be sorted and unique")
    if kind == "doi":
        c.require(origins == [], "Standalone stdlib DOI CLI claimed package imports")
    else:
        c.require(
            "bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake"
            in names,
            "Publication parser package origin missing",
        )
        c.require(
            all(
                name.startswith(("bijux_pollenomics", "pollenomics", "lra."))
                or name == "lra"
                for name in names
            ),
            "Foreign claimed package origin",
        )


def bridge(generated: Any, governed: Any, field: str, old: str, current: str) -> None:
    """Only the declared provenance leaf may differ; every other JSON type/value/order is exact."""
    c.require(
        type(old) is str and type(current) is str and old != current,
        "Distinct literal metadata hashes required",
    )
    adjusted = deepcopy(governed)
    keys = field.split(".")
    a, b = adjusted, generated
    for key in keys[:-1]:
        c.require(
            type(a) is dict and type(b) is dict and key in a and key in b,
            "Metadata bridge path missing",
        )
        a, b = a[key], b[key]
    c.require(
        type(a) is dict
        and type(b) is dict
        and a.get(keys[-1]) == old
        and b.get(keys[-1]) == current,
        "Named provenance leaf changed unexpectedly",
    )
    a[keys[-1]] = current
    c.require(c.exact(adjusted, generated), "Difference outside named provenance leaf")


def retained_inputs(
    context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str], list[dict[str, Any]]]:
    """Keep original expected hashes while mapping copied sources to their retained bytes."""
    for label in (
        "original_plan",
        "original_common",
        "original_inner",
        "original_outer",
        "source_retention",
    ):
        c.require(
            c.pin(Path(context[label]["path"])) == context[label],
            "Saved native/reference bytes changed: " + label,
        )
    c.require(
        context["original_plan"]["sha256"] == ORIGINAL_PLAN_SHA
        and context["source_retention"]["sha256"] == RETENTION_SHA,
        "Original source authority differs",
    )
    plan = c.load(Path(context["original_plan"]["path"]))
    common = c.load(Path(context["original_common"]["path"]))
    inner = c.load(Path(context["original_inner"]["path"]))
    outer = c.load(Path(context["original_outer"]["path"]))
    c.require(
        type(common["actual_exit"]) is int
        and common["actual_exit"] == 1
        and inner["actual_exit"] == 1
        and outer["actual_exit"] == 1,
        "Original failed whole execution was relabelled",
    )
    c.require(
        common["plan_sha256"]
        == inner["plan_sha256"]
        == outer["plan_sha256"]
        == ORIGINAL_PLAN_SHA,
        "Original terminal/plan binding differs",
    )
    c.require(
        common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
        and common["absent_input_paths_unchanged"] is True,
        "Original input custody failed",
    )
    c.require(
        len(common["stages"]) == 3
        and [s["actual_exit"] for s in common["stages"]] == [0, 0, 1]
        and all(type(s["actual_exit"]) is int for s in common["stages"]),
        "Original producer/observer statuses differ",
    )
    c.require(
        outer["before_runtime_error"] is None
        and outer["after_runtime_error"] is None
        and outer["timed_out"] is False,
        "Original runtime errors differ",
    )
    c.require(
        [x["checker_actual_exit"] for x in inner["tracked_byte_comparisons"]] == [2, 2],
        "Original tracked checker failures were relabelled",
    )
    c.require(
        c.exact(
            common["products"],
            [r["original_common_product"] for r in context["original_common_products"]],
        ),
        "Original complete product inventory differs",
    )
    pins = [
        context[k]
        for k in (
            "original_plan",
            "original_common",
            "original_inner",
            "original_outer",
            "source_retention",
        )
    ]
    for record in context["original_common_products"]:
        old, final = record["original_common_product"], record["completed_pin"]
        c.require(
            c.pin(Path(final["path"])) == final and old["path"] == final["path"],
            "Saved native output changed",
        )
        raw = Path(final["path"]).read_bytes()
        c.require(
            hashlib.sha256(raw[: old["bytes"]]).hexdigest() == old["sha256"]
            and raw[old["bytes"] :].hex() == record["append_only_tail_hex"]
            and len(raw) - old["bytes"] == record["append_only_tail_bytes"],
            "Original output prefix/tail differs",
        )
        c.require(
            old == final or Path(final["path"]).name == "runtime-delegate.stdout",
            "Only the final common-terminal print may extend its original stream",
        )
        pins.append(final)
    retention_path = Path(context["source_retention"]["path"])
    retention = c.load(retention_path)
    catalog_path = retention_path.parent / "ordered-original-input-identities.json"
    catalog = c.load(catalog_path)
    c.require(
        len(catalog) == len(plan["input_pins"]) == 66723,
        "Complete original ordered inputs required",
    )
    for name, expected in retention["members"].items():
        p = retention_path.parent / name
        c.require(c.pin(p) == {"path": str(p), **expected}, "Retained member changed")
        pins.append(c.pin(p))
    mapped = {}
    for index, (row, original) in enumerate(
        zip(catalog, plan["input_pins"], strict=True)
    ):
        c.require(
            c.exact({k: row[k] for k in ("path", "sha256", "bytes")}, original)
            and type(row["original_index"]) is int
            and row["original_index"] == index,
            "Original ordered input identity differs",
        )
        member = row["retained_member"]
        if member is not None:
            target = retention_path.parent / member
            expected = {**original, "path": str(target)}
            c.require(c.pin(target) == expected, "Retained original source differs")
            mapped[original["path"]] = str(target)
        else:
            c.require(
                row["retention_role"]
                in {
                    "omitted_runtime_or_dependency_identity_only",
                    "omitted_private_capture_payload_identity_only",
                    "omitted_first_party_bytecode_identity_only",
                },
                "Unknown omitted role",
            )
            c.require(
                c.pin(Path(original["path"])) == original,
                "Original uncopied input changed",
            )
            pins.append(original)
    return plan, mapped, c.union(pins)


def original_file(custody: dict[str, Any], path: Path) -> Path:
    return Path(custody["retained_original_paths"].get(str(path), str(path)))


def producer_progress(actual: Any, sealed: Any) -> list[dict[str, Any]]:
    """The completed failed run includes its third observer row; retain that row unchanged."""
    c.require(
        type(actual) is list and c.exact(actual, sealed) and len(actual) == 3,
        "Complete original stage history differs",
    )
    c.require(
        all(type(row["actual_exit"]) is int for row in actual)
        and [row["actual_exit"] for row in actual] == [0, 0, 1],
        "Original native/observer exits differ",
    )
    return list(actual[:2])
