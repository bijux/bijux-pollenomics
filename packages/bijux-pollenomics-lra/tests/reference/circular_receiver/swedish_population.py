"""Exact saved Swedish core/profile population and conditional input export."""

from __future__ import annotations

import csv
import io
import math
import re
from typing import Any, TypedDict


class CoreSpec(TypedDict):
    """Retain native core, chronology, radius, membership and taxon support."""

    dataset: int
    chronology: int
    radius: int
    included: int
    native: int
    windows: int
    taxa: list[str]


class TransportProfile(TypedDict):
    """Declare the conditional radius multiplier and wind-speed profile."""

    id: str
    radius_multiplier: float
    wind_speed_m_s: float


def _columns(names: str) -> tuple[str, ...]:
    return tuple(names.split())


CORES: dict[str, CoreSpec] = {
    "ABB": {
        "dataset": 19913,
        "chronology": 11516,
        "radius": 98,
        "included": 106,
        "native": 107,
        "windows": 22,
        "taxa": ["Betula", "Pinus sylvestris"],
    },
    "BOKE": {
        "dataset": 54001,
        "chronology": 38422,
        "radius": 80,
        "included": 50,
        "native": 52,
        "windows": 13,
        "taxa": ["Betula", "Fraxinus", "Ulmus"],
    },
    "BUS": {
        "dataset": 53995,
        "chronology": 38418,
        "radius": 69,
        "included": 60,
        "native": 69,
        "windows": 19,
        "taxa": ["Betula", "Ulmus"],
    },
    "TIB": {
        "dataset": 53980,
        "chronology": 38408,
        "radius": 100,
        "included": 45,
        "native": 45,
        "windows": 23,
        "taxa": ["Pinus sylvestris", "Poaceae"],
    },
}
PROFILES: list[TransportProfile] = [
    {"id": "metadata_radius_wind_3", "radius_multiplier": 1, "wind_speed_m_s": 3},
    {
        "id": "half_metadata_radius_wind_3",
        "radius_multiplier": 0.5,
        "wind_speed_m_s": 3,
    },
    {
        "id": "double_metadata_radius_wind_3",
        "radius_multiplier": 2,
        "wind_speed_m_s": 3,
    },
    {"id": "metadata_radius_wind_2", "radius_multiplier": 1, "wind_speed_m_s": 2},
    {"id": "metadata_radius_wind_4", "radius_multiplier": 1, "wind_speed_m_s": 4},
]
PROFILE_IDS = [p["id"] for p in PROFILES] + [
    "metadata_radius_wind_3_zero_ppe_uncertainty"
]
TUPLE_COLUMNS = _columns(
    "tuple_id receiver_radius_m source_inner_radius_m regional_extent_m fall_speed_m_s empirical_diffusion_coefficient turbulence_parameter wind_speed_m_s"
)
SCENARIO_COLUMNS = _columns(
    "case_id taxon_index taxon tuple_id ppe ppe_sd saved_factor"
)
WINDOW_COLUMNS = _columns(
    "case_id window_id younger_cal_bp older_cal_bp_exclusive taxon_index count panel_count_denominator"
)
FACTOR_COLUMNS = _columns(
    "tuple_id factor raw_factor estimated_absolute_error tail_mass_bound subdivisions_used"
)
VALUE_COLUMNS = _columns("case_id window_id track quantity i j value")
VECTORS = (
    "conditional_cover",
    "direct_pollen_panel_fraction",
    "conditional_standard_error",
)
MATRICES = (
    "counting_covariance",
    "assumed_ppe_covariance",
    "total_conditional_covariance",
)
QUANTITIES = dict(
    zip(
        VECTORS + MATRICES,
        (
            "cover",
            "direct_pollen_panel_fraction",
            "standard_error",
            "counting_covariance",
            "ppe_covariance",
            "total_covariance",
        ),
        strict=True,
    )
)
TRACKS = {"fresh_factor": 1e-8, "saved_factor": 2e-12}
MAX_BYTES = 8 * 1024 * 1024


def _identity(value: str, length: int) -> str:
    if not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ValueError("Expected a lowercase hexadecimal source identity")
    return value


def _number(value: Any, *, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Expected a finite numeric source value")
    if positive and value <= 0:
        raise ValueError("Expected a positive source value")
    return float(value)


def _integer(value: Any) -> int:
    if type(value) is not int or not 0 <= value < 2**53:
        raise ValueError("Counts must be exact nonnegative integers below 2**53")
    return value


def _tsv(columns: tuple[str, ...], rows: list[list[Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def population(report: dict[str, Any]) -> dict[str, Any]:
    """Reconcile all saved core/profile inputs without any model evaluation."""
    protocol = report["protocol"]
    if protocol["profiles"] != PROFILES or any(
        protocol[k] != v
        for k, v in {
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "regional_extent_m": 100000,
        }.items()
    ):
        raise ValueError("Unsupported physical profile")
    if [c["metadata_code"] for c in report["cores"]] != list(CORES):
        raise ValueError("Exact ordered four-core population required")
    _identity(report["producer_candidate"], 40)
    tuples: dict[tuple[float, ...], str] = {}
    tuple_rows, scenarios, window_rows = [], [], []
    factors: dict[str, float] = {}
    expected: dict[tuple[str, int, str, int, int], float] = {}
    r_only: set[tuple[str, int, str, int, int]] = set()
    window_ids = []
    for core in report["cores"]:
        code = core["metadata_code"]
        spec = CORES[code]
        taxa = core["parameter_taxa"]
        n, count = len(taxa), spec["windows"]
        if (
            taxa != spec["taxa"]
            or core["native_dataset_id"] != spec["dataset"]
            or core["chronology_id"] != spec["chronology"]
            or core["metadata_static_radius_m"] != spec["radius"]
            or core["included_sample_count"] != spec["included"]
            or core["native_sample_count"] != spec["native"]
            or core["occupied_window_count"] != count
        ):
            raise ValueError("Core identity, support or original population differs")
        for name in ("ppe", "ppe_standard_deviation", "fall_speed_m_s"):
            if len(core[name]) != n:
                raise ValueError("Parameter axis differs")
        ppe = [_number(x, positive=True) for x in core["ppe"]]
        sd = [_number(x) for x in core["ppe_standard_deviation"]]
        falls = [_number(x, positive=True) for x in core["fall_speed_m_s"]]
        covariance = core["ppe_covariance"]
        if (
            any(x < 0 for x in sd)
            or len(covariance) != n
            or any(len(row) != n for row in covariance)
            or any(
                _number(covariance[i][j]) != (sd[i] ** 2 if i == j else 0)
                for i in range(n)
                for j in range(n)
            )
        ):
            raise ValueError(
                "R marginal formula requires exactly declared diagonal PPE covariance"
            )
        quadrature = core["quadrature"]
        if [q["profile"] for q in quadrature] != [p["id"] for p in PROFILES]:
            raise ValueError("Missing/duplicate/reordered physical alternatives")
        tids: dict[str, list[str]] = {}
        for profile, q in zip(PROFILES, quadrature, strict=True):
            values, errors = q["factors"], q["estimated_absolute_error"]
            if (
                len(values) != 1
                or len(values[0]) != n
                or len(errors) != n
                or q["rigorous_error_bound"] is not False
            ):
                raise ValueError("Incomplete physical response axis/diagnostics")
            tids[profile["id"]] = []
            for j in range(n):
                radius = spec["radius"] * profile["radius_multiplier"]
                key = (
                    radius,
                    radius,
                    100000,
                    falls[j],
                    0.12,
                    0.25,
                    profile["wind_speed_m_s"],
                )
                value = _number(values[0][j], positive=True)
                if value > 1 or _number(errors[j]) < 0:
                    raise ValueError("Invalid saved physical factor/error")
                tid = tuples.setdefault(key, f"t{len(tuples) + 1:03d}")
                if tid not in factors:
                    tuple_rows.append([tid, *key])
                elif factors[tid] != value:
                    raise ValueError(
                        "Identical physical tuple has conflicting saved factors"
                    )
                factors[tid] = value
                tids[profile["id"]].append(tid)
        results = core["results"]
        if len(results) != 6 * count or [x["profile"] for x in results] != [
            p for _ in range(count) for p in PROFILE_IDS
        ]:
            raise ValueError("Incomplete/reordered six-profile moment population")
        baseline = results[::6]
        if (
            sum(_integer(x["native_sample_count"]) for x in baseline)
            != spec["included"]
        ):
            raise ValueError("Native sample population does not reconcile")
        previous = -math.inf
        intervals = list(
            zip(
                protocol["age_window_edges_cal_bp"],
                protocol["age_window_edges_cal_bp"][1:],
                strict=False,
            )
        )
        for row in baseline:
            interval = (
                _number(row["younger_cal_bp"]),
                _number(row["older_cal_bp_exclusive"]),
            )
            if interval not in intervals or interval[0] < previous:
                raise ValueError("Foreign/duplicate/overlapping time window")
            previous = interval[1]
        for pi, profile_id in enumerate(PROFILE_IDS):
            cid = code + "." + profile_id
            source_profile = PROFILES[pi]["id"] if pi < 5 else PROFILES[0]["id"]
            for j, taxon in enumerate(taxa):
                tid = tids[source_profile][j]
                scenarios.append(
                    [
                        cid,
                        j + 1,
                        taxon,
                        tid,
                        ppe[j],
                        sd[j] if pi < 5 else 0,
                        factors[tid],
                    ]
                )
            for wi in range(count):
                row, original = results[6 * wi + pi], baseline[wi]
                full = {
                    "younger_cal_bp",
                    "older_cal_bp_exclusive",
                    "native_sample_count",
                    "local_native_sample_support_sha256",
                    "raw_age_bounds_missing",
                    "counts",
                    "panel_count_denominator",
                    "reported_all_pollen_NISP_sum",
                    "direct_pollen_panel_fraction",
                    "profile",
                    "cover",
                    "standard_error",
                    "counting_covariance",
                    "ppe_covariance",
                    "total_covariance",
                }
                reduced = {
                    "profile",
                    "younger_cal_bp",
                    "older_cal_bp_exclusive",
                    "cover",
                    "standard_error",
                }
                if set(row) != (full if pi < 5 else reduced):
                    raise ValueError("Exact full/reduced saved row shape required")
                shared: tuple[str, ...] = ("younger_cal_bp", "older_cal_bp_exclusive")
                if pi < 5:
                    shared += (
                        "native_sample_count",
                        "local_native_sample_support_sha256",
                        "raw_age_bounds_missing",
                        "counts",
                        "panel_count_denominator",
                        "reported_all_pollen_NISP_sum",
                        "direct_pollen_panel_fraction",
                    )
                if any(row[name] != original[name] for name in shared):
                    raise ValueError(
                        "Profile changes original chronology/count/support/denominator"
                    )
                # Reduced zero-PPE rows reuse declared baseline inputs, never missing saved arrays.
                input_row = original if pi == 5 else row
                _identity(input_row["local_native_sample_support_sha256"], 64)
                if _integer(input_row["raw_age_bounds_missing"]) != _integer(
                    input_row["native_sample_count"]
                ):
                    raise ValueError("Missing age-bound scope changed")
                counts = input_row["counts"]
                panel = _integer(input_row["panel_count_denominator"])
                if (
                    len(counts) != 1
                    or len(counts[0]) != n
                    or panel == 0
                    or sum(map(_integer, counts[0])) != panel
                    or _integer(input_row["reported_all_pollen_NISP_sum"]) < panel
                ):
                    raise ValueError(
                        "Exact native panel count/denominator closure differs"
                    )
                wid = wi + 1
                window_ids.append((cid, wid))
                for j, value in enumerate(counts[0], 1):
                    window_rows.append(
                        [
                            cid,
                            wid,
                            row["younger_cal_bp"],
                            row["older_cal_bp_exclusive"],
                            j,
                            value,
                            panel,
                        ]
                    )
                for quantity, source in QUANTITIES.items():
                    if pi == 5 and source not in ("cover", "standard_error"):
                        for i in range(n):
                            for j in range(n) if quantity in MATRICES else [-1]:
                                r_only.add((cid, wid, quantity, i + 1, j + 1))
                        continue
                    cells = row[source]
                    if len(cells) != n or (
                        quantity in MATRICES and any(len(v) != n for v in cells)
                    ):
                        raise ValueError("Missing or malformed saved vector/covariance")
                    for i in range(n):
                        for j in range(n) if quantity in MATRICES else [-1]:
                            value = _number(cells[i][j] if j >= 0 else cells[i])
                            expected[cid, wid, quantity, i + 1, j + 1] = value
                if pi == 5 and row["cover"] != original["cover"]:
                    raise ValueError("Zero-PPE control changes baseline cover")

    if (
        len(tuples),
        len(scenarios),
        len(window_ids),
        len(window_rows),
        len(expected),
    ) != (45, 54, 462, 1002, 8434):
        raise ValueError("Complete Swedish tuple/use/window/moment bijection failed")
    return {
        "files": {
            "tuples.tsv": _tsv(TUPLE_COLUMNS, tuple_rows),
            "scenarios.tsv": _tsv(SCENARIO_COLUMNS, scenarios),
            "windows.tsv": _tsv(WINDOW_COLUMNS, window_rows),
        },
        "expected": expected,
        "r_only": r_only,
        "factors": factors,
        "windows": window_ids,
    }
