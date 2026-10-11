"""Keep native panels, cohort denominators and saved numerical axes distinct."""

from __future__ import annotations

from collections.abc import Callable
import math
from typing import NotRequired, TypedDict, TypeGuard

from .numerical import compare, oracle


class NativeCore(TypedDict):
    """Keep dataset, collection and site identities on their native axes."""

    native_dataset_id: int
    native_collection_unit_id: int
    native_site_id: int


class SourceMetadata(TypedDict):
    """Expose consumed dataset and collection metadata without dropping extras."""

    dataset: dict[str, object]
    collection_unit: dict[str, object]


class SourceRecord(TypedDict):
    """Describe the saved source cohort and named chronology."""

    source_core: NativeCore
    selected_named_calibrated_chronology: object
    named_point_domain_eligible_samples: int
    source_sample_count: int
    prior_nonnegative_BP_point_or_bounds_refusals: int
    native_default_chronology: object
    metadata_locator: object
    raw_metadata_fields: dict[str, object]
    raw_source_metadata: SourceMetadata


class SourceCensus(TypedDict):
    """Bind the source core population."""

    cores: list[SourceRecord]


class StaticGeometry(TypedDict):
    """Keep radius distinct from optional reported area."""

    radius_m: float
    id: str
    reported_area_ha: NotRequired[float]


class WindowResult(TypedDict):
    """Preserve count conservation and native chronology support per window."""

    younger_cal_bp: float
    older_cal_bp_exclusive: float
    counts: list[list[int]]
    panel_count_denominator: int
    unparameterized_reported_NISP_sum: int
    reported_all_pollen_NISP_sum: int
    actual_source_panel_presence: bool
    assumed_zero_cells: int
    native_sample_count: int
    source_age_bounds_missing: int
    source_signed_reported_age_bounds_count: int
    conditional_cover: list[float]
    direct_pollen_panel_fraction: list[float]


class PhysicalResponse(TypedDict):
    """Expose the retained per-target physical factors."""

    factors: list[list[float]]


class BasinCase(TypedDict):
    """Bind one numerical panel to its native source and static geometry."""

    case_id: str
    native_dataset_id: int
    native_collection_unit_id: int
    native_site_id: int
    parameter_taxa: list[str]
    selected_named_calibrated_chronology: object
    panel_N_not_full_NISP: bool
    source_present_not_hypothesized_zero: bool
    accepted_samples: int
    source_samples: int
    exclusions: dict[str, int]
    static_geometry: StaticGeometry
    results: list[WindowResult]
    PPE: list[float]
    PPE_SD: list[float]
    physical_response: PhysicalResponse
    occupied_windows: int
    source_handle: str
    country: str


class WindowComparison(TypedDict):
    """Keep both within-core changes on the original window axis."""

    window_cal_bp: list[float]
    physical_corrected_cover_minus_direct_panel_fraction: list[float]
    static_geometry_cover_minus_metadata_baseline: list[float]


class WithinCoreComparison(TypedDict):
    """Bind saved comparison windows to their source case and taxon panel."""

    case_id: str
    parameter_taxa: list[str]
    windows: list[WindowComparison]


class BasinProtocol(TypedDict):
    """Expose the emitted age-window axis while retaining other protocol fields."""

    age_window_edges_cal_bp: list[float]


class BasinReport(TypedDict):
    """Retain the source cases and their declared age-window protocol."""

    cases: list[BasinCase]
    protocol: BasinProtocol
    within_core_comparisons: list[WithinCoreComparison]
    new_physical_independent_review_complete: bool


class ValidatedBasin(TypedDict):
    """Expose admitted case windows and native source rows without flattening axes."""

    cases: dict[str, tuple[BasinCase, dict[tuple[float, float], WindowResult]]]
    rows: int
    cells: int
    source_by_dataset: dict[int, SourceRecord]


def _fields(value: object, predicates: dict[str, Callable[[object], bool]]) -> bool:
    return isinstance(value, dict) and all(
        key in value and predicate(value[key]) for key, predicate in predicates.items()
    )


def _native_integer(value: object) -> bool:
    return type(value) is int


def _number(value: object) -> bool:
    return type(value) in (int, float)


def _text(value: object) -> bool:
    return isinstance(value, str)


def _boolean(value: object) -> bool:
    return type(value) is bool


def _sequence(value: object, predicate: Callable[[object], bool]) -> bool:
    return isinstance(value, list) and all(predicate(item) for item in value)


def _mapping(value: object, predicate: Callable[[object], bool]) -> bool:
    return isinstance(value, dict) and all(
        isinstance(key, str) and predicate(item) for key, item in value.items()
    )


def _window(value: object) -> bool:
    fields: dict[str, Callable[[object], bool]] = dict.fromkeys(
        (
            "panel_count_denominator",
            "unparameterized_reported_NISP_sum",
            "reported_all_pollen_NISP_sum",
            "assumed_zero_cells",
            "native_sample_count",
            "source_age_bounds_missing",
            "source_signed_reported_age_bounds_count",
        ),
        _native_integer,
    )
    fields.update(
        {
            "younger_cal_bp": _number,
            "older_cal_bp_exclusive": _number,
            "counts": lambda item: _sequence(
                item, lambda row: _sequence(row, _native_integer)
            ),
            "actual_source_panel_presence": _boolean,
            "conditional_cover": lambda item: _sequence(item, _number),
            "direct_pollen_panel_fraction": lambda item: _sequence(item, _number),
        }
    )
    return _fields(value, fields)


def _case(value: object) -> bool:
    fields: dict[str, Callable[[object], bool]] = dict.fromkeys(
        (
            "native_dataset_id",
            "native_collection_unit_id",
            "native_site_id",
            "accepted_samples",
            "source_samples",
            "occupied_windows",
        ),
        _native_integer,
    )
    fields.update(
        {
            "case_id": _text,
            "source_handle": _text,
            "country": _text,
            "parameter_taxa": lambda item: _sequence(item, _text),
            "selected_named_calibrated_chronology": lambda item: True,
            "panel_N_not_full_NISP": _boolean,
            "source_present_not_hypothesized_zero": _boolean,
            "exclusions": lambda item: _mapping(item, _native_integer),
            "static_geometry": lambda item: (
                _fields(item, {"radius_m": _number, "id": _text})
                and (
                    not isinstance(item, dict)
                    or "reported_area_ha" not in item
                    or _number(item["reported_area_ha"])
                )
            ),
            "results": lambda item: _sequence(item, _window),
            "PPE": lambda item: _sequence(item, _number),
            "PPE_SD": lambda item: _sequence(item, _number),
            "physical_response": lambda item: _fields(
                item,
                {
                    "factors": lambda rows: _sequence(
                        rows, lambda row: _sequence(row, _number)
                    )
                },
            ),
        }
    )
    return _fields(value, fields)


def _comparison(value: object) -> bool:
    return _fields(
        value,
        {
            "case_id": _text,
            "parameter_taxa": lambda item: _sequence(item, _text),
            "windows": lambda item: _sequence(
                item,
                lambda row: _fields(
                    row,
                    {
                        "window_cal_bp": lambda cells: _sequence(cells, _number),
                        "physical_corrected_cover_minus_direct_panel_fraction": lambda cells: (
                            _sequence(cells, _number)
                        ),
                        "static_geometry_cover_minus_metadata_baseline": lambda cells: (
                            _sequence(cells, _number)
                        ),
                    },
                ),
            ),
        },
    )


def _is_report(value: object) -> TypeGuard[BasinReport]:
    return _fields(
        value,
        {
            "cases": lambda item: _sequence(item, _case),
            "protocol": lambda item: _fields(
                item,
                {"age_window_edges_cal_bp": lambda cells: _sequence(cells, _number)},
            ),
            "within_core_comparisons": lambda item: _sequence(item, _comparison),
            "new_physical_independent_review_complete": _boolean,
        },
    )


def _is_census(value: object) -> TypeGuard[SourceCensus]:
    return _fields(
        value,
        {
            "cores": lambda item: _sequence(
                item,
                lambda row: _fields(
                    row,
                    {
                        "source_core": lambda core: _fields(
                            core,
                            dict.fromkeys(
                                (
                                    "native_dataset_id",
                                    "native_collection_unit_id",
                                    "native_site_id",
                                ),
                                _native_integer,
                            ),
                        ),
                        "selected_named_calibrated_chronology": lambda item: True,
                        "named_point_domain_eligible_samples": _native_integer,
                        "source_sample_count": _native_integer,
                        "prior_nonnegative_BP_point_or_bounds_refusals": _native_integer,
                        "native_default_chronology": lambda item: True,
                        "metadata_locator": lambda item: True,
                        "raw_metadata_fields": lambda item: _mapping(
                            item, lambda field: True
                        ),
                        "raw_source_metadata": lambda item: _fields(
                            item,
                            {
                                key: lambda record: _mapping(record, lambda field: True)
                                for key in ("dataset", "collection_unit")
                            },
                        ),
                    },
                ),
            )
        },
    )


def require_report(value: object) -> BasinReport:
    """Admit consumed report shapes without copying or normalizing source values."""
    if not _is_report(value):
        raise ValueError("Nordic retained report field shapes differ")
    return value


def require_census(value: object) -> SourceCensus:
    """Admit native census shapes while preserving every original source field."""
    if not _is_census(value):
        raise ValueError("Nordic retained census field shapes differ")
    return value


def integer(value: object) -> int:
    """Require a nonnegative native integer count."""
    if type(value) is not int or value < 0:
        raise ValueError("Nordic count must be a nonnegative integer")
    return value


def validate(report: object, census: object) -> ValidatedBasin:
    """Reconcile native cohorts, window counts and saved scalar equations."""
    report = require_report(report)
    census = require_census(census)
    cases: dict[str, tuple[BasinCase, dict[tuple[float, float], WindowResult]]] = {}
    datasets: dict[
        int,
        tuple[
            int,
            int,
            dict[str, int],
            list[str],
            list[tuple[tuple[float, float], list[list[int]], int, int, int]],
        ],
    ] = {}
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
            if window in windows or window not in list(
                zip(edges, edges[1:], strict=False)
            ):
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
                cells += compare(value, dict(row)[key])
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
