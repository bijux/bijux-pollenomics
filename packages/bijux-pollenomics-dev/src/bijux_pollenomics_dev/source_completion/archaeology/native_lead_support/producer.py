"""Preserve the complete finite indexed support in private native witnesses."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import cast

from pyproj import Transformer

from bijux_pollenomics.collection.sources.raa.geometry.binary import describe_geometry
from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    read_only_database,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    read_blob,
)

from .geometry import envelope_distances, support_class
from .native import (
    allow_native_rtree_reads,
    candidates,
    indexed_rows,
    inspect_local_schema,
    native,
    require,
)
from .streams import NativeWitness, WitnessBudget

_HISTORICAL_LEAD_CONTEXT = GitSourceMember(
    member="reports/needed/field-decisions.json",
    repository_path="reports/needed/field-decisions.json",
    source_revision="1410f5f0f33d32410191d27edc8862037fe89e00",
    git_blob="1d79a53507beb3dffc6d68a1b71fa62afe5955c3",
    sha256="a7cfb5a9521c17e56cbb96f113ab6a7b3619f4047000de0690718ff7b364eda5",
    bytes=64527,
)


def _lead_input_bytes(root: Path, pinned: Mapping[str, object]) -> bytes:
    """Read the sealed lead context without restoring a current decision registry."""
    if pinned["path"] == _HISTORICAL_LEAD_CONTEXT.member:
        require(
            type(pinned.get("bytes")) is int
            and pinned
            == {
                "path": _HISTORICAL_LEAD_CONTEXT.member,
                "sha256": _HISTORICAL_LEAD_CONTEXT.sha256,
                "bytes": _HISTORICAL_LEAD_CONTEXT.bytes,
            },
            "historical lead context pin differs",
        )
        return read_blob(root, _HISTORICAL_LEAD_CONTEXT)
    path = root / str(pinned["path"])
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "lead input symlink ancestor",
    )
    return path.read_bytes()


def native_family(
    connection: sqlite3.Connection, table: str, uuid: str, limit: int
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """A large ancillary family is a named refusal, never a truncated population."""
    try:
        return indexed_rows(connection, table, uuid, limit)
    except ValueError as error:
        if str(error) != "local native owner/child limit exceeded":
            raise
        return [], {
            "status": "refused_direct_family_exceeds_finite_row_limit",
            "minimum_source_rows": limit + 1,
            "row_limit": limit,
            "source_rows_retained": 0,
            "truncated_rows_admitted": False,
        }


def build_private(
    root: Path, source_root: Path, destination: Path
) -> dict[str, object]:
    """Retain finite indexed geometry and native ownership witnesses."""
    require(
        not destination.exists()
        and ".." not in destination.parts
        and destination.is_relative_to(root / "artifacts"),
        "fresh owned output required",
    )
    require(
        not any(p.is_symlink() for p in (destination, *destination.parents)),
        "output lexical symlink ancestor",
    )
    protocol = json.loads(
        (
            root / "reports/science/archaeology-native-lead-support/protocol.json"
        ).read_bytes()
    )
    required_inputs = {
        "data/raa/raw/national_geopackage_source.json",
        "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json",
    }
    require(
        len(protocol["inputs"]) == len(required_inputs)
        and {row["path"] for row in protocol["inputs"]} == required_inputs,
        "finite lead input population differs",
    )
    for pinned in protocol["inputs"]:
        body = _lead_input_bytes(root, pinned)
        require(
            sha256(body).hexdigest() == pinned["sha256"],
            "source lead decision bytes differ",
        )
    source = protocol["source"]
    source_path = source_root / source["relative_path"]
    require(
        not destination.is_relative_to(source_path.parent)
        and not source_path.parent.is_relative_to(destination),
        "source output overlap",
    )
    bounds = protocol["bounds"]
    leads = protocol["lead_population"]
    radii = protocol["radii_metres"]
    require(
        radii == [10000, 20000] and len(leads) == 5, "frozen finite supports differ"
    )
    require(
        bounds["max_total_selected_geometry_occurrences"]
        == bounds["max_candidate_support_links"]
        == 4 * 4 * bounds["max_geometry_candidates_per_table_per_lead"],
        "finite source support ceiling derivation differs",
    )
    transformer = Transformer.from_crs(4326, 3006, always_xy=True)
    seen: set[tuple[str, int]] = set()
    owners: set[str] = set()
    lead_results: list[dict[str, object]] = []
    support_count = 0
    started = time.monotonic()
    vm_calls = 0
    outputs: dict[str, object] = {}
    source_fields: Counter[str] = Counter()
    lookup_statuses: Counter[str] = Counter()
    decoded = WitnessBudget(bounds["max_decoded_witness_bytes"])
    with read_only_database(
        source_path,
        expected_sha256=source["sha256"],
        expected_byte_count=source["bytes"],
    ) as connection:

        def progress() -> int:
            nonlocal vm_calls
            vm_calls += 1
            return int(
                vm_calls * 1000 > bounds["sqlite_vm_progress_steps"]
                or time.monotonic() - started > 180
            )

        connection.set_progress_handler(progress, 1000)
        schema = inspect_local_schema(connection)
        preparations = allow_native_rtree_reads(connection)
        destination.mkdir()
        writers = {
            name: NativeWitness(
                destination / (name + ".ndjson.gz"),
                decoded,
                bounds["max_native_value_bytes"] * 2,
            )
            for name in ("geometry", "support", "native-owners")
        }
        try:
            for lead in leads:
                if lead["latitude"] is None or lead["longitude"] is None:
                    lead_results.append(
                        {
                            "lead_id": lead["lead_id"],
                            "status": "refused_physical_study_object_unresolved",
                            "geometry_occurrences": 0,
                            "queries_performed": 0,
                        }
                    )
                    continue
                lon, lat = float(lead["longitude"]), float(lead["latitude"])
                x, y = transformer.transform(lon, lat, errcheck=True)
                centre = (float(x), float(y))
                require(
                    all(math.isfinite(v) for v in centre),
                    "lead transformation nonfinite",
                )
                counts: Counter[str] = Counter()
                candidate_counts: Counter[str] = Counter()
                for table, kind in GEOMETRY_TYPES.items():
                    for candidate in candidates(
                        connection,
                        table,
                        centre,
                        float(max(radii)),
                        bounds["max_geometry_candidates_per_table_per_lead"],
                    ):
                        raw = cast(dict[str, object], candidate["source"])
                        fid = cast(int, raw["fid"])
                        key = (table, fid)
                        desc = describe_geometry(raw["geometri"], geometry_type=kind)
                        role = (
                            "positional_uncertainty_region"
                            if table not in {"point", "linestring", "polygon"}
                            else "native_remains_geometry"
                        )
                        candidate_counts[table] += 1
                        if key not in seen:
                            seen.add(key)
                            require(
                                len(seen)
                                <= bounds["max_total_selected_geometry_occurrences"],
                                "derived finite geometry limit exceeded",
                            )
                            writers["geometry"].write(
                                {
                                    "table": table,
                                    "fid": fid,
                                    "role": role,
                                    "fields": {
                                        n: native(v)
                                        for n, v in raw.items()
                                        if n != "geometri"
                                    },
                                    "geometry": desc,
                                    "rtree_envelope": candidate["index_envelope"],
                                }
                            )
                            uuid = raw.get("lamning_uuid")
                            if isinstance(uuid, str):
                                owners.add(uuid)
                            require(
                                len(owners) <= bounds["max_unique_native_owners"],
                                "derived finite native owner limit exceeded",
                            )
                        statuses: list[dict[str, object]] = []
                        extrema = desc.get("coordinate_extrema_xy")
                        if desc[
                            "status"
                        ] == "structurally_valid_nonempty" and isinstance(
                            extrema, list
                        ):
                            lower, upper = envelope_distances(
                                [float(v) for v in extrema], centre
                            )
                            for radius in radii:
                                status = support_class(
                                    lower, upper, float(radius), point=kind == "POINT"
                                )
                                statuses.append(
                                    {
                                        "radius_metres": radius,
                                        "status": status,
                                        "lower_distance_metres": lower,
                                        "upper_distance_metres": upper,
                                        "lower_distance_hex": lower.hex(),
                                        "upper_distance_hex": upper.hex(),
                                    }
                                )
                                counts[f"{radius}:{role}:{status}"] += 1
                        else:
                            statuses = [
                                {
                                    "radius_metres": radius,
                                    "status": "refused_native_geometry",
                                    "reason": desc.get("reason_codes"),
                                }
                                for radius in radii
                            ]
                        writers["support"].write(
                            {
                                "lead_id": lead["lead_id"],
                                "geometry_table": table,
                                "geometry_fid": fid,
                                "native_uuid": raw.get("lamning_uuid"),
                                "role": role,
                                "support": statuses,
                            }
                        )
                        support_count += 1
                        require(
                            support_count <= bounds["max_candidate_support_links"],
                            "derived finite support link limit exceeded",
                        )
                lead_results.append(
                    {
                        "lead_id": lead["lead_id"],
                        "status": "bounded_indexed_candidates",
                        "projected_centre_xy": list(centre),
                        "projected_centre_hex": [v.hex() for v in centre],
                        "source_latitude": lat,
                        "source_longitude": lon,
                        "coordinate_role": "source_brief_modern_reference_only",
                        "candidate_counts_by_native_table": dict(
                            sorted(candidate_counts.items())
                        ),
                        "classification_counts": dict(sorted(counts.items())),
                    }
                )
            for uuid in sorted(owners):
                families: dict[str, object] = {}
                for table in ("lamning", "ingaendelamning", "egenskap"):
                    rows, lookup = native_family(
                        connection,
                        table,
                        uuid,
                        bounds["max_indexed_children_per_owner"],
                    )
                    lookup_statuses[table + ":" + str(lookup["status"])] += 1
                    for row in rows:
                        for name, value in row.items():
                            source_fields[
                                table
                                + ":"
                                + name
                                + ":"
                                + str(native(value)["sqlite_type"])
                            ] += 1
                    families[table] = {
                        "lookup": lookup,
                        "rows": [
                            {n: native(v) for n, v in row.items()} for row in rows
                        ],
                    }
                writers["native-owners"].write(
                    {
                        "native_uuid": uuid,
                        "families": families,
                        "date_admission": False,
                        "role": "source_record_and_verbatim_attributes_only",
                        "indirect_nested_attribute_scope": "Only direct lamning_uuid lookup performed; attributes with null/different owner and only ingaendelamning_id are not represented. No complete bibliography or nested-attribute claim.",
                    }
                )
        finally:
            for name, writer in writers.items():
                outputs[name + ".ndjson.gz"] = writer.close()
    physical_bytes = sum(p.stat().st_size for p in destination.iterdir() if p.is_file())
    require(
        physical_bytes <= bounds["max_private_output_bytes"],
        "physical private gzip witness budget exceeded",
    )
    report = {
        "schema": "archaeology-native-lead-support-result.v1",
        "scope": protocol["scope"],
        "protocol_sha256": sha256(
            (
                root / "reports/science/archaeology-native-lead-support/protocol.json"
            ).read_bytes()
        ).hexdigest(),
        "source": source,
        "native_schema": schema,
        "leads": lead_results,
        "unique_geometry_occurrences": len(seen),
        "unique_native_uuids": len(owners),
        "support_links": support_count,
        "sqlite_progress_calls": vm_calls,
        "builtin_rtree_shadow_statement_preparations": dict(preparations),
        "native_field_storage_type_counts": dict(sorted(source_fields.items())),
        "native_owner_lookup_status_counts": dict(sorted(lookup_statuses.items())),
        "output_files": outputs,
        "decoded_witness_bytes": decoded.decoded,
        "physical_witness_bytes": physical_bytes,
        "source_preserved_by_maintained_read_only_guard": True,
        "chronology_admission": False,
        "scientific_admission": False,
        "canonical_source_adoption": False,
        "field_permission": False,
        "historical_density_equivalence": False,
        "textual_period_numeric_conversion": False,
        "chronology_intervals": None,
        "radius_scope": "Projected point/envelope bounds of native indexed candidates; no exact line/polygon intersection or geodesic claim.",
    }
    (destination / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    return report
