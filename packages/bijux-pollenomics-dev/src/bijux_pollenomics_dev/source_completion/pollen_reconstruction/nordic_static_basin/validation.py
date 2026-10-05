"""Keep native panels, cohort denominators and saved numerical axes distinct."""

from __future__ import annotations

import math

from .numerical import compare, oracle


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("Nordic count must be a nonnegative integer")
    return value


def validate(report: dict, census: dict) -> dict:
    cases = {}
    datasets = {}
    rows = 0
    cells = 0
    source_by_dataset = {
        row["source_core"]["native_dataset_id"]: row for row in census["cores"]
    }
    if len(source_by_dataset) != 4 or len(census["cores"]) != 4:
        raise ValueError("Nordic source core axis differs")
    for case in report["cases"]:
        name = case["case_id"]
        core = case["native_dataset_id"]
        source = source_by_dataset.get(core)
        taxa = case["parameter_taxa"]
        if (
            name in cases
            or source is None
            or len(taxa) not in (2, 3, 6)
            or len(set(taxa)) != len(taxa)
        ):
            raise ValueError("Nordic case, source or panel axis differs")
        if (
            case["native_collection_unit_id"]
            != source["source_core"]["native_collection_unit_id"]
            or case["native_site_id"] != source["source_core"]["native_site_id"]
            or case["selected_named_calibrated_chronology"]
            != source["selected_named_calibrated_chronology"]
        ):
            raise ValueError("Nordic native entity or named chronology differs")
        if (
            not case["panel_N_not_full_NISP"]
            or not case["source_present_not_hypothesized_zero"]
        ):
            raise ValueError("Nordic source panel scope differs")
        if (
            case["accepted_samples"] != source["named_point_domain_eligible_samples"]
            or case["source_samples"] != source["source_sample_count"]
        ):
            raise ValueError("Nordic cohort population differs")
        if (
            case["accepted_samples"]
            + sum(integer(value) for value in case["exclusions"].values())
            != case["source_samples"]
        ):
            raise ValueError("Nordic source inclusion/exclusion population differs")
        radius = case["static_geometry"]["radius_m"]
        if not math.isfinite(radius) or radius <= 0:
            raise ValueError("Nordic static basin radius differs")
        if "reported_area_ha" in case["static_geometry"] and radius != math.sqrt(
            case["static_geometry"]["reported_area_ha"] * 10000 / math.pi
        ):
            raise ValueError("Nordic hectare-to-radius conversion differs")
        windows = {}
        for row in case["results"]:
            window = row["younger_cal_bp"], row["older_cal_bp_exclusive"]
            edges = report["protocol"]["age_window_edges_cal_bp"]
            if window in windows or window not in list(zip(edges, edges[1:])):
                raise ValueError("Nordic emitted window axis differs")
            if len(row["counts"]) != 1 or len(row["counts"][0]) != len(taxa):
                raise ValueError("Nordic source single-core count shape differs")
            counts = row["counts"][0]
            if (
                sum(integer(value) for value in counts)
                != integer(row["panel_count_denominator"])
                or row["panel_count_denominator"] == 0
            ):
                raise ValueError("Nordic panel denominator differs")
            if row["panel_count_denominator"] + integer(
                row["unparameterized_reported_NISP_sum"]
            ) != integer(row["reported_all_pollen_NISP_sum"]):
                raise ValueError("Nordic source/residual NISP conservation differs")
            if (
                not row["actual_source_panel_presence"]
                or row["assumed_zero_cells"] != 0
            ):
                raise ValueError("Nordic source-present mask changed to an imputation")
            integer(row["native_sample_count"])
            if (
                row["source_age_bounds_missing"] > row["native_sample_count"]
                or row["source_signed_reported_age_bounds_count"]
                > row["native_sample_count"]
            ):
                raise ValueError("Nordic chronology-bound support population differs")
            expected = oracle(
                counts,
                case["PPE"],
                case["physical_response"]["factors"][0],
                case["PPE_SD"],
            )
            for key, value in expected.items():
                cells += compare(value, row[key])
            windows[window] = row
            rows += 1
        if (
            len(windows) != case["occupied_windows"]
            or sum(row["native_sample_count"] for row in windows.values())
            != case["accepted_samples"]
        ):
            raise ValueError("Nordic emitted sample/window population differs")
        cases[name] = (case, windows)
        signature = (
            case["source_samples"],
            case["accepted_samples"],
            case["exclusions"],
            taxa,
            [
                (
                    window,
                    row["counts"],
                    row["reported_all_pollen_NISP_sum"],
                    row["source_age_bounds_missing"],
                    row["source_signed_reported_age_bounds_count"],
                )
                for window, row in windows.items()
            ],
        )
        if core in datasets and datasets[core] != signature:
            raise ValueError(
                "Nordic geometry alternatives changed source cohort or counts"
            )
        datasets[core] = signature
    if len(cases) != 9 or len(datasets) != 4 or rows != 182 or cells != 6840:
        raise ValueError("Nordic retained numerical population differs")
    if (
        sum(value[0] for value in datasets.values()) != 314
        or sum(value[1] for value in datasets.values()) != 313
    ):
        raise ValueError("Nordic de-duplicated source sample population differs")
    return {
        "cases": cases,
        "rows": rows,
        "cells": cells,
        "source_by_dataset": source_by_dataset,
    }
