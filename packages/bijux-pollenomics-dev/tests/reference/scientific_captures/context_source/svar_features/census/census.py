"""Describe normalized source features without admitting registry authority or ranking."""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys
from typing import Any

_entry_file = Path(__file__).absolute()
if (
    _entry_file != _entry_file.resolve(strict=True)
    or not _entry_file.is_file()
    or any(part.is_symlink() for part in (_entry_file, *_entry_file.parents))
):
    raise ValueError("Physical absolute source entrypoint and ancestors required")
_entry_directory = _entry_file.parent
_expected_python = {
    "first_feature.py",
    "check_contracts.py",
    "common_runner.py",
    "observe.py",
    "stream.py",
    "census.py",
    "prepare.py",
    "run.py",
    "contracts.py",
    "scanner.py",
    "runtime.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Source alias or special entry refused before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected source directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected source import before helper import")
sys.path.insert(0, str(_entry_directory))
from contracts import (  # noqa: E402 - authenticate the owned namespace before importing helpers.
    SOURCE,
    dump,
    exact,
    load,
    pin,
    require,
    source_namespace,
    verify_frozen_pins,
)
from runtime import (  # noqa: E402 - authenticate the owned namespace before importing helpers.
    profile_guard,
    qualify_process_snapshot,
    raw_process_snapshot,
)
from stream import (  # noqa: E402 - authenticate the owned namespace before importing helpers.
    Collection,
)


def tagged(value: Any) -> Any:
    """Keep native JSON number types; raw feature hashes additionally retain lexemes."""
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["boolean", value]
    if type(value) is int:
        return ["integer", str(value)]
    if isinstance(value, Decimal):
        return ["decimal", str(value)]
    if type(value) is str:
        return ["string", value]
    if type(value) is list:
        return ["array", [tagged(v) for v in value]]
    require(type(value) is dict, "Unsupported decoded JSON type")
    return ["object", [[k, tagged(v)] for k, v in value.items()]]


def geometry_profile(geometry: Any) -> dict[str, Any]:
    arrays: Counter[str] = Counter()
    scalars: Counter[str] = Counter()
    positions: Counter[str] = Counter()
    bounds: list[Decimal] | None = None
    coordinates = geometry.get("coordinates") if type(geometry) is dict else None
    pending = [coordinates]
    while pending:
        value = pending.pop()
        if type(value) is list:
            arrays[str(len(value))] += 1
            if len(value) >= 2 and all(
                type(x) is int or isinstance(x, Decimal) for x in value
            ):
                positions[str(len(value))] += 1
                x, y = Decimal(value[0]), Decimal(value[1])
                if bounds is None:
                    bounds = [x, y, x, y]
                else:
                    bounds = [
                        min(bounds[0], x),
                        min(bounds[1], y),
                        max(bounds[2], x),
                        max(bounds[3], y),
                    ]
            pending.extend(reversed(value))
        else:
            scalars[tagged(value)[0]] += 1
    return {
        "geometry_value_type": "object"
        if type(geometry) is dict
        else "array"
        if type(geometry) is list
        else tagged(geometry)[0],
        "coordinates_present": type(geometry) is dict and "coordinates" in geometry,
        "geometry_type": tagged(
            geometry.get("type") if type(geometry) is dict else None
        ),
        "coordinate_array_lengths": dict(sorted(arrays.items())),
        "coordinate_scalar_types": dict(sorted(scalars.items())),
        "numeric_position_dimensions": dict(sorted(positions.items())),
        "native_xy_bounds": None if bounds is None else [str(x) for x in bounds],
        "CRS_or_geometric_validity_qualified": False,
    }


def record(index: int, feature: Any, raw_sha: str) -> dict[str, Any]:
    obj = feature if type(feature) is dict else {}
    return {
        "index": index,
        "raw_feature_sha256": raw_sha,
        "feature_type": tagged(obj.get("type")),
        "properties_present": "properties" in obj,
        "properties": tagged(obj.get("properties")),
        "geometry_present": "geometry" in obj,
        "geometry": geometry_profile(obj.get("geometry")),
    }


def summarize(path: Path, ledger: Path) -> dict[str, Any]:
    collection = Collection(path)
    total = 0
    proper = 0
    missing_geometry = 0
    geometry_types: Counter[str] = Counter()
    property_types: dict[str, Counter[str]] = {}
    identities: Counter[str] = Counter()
    native_ids: dict[str, Counter[str]] = {
        key: Counter() for key in ("record_id", "sjoid", "sj_uuid", "sj_vatten_id")
    }
    absent_ids: Counter[str] = Counter()
    missing_identity = 0
    other_properties = 0
    with ledger.open("x", encoding="utf-8") as target:
        for index, feature, digest in collection.features():
            total += 1
            obj = feature if type(feature) is dict else {}
            proper += obj.get("type") == "Feature"
            geometry = obj.get("geometry")
            missing_geometry += geometry is None
            geometry_types[
                json.dumps(
                    tagged(geometry.get("type") if type(geometry) is dict else None),
                    separators=(",", ":"),
                )
            ] += 1
            props = obj.get("properties")
            if type(props) is dict:
                for key, value in props.items():
                    property_types.setdefault(key, Counter())[tagged(value)[0]] += 1
                native = props.get("record_id")
                if type(native) is str and native:
                    identities[native] += 1
                else:
                    missing_identity += 1
            else:
                other_properties += 1
                missing_identity += 1
            for field, values in native_ids.items():
                item = props.get(field) if type(props) is dict else None
                if type(item) is str and item:
                    values[item] += 1
                else:
                    absent_ids[field] += 1
            target.write(
                json.dumps(
                    record(index, feature, digest),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            )
    require(collection.document_complete, "Incomplete normalized source")
    return {
        "feature_array_items": total,
        "proper_Feature_objects": proper,
        "missing_or_null_geometry": missing_geometry,
        "geometry_type_counts": dict(sorted(geometry_types.items())),
        "property_native_type_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(property_types.items())
        },
        "non_object_properties": other_properties,
        "missing_or_non_string_or_empty_record_id": missing_identity,
        "distinct_nonempty_string_record_ids": len(identities),
        "duplicate_record_id_occurrences": sum(n - 1 for n in identities.values()),
        "duplicate_record_id_values": sum(n > 1 for n in identities.values()),
        "native_identity_field_counts": {
            field: {
                "nonempty_string_values": sum(values.values()),
                "distinct_values": len(values),
                "duplicate_occurrences": sum(n - 1 for n in values.values()),
                "duplicate_values": sum(n > 1 for n in values.values()),
                "missing_or_null_or_empty_or_non_string": absent_ids[field],
            }
            for field, values in native_ids.items()
        },
        "wrapper_metadata": tagged(collection.metadata),
        "max_raw_feature_bytes": collection.max_feature_bytes,
        "raw_feature_bytes": collection.total_feature_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    plan = load(args.plan)
    verify_frozen_pins(plan["input_pins"])
    output = Path(plan["output"])
    observation: dict[str, Any] = {
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "source_exit": None,
        "metadata_exit": None,
        "before": None,
        "after": None,
    }
    observation["before"] = raw_process_snapshot()
    dump(output / "census-runtime.json", observation)
    qualify_process_snapshot(observation["before"], plan["input_pins"], SOURCE)
    source = Path(plan["full_registry"]["path"])
    require(exact(pin(source), plan["full_registry"]), "Original registry changed")
    ledger = output / "feature-ledger.jsonl"
    summary = summarize(source, ledger)
    observation["source_exit"] = 0
    dump(output / "census-runtime.json", observation)
    dump(
        output / "census.json",
        {
            "schema_version": "svar-normalized-feature-census.v1",
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "source": plan["full_registry"],
            "feature_ledger": pin(ledger),
            "measured_source": summary,
            "scope": "Normalized source feature census only; original WFS provenance, provider units/CRS, rights, qualified registry review, dated basin truth and ranking remain unqualified.",
        },
    )
    observation["after"] = raw_process_snapshot()
    dump(output / "census-runtime.json", observation)
    qualify_process_snapshot(observation["after"], plan["input_pins"], SOURCE)
    verify_frozen_pins(plan["input_pins"])
    observation["metadata_exit"] = 0
    dump(output / "census-runtime.json", observation)
    print(
        json.dumps(
            {
                "census": pin(output / "census.json"),
                "source_exit": 0,
                "metadata_exit": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
