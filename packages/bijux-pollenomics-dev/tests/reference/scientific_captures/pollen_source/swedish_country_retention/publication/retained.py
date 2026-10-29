"""Freeze genuine normally returned country and separately qualified saved-observer records."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from contracts import SOURCE, require, strict_equal, verify_private_ancestry
from publication import REF_NAMES, qualify_saved
from runtime_contracts import namespace_snapshot, verify_base_namespaces
from source_inputs import exact_union, verify_rows

COUNTRY_AUTHORITY_SHA = (
    "b2d202e0cb62088cc9e754effcb8a10db9f2436aae8b1e25ad4429ff7fe8f1c5"
)
SAVED_AUTHORITY_SHA = "2e30ecdd2e64581afb30f8ad1c9990511c553db14c8a8626ca853ccdaed0bced"
MAXIMUM_METADATA_BYTES = 128 * 1024**2


def raw_json(row: dict[str, Any], *, list_allowed: bool = False) -> Any:
    path = Path(row["path"])
    require(
        path.is_absolute()
        and ".." not in path.parts
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents))
        and path.is_file()
        and path.stat().st_nlink == 1
        and type(row["bytes"]) is int
        and 0 <= row["bytes"] <= MAXIMUM_METADATA_BYTES
        and path.stat().st_size == row["bytes"],
        "Physical exact bounded metadata required",
    )
    raw = path.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Expected metadata buffer differs",
    )

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        require(
            len(values) == len({key for key, _ in values}), "Duplicate metadata key"
        )
        return dict(values)

    def refused(value: str) -> None:
        raise ValueError("Nonfinite metadata scalar: " + value)

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=refused)
    require(
        type(value) is dict or list_allowed and type(value) is list,
        "Metadata role type differs",
    )
    return value


def source_authority(name: str, sha: str) -> dict[str, Any]:
    path = SOURCE / name
    require(path.stat().st_size <= 16384, "Source authority metadata exceeds ceiling")
    value = raw_json({"path": str(path), "sha256": sha, "bytes": path.stat().st_size})
    assert isinstance(value, dict)
    return value


def closed_namespace(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    entries: dict[str, dict[str, str]] = {}
    for row in rows:
        path = Path(row["path"])
        require(
            path.is_relative_to(root), "Original output escaped its exact namespace"
        )
        relative = path.relative_to(root)
        require(bool(relative.parts), "Output row names directory root")
        entries[relative.as_posix()] = {"kind": "file"}
        for parent in relative.parents:
            if parent != Path("."):
                require(
                    entries.get(parent.as_posix(), {"kind": "directory"})
                    == {"kind": "directory"},
                    "Original output type conflict",
                )
                entries[parent.as_posix()] = {"kind": "directory"}
    for name in ("cache", "cache/matplotlib", "scratch"):
        require(
            entries.get(name, {"kind": "directory"}) == {"kind": "directory"},
            "Original empty directory role differs",
        )
        entries[name] = {"kind": "directory"}
    return {"root": str(root), "excluded": [], "entries": dict(sorted(entries.items()))}


def authenticate() -> dict[str, Any]:
    country_authority = source_authority(
        "country-authority.json", COUNTRY_AUTHORITY_SHA
    )
    saved_authority = source_authority("saved-authority.json", SAVED_AUTHORITY_SHA)
    require(
        saved_authority["collected_whole_exit"] == 0
        and strict_equal(saved_authority["stage_exits"], [0])
        and saved_authority["original_controller_actual_exit"] == 1
        and saved_authority["original_whole_actual_exit"] == 1
        and saved_authority["country_call_returned_normally"] is True,
        "Only genuine collected saved observation may be retained",
    )
    country_refs = country_authority["references"]
    saved_refs = saved_authority["references"]
    documents: dict[str, Any] = {}
    identities: dict[str, dict[str, Any]] = {}

    def attach(name: str, row: dict[str, Any]) -> None:
        require(name not in documents, "Duplicate reference role")
        identities[name] = deepcopy(row)
        documents[name] = raw_json(row, list_allowed=name == "country-progress")

    for name, filename in (
        ("country-plan", "plan.json"),
        ("country-inner", "sweden-country-semantic-terminal.json"),
        ("country-outer", "sweden-country-semantic-launch-terminal.json"),
        ("country-progress", "stage-progress.json"),
        ("country-clock", "country-clock-observation.json"),
        ("country-callable", "country-callable-identity.json"),
        ("country-products", "output-products.json"),
        ("country-receipt", "producer/receipt.json"),
    ):
        attach(name, country_refs[filename])
    for name, filename in (
        ("saved-plan", "plan.json"),
        ("saved-inner", "sweden-country-semantic-terminal.json"),
        ("saved-outer", "sweden-country-semantic-launch-terminal.json"),
        ("saved-review", "independent-country-review.json"),
        ("saved-products", "output-products.json"),
        ("saved-history", "retained-country-authority.json"),
    ):
        attach(name, saved_refs[filename])
    country = documents["country-plan"]
    saved = documents["saved-plan"]
    attach("owned-source-ledger", country["source_ledger"])
    attach("pre-country-history", country["retained_failed_controller_history"])
    attach("runtime-plan", country["qualified_source_runtime"]["plan"])
    for name, role in (
        ("runtime-common", "common"),
        ("runtime-outer", "outer"),
        ("runtime-review", "independent_review"),
    ):
        attach(name, country["qualified_source_runtime"][role])
    source_rows = {}
    for prefix, plan, suffix in (
        ("country", country, "sweden-country-callable-evidence-custody"),
        ("saved", saved, "sweden-country-saved-semantic-custody"),
    ):
        for key, filename in (
            ("manifest", "prepared-source-manifest.json"),
            ("review", "independent-source-review.json"),
        ):
            found = [
                row
                for row in plan["input_pins"]
                if row["path"].endswith("/" + suffix + "/" + filename)
            ]
            require(len(found) == 1, "One exact executed source authority required")
            attach(prefix + "-controller-" + key, found[0])
        manifest = documents[prefix + "-controller-manifest"]
        source_rows[prefix] = deepcopy(manifest["files"])
    original_declaration = [
        row
        for row in source_rows["country"]
        if row["path"].endswith("/declared-inputs.json")
    ]
    require(
        len(original_declaration) == 1,
        "Exact original complete source declaration required",
    )
    attach("source-declaration", original_declaration[0])
    require(set(documents) == set(REF_NAMES), "Reference role union incomplete")
    witness = qualify_saved(documents, identities, country_refs)
    ancestry = sorted(
        {
            row["path"]
            for key in ("original_sources", "original_data_inputs")
            for row in documents["owned-source-ledger"][key]
        }
    )
    verify_private_ancestry(Path("/"), ancestry)
    output_rows = {}
    snapshots = deepcopy(saved["owned_namespace_snapshots"])
    for prefix, refs, plan in (
        ("country", country_refs, country),
        ("saved", saved_refs, saved),
    ):
        root = Path(plan["output"])
        inner = documents[prefix + "-inner"]
        outer = documents[prefix + "-outer"]
        streams = [
            stage[key] for stage in inner["stages"] for key in ("stdout", "stderr")
        ]
        streams += [outer[key] for key in ("stdout", "stderr")]
        rows = exact_union(
            documents[prefix + "-products"]["files"], list(refs.values()), streams
        )
        snapshot = closed_namespace(root, rows)
        require(
            namespace_snapshot(root, []) == snapshot,
            "Complete genuine output namespace changed",
        )
        output_rows[prefix] = rows
        existing = [row for row in snapshots if row["root"] == str(root)]
        require(
            not existing or strict_equal(existing, [snapshot]),
            "Retained original snapshot role differs",
        )
        if not existing:
            snapshots.append(snapshot)
    frozen = exact_union(
        saved["input_pins"], *output_rows.values(), list(identities.values())
    )
    verify_rows(frozen)
    verify_base_namespaces(snapshots)
    return {
        "documents": documents,
        "identities": identities,
        "original_references": country_refs,
        "witness": witness,
        "original_physical_ancestry_paths": ancestry,
        "input_pins": frozen,
        "snapshots": snapshots,
        "output_rows": output_rows,
        "source_rows": source_rows,
        "saved_plan": saved,
        "country_plan": country,
        "retained_logical_output_bytes": saved["retained_logical_output_bytes"]
        + sum(row["bytes"] for row in output_rows["saved"]),
    }
