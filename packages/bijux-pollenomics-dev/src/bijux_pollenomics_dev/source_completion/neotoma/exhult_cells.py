"""Compare unique literal numeric anchors and exact-name Exhult NISP cells."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from math import isfinite
from typing import Any

from bijux_pollenomics.collection.sources.rootsi.cells.decoding import Sheet

STATUSES = (
    "explicit_agreement",
    "explicit_difference",
    "absent_source_workbook_zero",
    "absent_source_workbook_positive",
    "ambiguous_source",
    "invalid_source_nisp",
    "invalid_workbook_count",
    "duplicate_workbook_label",
    "invalid_workbook_label",
    "unassessed_anchor",
)
NATIVE_IDENTITY_FIELDS = (
    "taxonid",
    "variableid",
    "element",
    "elementtype",
    "symmetry",
    "taxongroup",
    "ecologicalgroup",
    "context",
    "taphonomics",
)
LATIN_HEADERS = {
    r"\iBetula\i (björk)": "Betula",
    r"\iPinus\i (tall)": "Pinus",
    r"\iAlnus\i (al)": "Alnus",
}


def _numeric(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    )


def _count(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value >= 0
        and int(value) == value
    )


def _age_metadata(sample: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {key: age.get(key) for key in ("chronologyid", "chronologyname", "agetype")}
        for age in sample.get("ages", [])
    ]


def workbook_rows(sheet: Sheet) -> list[dict[str, Any]]:
    """Preserve cached labels/types; never interpret Sample as a depth unit."""
    if (
        sheet.cell(0, 0).value != "Sample"
        or sheet.cell(0, 1).value != "Sample age (cal AD/BC)"
    ):
        raise ValueError("Exhult literal metadata headers differ")
    return [
        {
            "row_number": row + 1,
            "sample": sheet.cell(row, 0).value,
            "sample_type": sheet.cell(row, 0).ctype,
            "age": sheet.cell(row, 1).value,
            "age_type": sheet.cell(row, 1).ctype,
            "features": [
                {
                    "column": col + 1,
                    "label": sheet.cell(0, col).value,
                    "value": sheet.cell(row, col).value,
                    "type": sheet.cell(row, col).ctype,
                }
                for col in range(2, sheet.ncols)
            ],
        }
        for row in range(1, sheet.nrows)
    ]


def _identity(datum: dict[str, Any]) -> str:
    return json.dumps(
        {key: datum.get(key) for key in NATIVE_IDENTITY_FIELDS},
        sort_keys=True,
        allow_nan=False,
    )


def compare(
    rows: list[dict[str, Any]],
    samples: list[dict[str, Any]],
    *,
    profile: str = "literal",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Retain unresolved anchors and sparse exceptions without inventing zeros."""
    if profile not in {"literal", "explicit-latin-headers"}:
        raise ValueError("Unsupported Exhult comparison profile")
    header_pairs = dict(LATIN_HEADERS) if profile == "explicit-latin-headers" else {}
    if header_pairs and (
        not rows
        or any(
            sum(feature["label"] == header for feature in row["features"]) != 1
            for row in rows
            for header in header_pairs
        )
    ):
        raise ValueError("Each declared Latin header must be present exactly once")
    workbook_anchors: Counter[int | float] = Counter(
        row["sample"]
        for row in rows
        if row["sample_type"] == 2 and _numeric(row["sample"])
    )
    native_anchors: dict[int | float, list[dict[str, Any]]] = defaultdict(list)
    native_names: dict[str, set[str]] = defaultdict(set)
    for native in samples:
        if _numeric(native.get("depth")):
            native_anchors[native["depth"]].append(native)
        for datum in native["datum"]:
            name = datum.get("variablename")
            if isinstance(name, str) and name and datum.get("units") == "NISP":
                native_names[name].add(_identity(datum))
    outputs = []
    selected: set[int] = set()
    totals: Counter[str] = Counter()
    for row in rows:
        anchor = row["sample"]
        numeric = row["sample_type"] == 2 and _numeric(anchor)
        candidates = native_anchors.get(anchor, []) if numeric else []
        if not numeric:
            status = "invalid_workbook_anchor"
        elif workbook_anchors[anchor] > 1:
            status = "duplicate_workbook_anchor"
        elif len(candidates) > 1:
            status = "duplicate_native_anchor"
        elif not candidates:
            status = "unmatched_workbook_anchor"
        else:
            status = "unique_numeric_anchor_concordance"
        sample = (
            candidates[0] if status == "unique_numeric_anchor_concordance" else None
        )
        if sample is not None:
            selected.add(id(sample))
        labels = Counter(
            x["label"] for x in row["features"] if isinstance(x["label"], str)
        )
        datums: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if sample is not None:
            for datum in sample["datum"]:
                label = datum.get("variablename")
                if isinstance(label, str) and label:
                    datums[label].append(datum)
        counts: Counter[str] = Counter()
        exceptions = []
        paired_workbook_mass = paired_native_mass = 0
        for feature in row["features"]:
            name, value = feature["label"], feature["value"]
            native_name = header_pairs.get(name, name) if isinstance(name, str) else ""
            matching = datums.get(native_name, [])
            nisp = [x for x in matching if x.get("units") == "NISP"]
            if not isinstance(name, str) or not name:
                cell_status = "invalid_workbook_label"
            elif labels[name] > 1:
                cell_status = "duplicate_workbook_label"
            elif header_pairs and name not in header_pairs:
                cell_status = "excluded_nonselected_header"
            elif feature["type"] != 2 or not _count(value):
                cell_status = "invalid_workbook_count"
            elif sample is None:
                cell_status = "unassessed_anchor"
            elif len(nisp) > 1 or len(native_names.get(native_name, set())) > 1:
                cell_status = "ambiguous_source"
            elif not nisp:
                cell_status = (
                    "absent_source_workbook_zero"
                    if value == 0
                    else "absent_source_workbook_positive"
                )
            elif not _count(nisp[0].get("value")):
                cell_status = "invalid_source_nisp"
            else:
                cell_status = (
                    "explicit_agreement"
                    if value == nisp[0]["value"]
                    else "explicit_difference"
                )
                paired_workbook_mass += int(value)
                paired_native_mass += int(nisp[0]["value"])
            counts[cell_status] += 1
            if cell_status not in {
                "explicit_agreement",
                "unassessed_anchor",
                "absent_source_workbook_zero",
                "duplicate_workbook_label",
                "excluded_nonselected_header",
            }:
                exceptions.append(
                    {
                        "column": feature["column"],
                        "label": name,
                        "status": cell_status,
                        "workbook_value": value,
                        "workbook_type": feature["type"],
                        "native_datums": [
                            {
                                key: datum.get(key)
                                for key in (*NATIVE_IDENTITY_FIELDS, "value", "units")
                            }
                            for datum in matching
                        ],
                    }
                )
        ages = _age_metadata(sample) if sample is not None else []
        output = {
            "row_kind": "workbook",
            "workbook_row": row["row_number"],
            "workbook_sample": anchor,
            "workbook_sample_type": row["sample_type"],
            "workbook_age": row["age"],
            "workbook_age_type": row["age_type"],
            "anchor_status": status,
            "native_sample_ids": [x["sampleid"] for x in candidates],
            "native_depth": sample.get("depth") if sample is not None else None,
            "native_ages": ages,
            "native_age_claim_count": len(ages),
            "age_claim_status": "not_paired"
            if sample is None
            else "missing"
            if not ages
            else "multiple_claims_unqualified"
            if len(ages) > 1
            else "single_claim_unqualified",
            "native_non_nisp_datums": sum(
                x.get("units") != "NISP" for values in datums.values() for x in values
            ),
            "native_non_nisp_labels": sorted(
                {
                    name
                    for name, values in datums.items()
                    if any(x.get("units") != "NISP" for x in values)
                }
            ),
            "native_only_labels": sorted(
                set(datums)
                - (set(header_pairs.values()) if header_pairs else set(labels))
            ),
            "native_invalid_label_datums": sum(
                not isinstance(datum.get("variablename"), str)
                or not datum["variablename"]
                for datum in sample["datum"]
            )
            if sample is not None
            else 0,
            "paired_workbook_mass": paired_workbook_mass,
            "paired_native_nisp_mass": paired_native_mass,
            **{name: counts[name] for name in STATUSES},
            **(
                {"excluded_nonselected_header": counts["excluded_nonselected_header"]}
                if header_pairs
                else {}
            ),
            "exceptions": exceptions,
        }
        outputs.append(output)
        totals.update(counts)
    for native in samples:
        if id(native) in selected:
            continue
        outputs.append(
            {
                "row_kind": "native_unpaired",
                "native_sample_ids": [native["sampleid"]],
                "native_depth": native.get("depth"),
                "native_ages": _age_metadata(native),
                "native_age_claim_count": len(native.get("ages", [])),
                "anchor_status": "not_uniquely_paired",
                "age_claim_status": "not_paired",
            }
        )
    return outputs, {
        "comparison_profile": profile,
        "declared_header_pairs": header_pairs,
        "workbook_feature_columns": len(rows[0]["features"]) if rows else 0,
        "selected_profile_columns": len(header_pairs)
        if header_pairs
        else "all_unique_literal_headers",
        "workbook_rows": len(rows),
        "native_samples": len(samples),
        "uniquely_paired_rows": len(selected),
        "native_unpaired_rows": len(samples) - len(selected),
        "anchor_status_counts": dict(
            Counter(
                row["anchor_status"] for row in outputs if row["row_kind"] == "workbook"
            )
        ),
        "cell_status_counts": dict(totals),
        "duplicate_workbook_columns_excluded": [
            {"column": feature["column"], "label": feature["label"]}
            for feature in (rows[0]["features"] if rows else [])
            if isinstance(feature["label"], str)
            and sum(other["label"] == feature["label"] for other in rows[0]["features"])
            > 1
        ],
        "globally_ambiguous_native_nisp_labels": sorted(
            name for name, ids in native_names.items() if len(ids) > 1
        ),
    }
