"""Independently stream saved native identities and Decimal50 support bounds."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from decimal import Decimal, localcontext
import gzip
from hashlib import file_digest
import json
from pathlib import Path
import sys
from typing import cast


def records(
    root: Path, name: str, expected: dict[str, object]
) -> Iterator[dict[str, object]]:
    """Read byte-pinned witness rows with bounded lines and exact final counts."""
    path = root / name
    with path.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    if digest != expected["sha256"] or path.stat().st_size != expected["bytes"]:
        raise ValueError("private saved witness byte identity differs")
    count = decoded = 0
    with gzip.open(path, "rb") as stream:
        while line := stream.readline(2097153):
            if len(line) > 2097152 or not line.endswith(b"\n"):
                raise ValueError("bounded native NDJSON line differs")
            decoded += len(line)
            count += 1
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("native witness object absent")
            yield value
    if count != expected["rows"] or decoded != expected["decoded_bytes"]:
        raise ValueError("saved witness population differs")


def verify(root: Path, output: Path) -> None:
    """Verify saved geometry, owner and support identities and counts."""
    summary = json.loads((root / "report.json").read_bytes())
    descriptions: dict[tuple[str, int], tuple[str, str, list[float] | None]] = {}
    owners: set[str] = set()
    for row in records(
        root, "geometry.ndjson.gz", summary["output_files"]["geometry.ndjson.gz"]
    ):
        key = (str(row["table"]), int(str(row["fid"])))
        if key in descriptions:
            raise ValueError("duplicate native geometry identity")
        fields = cast(dict[str, dict[str, object]], row["fields"])
        if fields["lamning_uuid"]["sqlite_type"] == "text":
            owners.add(str(fields["lamning_uuid"]["value"]))
        geometry = cast(dict[str, object], row["geometry"])
        bounds = cast(list[float] | None, geometry.get("coordinate_extrema_xy"))
        descriptions[key] = (str(row["role"]), str(geometry["status"]), bounds)
    if (
        len(descriptions) != summary["unique_geometry_occurrences"]
        or len(owners) != summary["unique_native_uuids"]
    ):
        raise ValueError("native geometry/UUID population differs")
    seen_owners: set[str] = set()
    fields_count: Counter[str] = Counter()
    lookups: Counter[str] = Counter()
    for row in records(
        root,
        "native-owners.ndjson.gz",
        summary["output_files"]["native-owners.ndjson.gz"],
    ):
        uuid = str(row["native_uuid"])
        if (
            uuid in seen_owners
            or uuid not in owners
            or row["date_admission"] is not False
        ):
            raise ValueError("native owner identity/date refusal differs")
        seen_owners.add(uuid)
        families = cast(dict[str, dict[str, object]], row["families"])
        for table, family in families.items():
            lookup = cast(dict[str, object], family["lookup"])
            lookups[table + ":" + str(lookup["status"])] += 1
            for native_row in cast(list[dict[str, dict[str, object]]], family["rows"]):
                for name, value in native_row.items():
                    fields_count[
                        table + ":" + name + ":" + str(value["sqlite_type"])
                    ] += 1
    if (
        seen_owners != owners
        or dict(fields_count) != summary["native_field_storage_type_counts"]
        or dict(lookups) != summary["native_owner_lookup_status_counts"]
    ):
        raise ValueError("native owner field/null/lookup denominators differ")
    leads = {row["lead_id"]: row for row in summary["leads"]}
    counts: dict[str, Counter[str]] = {str(key): Counter() for key in leads}
    candidate_counts: dict[str, Counter[str]] = {str(key): Counter() for key in leads}
    seen_links: set[tuple[str, str, int]] = set()
    comparisons = 0
    maximum_absolute = Decimal(0)
    with localcontext() as context:
        context.prec = 50
        for row in records(
            root, "support.ndjson.gz", summary["output_files"]["support.ndjson.gz"]
        ):
            lead = str(row["lead_id"])
            table = str(row["geometry_table"])
            fid = int(str(row["geometry_fid"]))
            link = (lead, table, fid)
            if link in seen_links:
                raise ValueError("duplicate native lead/geometry support link")
            seen_links.add(link)
            candidate_counts[lead][table] += 1
            role, status, bounds = descriptions[(table, fid)]
            if role != row["role"]:
                raise ValueError("positional uncertainty/main geometry role differs")
            saved_support = cast(list[dict[str, object]], row["support"])
            if status != "structurally_valid_nonempty":
                if any(s["status"] != "refused_native_geometry" for s in saved_support):
                    raise ValueError("invalid native geometry acquired support")
                continue
            if bounds is None:
                raise ValueError("nonempty native geometry lost its bounds")
            xmin, xmax, ymin, ymax = [Decimal.from_float(v) for v in bounds]
            x, y = [Decimal.from_float(v) for v in leads[lead]["projected_centre_xy"]]
            lower = (
                max(xmin - x, Decimal(0), x - xmax) ** 2
                + max(ymin - y, Decimal(0), y - ymax) ** 2
            ).sqrt()
            upper = max(
                ((xx - x) ** 2 + (yy - y) ** 2).sqrt()
                for xx in (xmin, xmax)
                for yy in (ymin, ymax)
            )
            for saved in saved_support:
                for label, exact in (("lower", lower), ("upper", upper)):
                    observed_distance = float(str(saved[label + "_distance_metres"]))
                    difference = abs(Decimal.from_float(observed_distance) - exact)
                    maximum_absolute = max(maximum_absolute, difference)
                    if (
                        difference > Decimal("3e-15") * max(Decimal(1), abs(exact))
                        or float.fromhex(str(saved[label + "_distance_hex"]))
                        != observed_distance
                    ):
                        raise ValueError(
                            "independent Decimal/binary64 native envelope bound differs"
                        )
                    comparisons += 1
                radius = int(str(saved["radius_metres"]))
                lo = float(str(saved["lower_distance_metres"]))
                hi = float(str(saved["upper_distance_metres"]))
                if table == "point":
                    expected = (
                        "point_within_projected_circle"
                        if lo <= radius
                        else "point_outside_projected_circle"
                    )
                elif lo > radius:
                    expected = "outside_envelope_lower_bound"
                elif hi <= radius:
                    expected = "entire_envelope_within_projected_circle"
                else:
                    expected = "ambiguous_envelope_overlap_not_exact_shape_intersection"
                if saved["status"] != expected:
                    raise ValueError(
                        "native projected point/envelope support class differs"
                    )
                counts[lead][str(radius) + ":" + role + ":" + expected] += 1
    for lead, value in leads.items():
        if value["status"] == "refused_physical_study_object_unresolved":
            if (
                lead != "uppakra-lund"
                or value["queries_performed"] != 0
                or counts[lead]
            ):
                raise ValueError("unresolved fifth lead acquired support")
        elif (
            dict(counts[lead]) != value["classification_counts"]
            or dict(candidate_counts[lead]) != value["candidate_counts_by_native_table"]
        ):
            raise ValueError("saved per-lead denominators differ")
    if (
        len(seen_links) != summary["support_links"]
        or summary["chronology_intervals"] is not None
    ):
        raise ValueError("native support link/date-null scope differs")
    output.write_text(
        json.dumps(
            {
                "native_exit": 0,
                "scope": "Independent saved stream/native identity/null/refusal/Decimal50 point-envelope arithmetic only; no new original source query or chronology/field/rights admission.",
                "geometry_occurrences": len(descriptions),
                "native_uuids": len(owners),
                "support_links": len(seen_links),
                "decimal_bound_comparisons": comparisons,
                "maximum_absolute_error_metres": str(maximum_absolute),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    verify(Path(sys.argv[1]), Path(sys.argv[2]))
