"""Re-read the full normalized source independently and qualify only descriptive census facts."""

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
from scanner import (  # noqa: E402 - authenticate the owned namespace before importing helpers.
    CollectionScanner,
    decode,
)

JOIN_FIELDS = (
    "record_id",
    "sjoid",
    "sj_uuid",
    "sj_vatten_id",
    "area_km2",
    "country",
    "layer_key",
)


def native(value: Any) -> Any:
    kind = type(value)
    if kind is dict:
        return ["object", [[key, native(item)] for key, item in value.items()]]
    if kind is list:
        return ["array", list(map(native, value))]
    if kind is str:
        return ["string", value]
    if kind is int:
        return ["integer", str(value)]
    if kind is bool:
        return ["boolean", value]
    if kind is Decimal:
        return ["decimal", str(value)]
    require(value is None, "Non-JSON native observation")
    return ["null"]


def shape(geometry: Any) -> dict[str, Any]:
    if type(geometry) is dict:
        coordinates = geometry.get("coordinates")
        kind = geometry.get("type")
    else:
        coordinates = None
        kind = None
    arrays: dict[str, int] = {}
    scalars: dict[str, int] = {}
    dimensions: dict[str, int] = {}
    xs: list[Decimal] = []
    ys: list[Decimal] = []

    def visit(value: Any) -> None:
        if isinstance(value, list):
            key = str(len(value))
            arrays[key] = arrays.get(key, 0) + 1
            if len(value) > 1 and all(type(v) in (int, Decimal) for v in value):
                dimensions[key] = dimensions.get(key, 0) + 1
                x, y = Decimal(value[0]), Decimal(value[1])
                if xs:
                    xs[:] = [min(xs[0], x), max(xs[1], x)]
                    ys[:] = [min(ys[0], y), max(ys[1], y)]
                else:
                    xs.extend((x, x))
                    ys.extend((y, y))
            for child in value:
                visit(child)
        else:
            name = native(value)[0]
            scalars[name] = scalars.get(name, 0) + 1

    visit(coordinates)
    return {
        "geometry_value_type": "object"
        if type(geometry) is dict
        else "array"
        if type(geometry) is list
        else native(geometry)[0],
        "coordinates_present": type(geometry) is dict and "coordinates" in geometry,
        "geometry_type": native(kind),
        "coordinate_array_lengths": dict(sorted(arrays.items())),
        "coordinate_scalar_types": dict(sorted(scalars.items())),
        "numeric_position_dimensions": dict(sorted(dimensions.items())),
        "native_xy_bounds": [str(xs[0]), str(ys[0]), str(xs[1]), str(ys[1])]
        if xs
        else None,
        "CRS_or_geometric_validity_qualified": False,
    }


def independently_validate(
    source: Path, ledger: Path, subset: dict[str, Any], limit: int = 16 * 1024**2
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    reader = CollectionScanner(source)
    count = 0
    proper = 0
    missing_geometry = 0
    missing_identity = 0
    other_properties = 0
    types: Counter[str] = Counter()
    properties: dict[str, Counter[str]] = {}
    ids: Counter[str] = Counter()
    identity_fields = ("record_id", "sjoid", "sj_uuid", "sj_vatten_id")
    field_values: dict[str, dict[str, int]] = {key: {} for key in identity_fields}
    field_missing = dict.fromkeys(identity_fields, 0)
    matches: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    references = subset["features"]
    require(type(references) is list, "Subset features array required")
    wanted = {row.get("properties", {}).get("record_id") for row in references}
    require(all(type(x) is str and x for x in wanted), "Subset native identity absent")
    with ledger.open("rb") as lines:
        for index, feature, digest in reader.features():
            raw = lines.readline(limit + 1)
            require(
                raw.endswith(b"\n") and len(raw) <= limit,
                "Missing/oversized feature ledger row",
            )
            actual = load_line(raw)
            obj = feature if type(feature) is dict else {}
            geometry = obj.get("geometry")
            props = obj.get("properties")
            expected = {
                "index": index,
                "raw_feature_sha256": digest,
                "feature_type": native(obj.get("type")),
                "properties_present": "properties" in obj,
                "properties": native(props),
                "geometry_present": "geometry" in obj,
                "geometry": shape(geometry),
            }
            require(
                exact(actual, expected),
                "Feature ledger differs from independent source at index " + str(index),
            )
            count += 1
            proper += obj.get("type") == "Feature"
            missing_geometry += geometry is None
            types[
                json.dumps(
                    native(geometry.get("type") if type(geometry) is dict else None),
                    separators=(",", ":"),
                )
            ] += 1
            if type(props) is dict:
                for name, value in props.items():
                    properties.setdefault(name, Counter())[native(value)[0]] += 1
                key = props.get("record_id")
                if type(key) is str and key:
                    ids[key] += 1
                    if key in wanted:
                        matches.setdefault(key, []).append((index, props))
                else:
                    missing_identity += 1
            else:
                other_properties += 1
                missing_identity += 1
            for field in identity_fields:
                item = props.get(field) if isinstance(props, dict) else None
                if type(item) is str and item:
                    existing = field_values[field]
                    existing[item] = existing.get(item, 0) + 1
                else:
                    field_missing[field] += 1
        require(lines.read(1) == b"", "Extra feature ledger row")
    require(reader.document_complete, "Independent source document incomplete")
    joins = []
    for index, ref in enumerate(references):
        props = ref["properties"]
        key = props["record_id"]
        observed = [
            {
                "full_source_index": full_index,
                "field_agreement": {
                    name: {
                        "subset_present": name in props,
                        "full_present": name in full,
                        "typed_value_equal": name in props
                        and name in full
                        and exact(native(props[name]), native(full[name])),
                    }
                    for name in JOIN_FIELDS
                },
            }
            for full_index, full in matches.get(key, [])
        ]
        joins.append(
            {
                "subset_index": index,
                "record_id": key,
                "full_source_matches": observed,
                "match_count": len(observed),
                "geometry_role": "Subset Point versus full source geometry is not geometric equivalence; no nearest-pollen selection rule is re-executed.",
            }
        )
    summary = {
        "feature_array_items": count,
        "proper_Feature_objects": proper,
        "missing_or_null_geometry": missing_geometry,
        "geometry_type_counts": dict(sorted(types.items())),
        "property_native_type_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(properties.items())
        },
        "non_object_properties": other_properties,
        "missing_or_non_string_or_empty_record_id": missing_identity,
        "distinct_nonempty_string_record_ids": len(ids),
        "duplicate_record_id_occurrences": sum(n - 1 for n in ids.values()),
        "duplicate_record_id_values": sum(n > 1 for n in ids.values()),
        "native_identity_field_counts": {
            field: {
                "nonempty_string_values": sum(values.values()),
                "distinct_values": len(values),
                "duplicate_occurrences": sum(value - 1 for value in values.values()),
                "duplicate_values": sum(value > 1 for value in values.values()),
                "missing_or_null_or_empty_or_non_string": field_missing[field],
            }
            for field, values in field_values.items()
        },
        "wrapper_metadata": native(reader.metadata),
        "max_raw_feature_bytes": reader.max_feature_bytes,
        "raw_feature_bytes": reader.total_feature_bytes,
    }
    return summary, joins


def load_line(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(values) == len({k for k, _ in values}), "Duplicate ledger key")
        return dict(values)

    return json.loads(
        raw,
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def validate_census_claims(actual: Any, expected: dict[str, Any]) -> None:
    require(
        exact(actual, expected), "Complete census claims differ from independent source"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    plan = load(args.plan)
    verify_frozen_pins(plan["input_pins"])
    output = Path(plan["output"])
    before = raw_process_snapshot()
    qualify_process_snapshot(before, plan["input_pins"], SOURCE)
    census = load(output / "census.json")
    require(
        census["candidate"] == plan["candidate"]
        and exact(census["plan"], pin(args.plan))
        and exact(census["source"], plan["full_registry"]),
        "Producer identity differs",
    )
    ledger = output / "feature-ledger.jsonl"
    require(
        exact(census["feature_ledger"], pin(ledger)), "Producer ledger binding differs"
    )
    subset = decode(Path(plan["subset"]["path"]).read_bytes())
    summary, joins = independently_validate(
        Path(plan["full_registry"]["path"]), ledger, subset
    )
    expected_census = {
        "schema_version": "svar-normalized-feature-census.v1",
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "source": plan["full_registry"],
        "feature_ledger": pin(ledger),
        "measured_source": summary,
        "scope": "Normalized source feature census only; original WFS provenance, provider units/CRS, rights, qualified registry review, dated basin truth and ranking remain unqualified.",
    }
    validate_census_claims(census, expected_census)
    progress = load(output / "stage-progress.json")
    require(
        type(progress) is list and len(progress) == 1,
        "Exactly one prior native producer required",
    )
    previous = progress[0]
    stage = plan["stages"][0]
    require(
        type(previous["actual_exit"]) is int
        and previous["actual_exit"] == 0
        and previous["timed_out"] is False
        and all(exact(previous[key], value) for key, value in stage.items()),
        "Original producer stage binding differs",
    )
    for role in ("stdout", "stderr"):
        target = output / (stage["id"] + "." + role)
        require(
            previous[role] == str(target)
            and previous[role + "_sha256"] == pin(target)["sha256"],
            "Producer log custody differs",
        )
    runtime = load(output / "census-runtime.json")
    require(
        exact(runtime["plan"], pin(args.plan))
        and runtime["candidate"] == plan["candidate"]
        and type(runtime["source_exit"]) is int
        and runtime["source_exit"] == 0
        and type(runtime["metadata_exit"]) is int
        and runtime["metadata_exit"] == 0,
        "Producer runtime custody failed",
    )
    for role in ("before", "after"):
        qualify_process_snapshot(runtime[role], plan["input_pins"], SOURCE)
    source_summary = load(Path(plan["source_summary"]["path"]))
    manifest = load(Path(plan["source_manifest"]["path"]))
    review = load(Path(plan["review_registry"]["path"]))
    rank = load(Path(plan["ranking_refusal"]["path"]))
    require(
        type(source_summary["lake_count"]) is int
        and source_summary["lake_count"] == 40565
        and manifest["normalized_lake_count"] == manifest["matched_lake_count"] == 40565
        and review["source_lake_count"] == 40523,
        "Original population claims changed",
    )
    require(
        len(joins) == 99
        and rank["candidate_count"] == 0
        and rank["methodology"]["refusal_reason"] == "governing_svar_registry_missing",
        "Original review/refusal scope changed",
    )
    dump(output / "subset-native-joins.json", joins)
    after = raw_process_snapshot()
    qualify_process_snapshot(after, plan["input_pins"], SOURCE)
    verify_frozen_pins(plan["input_pins"])
    dump(
        output / "independent-source-review.json",
        {
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "census": pin(output / "census.json"),
            "feature_ledger": pin(ledger),
            "subset_joins": pin(output / "subset-native-joins.json"),
            "complete_independent_source_and_typed_ledger_equal": True,
            "measured_source": summary,
            "retained_export_population_claim": 40565,
            "retained_review_population_claim": 40523,
            "measured_minus_export_claim": summary["feature_array_items"] - 40565,
            "measured_minus_review_claim": summary["feature_array_items"] - 40523,
            "original_review_population_membership_available": False,
            "identity_of_the_42_difference_established": False,
            "raw_WFS_export_link_qualified": False,
            "provider_units_CRS_or_effective_basin_area_qualified": False,
            "source_dates_are_chronology": False,
            "rights_or_human_review_admitted": False,
            "ranking_admitted": False,
            "current_ranked_candidate_count": 0,
            "tracked_byte_checker_exit": None,
            "observer_before": before,
            "observer_after": after,
        },
    )


if __name__ == "__main__":
    main()
