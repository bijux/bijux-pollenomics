"""Source-native window counts without converting omitted taxa into zeros."""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any, cast


def _integer(value: object) -> bool:
    return type(value) is int and value >= 0


def _finite(value: object) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return isfinite(cast(float, value))
    except OverflowError:
        return False


def _metadata(row: dict[str, Any]) -> bool:
    return (
        row.get("element") == row.get("elementtype") == "pollen"
        and row.get("units") == "NISP"
        and "context" in row
        and row["context"] is None
        and _integer(row.get("taxonid"))
        and isinstance(row.get("variablename"), str)
        and bool(row["variablename"])
    )


def _pollen(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        r
        for r in rows
        if r.get("element") == "pollen" or r.get("elementtype") == "pollen"
    ]


def audit_native_window(
    raw: dict[str, Any],
    *,
    dataset_id: int,
    collection_unit_id: int,
    chronology_id: int,
    window: tuple[int, int],
) -> dict[str, Any]:
    """Keep literal reports, conditional nondetection candidates and invalid cells distinct."""
    if window[0] >= window[1]:
        raise ValueError("Invalid half-open window")
    sites = [
        r["site"]
        for r in raw["rows"]
        if r["site"]["dataset"]["datasetid"] == dataset_id
    ]
    if len(sites) != 1:
        raise ValueError("Unique source dataset required")
    site = sites[0]
    collection = site["collectionunit"]
    if (
        collection["collectionunitid"] != collection_unit_id
        or collection["dataset"]["datasetid"] != dataset_id
    ):
        raise ValueError("Source dataset/collection-unit identity mismatch")
    samples = collection["dataset"]["samples"]
    if len({s["sampleid"] for s in samples}) != len(samples):
        raise ValueError("Duplicate source sample owner")
    axis: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    duplicated: set[tuple[Any, Any]] = set()
    for sample in samples:
        pollen_rows = _pollen(sample["datum"])
        ids = Counter(r.get("taxonid") for r in pollen_rows)
        labels = Counter(r.get("variablename") for r in pollen_rows)
        for row in pollen_rows:
            key = (row.get("taxonid"), row.get("variablename"))
            axis.setdefault(key, []).append(row)
            if ids[key[0]] != 1 or labels[key[1]] != 1:
                duplicated.add(key)
    id_labels: dict[Any, set[Any]] = {}
    label_ids: dict[Any, set[Any]] = {}
    for tid, label in axis:
        id_labels.setdefault(tid, set()).add(label)
        label_ids.setdefault(label, set()).add(tid)
    eligible = {
        key: (
            all(_metadata(r) and _integer(r.get("value")) for r in rows)
            and len(id_labels[key[0]]) == len(label_ids[key[1]]) == 1
            and key not in duplicated
            and any(r["value"] > 0 for r in rows)
        )
        for key, rows in axis.items()
    }
    selected: list[dict[str, Any]] = []
    ages: list[dict[str, Any]] = []
    unknown = []
    for sample in samples:
        matches = [a for a in sample["ages"] if a.get("chronologyid") == chronology_id]
        valid = len(matches) == 1
        age = matches[0] if valid else {}
        point = age.get("age")
        valid = (
            valid
            and age.get("agetype") == "Calibrated radiocarbon years BP"
            and _finite(point)
        )
        for bound_name in ("ageyounger", "ageolder"):
            valid = valid and (age.get(bound_name) is None or _finite(age[bound_name]))
        if valid:
            valid = (age.get("ageyounger") is None or age["ageyounger"] <= point) and (
                age.get("ageolder") is None or point <= age["ageolder"]
            )
        disposition = "unassignable_selected_age"
        if valid:
            assert point is not None
            disposition = (
                "in_window" if window[0] <= point < window[1] else "outside_window"
            )
        else:
            unknown.append(sample["sampleid"])
        ages.append(
            {
                "sample_id": sample["sampleid"],
                "selected_age_matches": matches,
                "disposition": disposition,
            }
        )
        if disposition == "in_window":
            selected.append(sample)
    taxon_rows = []
    for (tid, label), source_rows in sorted(
        axis.items(), key=lambda item: (str(item[0][1]), str(item[0][0]))
    ):
        cells = []
        for sample in selected:
            matches = [
                r
                for r in _pollen(sample["datum"])
                if r.get("taxonid") == tid or r.get("variablename") == label
            ]
            count = None
            if not matches:
                state = (
                    "omitted_known_dataset_taxon_conditional_nondetection"
                    if eligible[(tid, label)]
                    else "omitted_incompatible_dataset_taxon"
                )
            elif (
                len(matches) != 1
                or matches[0].get("taxonid") != tid
                or matches[0].get("variablename") != label
            ):
                state = "duplicate_or_conflicting_identity"
            elif not _metadata(matches[0]):
                state = "incompatible_native_metadata"
            elif "value" not in matches[0]:
                state = "missing_native_value"
            elif matches[0]["value"] is None:
                state = "null_native_value"
            elif not _integer(matches[0]["value"]):
                state = "invalid_native_count"
            else:
                count = matches[0]["value"]
                state = "reported_positive" if count else "reported_zero"
            cells.append(
                {
                    "sample_id": sample["sampleid"],
                    "state": state,
                    "count": count,
                    "native_matches": matches,
                }
            )
        complete = (
            bool(cells) and not unknown and all(c["count"] is not None for c in cells)
        )
        taxon_rows.append(
            {
                "taxon_id": tid,
                "native_label": label,
                "dataset_reported_cell_count": len(source_rows),
                "conditional_nondetection_eligible": eligible[(tid, label)],
                "known_NISP_sum": sum(
                    c["count"] for c in cells if c["count"] is not None
                ),
                "aggregate_all_owner_count": sum(c["count"] for c in cells)
                if complete
                else None,
                "cells": cells,
            }
        )
    sample_rows = []
    for sample in selected:
        pollen = _pollen(sample["datum"])
        ids = Counter(r.get("taxonid") for r in pollen)
        labels = Counter(r.get("variablename") for r in pollen)
        valid_pollen_rows = [
            _metadata(r)
            and _integer(r.get("value"))
            and ids[r["taxonid"]] == labels[r["variablename"]] == 1
            for r in pollen
        ]
        known = sum(
            r["value"] for r, ok in zip(pollen, valid_pollen_rows, strict=True) if ok
        )
        complete = bool(pollen) and all(valid_pollen_rows)
        sample_rows.append(
            {
                "sample_id": sample["sampleid"],
                "depth": sample.get("depth"),
                "native_ages": sample["ages"],
                "pollen_row_count": len(pollen),
                "non_pollen_row_count": len(sample["datum"]) - len(pollen),
                "known_valid_reported_pollen_N": known,
                "pollen_N": known if complete else None,
                "pollen_denominator_status": "complete_literal_reported_rows"
                if complete
                else "refused_invalid_or_duplicate_pollen_rows",
            }
        )
    complete = (
        bool(sample_rows)
        and not unknown
        and all(s["pollen_N"] is not None for s in sample_rows)
    )
    return {
        "schema_version": "bokesjon-pilot-native-taxon-window.v1",
        "dataset_id": dataset_id,
        "site_id": site["siteid"],
        "collection_unit_id": collection_unit_id,
        "chronology_id": chronology_id,
        "window": list(window),
        "interval_rule": "half_open_selected_calibrated_BP1950_point",
        "source_sample_count": len(samples),
        "selected_sample_ids": [s["sampleid"] for s in selected],
        "unassignable_age_sample_ids": unknown,
        "age_accounting": ages,
        "samples": sample_rows,
        "source_pollen_taxon_count": len(axis),
        "taxon_axis": taxon_rows,
        "known_window_native_pollen_N": sum(
            s["known_valid_reported_pollen_N"] for s in sample_rows
        ),
        "window_native_pollen_N": sum(s["pollen_N"] for s in sample_rows)
        if complete
        else None,
        "zero_imputation_applied": False,
        "qualified_terrestrial_denominator": False,
        "conditional_nondetection_assumption": "Williams etal2018 doi10.1017/qua.2017.105 p164: organismal zeros are not stored; conditional nondetection requires source taxon identification and an analyst looking throughout the dataset. Candidate states are not measured zeros or true vegetation absences.",
    }
